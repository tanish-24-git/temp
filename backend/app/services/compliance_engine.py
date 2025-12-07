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
from .content_parser import chunk_text

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
        Analyze a submission for compliance.

        Workflow:
        1. Load submission
        2. Load active rules
        3. Build compliance prompt
        4. Send to Ollama
        5. Parse response
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

            # 2. Load active rules
            rules = ComplianceEngine._load_active_rules(db)

            # 3. Build prompt
            prompt = ComplianceEngine._build_compliance_prompt(
                content=submission.original_content,
                rules=rules
            )

            # 4. Send to Ollama
            logger.info("Sending to Ollama for analysis...")
            
            # ==============================================
            # FEATURE 2: PER-CHUNK ANALYSIS
            # Runs the LLM on each chunk independently
            # WHY: Long documents exceed LLM context limits; chunking ensures
            #      all content is analyzed without truncation
            # ==============================================
            
            # Create chunks from content
            chunks = chunk_text(submission.original_content, chunk_size=600, overlap=100)
            logger.info(f"Created {len(chunks)} chunks for analysis")
            
            # Build rules text once
            rules_text = ComplianceEngine._format_rules_for_llm(rules)
            
            # Collect all violations from all chunks
            all_violations = []
            
            for chunk in chunks:
                logger.info(f"Analyzing chunk {chunk['index']} (chars {chunk['start']}-{chunk['end']})")
                
                # Build prompt for this chunk
                prompt = ollama_service.build_prompt_for_chunk(chunk["text"], rules_text)
                
                # Get and validate LLM response
                llm_resp = await ollama_service.generate_and_validate_llm_response(prompt)
                
                # Process violations from this chunk
                chunk_violations = llm_resp.get("violations", [])
                
                for vdict in chunk_violations:
                    # ==============================================
                    # FEATURE 7: OFFSET NORMALIZATION
                    # Converts chunk offsets to global document offsets
                    # WHY: Violations need to reference original document positions
                    #      not chunk-relative positions
                    # ==============================================
                    if vdict.get("start_offset") is not None:
                        vdict["start_offset"] = chunk["start"] + vdict["start_offset"]
                    if vdict.get("end_offset") is not None:
                        vdict["end_offset"] = chunk["start"] + vdict["end_offset"]
                    
                    # ==============================================
                    # FEATURE 8: EXPLAINABILITY-READY OUTPUT
                    # Prepares standardized output for future UI and audits
                    # WHY: Downstream systems need chunk context, priority scores,
                    #      and normalized offsets for proper display and sorting
                    # ==============================================
                    vdict["chunk_index"] = chunk["index"]
                    
                    # Import compute_priority here to avoid circular import
                    from .scoring_service import compute_priority
                    vdict["priority"] = compute_priority(vdict)
                    
                    all_violations.append(vdict)
            
            logger.info(f"Total violations found across all chunks: {len(all_violations)}")
            
            # Create analysis result
            analysis_result = {
                "violations": all_violations,
                "overall_assessment": f"Analyzed {len(chunks)} chunks, found {len(all_violations)} violations."
            }

            # 6. Calculate scores (Phase 2: Pass DB session for rule-based scoring)
            scores = scoring_service.calculate_scores(analysis_result["violations"], db=db)

            # 7. Store results
            compliance_check = ComplianceCheck(
                submission_id=submission.id,
                overall_score=scores["overall"],
                irdai_score=scores["irdai"],
                brand_score=scores["brand"],
                seo_score=scores["seo"],
                status=scores["status"],
                grade=scores["grade"],
                ai_summary=analysis_result.get("overall_assessment", "")
            )
            db.add(compliance_check)
            db.flush()

            # Store violations
            for violation_data in analysis_result["violations"]:
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
            submission.status = "completed"
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
    def _format_rules_for_llm(rules: Dict[str, List[Rule]]) -> str:
        """Format rules into text for LLM prompts (used in per-chunk analysis)."""
        rules_sections = []

        # IRDAI Rules
        if rules["irdai"]:
            irdai_text = "**IRDAI Regulations:**\n"
            for rule in rules["irdai"]:
                irdai_text += f"- [ID: {rule.id}] {rule.rule_text} (Severity: {rule.severity})\n"
            rules_sections.append(irdai_text)

        # Brand Rules
        if rules["brand"]:
            brand_text = "**Brand Guidelines:**\n"
            for rule in rules["brand"]:
                brand_text += f"- [ID: {rule.id}] {rule.rule_text} (Severity: {rule.severity})\n"
            rules_sections.append(brand_text)

        # SEO Rules
        if rules["seo"]:
            seo_text = "**SEO Requirements:**\n"
            for rule in rules["seo"]:
                seo_text += f"- [ID: {rule.id}] {rule.rule_text} (Severity: {rule.severity})\n"
            rules_sections.append(seo_text)

        return "\n".join(rules_sections)

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
