from typing import Generator
from app.core.config import settings
from app.core import security
from app.models.base import SessionLocal


def get_db() -> Generator:
    """
    Get database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# Re-export authentication dependencies
get_current_user = security.get_current_user
get_current_active_user = security.get_current_active_user
