"""Database seeding script for compliance rules and sample data."""
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.rule import Rule
from app.models.submission import Submission
import uuid


def seed_users(db: Session):
    """Seed sample users."""
    users = [
        User(name="John Agent", email="john@example.com", role="agent"),
        User(name="Sarah Reviewer", email="sarah@example.com", role="reviewer"),
    ]

    for user in users:
        db.add(user)

    db.commit()
    print(f"✅ Seeded {len(users)} users")


def seed_rules(db: Session):
    """Seed compliance rules for Bajaj Life Insurance."""

    # IRDAI Rules (Critical/High/Medium) - Bajaj Life Insurance Specific
    irdai_rules = [
        # Rule 1: No Abbreviations
        Rule(
            category="irdai",
            rule_text="Full forms must be mentioned for all abbreviations (e.g., OCI, PIO, IRDAI, FEMA). Do not use abbreviations without defining them first.",
            severity="medium",
            keywords=["OCI", "PIO", "IRDAI", "FEMA", "ULIP", "abbreviation", "acronym"]
        ),
        # Rule 2: Taxation
        Rule(
            category="irdai",
            rule_text="All taxation references must mention 'Income Tax Act, 1961' and specify the regime (old or new). Tax content requires tax team approval.",
            severity="critical",
            keywords=["tax", "taxation", "Income Tax Act", "tax benefit", "deduction", "80C", "80D", "10(10D)"]
        ),
        # Rule 3: ULIP Investment Terminology
        Rule(
            category="irdai",
            rule_text="ULIP cannot be referred to as 'Investment Plan'. Must be called 'Unit Linked Insurance Plan' or 'ULIP'.",
            severity="high",
            keywords=["ULIP", "investment plan", "investment", "unit linked"]
        ),
        # Rule 4: Guaranteed Claims Disclaimer
        Rule(
            category="irdai",
            rule_text="When using 'guaranteed', it must be linked to disclaimer with legend: 'Conditions Apply – The Guaranteed benefits are dependent on policy term, premium payment term availed along with other variable factors. For more details, please refer to sales brochure.'",
            severity="critical",
            keywords=["guaranteed", "guarantee", "assured", "promise"]
        ),
        # Rule 5: ULIP Description Order
        Rule(
            category="irdai",
            rule_text="When describing ULIPs, life insurance aspect must come first, then wealth creation. Format: 'Life Insurance with Wealth Creation' not 'Wealth Creation with Life Insurance'.",
            severity="medium",
            keywords=["ULIP", "life insurance", "wealth creation", "investment", "protection"]
        ),
        # Rule 6: ULIP Charges Compliance
        Rule(
            category="irdai",
            rule_text="Only charges listed under latest IRDAI regulations should be mentioned for ULIPs. Omit outdated or non-compliant charge descriptions.",
            severity="high",
            keywords=["charges", "fees", "ULIP charges", "premium allocation", "fund management", "mortality"]
        ),
        # Rule 7: Past Performance Disclaimer
        Rule(
            category="irdai",
            rule_text="Past performance of any fund must include disclaimer: 'Past performance is not indicative of future performance.' with proper legend.",
            severity="critical",
            keywords=["past performance", "historical returns", "fund performance", "NAV", "returns"]
        ),
        # Rule 8: Riders Premium Disclosure
        Rule(
            category="irdai",
            rule_text="When mentioning riders, must state: 'at additional nominal premium over and above the base premium'.",
            severity="high",
            keywords=["rider", "add-on", "additional cover", "supplementary benefit"]
        ),
        # Rule 9: Pension vs Annuity Distinction
        Rule(
            category="irdai",
            rule_text="Pension and Annuity cannot be used interchangeably. Annuity is a type of pension plan. Use precise terminology.",
            severity="medium",
            keywords=["pension", "annuity", "retirement", "pension plan"]
        ),
        # Rule 10: Life Insured vs Policyholder
        Rule(
            category="irdai",
            rule_text="Life Insured and Policyholder cannot be used interchangeably. Policyholder may or may not be the life insured and vice versa.",
            severity="medium",
            keywords=["life insured", "policyholder", "insured", "policy owner"]
        ),
        # Rule 11: Source Links for Claims
        Rule(
            category="irdai",
            rule_text="All facts and figures must be backed up with relevant source links. Competitor or aggregator platform links not allowed. Source content must match destination content.",
            severity="medium",
            keywords=["source", "reference", "statistics", "data", "research", "study"]
        ),
        # Rule 12: Policy Buying Process per IRDAI
        Rule(
            category="irdai",
            rule_text="Policy buying process must follow latest IRDAI regulations. Premium can only be paid after policy is approved by underwriter.",
            severity="high",
            keywords=["buying process", "purchase", "underwriting", "premium payment", "policy issuance"]
        ),
        # Rule 13: No Customized Plans
        Rule(
            category="irdai",
            rule_text="Bajaj Life Insurance does not sell tailor-made or customized plans. Do not use phrases like 'customized for you', 'tailor-made', or 'personalized plan design'.",
            severity="high",
            keywords=["tailor-made", "customized", "personalized plan", "custom plan", "bespoke"]
        ),
    ]

    # Brand Rules (Medium)
    brand_rules = [
        Rule(
            category="brand",
            rule_text="Use 'Bajaj Life Insurance' not abbreviations in customer-facing content",
            severity="medium",
            keywords=["BLIC", "BL", "abbreviation"]
        ),
        Rule(
            category="brand",
            rule_text="Prohibited words: cheap, best, guarantee (unless factually backed)",
            severity="medium",
            keywords=["cheap", "best", "guarantee", "cheapest"]
        ),
        Rule(
            category="brand",
            rule_text="Tone must be professional yet approachable, not overly casual",
            severity="medium",
            keywords=["slang", "casual", "unprofessional"]
        ),
        Rule(
            category="brand",
            rule_text="Brand colors and logos must follow visual guidelines",
            severity="low",
            keywords=["logo", "color", "brand"]
        ),
        # NEW RULE 1: ULIP Hyphenation Format
        Rule(
            category="brand",
            rule_text="ULIP abbreviation must be expanded as 'Unit-Linked Insurance Plan' (with hyphen), not 'Unit Linked Insurance Plan' (without hyphen). This is the official Bajaj Life Insurance brand terminology.",
            severity="medium",
            keywords=["Unit Linked Insurance Plan", "Unit Linked", "ULIP expansion", "unit linked"]
        ),
        # NEW RULE 2: Lock-in Period Terminology
        Rule(
            category="brand",
            rule_text="Do not use the word 'period' when referring to lock-in duration. Use 'lock-in duration', 'lock-in term', or 'lock-in tenure' instead. Example: Say 'lock-in duration of 5 years' not 'lock-in period of 5 years'.",
            severity="medium",
            keywords=["lock-in period", "lockin period", "lock in period", "period", "lock-in"]
        ),
        # NEW RULE 3: Avoid "During"
        Rule(
            category="brand",
            rule_text="Avoid using the word 'during' in insurance content. Use more specific temporal references like 'in the [time period]', 'throughout', 'while', or specific date ranges instead. Example: Say 'in the first 5 years' instead of 'during the first 5 years'.",
            severity="medium",
            keywords=["during", "during the", "during your"]
        ),
    ]

    # SEO Rules (Low/Medium)
    seo_rules = [
        Rule(
            category="seo",
            rule_text="Title should be 50-60 characters for optimal display",
            severity="low",
            keywords=["title", "heading", "h1"]
        ),
        Rule(
            category="seo",
            rule_text="Meta description required (150-160 characters)",
            severity="medium",
            keywords=["meta", "description"]
        ),
        Rule(
            category="seo",
            rule_text="Focus keyword should appear in first paragraph",
            severity="low",
            keywords=["keyword", "seo"]
        ),
        Rule(
            category="seo",
            rule_text="Images must have alt text for accessibility",
            severity="medium",
            keywords=["alt", "image", "accessibility"]
        ),
    ]

    all_rules = irdai_rules + brand_rules + seo_rules

    for rule in all_rules:
        db.add(rule)

    db.commit()
    print(f"✅ Seeded {len(all_rules)} rules")
    print(f"   - IRDAI: {len(irdai_rules)} rules")
    print(f"   - Brand: {len(brand_rules)} rules")
    print(f"   - SEO: {len(seo_rules)} rules")


def main():
    """Run all seed functions."""
    print("🌱 Starting database seeding...")

    db = SessionLocal()

    try:
        seed_users(db)
        seed_rules(db)

        print("✅ Database seeding completed!")

    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    main()
