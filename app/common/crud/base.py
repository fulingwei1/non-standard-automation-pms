# -*- coding: utf-8 -*-
"""
核心基础 CRUD 与 Service 层
通过泛型减少重复代码，优化后端开发效率
"""

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .sync_repository import SyncBaseRepository
from .base_crud_service import BaseCRUDService
from .types import PaginatedResult, QueryParams, SortOrder

# 类型变量声明
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class CRUDBase(SyncBaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用 CRUD 操作基类
    """

    pass


class BaseService(
    BaseCRUDService[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]
):
    """
    通用业务逻辑服务基类
    """

    def __init__(
        self,
        *,
        model: Type[ModelType],
        db: Session,
        response_schema: Type[ResponseSchemaType],
        resource_name: Optional[str] = None,
        default_filters: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            model=model,
            db=db,
            response_schema=response_schema,
            resource_name=resource_name,
            default_filters=default_filters,
        )
        # CRUDBase 可以直接在 service 中使用
        self.crud = CRUDBase(model, db, self.resource_name)
