from typing import Dict, List, Any
import json
import logging
from sqlalchemy.orm import Session
from ..models.rule import Rule
from ..models.submission import Submission
from ..models.compliance_check import ComplianceCheck
from ..models.violation import Violation
from .ollama_service import ollama_service
from .scoring_service import scoring_service

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """Core compliance checking engine."""

    COMPLIANCE_PROMPT_TEMPLATE = """
You are a compliance expert for insurance marketing content.

Analyze the following content against these compliance rules:

{rules_section}

**Content to Analyze:**
{content}

**Output Format (JSON only, no other text):**
{{
  "violations": [
    {{
      "category": "irdai|brand|seo",
      "severity": "critical|high|medium|low",
      "rule_id": "rule identifier from above",
      "description": "Brief violation description",
      "location": "Line/section reference",
      "current_text": "Problematic text excerpt (max 200 chars)",
      "suggested_fix": "Corrected version",
      "auto_fixable": true/false
    }}
  ],
  "overall_assessment": "Brief 10 sentence summary of compliance status",
  "key_issues": ["issue 1", "issue 2", "issue 3"]
}}

**Important:**
- Return ONLY valid JSON, no markdown or other text
- Be specific about violations
- Provide actionable suggestions
- Reference actual rule IDs
"""

    @staticmethod
    async def analyze_submission(submission_id: str, db: Session) -> ComplianceCheck:
        """
        Analyze a submission for compliance (CHUNK-AWARE).

        Workflow:
        1. Load submission
        2. Get chunks via ContentRetrievalService (backward compatible)
        3. Load active rules
        4. Process each chunk through Ollama
        5. Aggregate violations with chunk references
        6. Calculate scores
        7. Store results
        """
        try:
            # 1. Load submission
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")

            logger.info(f"Analyzing submission: {submission.title}")

            # Update status
            submission.status = "analyzing"
            db.commit()

            # 2. Get chunks via ContentRetrievalService (handles both chunked and legacy)
            from .content_retrieval_service import ContentRetrievalService
            content_service = ContentRetrievalService(db)
            chunks = content_service.get_analyzable_content(submission_id)
            
            logger.info(f"Processing {len(chunks)} chunk(s) for analysis")

            # 3. Load active rules
            rules = ComplianceEngine._load_active_rules(db)

            # 4. Process each chunk
            all_violations = []
            
            for chunk in chunks:
                logger.info(f"Analyzing chunk {chunk.chunk_index + 1}/{len(chunks)}")
                
                # Build prompt with chunk content
                prompt = ComplianceEngine._build_compliance_prompt(
                    content=chunk.text,
                    rules=rules
                )

                # Send to Ollama
                response = await ollama_service.generate_response(
                    prompt=prompt,
                    system_prompt="You are a compliance expert. Return ONLY valid JSON."
                )

                # Parse response
                analysis_result = ComplianceEngine._parse_ollama_response(response)
                
                # Attach chunk reference to each violation
                for violation_data in analysis_result["violations"]:
                    # Build location string with chunk reference
                    location = f"chunk:{chunk.id}"
                    
                    # Add metadata info if available
                    if chunk.metadata.get("page_number"):
                        location += f":page:{chunk.metadata['page_number']}"
                    elif chunk.metadata.get("char_offset_start") is not None:
                        location += f":offset:{chunk.metadata['char_offset_start']}"
                    
                    violation_data["location"] = location
                    violation_data["chunk_index"] = chunk.chunk_index
                    
                all_violations.extend(analysis_result["violations"])

            # 6. Calculate scores (Phase 2: Pass DB session for rule-based scoring)
            scores = scoring_service.calculate_scores(all_violations, db=db)

            # 7. Store results
            compliance_check = ComplianceCheck(
                submission_id=submission.id,
                overall_score=scores["overall"],
                irdai_score=scores["irdai"],
                brand_score=scores["brand"],
                seo_score=scores["seo"],
                status=scores["status"],
                grade=scores["grade"],
                ai_summary=f"Analyzed {len(chunks)} chunk(s). {analysis_result.get('overall_assessment', '')}"
            )
            db.add(compliance_check)
            db.flush()

            # Store violations
            for violation_data in all_violations:
                # Find rule by ID (if provided)
                rule = None
                if violation_data.get("rule_id"):
                    try:
                        rule = db.query(Rule).filter(Rule.id == violation_data.get("rule_id")).first()
                    except:
                        pass

                violation = Violation(
                    check_id=compliance_check.id,
                    rule_id=rule.id if rule else None,
                    severity=violation_data["severity"],
                    category=violation_data["category"],
                    description=violation_data["description"],
                    location=violation_data.get("location", ""),
                    current_text=violation_data.get("current_text", ""),
                    suggested_fix=violation_data.get("suggested_fix", ""),
                    is_auto_fixable=violation_data.get("auto_fixable", False)
                )
                db.add(violation)

            # Update submission status
            submission.status = "analyzed"
            db.commit()

            logger.info(f"Analysis complete. Score: {scores['overall']}, Status: {scores['status']}")

            return compliance_check

        except Exception as e:
            logger.error(f"Error analyzing submission: {str(e)}")
            if submission:
                submission.status = "failed"
                db.commit()
            raise

    @staticmethod
    def _load_active_rules(db: Session) -> Dict[str, List[Rule]]:
        """Load top 3 active rules per category by severity."""
        rules = db.query(Rule).filter(Rule.is_active == True).all()

        # Sort by severity weight (critical > high > medium > low)
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        rules.sort(key=lambda r: severity_order.get(r.severity, 0), reverse=True)

        grouped = {
            "irdai": [],
            "brand": [],
            "seo": []
        }

        for rule in rules:
            if rule.category in grouped and len(grouped[rule.category]) < 3:
                grouped[rule.category].append(rule)

        return grouped

    @staticmethod
    def _build_compliance_prompt(content: str, rules: Dict[str, List[Rule]]) -> str:
        """Build the compliance checking prompt."""
        rules_sections = []

        # IRDAI Rules
        if rules["irdai"]:
            irdai_text = "**IRDAI Regulations:**\n"
            for rule in rules["irdai"]:
                irdai_text += f"- [ID: {rule.id}] {rule.rule_text} (Severity: {rule.severity})\n"
                logger.info(rule)
            rules_sections.append(irdai_text)

        # Brand Rules
        if rules["brand"]:
            brand_text = "**Brand Guidelines:**\n"
            for rule in rules["brand"]:
                brand_text += f"- [ID: {rule.id}] {rule.rule_text} (Severity: {rule.severity})\n"
                logger.info(rule)

            rules_sections.append(brand_text)

        # SEO Rules
        if rules["seo"]:
            seo_text = "**SEO Requirements:**\n"
            for rule in rules["seo"]:
                seo_text += f"- [ID: {rule.id}] {rule.rule_text} (Severity: {rule.severity})\n"
                logger.info(rule)
            rules_sections.append(seo_text)

        rules_section = "\n".join(rules_sections)

        # Truncate content if too long (reduced to 2000 chars for faster eval)
        truncated_content = content[:2000] if len(content) > 2000 else content

        return ComplianceEngine.COMPLIANCE_PROMPT_TEMPLATE.format(
            rules_section=rules_section,
            content=truncated_content
        )

    @staticmethod
    def _parse_ollama_response(response: str) -> Dict[str, Any]:
        """Parse Ollama's JSON response."""
        try:
            # Try to extract JSON if wrapped in markdown
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            result = json.loads(response)

            # Validate structure
            if "violations" not in result:
                result["violations"] = []
            if "overall_assessment" not in result:
                result["overall_assessment"] = "Analysis completed."

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response as JSON: {str(e)}")
            logger.error(f"Response: {response[:500]}")

            # Return empty result
            return {
                "violations": [],
                "overall_assessment": "Unable to parse AI response.",
                "key_issues": ["AI response parsing error"]
            }


compliance_engine = ComplianceEngine()
