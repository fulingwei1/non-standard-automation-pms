from typing import Generator

from app.core import security
from app.core.config import settings
from app.models.base import SessionLocal
from app.models.base import get_db as get_db_session


def get_db() -> Generator:
    """
    Get database session
    """
    yield from get_db_session()


# Re-export authentication dependencies
get_current_user = security.get_current_user
get_current_active_user = security.get_current_active_user
get_current_active_superuser = security.get_current_active_superuser
