# -*- coding: utf-8 -*-
"""
通用CRUD路由生成器

自动生成标准的CRUD端点，减少重复代码。
"""

from typing import TypeVar, Type, Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_db
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.common.crud import BaseService
from app.common.pagination import PaginationParams, get_pagination_query

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def create_crud_router(
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
) -> APIRouter:
    """
    创建通用CRUD路由
    
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
    
    Returns:
        APIRouter: 配置好的路由
    """
    router = APIRouter(prefix=prefix, tags=tags or [resource_name])
    resource_name_plural = resource_name_plural or resource_name
    
    # 创建端点
    @router.post(
        "/",
        response_model=SuccessResponse[response_schema],
        status_code=status.HTTP_201_CREATED,
        summary=f"创建{resource_name}",
        description=f"创建新的{resource_name}记录"
    )
    async def create_item(
        item_in: create_schema,
        db: AsyncSession = Depends(get_db),
    ) -> SuccessResponse[response_schema]:
        """创建资源"""
        service = service_class(db)
        
        # 检查唯一性
        if unique_fields:
            for field in unique_fields:
                value = getattr(item_in, field, None)
                if value:
                    existing = await service.repository.get_by_field(field, value)
                    if existing:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"{resource_name}的{field}={value}已存在"
                        )
        
        item_data = await service.create(item_in)
        return success_response(
            data=item_data,
            message=f"{resource_name}创建成功",
            code=status.HTTP_201_CREATED
        )
    
    # 获取详情端点
    @router.get(
        "/{item_id}",
        response_model=SuccessResponse[response_schema],
        summary=f"获取{resource_name}详情",
        description=f"根据ID获取{resource_name}详细信息"
    )
    async def get_item(
        item_id: int = Path(..., description=f"{resource_name}ID", ge=1),
        db: AsyncSession = Depends(get_db),
    ) -> SuccessResponse[response_schema]:
        """获取资源详情"""
        service = service_class(db)
        item = await service.get(item_id)
        return success_response(data=item, message="获取成功")
    
    # 列表查询端点
    @router.get(
        "/",
        response_model=PaginatedResponse[response_schema],
        summary=f"{resource_name_plural}",
        description=f"分页查询{resource_name_plural}，支持筛选、搜索、排序"
    )
    async def list_items(
        pagination: PaginationParams = Depends(get_pagination_query),
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        status: Optional[str] = Query(None, description="状态筛选"),
        order_by: Optional[str] = Query(None, description="排序字段"),
        order_direction: str = Query("desc", description="排序方向（asc/desc）"),
        db: AsyncSession = Depends(get_db),
    ) -> PaginatedResponse[response_schema]:
        """列表查询"""

        service = service_class(db)

        # 构建筛选条件
        filters = {}
        if status:
            filters["status"] = status

        # 查询
        result = await service.list(
            skip=pagination.offset,
            limit=pagination.limit,
            keyword=keyword,
            keyword_fields=keyword_fields,
            filters=filters if filters else None,
            order_by=order_by or "created_at",
            order_direction=order_direction
        )

        return paginated_response(
            items=result["items"],
            total=result["total"],
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    # 更新端点
    @router.put(
        "/{item_id}",
        response_model=SuccessResponse[response_schema],
        summary=f"更新{resource_name}",
        description=f"更新{resource_name}信息"
    )
    async def update_item(
        item_id: int,
        item_in: update_schema,
        db: AsyncSession = Depends(get_db),
    ) -> SuccessResponse[response_schema]:
        """更新资源"""
        service = service_class(db)
        
        # 检查唯一性（如果更新唯一字段）
        if unique_fields:
            for field in unique_fields:
                value = getattr(item_in, field, None)
                if value:
                    existing = await service.repository.get_by_field(field, value)
                    if existing and existing.id != item_id:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"{resource_name}的{field}={value}已存在"
                        )
        
        item_data = await service.update(item_id, item_in)
        return success_response(data=item_data, message=f"{resource_name}更新成功")
    
    # 删除端点
    @router.delete(
        "/{item_id}",
        response_model=SuccessResponse,
        summary=f"删除{resource_name}",
        description=f"删除{resource_name}（软删除）"
    )
    async def delete_item(
        item_id: int,
        soft_delete: bool = Query(True, description="是否软删除"),
        db: AsyncSession = Depends(get_db),
    ) -> SuccessResponse:
        """删除资源"""
        service = service_class(db)
        await service.delete(item_id, soft_delete=soft_delete)
        return success_response(data=None, message=f"{resource_name}删除成功")
    
    # 统计端点
    @router.get(
        "/stats/count",
        response_model=SuccessResponse[dict],
        summary=f"{resource_name}统计",
        description=f"获取{resource_name}数量统计"
    )
    async def get_item_stats(
        status: Optional[str] = Query(None, description="按状态筛选"),
        db: AsyncSession = Depends(get_db),
    ) -> SuccessResponse[dict]:
        """获取统计信息"""
        service = service_class(db)
        
        filters = {}
        if status:
            filters["status"] = status
        
        total = await service.count(filters=filters if filters else None)
        
        return success_response(
            data={"total": total},
            message="统计成功"
        )
    
    return router
