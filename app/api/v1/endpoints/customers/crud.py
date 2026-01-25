# -*- coding: utf-8 -*-
"""
客户基本CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
def read_customers(
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
) -> Any:
    """
    获取客户列表（支持分页、搜索、筛选）
    """
    service = CustomerService(db)
    result = service.list_customers(
        page=page,
        page_size=page_size,
        keyword=keyword,
        industry=industry,
        status="ACTIVE" if is_active is True else None,
    )
    return PaginatedResponse(**result)


@router.post("/", response_model=CustomerResponse)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
    current_user: User = Depends(security.require_permission("customer:create")),
) -> Any:
    """
    创建新客户

    如果未提供客户编码，系统将自动生成 CUS-xxxxxxx 格式的编码
    """
    service = CustomerService(db)
    if not customer_in.customer_code:
        customer_in.customer_code = service.generate_code()

    return service.create(
        customer_in, check_unique={"customer_code": customer_in.customer_code}
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
def read_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.require_permission("customer:read")),
) -> Any:
    """
    Get customer by ID.
    """
    service = CustomerService(db)
    return service.get(customer_id)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    customer_in: CustomerUpdate,
    auto_sync: bool = Query(True, description="是否自动同步客户信息到项目和合同"),
    current_user: User = Depends(security.require_permission("customer:update")),
) -> Any:
    """
    更新客户信息

    支持自动同步客户信息到关联的项目和合同
    """
    service = CustomerService(db)
    # 自动同步逻辑可以在 service._after_update 中处理，或者在这里显式调用
    # 为了保持透明度，我们在 service 中增加相关的处理
    if hasattr(service, "set_auto_sync"):
        service.set_auto_sync(auto_sync)

    return service.update(customer_id, customer_in)


@router.delete("/{customer_id}", status_code=200)
def delete_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.require_permission("customer:delete")),
) -> Any:
    """
    删除客户（建议使用软删除）
    """
    service = CustomerService(db)
    service.delete(customer_id, soft_delete=True)
    return ResponseModel(code=200, message="客户已删除")
