# -*- coding: utf-8 -*-
"""
客户基本CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import CustomerCreate, CustomerResponse, CustomerUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
def read_customers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（客户名称/编码）"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("customer:read")),
) -> Any:
    """
    获取客户列表（支持分页、搜索、筛选）
    """
    query = db.query(Customer)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Customer.customer_name.contains(keyword),
                Customer.customer_code.contains(keyword),
            )
        )

    # 行业筛选
    if industry:
        query = query.filter(Customer.industry == industry)

    # 启用状态筛选
    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    customers = query.order_by(desc(Customer.created_at)).offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=customers,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


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
    from app.utils.number_generator import generate_customer_code

    # 如果没有提供客户编码，自动生成
    customer_data = customer_in.model_dump()
    if not customer_data.get('customer_code'):
        customer_data['customer_code'] = generate_customer_code(db)

    # 检查客户编码是否已存在
    customer = (
        db.query(Customer)
        .filter(Customer.customer_code == customer_data['customer_code'])
        .first()
    )
    if customer:
        raise HTTPException(
            status_code=400,
            detail="该客户编码已存在",
        )

    customer = Customer(**customer_data)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


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
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


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
    import logging
    logger = logging.getLogger(__name__)

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 记录需要同步的字段
    update_data = customer_in.model_dump(exclude_unset=True)
    sync_fields = ["customer_name", "contact_person", "contact_phone"]
    has_sync_fields = any(field in update_data for field in sync_fields)

    # 更新客户信息
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.add(customer)
    db.flush()  # 先flush，确保customer对象已更新

    # 如果启用了自动同步，且更新了需要同步的字段，则自动同步
    if auto_sync and has_sync_fields:
        try:
            from app.services.data_sync_service import DataSyncService
            sync_service = DataSyncService(db)

            # 同步到项目
            project_sync_result = sync_service.sync_customer_to_projects(customer_id)
            if project_sync_result.get("success") and project_sync_result.get("updated_count", 0) > 0:
                logger.info(
                    f"客户 {customer_id} 信息已自动同步到 {project_sync_result.get('updated_count')} 个项目: "
                    f"{', '.join(project_sync_result.get('updated_fields', []))}"
                )

            # 同步到合同
            contract_sync_result = sync_service.sync_customer_to_contracts(customer_id)
            if contract_sync_result.get("success") and contract_sync_result.get("updated_count", 0) > 0:
                logger.info(
                    f"客户 {customer_id} 信息已自动同步到 {contract_sync_result.get('updated_count')} 个合同: "
                    f"{', '.join(contract_sync_result.get('updated_fields', []))}"
                )
        except Exception as e:
            # 同步失败不影响客户更新，只记录错误日志
            logger.error(f"客户信息自动同步失败: {str(e)}", exc_info=True)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=200)
def delete_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.require_permission("customer:delete")),
) -> Any:
    """
    删除客户（软删除）
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查是否有关联项目
    project_count = db.query(Project).filter(Project.customer_id == customer_id).count()
    if project_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该客户下还有 {project_count} 个项目，无法删除"
        )

    # 软删除：设置为非激活状态
    customer.is_active = False
    db.add(customer)
    db.commit()

    return ResponseModel(code=200, message="客户已删除")
