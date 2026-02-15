# -*- coding: utf-8 -*-
"""
客户档案管理 - CRUD操作
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.common.pagination import get_pagination_query, PaginationParams
from app.common.query_filters import apply_keyword_filter
from app.models.project.customer import Customer
from app.models.sales.contacts import Contact
from app.models.sales.customer_tags import CustomerTag
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerStatsResponse,
)

router = APIRouter()


def generate_customer_code(db: Session) -> str:
    """生成客户编码"""
    # 生成格式: CUS + 年月 + 4位序号 (例如: CUS202402150001)
    today = datetime.now()
    prefix = f"CUS{today.strftime('%Y%m%d')}"
    
    last_customer = (
        db.query(Customer)
        .filter(Customer.customer_code.like(f"{prefix}%"))
        .order_by(desc(Customer.customer_code))
        .first()
    )
    
    if last_customer:
        last_seq = int(last_customer.customer_code[-4:])
        new_seq = last_seq + 1
    else:
        new_seq = 1
    
    return f"{prefix}{new_seq:04d}"


@router.get("/customers", response_model=PaginatedResponse[CustomerResponse])
def read_customers(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（客户名称、编号）"),
    customer_level: Optional[str] = Query(None, description="客户等级筛选（A/B/C/D）"),
    status: Optional[str] = Query(None, description="客户状态筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    sales_owner_id: Optional[int] = Query(None, description="负责销售人员ID筛选"),
    order_by: Optional[str] = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户列表
    支持搜索、筛选和排序
    """
    query = db.query(Customer).options(
        joinedload(Customer.sales_owner),
        joinedload(Customer.tags),
        joinedload(Customer.contacts),
    )

    # 应用数据权限过滤（销售人员只能看到自己负责的客户）
    query = security.filter_sales_data_by_scope(query, current_user, db, Customer, 'sales_owner_id')

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Customer.customer_name.contains(keyword),
                Customer.customer_code.contains(keyword),
                Customer.short_name.contains(keyword),
            )
        )

    # 筛选条件
    if customer_level:
        query = query.filter(Customer.customer_level == customer_level)
    
    if status:
        query = query.filter(Customer.status == status)
    
    if industry:
        query = query.filter(Customer.industry == industry)
    
    if sales_owner_id:
        query = query.filter(Customer.sales_owner_id == sales_owner_id)

    # 排序
    order_column = getattr(Customer, order_by, Customer.created_at)
    if order_desc:
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(order_column)

    total = query.count()
    customers = query.offset(pagination.offset).limit(pagination.limit).all()

    # 构建响应
    customer_responses = []
    for customer in customers:
        customer_dict = {
            **{c.name: getattr(customer, c.name) for c in customer.__table__.columns},
            "sales_owner_name": customer.sales_owner.real_name if customer.sales_owner else None,
            "contacts_count": len(customer.contacts),
            "tags": [tag.tag_name for tag in customer.tags],
        }
        customer_responses.append(CustomerResponse(**customer_dict))

    return pagination.to_response(customer_responses, total)


@router.get("/customers/stats", response_model=CustomerStatsResponse)
def get_customer_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户统计数据
    """
    query = db.query(Customer)
    
    # 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Customer, 'sales_owner_id')

    # 统计各状态客户数
    total_customers = query.count()
    potential_count = query.filter(Customer.status == "potential").count()
    prospect_count = query.filter(Customer.status == "prospect").count()
    customer_count = query.filter(Customer.status == "customer").count()
    lost_count = query.filter(Customer.status == "lost").count()

    # 统计各等级客户数
    level_a_count = query.filter(Customer.customer_level == "A").count()
    level_b_count = query.filter(Customer.customer_level == "B").count()
    level_c_count = query.filter(Customer.customer_level == "C").count()
    level_d_count = query.filter(Customer.customer_level == "D").count()

    # 统计年成交额和平均合作年限
    revenue_result = query.with_entities(
        func.sum(Customer.annual_revenue),
        func.avg(Customer.cooperation_years)
    ).first()

    total_annual_revenue = revenue_result[0] or 0
    avg_cooperation_years = float(revenue_result[1] or 0)

    return CustomerStatsResponse(
        total_customers=total_customers,
        potential_count=potential_count,
        prospect_count=prospect_count,
        customer_count=customer_count,
        lost_count=lost_count,
        level_a_count=level_a_count,
        level_b_count=level_b_count,
        level_c_count=level_c_count,
        level_d_count=level_d_count,
        total_annual_revenue=total_annual_revenue,
        avg_cooperation_years=avg_cooperation_years,
    )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def read_customer(
    customer_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户详情
    """
    customer = db.query(Customer).options(
        joinedload(Customer.sales_owner),
        joinedload(Customer.tags),
        joinedload(Customer.contacts),
    ).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查数据权限
    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权访问该客户")

    customer_dict = {
        **{c.name: getattr(customer, c.name) for c in customer.__table__.columns},
        "sales_owner_name": customer.sales_owner.real_name if customer.sales_owner else None,
        "contacts_count": len(customer.contacts),
        "tags": [tag.tag_name for tag in customer.tags],
    }

    return CustomerResponse(**customer_dict)


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建客户
    """
    # 生成客户编码
    if not customer_in.customer_code:
        customer_code = generate_customer_code(db)
    else:
        # 检查编码是否重复
        existing = db.query(Customer).filter(Customer.customer_code == customer_in.customer_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="客户编码已存在")
        customer_code = customer_in.customer_code

    # 创建客户
    customer_data = customer_in.model_dump(exclude_unset=True)
    customer_data["customer_code"] = customer_code
    
    # 如果没有指定负责人，默认为当前用户
    if not customer_data.get("sales_owner_id"):
        customer_data["sales_owner_id"] = current_user.id

    customer = Customer(**customer_data)
    
    # 自动更新客户等级
    customer.update_level()
    
    db.add(customer)
    db.commit()
    db.refresh(customer)

    # 加载关联数据
    db.refresh(customer, attribute_names=['sales_owner', 'tags', 'contacts'])

    customer_dict = {
        **{c.name: getattr(customer, c.name) for c in customer.__table__.columns},
        "sales_owner_name": customer.sales_owner.real_name if customer.sales_owner else None,
        "contacts_count": 0,
        "tags": [],
    }

    return CustomerResponse(**customer_dict)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新客户信息
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查数据权限
    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权修改该客户")

    # 更新字段
    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    # 如果更新了年成交额或合作年限，重新计算客户等级
    if "annual_revenue" in update_data or "cooperation_years" in update_data:
        customer.update_level()

    db.commit()
    db.refresh(customer)

    # 加载关联数据
    db.refresh(customer, attribute_names=['sales_owner', 'tags', 'contacts'])

    customer_dict = {
        **{c.name: getattr(customer, c.name) for c in customer.__table__.columns},
        "sales_owner_name": customer.sales_owner.real_name if customer.sales_owner else None,
        "contacts_count": len(customer.contacts),
        "tags": [tag.tag_name for tag in customer.tags],
    }

    return CustomerResponse(**customer_dict)


@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> None:
    """
    删除客户
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查数据权限（管理员或负责人可删除）
    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        if not security.is_admin(current_user):
            raise HTTPException(status_code=403, detail="无权删除该客户")

    db.delete(customer)
    db.commit()
