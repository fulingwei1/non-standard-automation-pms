# -*- coding: utf-8 -*-
"""
FastAPI Dependencies

Moved from app/models/base to break circular import:
app/models/base → TenantQuery → app.core.security → app.core.auth → app.models.base.get_db
"""

from contextlib import contextmanager
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
        if db is not None:
            # 显式回滚任何未提交的更改，避免 macOS SQLite 权限问题
            try:
                db.rollback()
            except Exception:
                pass
            try:
                db.close()
            except Exception:
                pass

@contextmanager
def get_db_session():
    """
    非 FastAPI 场景使用的数据库会话上下文管理器。

    注意：
    - `get_db` 是 FastAPI 依赖注入生成器（`Depends(get_db)`）
    - `get_db_session` 供 `with get_db_session() as db:` 使用
    """
    from app.models.base import get_db_session as base_get_db_session

    with base_get_db_session() as db:
        yield db
