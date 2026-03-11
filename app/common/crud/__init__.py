# -*- coding: utf-8 -*-
"""
通用CRUD模块
提供统一的CRUD基类，减少重复代码
"""

# 同步版本（当前项目使用）
from app.common.crud.base_crud_service import BaseCRUDService
from app.common.crud.exceptions import (
    AlreadyExistsError,
    CRUDException,
    NotFoundError,
    ValidationError,
    raise_already_exists,
    raise_not_found,
)
from app.common.crud.filters import QueryBuilder
from app.common.crud.sales_query_builder import (
    SalesQueryBuilder,
    SalesQueryConfig,
    SalesQueryResult,
)

# 异步版本（用于未来迁移）
from app.common.crud.repository import BaseRepository
from app.common.crud.service import BaseService
from app.common.crud.sync_filters import SyncQueryBuilder
from app.common.crud.sync_repository import SyncBaseRepository
from app.common.crud.sync_service import SyncBaseService
from app.common.crud.types import PaginatedResult, QueryParams, SortOrder

__all__ = [
    # 异步版本
    "BaseRepository",
    "BaseService",
    "QueryBuilder",
    # 同步版本
    "SyncBaseRepository",
    "SyncBaseService",
    "SyncQueryBuilder",
    "SalesQueryBuilder",
    "SalesQueryConfig",
    "SalesQueryResult",
    "BaseCRUDService",
    "QueryParams",
    "PaginatedResult",
    "SortOrder",
    # 异常类
    "CRUDException",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "raise_not_found",
    "raise_already_exists",
]
