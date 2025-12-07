"""Clear existing rules and reseed with updated Bajaj Life Insurance rules."""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.rule import Rule
from app.models.violation import Violation
from app.seed_data import seed_rules


def clear_violations(db: Session):
    """Delete all existing violations first to avoid foreign key constraints."""
    count = db.query(Violation).delete()
    db.commit()
    print(f"🗑️  Deleted {count} existing violations")


def clear_rules(db: Session):
    """Delete all existing rules."""
    count = db.query(Rule).delete()
    db.commit()
    print(f"🗑️  Deleted {count} existing rules")


def main():
    """Clear and reseed rules."""
    print("🔄 Starting rule update process...")
    print()

    db = SessionLocal()

    try:
        # Step 1: Clear old violations first (foreign key constraint)
        clear_violations(db)
        print()

        # Step 2: Clear old rules
        clear_rules(db)
        print()

        # Step 3: Seed new rules
        print("🌱 Reseeding with updated Bajaj Life Insurance rules...")
        seed_rules(db)
        print()

        print("✅ Rule update completed successfully!")
        print()
        print("📊 New Rules Summary:")
        print("   - IRDAI: 13 rules (3 Critical, 5 High, 5 Medium)")
        print("   - Brand: 7 rules (6 Medium, 1 Low) - ADDED 3 NEW RULES")
        print("   - SEO: 4 rules (2 Medium, 2 Low)")
        print("   - MEDIUM penalty: Reduced from -5 to -3 points")

    except Exception as e:
        print(f"❌ Error updating rules: {str(e)}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
