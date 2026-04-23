# -*- coding: utf-8 -*-
"""
数据库核心模块

提供租户感知的数据库查询功能。
"""

from .tenant_query import TenantQuery, create_tenant_aware_session

# Backward-compatible re-export so legacy imports from app.core.database still work
try:
    from app.models.base import Base, SessionLocal, get_db
except ImportError:
    # 某些旧测试会在应用初始化早期导入这里，做一次延迟兜底
    try:
        import importlib

        _models_base = importlib.import_module("app.models.base")
        Base = getattr(_models_base, "Base", None)
        SessionLocal = getattr(_models_base, "SessionLocal", None)
        get_db = getattr(_models_base, "get_db", None)
    except Exception:
        Base = None
        SessionLocal = None
        get_db = None

__all__ = [
    "TenantQuery",
    "create_tenant_aware_session",
    "Base",
    "SessionLocal",
    "get_db",
]
