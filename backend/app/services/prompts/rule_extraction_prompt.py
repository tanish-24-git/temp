"""
Ollama prompt templates for Phase 2 rule extraction.

This module contains structured prompts for extracting compliance rules
from regulatory documents using Ollama LLM.
"""

RULE_EXTRACTION_SYSTEM_PROMPT = """You are a compliance rule extractor for IRDAI (Insurance Regulatory and Development Authority of India) insurance marketing regulations.

Your task is to analyze provided document text and extract compliance rules in a structured JSON format.

Rules to follow:
1. Extract 5-15 rules maximum from the document
2. Focus on actionable guidelines, prohibitions, and requirements
3. Categorize each rule as: "irdai", "brand", or "seo"
4. Assign severity: "critical", "high", "medium", or "low"
5. Extract 3-5 relevant keywords that trigger this rule
6. Optionally provide a regex pattern for pattern matching
7. Assign appropriate point deductions based on severity:
   - critical: -20 to -15 points
   - high: -15 to -10 points
   - medium: -10 to -5 points
   - low: -5 to -2 points

Output ONLY valid JSON in this exact format (no extra text, comments, or explanations):
[
  {
    "category": "irdai",
    "rule_text": "Clear, actionable description of the rule",
    "severity": "critical",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "pattern": "optional_regex_pattern",
    "points_deduction": -20.00
  },
  {
    "category": "brand",
    "rule_text": "Another rule description",
    "severity": "high",
    "keywords": ["word1", "word2", "word3"],
    "pattern": null,
    "points_deduction": -10.00
  }
]

IMPORTANT:
- Output ONLY the JSON array, nothing else
- Ensure valid JSON syntax (proper quotes, commas, brackets)
- All numeric values must be negative decimals
- Keywords array must have 3-5 items
- Pattern can be null if not applicable
"""

RULE_EXTRACTION_USER_PROMPT_TEMPLATE = """Analyze the following regulatory document and extract compliance rules:

Document Title: {document_title}
Document Type: {document_type}
Content Length: {content_length} characters

--- DOCUMENT TEXT START ---
{document_content}
--- DOCUMENT TEXT END ---

Extract 5-15 compliance rules from this document in the specified JSON format.
Focus on the most important and actionable rules.
Output ONLY the JSON array, no additional text."""


def build_rule_extraction_prompt(
    document_title: str,
    document_type: str,
    document_content: str
) -> dict:
    """
    Build the complete prompt for rule extraction.

    Args:
        document_title: Title/filename of the document
        document_type: Type of document (pdf, docx, html, etc.)
        document_content: Parsed text content of the document

    Returns:
        dict with 'system_prompt' and 'user_prompt' keys
    """
    # Truncate content if too long (max 10000 chars for rule extraction)
    max_content_length = 10000
    truncated_content = document_content[:max_content_length]
    if len(document_content) > max_content_length:
        truncated_content += "\n\n[... content truncated for analysis ...]"

    user_prompt = RULE_EXTRACTION_USER_PROMPT_TEMPLATE.format(
        document_title=document_title,
        document_type=document_type,
        content_length=len(document_content),
        document_content=truncated_content
    )

    return {
        "system_prompt": RULE_EXTRACTION_SYSTEM_PROMPT,
        "user_prompt": user_prompt
    }


# Validation schemas for extracted rules
VALID_CATEGORIES = {"irdai", "brand", "seo"}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}

SEVERITY_POINT_RANGES = {
    "critical": (-20.0, -15.0),
    "high": (-15.0, -10.0),
    "medium": (-10.0, -5.0),
    "low": (-5.0, -2.0)
}


def validate_extracted_rule(rule: dict) -> tuple[bool, str]:
    """
    Validate a single extracted rule.

    Args:
        rule: Dict containing extracted rule data

    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # Check required fields
    required_fields = ["category", "rule_text", "severity", "keywords", "points_deduction"]
    for field in required_fields:
        if field not in rule:
            return False, f"Missing required field: {field}"

    # Validate category
    if rule["category"] not in VALID_CATEGORIES:
        return False, f"Invalid category: {rule['category']}. Must be one of {VALID_CATEGORIES}"

    # Validate severity
    if rule["severity"] not in VALID_SEVERITIES:
        return False, f"Invalid severity: {rule['severity']}. Must be one of {VALID_SEVERITIES}"

    # Validate rule_text
    if not isinstance(rule["rule_text"], str) or len(rule["rule_text"]) < 10:
        return False, "rule_text must be a string with at least 10 characters"

    # Validate keywords
    if not isinstance(rule["keywords"], list) or len(rule["keywords"]) < 1:
        return False, "keywords must be a list with at least 1 item"

    # Validate points_deduction
    try:
        points = float(rule["points_deduction"])
        if points > 0:
            return False, "points_deduction must be negative"

        # Check if points are in expected range for severity
        severity = rule["severity"]
        min_points, max_points = SEVERITY_POINT_RANGES[severity]
        if not (min_points <= points <= max_points):
            # Auto-adjust if slightly out of range
            rule["points_deduction"] = max(min_points, min(max_points, points))

    except (ValueError, TypeError):
        return False, "points_deduction must be a valid number"

    # Validate pattern (optional)
    if "pattern" in rule and rule["pattern"] is not None:
        if not isinstance(rule["pattern"], str):
            return False, "pattern must be a string or null"

    return True, ""
