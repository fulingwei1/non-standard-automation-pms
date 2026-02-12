# -*- coding: utf-8 -*-
"""
供应商API端点（重构版 v2）

使用通用CRUD路由生成器和统一响应格式，去除重复代码。
保留特殊端点和权限检查。
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.models.user import User
from app.models.material import Material, MaterialSupplier
from app.schemas.material import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from app.services.vendor_service import VendorService
from app.api.v1.endpoints.base_crud_router_sync import create_crud_router_sync
from app.common.query_filters import apply_pagination

# 创建通用CRUD路由
crud_router = create_crud_router_sync(
    service_class=VendorService,
    create_schema=SupplierCreate,
    update_schema=SupplierUpdate,
    response_schema=SupplierResponse,
    resource_name="供应商",
    resource_name_plural="供应商列表",
    prefix="",
    tags=["suppliers"],
    keyword_fields=["supplier_name", "supplier_code", "supplier_short_name"],
    unique_fields=["supplier_code"],
    default_filters={"vendor_type": "MATERIAL"},
    permission_read="supplier:read",
    permission_create="supplier:create",
    permission_update="supplier:read",  # 注意：原代码使用的是supplier:read
    permission_delete="supplier:read",  # 注意：原代码没有delete端点，这里假设使用read权限
    enable_list=False,  # 禁用通用列表端点，使用自定义的列表端点
)

# 创建主路由，包含通用CRUD和特殊端点
router = APIRouter()

# 包含通用CRUD路由
router.include_router(crud_router)

# ========== 覆盖列表查询端点（支持额外筛选参数） ==========

@router.get(
    "/",
    response_model=PaginatedResponse[SupplierResponse],
    summary="供应商列表",
    description="分页查询供应商列表，支持筛选、搜索、排序"
)
def list_suppliers(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（供应商名称/编码）"),
    supplier_type: Optional[str] = Query(None, description="供应商类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_level: Optional[str] = Query(None, description="供应商等级筛选"),
    current_user: User = Depends(security.require_permission("supplier:read")),
) -> PaginatedResponse[SupplierResponse]:
    """
    获取供应商列表（支持分页、搜索、筛选）
    
    - **keyword**: 关键词搜索（供应商名称/编码）
    - **supplier_type**: 供应商类型筛选
    - **status**: 状态筛选
    - **supplier_level**: 供应商等级筛选
    """
    service = VendorService(db)
    result = service.list_suppliers(
        page=pagination.page,
        page_size=pagination.page_size,
        keyword=keyword,
        supplier_type=supplier_type,
        status=status,
        supplier_level=supplier_level,
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )

# ========== 特殊端点 ==========

@router.put(
    "/{supplier_id}/rating",
    response_model=SuccessResponse[SupplierResponse],
    summary="更新供应商评级",
    description="更新供应商的质量、交期、服务评分，自动计算综合评分和等级"
)
def update_supplier_rating(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: int,
    quality_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="质量评分"),
    delivery_rating: Optional[Decimal] = Query(
        None, ge=0, le=5, description="交期评分"
    ),
    service_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="服务评分"),
    current_user: User = Depends(security.require_permission("supplier:read")),
) -> SuccessResponse[SupplierResponse]:
    """
    更新供应商评级
    
    - **quality_rating**: 质量评分（0-5）
    - **delivery_rating**: 交期评分（0-5）
    - **service_rating**: 服务评分（0-5）
    
    系统会自动计算综合评分和等级：
    - A级：综合评分 >= 4.5
    - B级：综合评分 >= 3.5
    - C级：综合评分 >= 2.5
    - D级：综合评分 < 2.5
    """
    service = VendorService(db)
    supplier = (
        service.db.query(service.model).filter(service.model.id == supplier_id).first()
    )
    if not supplier:
        from app.common.crud.exceptions import raise_not_found
        raise_not_found("供应商", supplier_id)

    if quality_rating is not None:
        supplier.quality_rating = quality_rating
    if delivery_rating is not None:
        supplier.delivery_rating = delivery_rating
    if service_rating is not None:
        supplier.service_rating = service_rating

    ratings = []
    if supplier.quality_rating:
        ratings.append(float(supplier.quality_rating))
    if supplier.delivery_rating:
        ratings.append(float(supplier.delivery_rating))
    if supplier.service_rating:
        ratings.append(float(supplier.service_rating))

    if ratings:
        supplier.overall_rating = Decimal(sum(ratings) / len(ratings))
        avg_rating = float(supplier.overall_rating)
        if avg_rating >= 4.5:
            supplier.supplier_level = "A"
        elif avg_rating >= 3.5:
            supplier.supplier_level = "B"
        elif avg_rating >= 2.5:
            supplier.supplier_level = "C"
        else:
            supplier.supplier_level = "D"

    service.db.add(supplier)
    service.db.commit()
    service.db.refresh(supplier)
    return success_response(
        data=service._to_response(supplier),
        message="供应商评级更新成功"
    )


@router.get(
    "/{supplier_id}/materials",
    response_model=PaginatedResponse[Any],
    summary="获取供应商物料列表",
    description="获取指定供应商关联的物料列表"
)
def get_supplier_materials(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.require_permission("supplier:read")),
) -> PaginatedResponse[Any]:
    """
    获取供应商的物料列表
    
    - **supplier_id**: 供应商ID
    - **page**: 页码
    - **page_size**: 每页数量
    """
    query = (
        db.query(Material)
        .join(MaterialSupplier, Material.id == MaterialSupplier.material_id)
        .filter(MaterialSupplier.supplier_id == supplier_id)
    )

    total = query.count()
    materials = (
        apply_pagination(query.order_by(desc(Material.created_at)), pagination.offset, pagination.limit).all()
    )

    return paginated_response(
        items=materials,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )
