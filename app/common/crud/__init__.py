# -*- coding: utf-8 -*-
"""
通用CRUD模块
提供统一的CRUD基类，减少重复代码
"""

# 异步版本（用于未来迁移）
from app.common.crud.repository import BaseRepository
from app.common.crud.service import BaseService
from app.common.crud.filters import QueryBuilder

# 同步版本（当前项目使用）
from app.common.crud.sync_repository import SyncBaseRepository
from app.common.crud.sync_service import SyncBaseService
from app.common.crud.sync_filters import SyncQueryBuilder

from app.common.crud.exceptions import (
    CRUDException,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    raise_not_found,
    raise_already_exists
)

__all__ = [
    # 异步版本
    "BaseRepository",
    "BaseService",
    "QueryBuilder",
    # 同步版本
    "SyncBaseRepository",
    "SyncBaseService",
    "SyncQueryBuilder",
    # 异常类
    "CRUDException",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "raise_not_found",
    "raise_already_exists",
]
