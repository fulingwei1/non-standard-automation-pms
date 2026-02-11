# -*- coding: utf-8 -*-
"""
物料CRUD端点（重构版）

使用通用CRUD路由生成器和统一响应格式，去除重复代码。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.core.config import settings
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.models.user import User
from app.schemas.material import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from app.services.material_service import MaterialService
from app.api.v1.endpoints.base_crud_router_sync import create_crud_router_sync

# 创建通用CRUD路由
crud_router = create_crud_router_sync(
    service_class=MaterialService,
    create_schema=MaterialCreate,
    update_schema=MaterialUpdate,
    response_schema=MaterialResponse,
    resource_name="物料",
    resource_name_plural="物料列表",
    prefix="",
    tags=["materials"],
    keyword_fields=["material_code", "material_name"],
    unique_fields=["material_code"],
    permission_read="procurement:read",  # 使用require_procurement_access的权限
    permission_create="procurement:read",
    permission_update="procurement:read",
    permission_delete="procurement:read",
    enable_list=False,  # 禁用通用列表端点，使用自定义的列表端点
)

# 创建主路由
router = APIRouter()

# 包含通用CRUD路由
router.include_router(crud_router)

# ========== 覆盖列表查询端点（支持额外筛选参数） ==========

@router.get(
    "/",
    response_model=PaginatedResponse[MaterialResponse],
    summary="物料列表",
    description="分页查询物料列表，支持筛选、搜索、排序"
)
def list_materials(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（物料编码/名称）"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    material_type: Optional[str] = Query(None, description="物料类型筛选"),
    is_key_material: Optional[bool] = Query(None, description="是否关键物料"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> PaginatedResponse[MaterialResponse]:
    """
    获取物料列表（支持分页、搜索、筛选）
    
    - **keyword**: 关键词搜索（物料编码/名称）
    - **category_id**: 分类ID筛选
    - **material_type**: 物料类型筛选
    - **is_key_material**: 是否关键物料
    - **is_active**: 是否启用
    """
    service = MaterialService(db)
    result = service.list_materials(
        page=pagination.page,
        page_size=pagination.page_size,
        keyword=keyword,
        category_id=category_id,
        material_type=material_type,
        is_key_material=is_key_material,
        is_active=is_active,
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


# ========== 覆盖创建端点（支持自动生成编码） ==========

@router.post(
    "/",
    response_model=SuccessResponse[MaterialResponse],
    status_code=201,
    summary="创建物料",
    description="创建新物料，如果未提供物料编码，系统将根据物料类别自动生成"
)
def create_material(
    *,
    db: Session = Depends(deps.get_db),
    material_in: MaterialCreate,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> SuccessResponse[MaterialResponse]:
    """
    创建新物料
    
    如果未提供物料编码，系统将根据物料类别自动生成 MAT-{类别}-xxxxx 格式的编码
    """
    service = MaterialService(db)
    
    # 如果没有提供物料编码，自动生成
    if not material_in.material_code:
        material_in.material_code = service.generate_code(material_in.category_id)
    
    # 业务逻辑（唯一性检查、外键检查）将在 Service 层处理或通过 check_unique 参数
    material_data = service.create(
        material_in, check_unique={"material_code": material_in.material_code}
    )
    
    return success_response(
        data=material_data,
        message="物料创建成功",
        code=201
    )
