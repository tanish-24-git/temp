"""
Deep Analysis Prompts for Ollama LLM

These prompts are used for line-by-line compliance analysis.
The LLM's role is LIMITED to:
1. Identifying potential rule violations
2. Generating relevance context

Score calculation is handled by deterministic Python code.
"""

DEEP_ANALYSIS_SYSTEM_PROMPT = """You are a compliance analysis agent for IRDAI (Insurance Regulatory and Development Authority of India) marketing content.

YOUR TASK: Analyze a single line of text and identify any compliance rule violations.

OUTPUT REQUIREMENTS:
1. Determine if any of the provided rules are violated
2. Explain the relevance/context of this line
3. Output ONLY valid JSON - no other text

OUTPUT FORMAT (strict JSON):
{
    "relevance_context": "Brief description of what this line is about and why it matters for compliance",
    "violations": [
        {
            "rule_id": "the-rule-uuid-that-was-violated",
            "rule_text": "the full text of the violated rule",
            "category": "irdai|brand|seo",
            "severity": "critical|high|medium|low",
            "reason": "specific explanation of HOW this line violates the rule"
        }
    ]
}

RULES:
1. If no violations are found, return an empty violations array: {"relevance_context": "...", "violations": []}
2. Be precise - only flag actual violations, not potential ones
3. The relevance_context should explain what the line is about (e.g., "pricing claim", "benefit description", "disclaimer")
4. Do NOT calculate scores - only identify violations
5. Output ONLY the JSON object, nothing else before or after
"""

DEEP_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze this line from an insurance marketing document:

DOCUMENT CONTEXT: {document_title}
LINE NUMBER: {line_number}
LINE CONTENT: "{line_content}"

ACTIVE COMPLIANCE RULES TO CHECK:
{rules_list}

Analyze the line and output JSON with violations (if any) and relevance context.
"""


def build_deep_analysis_prompt(
    line_content: str,
    line_number: int,
    document_title: str,
    rules: list
) -> dict:
    """
    Build prompts for line-by-line analysis.
    
    Args:
        line_content: The text of the line to analyze
        line_number: Position in document
        document_title: Title for context
        rules: List of rule dicts with id, category, rule_text, severity, keywords
    
    Returns:
        dict with 'system_prompt' and 'user_prompt'
    """
    # Format rules for the prompt
    rules_formatted = []
    for i, rule in enumerate(rules, 1):
        rules_formatted.append(
            f"{i}. [ID: {rule['id']}] [{rule['category'].upper()}] [{rule['severity'].upper()}]\n"
            f"   Rule: {rule['rule_text']}\n"
            f"   Keywords: {', '.join(rule.get('keywords', []))}"
        )
    
    rules_list = "\n\n".join(rules_formatted) if rules_formatted else "No active rules configured."
    
    user_prompt = DEEP_ANALYSIS_USER_PROMPT_TEMPLATE.format(
        document_title=document_title,
        line_number=line_number,
        line_content=line_content,
        rules_list=rules_list
    )
    
    return {
        "system_prompt": DEEP_ANALYSIS_SYSTEM_PROMPT,
        "user_prompt": user_prompt
    }


def parse_line_analysis_response(response_text: str) -> dict:
    """
    Parse the LLM response for line analysis.
    
    Returns:
        dict with 'relevance_context' and 'violations' list
    """
    import json
    import re
    
    default_response = {
        "relevance_context": "Unable to analyze this line",
        "violations": []
    }
    
    if not response_text:
        return default_response
    
    try:
        # Try to extract JSON from the response
        # Sometimes LLM adds text before/after JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            parsed = json.loads(json_match.group())
            
            # Validate structure
            if "relevance_context" not in parsed:
                parsed["relevance_context"] = "Context not provided"
            if "violations" not in parsed:
                parsed["violations"] = []
            
            return parsed
        
        return default_response
        
    except json.JSONDecodeError:
        return default_response
