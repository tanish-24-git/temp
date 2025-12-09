"""Compliance Knowledge Base - RAG Fallback

Hardcoded knowledge base of common compliance regulations by industry.
Used as fallback when web search APIs are unavailable.

This ensures the system can always generate baseline rules during onboarding.
"""

from typing import Dict, List

# Fallback compliance knowledge organized by industry
COMPLIANCE_KNOWLEDGE_BASE: Dict[str, List[Dict[str, str]]] = {
    "insurance": [
        {
            "title": "IRDAI Guidelines on Insurance Advertisements",
            "snippet": "All insurance advertisements must not contain any statement which exaggerates the benefits or minimizes the risk factors. Clear disclosure of terms, conditions, and exclusions is mandatory.",
            "url": "https://www.irdai.gov.in/ADMINCMS/cms/NormalData_Layout.aspx?page=PageNo234",
            "category": "irdai"
        },
        {
            "title": "IRDAI Circular on Guaranteed Returns",
            "snippet": "Insurance products must not make misleading claims about guaranteed returns. Any projections must be clearly marked as illustrative and include disclaimer about market risks.",
            "url": "https://www.irdai.gov.in/regulations",
            "category": "irdai"
        },
        {
            "title": "Risk Disclosure Requirements - IRDAI",
            "snippet": "All marketing materials must prominently disclose material risks, policy exclusions, waiting periods, and claim settlement procedures. Risk disclosure must be in clear, simple language.",
            "url": "https://www.irdai.gov.in/regulations",
            "category": "irdai"
        },
        {
            "title": "Medical Underwriting Disclosure",
            "snippet": "Insurance advertisements must not misrepresent medical conditions coverage. Pre-existing condition exclusions and waiting periods must be clearly stated.",
            "url": "https://www.irdai.gov.in/regulations",
            "category": "irdai"
        },
        {
            "title": "Fee Transparency Requirements",
            "snippet": "All charges, fees, premiums, and surrender penalties must be clearly disclosed. Hidden fees or complex premium structures must be explained in plain language.",
            "url": "https://www.irdai.gov.in/regulations",
            "category": "irdai"
        }
    ],
    
    "healthcare": [
        {
            "title": "HIPAA Privacy Rule - Marketing Communications",
            "snippet": "Healthcare marketing must comply with patient privacy regulations. Protected health information cannot be used for marketing without explicit authorization.",
            "url": "https://www.hhs.gov/hipaa/for-professionals/privacy/index.html",
            "category": "regulatory"
        },
        {
            "title": "FDA Regulations on Medical Claims",
            "snippet": "Marketing materials cannot make unsubstantiated health claims. All efficacy claims must be supported by clinical evidence and FDA approval where applicable.",
            "url": "https://www.fda.gov/regulatory-information",
            "category": "regulatory"
        },
        {
            "title": "Healthcare Advertising Standards",
            "snippet": "Healthcare services advertising must be truthful, not misleading, and substantiated. Testimonials must be genuine and representative of typical outcomes.",
            "url": "https://www.ftc.gov/business-guidance/advertising-marketing",
            "category": "regulatory"
        }
    ],
    
    "finance": [
        {
            "title": "SEBI Guidelines on Investment Advertising",
            "snippet": "Investment product advertisements must include risk warnings. Past performance disclaimers are mandatory. No guarantee of future returns can be implied.",
            "url": "https://www.sebi.gov.in/legal/regulations.html",
            "category": "regulatory"
        },
        {
            "title": "RBI Regulations on Banking Advertisements",
            "snippet": "Banking product marketing must clearly disclose interest rates, fees, and terms. Misleading representations of FDIC insurance or government guarantees are prohibited.",
            "url": "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx",
            "category": "regulatory"
        }
    ],
    
    "ecommerce": [
        {
            "title": "Consumer Protection Act - E-commerce Rules",
            "snippet": "E-commerce platforms must provide clear product descriptions, pricing, return policies, and customer grievance mechanisms. False advertising and unfair trade practices are prohibited.",
            "url": "https://consumeraffairs.nic.in/",
            "category": "regulatory"
        },
        {
            "title": "Advertising Standards for Online Retail",
            "snippet": "Product images and descriptions must accurately represent items sold. Discount claims must be genuine. Delivery timelines and return policies must be transparent.",
            "url": "https://ascionline.in/",
            "category": "regulatory"
        }
    ],
    
    "technology": [
        {
            "title": "GDPR Compliance for Marketing",
            "snippet": "Marketing communications must comply with data protection regulations. Explicit consent required for email marketing. Privacy policies must be clear and accessible.",
            "url": "https://gdpr.eu/",
            "category": "regulatory"
        }
    ]
}

# Brand guideline best practices (industry-agnostic)
BRAND_GUIDELINES_KNOWLEDGE: List[Dict[str, str]] = [
    {
        "title": "Consistent Brand Voice and Tone",
        "snippet": "Maintain consistent brand voice across all communications. Use approved terminology and avoid prohibited words. Tone should align with brand personality.",
        "category": "brand"
    },
    {
        "title": "Visual Identity Standards",
        "snippet": "Use approved logos, colors, and typography. Follow spacing and sizing guidelines. Ensure brand assets are not distorted or misrepresented.",
        "category": "brand"
    },
    {
        "title": "Competitor Mention Policy",
        "snippet": "Avoid disparaging competitor references. Comparative claims must be factual and substantiated. Focus on your brand's unique value proposition.",
        "category": "brand"
    }
]

# SEO best practices (universal)
SEO_KNOWLEDGE: List[Dict[str, str]] = [
    {
        "title": "Title Tag Optimization",
        "snippet": "Page titles should be 50-60 characters. Include primary keyword. Make titles compelling and descriptive for click-through rate.",
        "category": "seo"
    },
    {
        "title": "Meta Description Best Practices",
        "snippet": "Meta descriptions should be 150-160 characters. Include relevant keywords and clear call-to-action. Summarize page content accurately.",
        "category": "seo"
    },
    {
        "title": "Header Tag Structure",
        "snippet": "Use H1 for main page title (one per page). Use H2-H6 for hierarchical content structure. Include keywords naturally in headers.",
        "category": "seo"
    },
    {
        "title": "Image Alt Text Optimization",
        "snippet": "All images should have descriptive alt text for accessibility and SEO. Include relevant keywords naturally. Describe image content accurately.",
        "category": "seo"
    }
]


def get_fallback_knowledge(industry: str) -> List[Dict[str, str]]:
    """
    Get hardcoded compliance knowledge for an industry.
    
    Args:
        industry: Industry name (lowercase)
        
    Returns:
        List of compliance knowledge items
    """
    industry_lower = industry.lower()
    
    # Get industry-specific knowledge
    knowledge = COMPLIANCE_KNOWLEDGE_BASE.get(industry_lower, []).copy()
    
    # Add brand guidelines (always relevant)
    knowledge.extend(BRAND_GUIDELINES_KNOWLEDGE)
    
    # Add SEO knowledge (always relevant)
    knowledge.extend(SEO_KNOWLEDGE)
    
    return knowledge


def search_knowledge_base(query: str, industry: str = None) -> List[Dict[str, str]]:
    """
    Simple keyword-based search through knowledge base (RAG fallback).
    
    Args:
        query: Search query
        industry: Optional industry filter
        
    Returns:
        Relevant knowledge items
    """
    query_lower = query.lower()
    keywords = query_lower.split()
    
    # Get relevant knowledge pool
    if industry:
        knowledge_pool = get_fallback_knowledge(industry)
    else:
        # Search all industries
        knowledge_pool = []
        for industry_items in COMPLIANCE_KNOWLEDGE_BASE.values():
            knowledge_pool.extend(industry_items)
        knowledge_pool.extend(BRAND_GUIDELINES_KNOWLEDGE)
        knowledge_pool.extend(SEO_KNOWLEDGE)
    
    # Score each item by keyword matches
    scored_items = []
    for item in knowledge_pool:
        text = f"{item['title']} {item['snippet']}".lower()
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scored_items.append((score, item))
    
    # Sort by relevance and return
    scored_items.sort(reverse=True, key=lambda x: x[0])
    return [item for score, item in scored_items[:10]]
