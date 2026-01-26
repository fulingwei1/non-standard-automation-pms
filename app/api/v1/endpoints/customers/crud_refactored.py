# -*- coding: utf-8 -*-
"""
客户基本CRUD操作（重构版）

使用通用CRUD路由生成器和统一响应格式，去除重复代码。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.models.user import User
from app.schemas.project.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService
from app.api.v1.endpoints.base_crud_router_sync import create_crud_router_sync

# 创建通用CRUD路由
crud_router = create_crud_router_sync(
    service_class=CustomerService,
    create_schema=CustomerCreate,
    update_schema=CustomerUpdate,
    response_schema=CustomerResponse,
    resource_name="客户",
    resource_name_plural="客户列表",
    prefix="",
    tags=["customers"],
    keyword_fields=["customer_name", "customer_code", "short_name"],
    unique_fields=["customer_code"],
    permission_read="customer:read",
    permission_create="customer:create",
    permission_update="customer:update",
    permission_delete="customer:delete",
    enable_list=False,  # 禁用通用列表端点，使用自定义的列表端点
    enable_delete=False,  # 禁用通用删除端点，使用自定义的删除端点（支持软删除）
)

# 创建主路由
router = APIRouter()

# 包含通用CRUD路由
router.include_router(crud_router)

# ========== 覆盖列表查询端点（支持额外筛选参数） ==========

@router.get(
    "/",
    response_model=PaginatedResponse[CustomerResponse],
    summary="客户列表",
    description="分页查询客户列表，支持筛选、搜索、排序"
)
def list_customers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
    keyword: Optional[str] = Query(None, description="关键词搜索（客户名称/编码）"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("customer:read")),
) -> PaginatedResponse[CustomerResponse]:
    """
    获取客户列表（支持分页、搜索、筛选）
    
    - **keyword**: 关键词搜索（客户名称/编码）
    - **industry**: 行业筛选
    - **is_active**: 是否启用
    """
    service = CustomerService(db)
    result = service.list_customers(
        page=page,
        page_size=page_size,
        keyword=keyword,
        industry=industry,
        status="ACTIVE" if is_active is True else None,
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
    response_model=SuccessResponse[CustomerResponse],
    status_code=201,
    summary="创建客户",
    description="创建新客户，如果未提供客户编码，系统将自动生成"
)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
    current_user: User = Depends(security.require_permission("customer:create")),
) -> SuccessResponse[CustomerResponse]:
    """
    创建新客户
    
    如果未提供客户编码，系统将自动生成 CUS-xxxxxxx 格式的编码
    """
    service = CustomerService(db)
    if not customer_in.customer_code:
        customer_in.customer_code = service.generate_code()
    
    customer_data = service.create(
        customer_in, check_unique={"customer_code": customer_in.customer_code}
    )
    
    return success_response(
        data=customer_data,
        message="客户创建成功",
        code=201
    )


# ========== 覆盖更新端点（支持自动同步） ==========

@router.put(
    "/{customer_id}",
    response_model=SuccessResponse[CustomerResponse],
    summary="更新客户",
    description="更新客户信息，支持自动同步客户信息到关联的项目和合同"
)
def update_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    customer_in: CustomerUpdate,
    auto_sync: bool = Query(True, description="是否自动同步客户信息到项目和合同"),
    current_user: User = Depends(security.require_permission("customer:update")),
) -> SuccessResponse[CustomerResponse]:
    """
    更新客户信息
    
    支持自动同步客户信息到关联的项目和合同
    """
    service = CustomerService(db)
    # 自动同步逻辑可以在 service._after_update 中处理，或者在这里显式调用
    # 为了保持透明度，我们在 service 中增加相关的处理
    if hasattr(service, "set_auto_sync"):
        service.set_auto_sync(auto_sync)
    
    customer_data = service.update(customer_id, customer_in)
    return success_response(
        data=customer_data,
        message="客户更新成功"
    )


# ========== 覆盖删除端点（支持软删除） ==========

@router.delete(
    "/{customer_id}",
    response_model=SuccessResponse,
    status_code=200,
    summary="删除客户",
    description="删除客户（建议使用软删除）"
)
def delete_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.require_permission("customer:delete")),
) -> SuccessResponse:
    """
    删除客户（建议使用软删除）
    """
    service = CustomerService(db)
    service.delete(customer_id, soft_delete=True)
    return success_response(
        data=None,
        message="客户已删除"
    )
