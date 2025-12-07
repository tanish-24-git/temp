from typing import Generator
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
import uuid


def get_db_session() -> Generator[Session, None, None]:
    """Dependency for database session."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


# Phase 2: Role-based authentication dependencies
# Note: This is a simplified POC implementation
# In production, use proper JWT/OAuth authentication

async def get_current_user_id(
    x_user_id: str = Header(None, description="User ID header for POC")
) -> uuid.UUID:
    """
    Extract user ID from request header.

    POC Implementation: Accepts user ID via X-User-Id header.
    In production: Replace with JWT token validation.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header (X-User-Id) is required"
        )

    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
) -> User:
    """Get current user from database."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


async def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require super_admin role.

    Raises 403 Forbidden if user is not a super admin.
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required for this operation"
        )

    return current_user
