# -*- coding: utf-8 -*-
"""
联系人管理 - CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.common.pagination import get_pagination_query, PaginationParams
from app.models.project.customer import Customer
from app.models.sales.contacts import Contact
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    SetPrimaryRequest,
)

from app.utils.db_helpers import delete_obj, get_or_404, save_obj
router = APIRouter()


@router.get("/customers/{customer_id}/contacts", response_model=PaginatedResponse[ContactResponse])
def read_customer_contacts(
    customer_id: int,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取指定客户的联系人列表
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权访问该客户的联系人")

    # 查询联系人
    query = db.query(Contact).filter(Contact.customer_id == customer_id)
    total = query.count()

    # 主要联系人排在前面
    contacts = (
        query.options(joinedload(Contact.customer))
        .order_by(Contact.is_primary.desc(), Contact.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    # 构建响应
    contact_responses = []
    for contact in contacts:
        contact_dict = {
            **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
            "customer_name": contact.customer.customer_name if contact.customer else None,
        }
        contact_responses.append(ContactResponse(**contact_dict))

    return pagination.to_response(contact_responses, total)


@router.get("/contacts", response_model=PaginatedResponse[ContactResponse])
def read_contacts(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（姓名、手机、邮箱）"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取联系人列表（全局）
    """
    query = db.query(Contact).options(joinedload(Contact.customer))

    # 关键词搜索
    if keyword:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Contact.name.contains(keyword),
                Contact.mobile.contains(keyword),
                Contact.email.contains(keyword),
            )
        )

    if customer_id:
        query = query.filter(Contact.customer_id == customer_id)

    # 应用数据权限（通过客户的负责人过滤）
    if not security.is_admin(current_user):
        query = query.join(Customer).filter(Customer.sales_owner_id == current_user.id)

    total = query.count()
    contacts = (
        query.order_by(Contact.is_primary.desc(), Contact.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    # 构建响应
    contact_responses = []
    for contact in contacts:
        contact_dict = {
            **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
            "customer_name": contact.customer.customer_name if contact.customer else None,
        }
        contact_responses.append(ContactResponse(**contact_dict))

    return pagination.to_response(contact_responses, total)


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def read_contact(
    contact_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取联系人详情
    """
    contact = (
        db.query(Contact)
        .options(joinedload(Contact.customer))
        .filter(Contact.id == contact_id)
        .first()
    )

    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    # 检查权限
    if contact.customer and not security.check_sales_data_permission(
        contact.customer, current_user, db, 'sales_owner_id'
    ):
        raise HTTPException(status_code=403, detail="无权访问该联系人")

    contact_dict = {
        **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
        "customer_name": contact.customer.customer_name if contact.customer else None,
    }

    return ContactResponse(**contact_dict)


@router.post("/customers/{customer_id}/contacts", response_model=ContactResponse, status_code=201)
def create_contact(
    customer_id: int,
    *,
    db: Session = Depends(deps.get_db),
    contact_in: ContactCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为指定客户添加联系人
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权为该客户添加联系人")

    # 确保 customer_id 一致
    contact_data = contact_in.model_dump(exclude_unset=True)
    contact_data["customer_id"] = customer_id

    # 如果设置为主要联系人，先取消其他主要联系人
    if contact_data.get("is_primary"):
        db.query(Contact).filter(
            Contact.customer_id == customer_id,
            Contact.is_primary == True
        ).update({"is_primary": False})

    contact = Contact(**contact_data)
    save_obj(db, contact)

    # 加载客户信息
    db.refresh(contact, attribute_names=['customer'])

    contact_dict = {
        **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
        "customer_name": contact.customer.customer_name if contact.customer else None,
    }

    return ContactResponse(**contact_dict)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    *,
    db: Session = Depends(deps.get_db),
    contact_in: ContactUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新联系人信息
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    # 检查权限
    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
    if customer and not security.check_sales_data_permission(
        customer, current_user, db, 'sales_owner_id'
    ):
        raise HTTPException(status_code=403, detail="无权修改该联系人")

    # 更新字段
    update_data = contact_in.model_dump(exclude_unset=True)
    
    # 如果设置为主要联系人，先取消其他主要联系人
    if update_data.get("is_primary"):
        db.query(Contact).filter(
            Contact.customer_id == contact.customer_id,
            Contact.id != contact_id,
            Contact.is_primary == True
        ).update({"is_primary": False})

    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    # 加载客户信息
    db.refresh(contact, attribute_names=['customer'])

    contact_dict = {
        **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
        "customer_name": contact.customer.customer_name if contact.customer else None,
    }

    return ContactResponse(**contact_dict)


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(
    contact_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> None:
    """
    删除联系人
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    # 检查权限
    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
    if customer and not security.check_sales_data_permission(
        customer, current_user, db, 'sales_owner_id'
    ):
        if not security.is_admin(current_user):
            raise HTTPException(status_code=403, detail="无权删除该联系人")

    delete_obj(db, contact)


@router.post("/contacts/{contact_id}/set-primary", response_model=ContactResponse)
def set_primary_contact(
    contact_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    设置为主要联系人
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    # 检查权限
    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
    if customer and not security.check_sales_data_permission(
        customer, current_user, db, 'sales_owner_id'
    ):
        raise HTTPException(status_code=403, detail="无权修改该联系人")

    # 取消该客户的其他主要联系人
    db.query(Contact).filter(
        Contact.customer_id == contact.customer_id,
        Contact.id != contact_id,
        Contact.is_primary == True
    ).update({"is_primary": False})

    # 设置为主要联系人
    contact.is_primary = True
    db.commit()
    db.refresh(contact)

    # 加载客户信息
    db.refresh(contact, attribute_names=['customer'])

    contact_dict = {
        **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
        "customer_name": contact.customer.customer_name if contact.customer else None,
    }

    return ContactResponse(**contact_dict)
