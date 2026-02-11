# -*- coding: utf-8 -*-
"""
通用CRUD路由生成器（同步版本）

自动生成标准的CRUD端点，减少重复代码。
使用同步Session，兼容现有系统。
"""

from typing import Type, Optional, List, TypeVar
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.common.crud import BaseService
from app.common.crud.types import QueryParams
from app.models.user import User

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def create_crud_router_sync(
    service_class: Type[BaseService[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    resource_name: str,
    resource_name_plural: str = None,
    prefix: str = "",
    tags: List[str] = None,
    keyword_fields: Optional[List[str]] = None,
    unique_fields: Optional[List[str]] = None,
    default_filters: Optional[dict] = None,
    permission_read: Optional[str] = None,
    permission_create: Optional[str] = None,
    permission_update: Optional[str] = None,
    permission_delete: Optional[str] = None,
    enable_create: bool = True,
    enable_read: bool = True,
    enable_list: bool = True,
    enable_update: bool = True,
    enable_delete: bool = True,
    enable_stats: bool = True,
) -> APIRouter:
    """
    创建通用CRUD路由（同步版本）
    
    Args:
        service_class: Service类（继承BaseService）
        create_schema: 创建Schema
        update_schema: 更新Schema
        response_schema: 响应Schema
        resource_name: 资源名称（单数，如"供应商"）
        resource_name_plural: 资源名称（复数，如"供应商列表"，默认使用resource_name）
        prefix: 路由前缀（如"/suppliers"）
        tags: OpenAPI标签
        keyword_fields: 关键词搜索字段列表
        unique_fields: 唯一性检查字段列表
        default_filters: 默认筛选条件
        permission_read: 读取权限（如"supplier:read"）
        permission_create: 创建权限（如"supplier:create"）
        permission_update: 更新权限（如"supplier:update"）
        permission_delete: 删除权限（如"supplier:delete"）
        enable_create: 是否生成创建端点
        enable_read: 是否生成读取端点
        enable_list: 是否生成列表端点
        enable_update: 是否生成更新端点
        enable_delete: 是否生成删除端点
        enable_stats: 是否生成统计端点
    
    Returns:
        APIRouter: 配置好的路由
    """
    from typing import TypeVar
    
    router = APIRouter(prefix=prefix, tags=tags or [resource_name])
    resource_name_plural = resource_name_plural or resource_name
    
    # 创建端点
    if enable_create:
        @router.post(
            "/",
            response_model=SuccessResponse[response_schema],
            status_code=status.HTTP_201_CREATED,
            summary=f"创建{resource_name}",
            description=f"创建新的{resource_name}记录"
        )
        def create_item(
            item_in: create_schema,
            db: Session = Depends(get_db),
            current_user: User = Depends(
                security.require_permission(permission_create)
                if permission_create
                else security.get_current_active_user
            ),
        ) -> SuccessResponse[response_schema]:
            """创建资源"""
            service = service_class(db=db)
            
            # 检查唯一性
            if unique_fields:
                for field in unique_fields:
                    value = getattr(item_in, field, None)
                    if value:
                        existing = service.repository.get_by_field(field, value)
                        if existing:
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail=f"{resource_name}的{field}={value}已存在"
                            )
            
            # 构建唯一性检查字典
            check_unique = {}
            if unique_fields:
                for field in unique_fields:
                    if hasattr(item_in, field):
                        value = getattr(item_in, field)
                        if value:
                            check_unique[field] = value
            
            item_data = service.create(item_in, check_unique=check_unique if check_unique else None)
            return success_response(
                data=item_data,
                message=f"{resource_name}创建成功",
                code=status.HTTP_201_CREATED
            )
    
    # 获取详情端点
    if enable_read:
        @router.get(
            "/{item_id}",
            response_model=SuccessResponse[response_schema],
            summary=f"获取{resource_name}详情",
            description=f"根据ID获取{resource_name}详细信息"
        )
        def get_item(
            item_id: int = Path(..., description=f"{resource_name}ID", ge=1),
            db: Session = Depends(get_db),
            current_user: User = Depends(
                security.require_permission(permission_read)
                if permission_read
                else security.get_current_active_user
            ),
        ) -> SuccessResponse[response_schema]:
            """获取资源详情"""
            service = service_class(db=db)
            item = service.get(item_id)
            return success_response(data=item, message="获取成功")
    
    # 列表查询端点
    if enable_list:
        @router.get(
            "/",
            response_model=PaginatedResponse[response_schema],
            summary=f"{resource_name_plural}",
            description=f"分页查询{resource_name_plural}，支持筛选、搜索、排序"
        )
        def list_items(
            pagination: PaginationParams = Depends(get_pagination_query),
            keyword: Optional[str] = Query(None, description="关键词搜索"),
            status: Optional[str] = Query(None, description="状态筛选"),
            order_by: Optional[str] = Query(None, description="排序字段"),
            order_direction: str = Query("desc", description="排序方向（asc/desc）"),
            db: Session = Depends(get_db),
            current_user: User = Depends(
                security.require_permission(permission_read)
                if permission_read
                else security.get_current_active_user
            ),
        ) -> PaginatedResponse[response_schema]:
            """列表查询"""
            service = service_class(db=db)
            
            # 构建筛选条件
            filters = {}
            if default_filters:
                filters.update(default_filters)
            if status:
                filters["status"] = status
            
            # 构建查询参数
            params = QueryParams(
                page=pagination.page,
                page_size=pagination.page_size,
                search=keyword,
                search_fields=keyword_fields or [],
                filters=filters if filters else None,
                sort_by=order_by or "created_at",
                sort_order=order_direction.upper(),
            )
            
            # 查询
            result = service.list(params)
            
            return paginated_response(
                items=result.items,
                total=result.total,
                page=result.page,
                page_size=result.page_size
            )
    
    # 更新端点
    if enable_update:
        @router.put(
            "/{item_id}",
            response_model=SuccessResponse[response_schema],
            summary=f"更新{resource_name}",
            description=f"更新{resource_name}信息"
        )
        def update_item(
            item_id: int,
            item_in: update_schema,
            db: Session = Depends(get_db),
            current_user: User = Depends(
                security.require_permission(permission_update)
                if permission_update
                else security.get_current_active_user
            ),
        ) -> SuccessResponse[response_schema]:
            """更新资源"""
            service = service_class(db=db)
            
            # 检查唯一性（如果更新唯一字段）
            if unique_fields:
                for field in unique_fields:
                    value = getattr(item_in, field, None)
                    if value:
                        existing = service.repository.get_by_field(field, value)
                        if existing and existing.id != item_id:
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail=f"{resource_name}的{field}={value}已存在"
                            )
            
            item_data = service.update(item_id, item_in)
            return success_response(data=item_data, message=f"{resource_name}更新成功")
    
    # 删除端点
    if enable_delete:
        @router.delete(
            "/{item_id}",
            response_model=SuccessResponse,
            summary=f"删除{resource_name}",
            description=f"删除{resource_name}（软删除）"
        )
        def delete_item(
            item_id: int,
            soft_delete: bool = Query(True, description="是否软删除"),
            db: Session = Depends(get_db),
            current_user: User = Depends(
                security.require_permission(permission_delete)
                if permission_delete
                else security.get_current_active_user
            ),
        ) -> SuccessResponse:
            """删除资源"""
            service = service_class(db=db)
            service.delete(item_id, soft_delete=soft_delete)
            return success_response(data=None, message=f"{resource_name}删除成功")
    
    # 统计端点
    if enable_stats:
        @router.get(
            "/stats/count",
            response_model=SuccessResponse[dict],
            summary=f"{resource_name}统计",
            description=f"获取{resource_name}数量统计"
        )
        def get_item_stats(
            status: Optional[str] = Query(None, description="按状态筛选"),
            db: Session = Depends(get_db),
            current_user: User = Depends(
                security.require_permission(permission_read)
                if permission_read
                else security.get_current_active_user
            ),
        ) -> SuccessResponse[dict]:
            """获取统计信息"""
            service = service_class(db=db)
            
            filters = {}
            if default_filters:
                filters.update(default_filters)
            if status:
                filters["status"] = status
            
            total = service.count(filters=filters if filters else None)
            
            return success_response(
                data={"total": total},
                message="统计成功"
            )
    
    return router
