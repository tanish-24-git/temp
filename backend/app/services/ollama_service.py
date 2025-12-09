import httpx
import json
import asyncio
from typing import Dict, Any, Optional, List
import logging
from ..config import settings

logger = logging.getLogger(__name__)


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
    
    async def generate_rules_from_context(
        self,
        search_results: List[Dict[str, Any]],
        industry: str,
        scope: str
    ) -> List[Dict[str, Any]]:
        """
        Generate structured compliance rules from search results.
        
        Used during onboarding to extract actionable rules from
        regulatory documents and best practices.
        
        Args:
            search_results: List of search results with title, snippet, url
            industry: Industry context (e.g., "insurance")
            scope: Rule scope ("regulatory", "brand", "seo")
            
        Returns:
            List of rule dicts with category, severity, rule_text, keywords
        """
        # Map scope to category
        category_map = {
            "regulatory": "irdai",  # Can be made dynamic per industry
            "brand": "brand",
            "seo": "seo",
            "qualitative": "brand"
        }
        category = category_map.get(scope, "irdai")
        
        # Build prompt for rule extraction
        prompt = self._build_rule_extraction_prompt(
            search_results=search_results,
            industry=industry,
            category=category
        )
        
        system_prompt = (
            "You are a compliance expert specializing in extracting structured rules "
            "from regulatory documents and best practices. Return ONLY valid JSON."
        )
        
        try:
            response = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Parse JSON response
            rules = self._parse_rule_extraction_response(response, category)
            
            # Add source URLs
            for i, rule in enumerate(rules):
                if i < len(search_results):
                    rule["source_url"] = search_results[i].get("url", "")
            
            logger.info(f"Generated {len(rules)} rules for {category} from {len(search_results)} sources")
            
            return rules
            
        except Exception as e:
            logger.error(f"Rule generation failed: {str(e)}")
            return []
    
    def _build_rule_extraction_prompt(
        self,
        search_results: List[Dict],
        industry: str,
        category: str
    ) -> str:
        """Build prompt for extracting rules from search results."""
        # Format search results
        sources = []
        for i, result in enumerate(search_results[:5], 1):  # Limit to top 5
            sources.append(
                f"Source {i}:\n"
                f"Title: {result.get('title', 'N/A')}\n"
                f"Content: {result.get('snippet', 'N/A')}\n"
            )
        
        sources_text = "\n\n".join(sources)
        
        return f"""Extract actionable compliance rules from the following sources for the {industry} industry.

{sources_text}

**Your task:**
Extract 3-5 specific, actionable compliance rules from these sources.

**Output Format (JSON only, no markdown):**
[
  {{
    "rule_text": "Clear, specific compliance requirement",
    "severity": "critical|high|medium|low",
    "keywords": ["keyword1", "keyword2"],
    "points_deduction": -20.0 (for critical) | -10.0 (high) | -5.0 (medium) | -2.0 (low),
    "confidence_score": 0.0-1.0
  }}
]

**Guidelines:**
- Focus on specific, testable requirements
- Extract exact language from sources where possible
- Assign severity based on regulatory importance
- Include relevant keywords for rule matching
- Set high confidence (0.8+) for explicit regulations
- Limit to 5 most important rules

Return ONLY the JSON array, no other text.
"""
    
    def _parse_rule_extraction_response(
        self,
        response: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured rules."""
        try:
            # Clean response (remove markdown if present)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            rules_data = json.loads(response)
            
            # Ensure it's a list
            if isinstance(rules_data, dict):
                rules_data = [rules_data]
            
            # Validate and add category
            validated_rules = []
            for rule in rules_data:
                if "rule_text" in rule:
                    validated_rules.append({
                        "category": category,
                        "rule_text": rule["rule_text"],
                        "severity": rule.get("severity", "medium"),
                        "keywords": rule.get("keywords", []),
                        "points_deduction": rule.get("points_deduction", -5.0),
                        "confidence_score": rule.get("confidence_score", 0.7)
                    })
            
            return validated_rules
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse rule extraction response: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            return []

    async def analyze_line_for_violations(
        self,
        line_content: str,
        line_number: int,
        document_context: str,
        rules: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze a single line for compliance violations.
        
        Used by Deep Compliance Research Mode.
        LLM role is LIMITED to violation detection and context generation.
        Score calculation is handled by deterministic Python code.
        
        Args:
            line_content: The text of the line to analyze
            line_number: Position in document
            document_context: Document title for context
            rules: List of rule dicts with id, category, rule_text, severity, keywords
        
        Returns:
            dict with 'relevance_context' and 'violations' list
        """
        from .prompts.deep_analysis_prompt import (
            build_deep_analysis_prompt,
            parse_line_analysis_response
        )
        
        # Build prompts
        prompts = build_deep_analysis_prompt(
            line_content=line_content,
            line_number=line_number,
            document_title=document_context,
            rules=rules
        )
        
        try:
            # Call LLM
            response_text = await self.generate_response(
                prompt=prompts["user_prompt"],
                system_prompt=prompts["system_prompt"]
            )
            
            # Parse response
            result = parse_line_analysis_response(response_text)
            
            logger.debug(f"Line {line_number} analysis: {len(result.get('violations', []))} violations found")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing line {line_number}: {str(e)}")
            return {
                "relevance_context": "Error during analysis",
                "violations": []
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


# Singleton instance
ollama_service = OllamaService()
