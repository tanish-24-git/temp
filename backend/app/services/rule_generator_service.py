"""
Rule Generator Service for Phase 2.

This service handles dynamic rule generation from uploaded compliance documents.
It parses documents, sends them to Ollama for rule extraction, validates the output,
and stores the rules in the database.
"""

import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .ollama_service import ollama_service
from .content_parser import content_parser
from .prompts.rule_extraction_prompt import (
    build_rule_extraction_prompt,
    validate_extracted_rule,
    VALID_CATEGORIES,
    VALID_SEVERITIES
)
from ..models.rule import Rule
from ..models.user import User

logger = logging.getLogger(__name__)


class RuleGeneratorService:
    """Service for generating compliance rules from documents using LLM."""

    def __init__(self):
        self.ollama = ollama_service
        self.parser = content_parser

    async def generate_rules_from_document(
        self,
        file_path: str,
        content_type: str,
        document_title: str,
        created_by_user_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate compliance rules from an uploaded document.

        Args:
            file_path: Path to the uploaded document file
            content_type: Type of document (html, markdown, pdf, docx)
            document_title: Title/name of the document
            created_by_user_id: UUID of the super admin creating these rules
            db: Database session

        Returns:
            dict: {
                "success": bool,
                "rules_created": int,
                "rules_failed": int,
                "rules": List[dict],  # List of created rule data
                "errors": List[str]   # List of error messages if any
            }
        """
        logger.info(f"Starting rule generation from document: {document_title}")

        result = {
            "success": False,
            "rules_created": 0,
            "rules_failed": 0,
            "rules": [],
            "errors": []
        }

        try:
            # Step 1: Verify user is super_admin
            user = db.query(User).filter(User.id == created_by_user_id).first()
            if not user or user.role != "super_admin":
                result["errors"].append("Only super_admin users can generate rules")
                return result

            # Step 2: Parse document content
            logger.info(f"Parsing {content_type} document...")
            try:
                parsed_content = await self.parser.parse_content(file_path, content_type)
            except Exception as e:
                result["errors"].append(f"Failed to parse document: {str(e)}")
                return result

            if not parsed_content or len(parsed_content) < 100:
                result["errors"].append("Document content too short or empty")
                return result

            logger.info(f"Parsed content length: {len(parsed_content)} characters")

            # Step 3: Build prompt for rule extraction
            prompt_data = build_rule_extraction_prompt(
                document_title=document_title,
                document_type=content_type,
                document_content=parsed_content
            )

            # Step 4: Call Ollama for rule extraction
            logger.info("Sending document to Ollama for rule extraction...")
            try:
                ollama_response = await self.ollama.generate_response(
                    prompt=prompt_data["user_prompt"],
                    system_prompt=prompt_data["system_prompt"]
                )
            except Exception as e:
                result["errors"].append(f"Ollama service error: {str(e)}")
                return result

            # Step 5: Parse and validate JSON response
            logger.info("Parsing Ollama response...")
            extracted_rules = self._parse_ollama_response(ollama_response)

            if not extracted_rules:
                result["errors"].append("No rules extracted from document. Response may be invalid JSON.")
                return result

            logger.info(f"Extracted {len(extracted_rules)} rules from LLM response")

            # Step 6: Validate and insert rules into database
            for rule_data in extracted_rules:
                try:
                    # Validate rule
                    is_valid, error_msg = validate_extracted_rule(rule_data)
                    if not is_valid:
                        logger.warning(f"Invalid rule: {error_msg}")
                        result["rules_failed"] += 1
                        result["errors"].append(f"Invalid rule: {error_msg}")
                        continue

                    # Create rule in database
                    new_rule = Rule(
                        category=rule_data["category"],
                        rule_text=rule_data["rule_text"],
                        severity=rule_data["severity"],
                        keywords=rule_data["keywords"],
                        pattern=rule_data.get("pattern"),
                        points_deduction=float(rule_data["points_deduction"]),
                        is_active=True,
                        created_by=created_by_user_id
                    )

                    db.add(new_rule)
                    db.flush()  # Get the ID without committing

                    result["rules_created"] += 1
                    result["rules"].append({
                        "id": str(new_rule.id),
                        "category": new_rule.category,
                        "rule_text": new_rule.rule_text,
                        "severity": new_rule.severity,
                        "points_deduction": float(new_rule.points_deduction)
                    })

                    logger.info(f"Created rule: {new_rule.category} - {new_rule.severity}")

                except SQLAlchemyError as e:
                    logger.error(f"Database error creating rule: {str(e)}")
                    result["rules_failed"] += 1
                    result["errors"].append(f"Database error: {str(e)}")
                    db.rollback()
                except Exception as e:
                    logger.error(f"Unexpected error creating rule: {str(e)}")
                    result["rules_failed"] += 1
                    result["errors"].append(f"Unexpected error: {str(e)}")

            # Step 7: Commit all rules
            try:
                db.commit()
                result["success"] = result["rules_created"] > 0
                logger.info(
                    f"Rule generation complete: {result['rules_created']} created, "
                    f"{result['rules_failed']} failed"
                )
            except SQLAlchemyError as e:
                db.rollback()
                result["success"] = False
                result["errors"].append(f"Failed to commit rules: {str(e)}")
                logger.error(f"Failed to commit rules: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Unexpected error in rule generation: {str(e)}")
            result["errors"].append(f"Unexpected error: {str(e)}")
            return result

    def _parse_ollama_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse Ollama response and extract JSON array of rules.

        Args:
            response: Raw response string from Ollama

        Returns:
            List of rule dictionaries
        """
        try:
            # Try direct JSON parsing first
            rules = json.loads(response)
            if isinstance(rules, list):
                return rules
            elif isinstance(rules, dict) and "rules" in rules:
                return rules["rules"]
            else:
                logger.warning("Response is not a list or dict with 'rules' key")
                return []

        except json.JSONDecodeError:
            # Try to extract JSON from text with markdown or other formatting
            logger.info("Direct JSON parsing failed, attempting to extract JSON...")

            # Look for JSON array pattern
            import re
            json_pattern = r'\[\s*\{.*?\}\s*\]'
            match = re.search(json_pattern, response, re.DOTALL)

            if match:
                try:
                    rules = json.loads(match.group(0))
                    if isinstance(rules, list):
                        return rules
                except json.JSONDecodeError:
                    pass

            logger.error("Failed to extract valid JSON from Ollama response")
            logger.debug(f"Response preview: {response[:500]}")
            return []

    async def regenerate_rule(
        self,
        rule_id: uuid.UUID,
        new_rule_data: Dict[str, Any],
        updated_by_user_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """
        Update an existing rule (manual edit by super admin).

        Args:
            rule_id: UUID of the rule to update
            new_rule_data: Dict with updated rule fields
            updated_by_user_id: UUID of the super admin making the update
            db: Database session

        Returns:
            dict: {"success": bool, "rule": dict, "error": str}
        """
        try:
            # Verify user is super_admin
            user = db.query(User).filter(User.id == updated_by_user_id).first()
            if not user or user.role != "super_admin":
                return {"success": False, "error": "Only super_admin users can update rules"}

            # Find the rule
            rule = db.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return {"success": False, "error": f"Rule with ID {rule_id} not found"}

            # Update allowed fields
            updateable_fields = [
                "rule_text", "severity", "category", "keywords",
                "pattern", "points_deduction", "is_active"
            ]

            for field in updateable_fields:
                if field in new_rule_data:
                    setattr(rule, field, new_rule_data[field])

            db.commit()
            db.refresh(rule)

            return {
                "success": True,
                "rule": {
                    "id": str(rule.id),
                    "category": rule.category,
                    "rule_text": rule.rule_text,
                    "severity": rule.severity,
                    "points_deduction": float(rule.points_deduction),
                    "is_active": rule.is_active
                }
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating rule: {str(e)}")
            return {"success": False, "error": str(e)}

    async def delete_rule(
        self,
        rule_id: uuid.UUID,
        deleted_by_user_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """
        Delete a rule (soft delete by setting is_active=False).

        Args:
            rule_id: UUID of the rule to delete
            deleted_by_user_id: UUID of the super admin deleting the rule
            db: Database session

        Returns:
            dict: {"success": bool, "error": str}
        """
        try:
            # Verify user is super_admin
            user = db.query(User).filter(User.id == deleted_by_user_id).first()
            if not user or user.role != "super_admin":
                return {"success": False, "error": "Only super_admin users can delete rules"}

            # Find and soft delete the rule
            rule = db.query(Rule).filter(Rule.id == rule_id).first()
            if not rule:
                return {"success": False, "error": f"Rule with ID {rule_id} not found"}

            rule.is_active = False
            db.commit()

            return {"success": True}

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting rule: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
rule_generator_service = RuleGeneratorService()
