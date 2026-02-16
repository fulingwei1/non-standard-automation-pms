# -*- coding: utf-8 -*-
"""
FastAPI Dependencies

Moved from app/models/base to break circular import:
app/models/base → TenantQuery → app.core.security → app.core.auth → app.models.base.get_db
"""

from typing import Generator
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖使用的数据库会话生成器
    
    Yields:
        Session: SQLAlchemy数据库会话
    """
    from app.models.base import get_session
    
    db = get_session()
    try:
        yield db
    finally:
        # 显式回滚任何未提交的更改，避免 macOS SQLite 权限问题
        try:
            db.rollback()
        except Exception:
            pass
        db.close()
