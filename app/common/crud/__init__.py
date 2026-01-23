# -*- coding: utf-8 -*-
"""
通用CRUD模块
提供统一的CRUD基类，减少重复代码
"""

from app.common.crud.repository import BaseRepository
from app.common.crud.service import BaseService
from app.common.crud.filters import QueryBuilder
from app.common.crud.exceptions import (
    CRUDException,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    raise_not_found,
    raise_already_exists
)

__all__ = [
    "BaseRepository",
    "BaseService",
    "QueryBuilder",
    "CRUDException",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "raise_not_found",
    "raise_already_exists",
]
