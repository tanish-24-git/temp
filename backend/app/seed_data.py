"""
Database Seeding Script for Compliance Agent
Production-ready seed script that can:
1. Seed initial users
2. Seed compliance rules
3. Clear and reseed data
"""
import sys
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.rule import Rule
from app.models.violation import Violation
from app.models.compliance_check import ComplianceCheck
from app.models.submission import Submission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# USER SEEDING
# =============================================================================

def seed_users(db: Session):
    """Seed sample users if they don't exist."""
    users = [
        {
            "id": "11111111-1111-1111-1111-111111111111",  # Super Admin  
            "name": "Super Admin",
            "email": "admin@bajajlife.com",
            "role": "super_admin"
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Compliance Reviewer",
            "email": "reviewer@bajajlife.com", 
            "role": "reviewer"
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "name": "Marketing Agent",
            "email": "agent@bajajlife.com",
            "role": "agent"
        },
    ]

    seeded = 0
    for user_data in users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(**user_data)
            db.add(user)
            seeded += 1

    db.commit()
    logger.info(f"✅ Seeded {seeded} users (skipped {len(users) - seeded} existing)")


# =============================================================================
# RULE SEEDING
# =============================================================================

def seed_rules(db: Session):
    """Seed compliance rules for Bajaj Life Insurance."""

    # IRDAI Rules (Regulatory Compliance)
    irdai_rules = [
        {
            "category": "irdai",
            "rule_text": "Full forms must be mentioned for all abbreviations (e.g., OCI, PIO, IRDAI, FEMA). Do not use abbreviations without defining them first.",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["OCI", "PIO", "IRDAI", "FEMA", "ULIP", "abbreviation", "acronym"]
        },
        {
            "category": "irdai",
            "rule_text": "All taxation references must mention 'Income Tax Act, 1961' and specify the regime (old or new). Tax content requires tax team approval.",
            "severity": "critical",
            "points_deduction": -20.0,
            "keywords": ["tax", "taxation", "Income Tax Act", "tax benefit", "deduction", "80C", "80D", "10(10D)"]
        },
        {
            "category": "irdai",
            "rule_text": "ULIP cannot be referred to as 'Investment Plan'. Must be called 'Unit Linked Insurance Plan' or 'ULIP'.",
            "severity": "high",
            "points_deduction": -10.0,
            "keywords": ["ULIP", "investment plan", "investment", "unit linked"]
        },
        {
            "category": "irdai",
            "rule_text": "When using 'guaranteed', it must be linked to disclaimer with legend: 'Conditions Apply'.",
            "severity": "critical",
            "points_deduction": -20.0,
            "keywords": ["guaranteed", "guarantee", "assured", "promise"]
        },
        {
            "category": "irdai",
            "rule_text": "When describing ULIPs, life insurance aspect must come first, then wealth creation.",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["ULIP", "life insurance", "wealth creation", "investment", "protection"]
        },
        {
            "category": "irdai",
            "rule_text": "Only charges listed under latest IRDAI regulations should be mentioned for ULIPs.",
            "severity": "high",
            "points_deduction": -10.0,
            "keywords": ["charges", "fees", "ULIP charges", "premium allocation", "fund management"]
        },
        {
            "category": "irdai",
            "rule_text": "Past performance of any fund must include disclaimer: 'Past performance is not indicative of future performance.'",
            "severity": "critical",
            "points_deduction": -20.0,
            "keywords": ["past performance", "historical returns", "fund performance", "NAV", "returns"]
        },
        {
            "category": "irdai",
            "rule_text": "When mentioning riders, must state: 'at additional nominal premium over and above the base premium'.",
            "severity": "high",
            "points_deduction": -10.0,
            "keywords": ["rider", "add-on", "additional cover", "supplementary benefit"]
        },
        {
            "category": "irdai",
            "rule_text": "Pension and Annuity cannot be used interchangeably. Use precise terminology.",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["pension", "annuity", "retirement", "pension plan"]
        },
        {
            "category": "irdai",
            "rule_text": "Life Insured and Policyholder cannot be used interchangeably.",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["life insured", "policyholder", "insured", "policy owner"]
        },
        {
            "category": "irdai",
            "rule_text": "All facts and figures must be backed up with relevant source links.",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["source", "reference", "statistics", "data", "research"]
        },
        {
            "category": "irdai",
            "rule_text": "Policy buying process must follow latest IRDAI regulations.",
            "severity": "high",
            "points_deduction": -10.0,
            "keywords": ["buying process", "purchase", "underwriting", "premium payment"]
        },
        {
            "category": "irdai",
            "rule_text": "Bajaj Life Insurance does not sell tailor-made or customized plans.",
            "severity": "high",
            "points_deduction": -10.0,
            "keywords": ["tailor-made", "customized", "personalized plan", "custom plan"]
        },
    ]

    # Brand Rules
    brand_rules = [
        {
            "category": "brand",
            "rule_text": "Use 'Bajaj Life Insurance' not abbreviations in customer-facing content",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["BLIC", "BL", "abbreviation"]
        },
        {
            "category": "brand",
            "rule_text": "Prohibited words: cheap, best, guarantee (unless factually backed)",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["cheap", "best", "guarantee", "cheapest"]
        },
        {
            "category": "brand",
            "rule_text": "Tone must be professional yet approachable, not overly casual",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["slang", "casual", "unprofessional"]
        },
        {
            "category": "brand",
            "rule_text": "Brand colors and logos must follow visual guidelines",
            "severity": "low",
            "points_deduction": -2.0,
            "keywords": ["logo", "color", "brand"]
        },
        {
            "category": "brand",
            "rule_text": "ULIP abbreviation must be expanded as 'Unit-Linked Insurance Plan' (with hyphen)",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["Unit Linked Insurance Plan", "Unit Linked", "ULIP expansion"]
        },
        {
            "category": "brand",
            "rule_text": "Do not use 'lock-in period'. Use 'lock-in duration' or 'lock-in term' instead.",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["lock-in period", "lockin period", "lock in period"]
        },
        {
            "category": "brand",
            "rule_text": "Avoid using the word 'during'. Use 'in the [time period]' or 'throughout' instead.",
            "severity": "low",
            "points_deduction": -2.0,
            "keywords": ["during", "during the", "during your"]
        },
    ]

    # SEO Rules
    seo_rules = [
        {
            "category": "seo",
            "rule_text": "Title should be 50-60 characters for optimal display",
            "severity": "low",
            "points_deduction": -2.0,
            "keywords": ["title", "heading", "h1"]
        },
        {
            "category": "seo",
            "rule_text": "Meta description required (150-160 characters)",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["meta", "description"]
        },
        {
            "category": "seo",
            "rule_text": "Focus keyword should appear in first paragraph",
            "severity": "low",
            "points_deduction": -2.0,
            "keywords": ["keyword", "seo"]
        },
        {
            "category": "seo",
            "rule_text": "Images must have alt text for accessibility",
            "severity": "medium",
            "points_deduction": -5.0,
            "keywords": ["alt", "image", "accessibility"]
        },
    ]

    all_rules = irdai_rules + brand_rules + seo_rules
    seeded = 0

    for rule_data in all_rules:
        # Check if rule already exists
        existing = db.query(Rule).filter(Rule.rule_text == rule_data["rule_text"]).first()
        if not existing:
            rule = Rule(**rule_data)
            db.add(rule)
            seeded += 1

    db.commit()
    logger.info(f"✅ Seeded {seeded} rules (skipped {len(all_rules) - seeded} existing)")
    logger.info(f"   - IRDAI: {len(irdai_rules)} rules")
    logger.info(f"   - Brand: {len(brand_rules)} rules")  
    logger.info(f"   - SEO: {len(seo_rules)} rules")


# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

def clear_all_data(db: Session):
    """Clear all data from the database."""
    # Order matters due to foreign key constraints
    db.query(Violation).delete()
    db.query(ComplianceCheck).delete()
    db.query(Submission).delete()
    db.query(Rule).delete()
    # Keep users for auth purposes
    db.commit()
    logger.info("🗑️  Cleared all compliance data (kept users)")


def clear_rules(db: Session):
    """Clear only rules and violations."""
    db.query(Violation).delete()
    db.query(Rule).delete()
    db.commit()
    logger.info("🗑️  Cleared rules and violations")


# =============================================================================
# MAIN COMMANDS
# =============================================================================

def seed_all(db: Session):
    """Seed all initial data."""
    seed_users(db)
    seed_rules(db)


def reseed_rules(db: Session):
    """Clear and reseed rules only."""
    clear_rules(db)
    seed_rules(db)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compliance Agent Database Seeding")
    parser.add_argument(
        "command", 
        choices=["seed", "reseed-rules", "clear", "clear-rules"],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Running command: {args.command}")
    
    db = SessionLocal()
    
    try:
        if args.command == "seed":
            seed_all(db)
        elif args.command == "reseed-rules":
            reseed_rules(db)
        elif args.command == "clear":
            clear_all_data(db)
        elif args.command == "clear-rules":
            clear_rules(db)
            
        logger.info("✅ Command completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        db.rollback()
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
