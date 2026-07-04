# -*- coding: utf-8 -*-
"""
数据库核心模块

租户查询过滤见 app.core.database.tenant_scope（TEN-02，
基于 do_orm_execute + with_loader_criteria 的框架级实现）。
"""

# Backward-compatible re-export so tests importing SessionLocal from here still work
try:
    from app.models.base import SessionLocal
except ImportError:
    # 模块尚未初始化时的回退
    SessionLocal = None

__all__ = [
    "SessionLocal",
]
