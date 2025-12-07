import httpx
import json
import asyncio
from typing import Dict, Any, Optional, List
import logging
from pydantic import BaseModel
from ..config import settings

logger = logging.getLogger(__name__)


# ==============================================
# FEATURE 3: DETERMINISTIC LLM PROMPT TEMPLATE
# Ensures predictable JSON output from the model
# WHY: Standardized prompts produce more consistent, parseable responses
#      and reduce LLM hallucination/format errors
# ==============================================
LLM_PROMPT_TEMPLATE = """
You are a compliance assistant analyzing marketing content.

Analyze this chunk of content against the provided compliance rules.

Return ONLY JSON formatted exactly like this:
{{
  "violations": [
    {{
      "rule_id": "optional rule identifier",
      "message": "description of the violation",
      "confidence": 0.85,
      "severity": "critical|high|medium|low",
      "category": "irdai|brand|seo",
      "start_offset": 0,
      "end_offset": 100
    }}
  ]
}}

Rules:
{rules_text}

Chunk:
"""{chunk_text}"""

Return ONLY the JSON object, no other text.
"""


# ==============================================
# FEATURE 4: JSON SCHEMA VALIDATION USING PYDANTIC
# Ensures LLM response fits expected schema
# WHY: Type-safe validation prevents downstream errors from malformed LLM output
# ==============================================
class LLMViolation(BaseModel):
    """Pydantic model for a single violation from LLM."""
    rule_id: Optional[str] = None
    message: str
    confidence: float
    severity: Optional[str] = "medium"
    category: Optional[str] = "irdai"
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None


class LLMResponse(BaseModel):
    """Pydantic model for complete LLM response."""
    violations: List[LLMViolation]


class OllamaService:
    """Service for integrating with Ollama LLM."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
        self.max_retries = settings.ollama_max_retries
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.use_chat_api = True  # Try chat API first, fallback to generate

    async def health_check(self) -> bool:
        """Check if Ollama service is available and model is loaded."""
        try:
            url = f"{self.base_url}/api/tags"
            response = await self.client.get(url, timeout=5)

            if response.status_code != 200:
                return False

            tags_data = response.json()
            models = [model.get("name", "") for model in tags_data.get("models", [])]
            model_available = any(self.model in model for model in models)

            if not model_available:
                logger.warning(f"Model '{self.model}' not found. Available: {models}")
                return False

            logger.info(f"✅ Ollama service available with model '{self.model}'")
            return True

        except Exception as e:
            logger.warning(f"Ollama health check failed: {str(e)}")
            return False

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate response from Ollama with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                if self.use_chat_api:
                    messages = self._build_chat_messages(prompt, system_prompt, context)
                    response = await self._call_ollama_chat(messages)
                else:
                    full_prompt = self._build_prompt(prompt, system_prompt, context)
                    response = await self._call_ollama_generate(full_prompt)

                return response

            except Exception as e:
                logger.warning(f"Ollama attempt {attempt + 1} failed: {str(e)}")

                if attempt == self.max_retries - 1:
                    logger.error("All Ollama attempts failed. Returning fallback response.")
                    return self._get_fallback_response(prompt, context)

                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)

    def _build_chat_messages(
        self,
        user_prompt: str,
        system_prompt: str = None,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """Build messages array for Ollama chat API."""
        messages = []

        # Add system message
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add context as system message
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "system",
                "content": f"Context:\n{context_str}"
            })

        # Add user message
        messages.append({"role": "user", "content": user_prompt})

        return messages

    def _build_prompt(
        self,
        prompt: str,
        system_prompt: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Build single prompt string for generate API."""
        parts = []

        if system_prompt:
            parts.append(f"System: {system_prompt}")

        if context:
            parts.append(f"Context: {json.dumps(context)}")

        parts.append(f"User: {prompt}")

        return "\n\n".join(parts)

    async def _call_ollama_chat(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama chat API."""
        url = f"{self.base_url}/api/chat"
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "").strip()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404 and self.use_chat_api:
                # Fallback to generate API
                logger.info("Chat API not available, falling back to generate API")
                self.use_chat_api = False
                prompt = self._build_prompt(messages[-1]["content"])
                return await self._call_ollama_generate(prompt)
            raise

    async def _call_ollama_generate(self, prompt: str) -> str:
        """Call Ollama generate API."""
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        response = await self.client.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()

    def _get_fallback_response(self, prompt: str, context: Dict[str, Any]) -> str:
        """Fallback response when Ollama is unavailable."""
        return json.dumps({
            "violations": [],
            "overall_assessment": "AI analysis service temporarily unavailable. Please try again later.",
            "key_issues": ["AI service unavailable"]
        })

    # ==============================================
    # FEATURE 3 (CONTINUED): PROMPT BUILDING METHOD
    # Build prompts using the deterministic template
    # ==============================================
    def build_prompt_for_chunk(self, chunk_text: str, rules_text: str) -> str:
        """Build a standardized prompt for a single chunk."""
        return LLM_PROMPT_TEMPLATE.format(
            chunk_text=chunk_text,
            rules_text=rules_text
        )

    # ==============================================
    # FEATURE 4 (CONTINUED): VALIDATION METHOD
    # Generate and validate LLM response using Pydantic
    # ==============================================
    async def generate_and_validate_llm_response(self, prompt: str) -> Dict[str, Any]:
        """Generate LLM response and validate it against Pydantic schema."""
        try:
            # Get raw response from LLM
            raw_response = await self.generate_response(
                prompt=prompt,
                system_prompt="You are a compliance expert. Return ONLY valid JSON."
            )
            
            # Try to parse as JSON
            try:
                response_dict = json.loads(raw_response)
                # Validate with Pydantic
                validated = LLMResponse(**response_dict)
                return validated.model_dump()
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"LLM response validation failed: {str(e)}")
                # Use fallback parser
                return heuristic_parse(raw_response)
                
        except Exception as e:
            logger.error(f"Error in generate_and_validate_llm_response: {str(e)}")
            return {"violations": []}


# ==============================================
# FEATURE 5: FALLBACK PARSER
# Used when LLM output is broken or invalid JSON
# WHY: Graceful degradation ensures system doesn't crash on bad LLM output
#      while still attempting to extract useful information
# ==============================================
def heuristic_parse(resp_text: str) -> Dict[str, Any]:
    """Parse LLM response using heuristics when JSON parsing fails."""
    text = resp_text.lower()
    violations = []
    
    # Check for common compliance red flags
    if "guaranteed" in text or "100%" in text:
        violations.append({
            "rule_id": None,
            "message": "Possible guaranteed return claim detected",
            "confidence": 0.4,
            "severity": "high",
            "category": "irdai"
        })
    
    if "risk-free" in text or "no risk" in text:
        violations.append({
            "rule_id": None,
            "message": "Possible risk-free claim detected",
            "confidence": 0.35,
            "severity": "high",
            "category": "irdai"
        })
    
    return {"violations": violations}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


# Singleton instance
ollama_service = OllamaService()
