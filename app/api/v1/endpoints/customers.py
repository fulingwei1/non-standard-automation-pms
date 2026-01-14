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
    Customer360Response,
    Customer360Summary,
    Customer360ProjectItem,
    Customer360OpportunityItem,
    Customer360QuoteItem,
    Customer360ContractItem,
    Customer360InvoiceItem,
    Customer360PaymentPlanItem,
    Customer360CommunicationItem,
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.services.customer_360_service import Customer360Service
from app.services.data_scope_service import DataScopeService

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
    current_user: User = Depends(security.require_permission("customer:update")),
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


@router.get("/{customer_id}/projects", response_model=PaginatedResponse)
def get_customer_projects(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user: User = Depends(security.require_permission("customer:read")),
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


@router.get("/{customer_id}/360", response_model=Customer360Response)
def get_customer_360_overview(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.require_permission("customer:read")),
) -> Any:
    """
    获取客户360视图信息
    """
    if not DataScopeService.check_customer_access(db, current_user, customer_id):
        raise HTTPException(status_code=403, detail="无权访问该客户的数据")

    service = Customer360Service(db)
    try:
        overview = service.build_overview(customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    customer = overview["basic_info"]
    summary = overview["summary"]
    projects = [
        Customer360ProjectItem(
            project_id=p.id,
            project_code=p.project_code,
            project_name=p.project_name,
            stage=p.stage,
            status=p.status,
            progress_pct=p.progress_pct,
            contract_amount=p.contract_amount,
            planned_end_date=p.planned_end_date,
        )
        for p in overview["projects"]
    ]

    stage_probability = {
        "DISCOVERY": 0.15,
        "QUALIFIED": 0.3,
        "PROPOSAL": 0.55,
        "NEGOTIATION": 0.75,
        "WON": 1.0,
        "LOST": 0.0,
        "ON_HOLD": 0.1,
    }
    opportunities = [
        Customer360OpportunityItem(
            opportunity_id=o.id,
            opp_code=o.opp_code,
            opp_name=o.opp_name,
            stage=o.stage,
            est_amount=o.est_amount,
            owner_name=o.owner.real_name if o.owner else None,
            win_probability=stage_probability.get(o.stage or "", 0) * 100,
            updated_at=o.updated_at,
        )
        for o in overview["opportunities"]
    ]

    quotes = []
    for quote in overview["quotes"]:
        current_version = quote.current_version
        quotes.append(
            Customer360QuoteItem(
                quote_id=quote.id,
                quote_code=quote.quote_code,
                status=quote.status,
                total_price=current_version.total_price if current_version else None,
                gross_margin=current_version.gross_margin if current_version else None,
                owner_name=quote.owner.real_name if quote.owner else None,
                valid_until=quote.valid_until,
            )
        )

    contracts = [
        Customer360ContractItem(
            contract_id=c.id,
            contract_code=c.contract_code,
            status=c.status,
            contract_amount=c.contract_amount,
            signed_date=c.signed_date,
            project_code=c.project.project_code if c.project else None,
        )
        for c in overview["contracts"]
    ]

    invoices = [
        Customer360InvoiceItem(
            invoice_id=i.id,
            invoice_code=i.invoice_code,
            status=i.status,
            total_amount=i.total_amount,
            issue_date=i.issue_date,
            paid_amount=i.paid_amount,
        )
        for i in overview["invoices"]
    ]

    payment_plans = [
        Customer360PaymentPlanItem(
            plan_id=p.id,
            project_id=p.project_id,
            payment_name=p.payment_name,
            status=p.status,
            planned_amount=p.planned_amount,
            actual_amount=p.actual_amount,
            planned_date=p.planned_date,
            actual_date=p.actual_date,
        )
        for p in overview["payment_plans"]
    ]

    communications = [
        Customer360CommunicationItem(
            communication_id=comm.id,
            topic=comm.topic,
            communication_type=comm.communication_type,
            communication_date=comm.communication_date,
            owner_name=comm.created_by_name,
            follow_up_required=comm.follow_up_required,
        )
        for comm in overview["communications"]
    ]

    return Customer360Response(
        basic_info=customer,
        summary=Customer360Summary(**summary),
        projects=projects,
        opportunities=opportunities,
        quotes=quotes,
        contracts=contracts,
        invoices=invoices,
        payment_plans=payment_plans,
        communications=communications,
    )
