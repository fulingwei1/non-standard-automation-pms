from typing import Any, List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Customer, Project
from app.schemas.project import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
def read_customers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（客户名称/编码）"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建新客户
    """
    # 检查客户编码是否已存在
    customer = (
        db.query(Customer)
        .filter(Customer.customer_code == customer_in.customer_code)
        .first()
    )
    if customer:
        raise HTTPException(
            status_code=400,
            detail="该客户编码已存在",
        )

    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def read_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
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
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新客户信息
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=200)
def delete_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.get_current_active_user),
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


@router.get("/{customer_id}/projects", response_model=PaginatedResponse)
def get_customer_projects(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户的项目列表
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    query = db.query(Project).filter(Project.customer_id == customer_id)
    total = query.count()
    offset = (page - 1) * page_size
    projects = query.order_by(desc(Project.created_at)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=projects,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
