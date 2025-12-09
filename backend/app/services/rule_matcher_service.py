from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging
import json
import uuid
from ..models.rule import Rule
from .ollama_service import ollama_service

logger = logging.getLogger(__name__)


class RuleMatcherService:
    """Match AI-generated violations to existing database rules using semantic similarity."""
    
    # Minimum confidence threshold for accepting a match
    CONFIDENCE_THRESHOLD = 0.7
    
    # Cache for violation -> rule_id mappings
    _match_cache: Dict[str, Optional[uuid.UUID]] = {}
    
    async def match_violation_to_rule(
        self,
        violation_description: str,
        category: str,
        severity: str,
        db: Session
    ) -> Optional[uuid.UUID]:
        """
        Use AI to find the best matching rule from the database.
        
        Args:
            violation_description: The violation text from Deep Analysis
            category: "brand", "irdai", or "seo"
            severity: "critical", "high", "medium", or "low"
            db: Database session
            
        Returns:
            UUID of matched rule, or None if no good match found
        """
        # Create cache key
        cache_key = f"{category}:{severity}:{hash(violation_description)}"
        
        # Check cache
        if cache_key in self._match_cache:
            logger.debug(f"Cache hit for violation: {violation_description[:50]}...")
            return self._match_cache[cache_key]
        
        try:
            # Fetch rules from database for this category
            rules = db.query(Rule).filter(Rule.category == category).all()
            
            if not rules:
                logger.warning(f"No rules found for category '{category}'")
                self._match_cache[cache_key] = None
                return None
            
            # Build AI prompt
            prompt = self._build_matching_prompt(
                violation_description, category, severity, rules
            )
            
            # Call Ollama for semantic matching
            response_text = await ollama_service.generate_response(
                prompt=prompt["user_prompt"],
                system_prompt=prompt["system_prompt"]
            )
            
            # Parse AI response
            match_result = self._parse_match_response(response_text, rules)
            
            # Check confidence threshold
            if match_result and match_result["confidence"] >= self.CONFIDENCE_THRESHOLD:
                matched_rule_id = match_result["rule_id"]
                logger.info(
                    f"Matched violation to rule {matched_rule_id} "
                    f"(confidence: {match_result['confidence']:.2f})"
                )
                self._match_cache[cache_key] = matched_rule_id
                return matched_rule_id
            else:
                logger.debug(
                    f"No high-confidence match found for violation "
                    f"(best confidence: {match_result['confidence'] if match_result else 0:.2f})"
                )
                self._match_cache[cache_key] = None
                return None
                
        except Exception as e:
            logger.error(f"Error matching violation to rule: {str(e)}")
            self._match_cache[cache_key] = None
            return None
    
    def _build_matching_prompt(
        self,
        violation_description: str,
        category: str,
        severity: str,
        rules: List[Rule]
    ) -> Dict[str, str]:
        """Build the AI prompt for rule matching."""
        
        # Format rules list for AI
        rules_text = ""
        for idx, rule in enumerate(rules):
            rules_text += f"{idx}. \"{rule.rule_text}\" (Severity: {rule.severity}, Points: {rule.points_deduction})\n"
        
        system_prompt = """You are a compliance rule matching expert. Your task is to find the BEST matching rule for a given violation based on semantic similarity.

Consider:
1. Topic and subject matter similarity
2. Regulatory domain alignment  
3. Violation type match
4. Severity level appropriateness

Respond ONLY with valid JSON, no additional text."""

        user_prompt = f"""Match this violation to the most similar rule:

VIOLATION TO MATCH:
Description: "{violation_description}"
Category: {category}
Severity: {severity}

AVAILABLE RULES IN DATABASE:
{rules_text}

Respond with JSON in this exact format:
{{
  "matched_rule_index": <index number or null>,
  "confidence": <number between 0.0 and 1.0>,
  "reasoning": "<brief explanation>"
}}

If no rule is semantically similar (confidence < 0.7), set matched_rule_index to null."""

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def _parse_match_response(
        self, 
        response_text: str, 
        rules: List[Rule]
    ) -> Optional[Dict]:
        """Parse AI response and extract matched rule."""
        try:
            # Extract JSON from response
            response_text = response_text.strip()
            
            # Handle markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            matched_index = result.get("matched_rule_index")
            confidence = float(result.get("confidence", 0.0))
            
            # Validate index
            if matched_index is None or matched_index < 0 or matched_index >= len(rules):
                return {"rule_id": None, "confidence": confidence}
            
            matched_rule = rules[matched_index]
            
            return {
                "rule_id": matched_rule.id,
                "confidence": confidence,
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Failed to parse AI matching response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            return {"rule_id": None, "confidence": 0.0}


# Singleton instance
rule_matcher_service = RuleMatcherService()
