# -*- coding: utf-8 -*-
"""
联系人管理 - CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.project.customer import Customer
from app.models.sales.contacts import Contact
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
)
from app.services.sales.contact_operation_audit import (
    contact_audit_value,
    log_contact_operation,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _log_primary_contact_demotions(
    db: Session,
    customer_id: int,
    operator: User,
    *,
    exclude_contact_id: Optional[int] = None,
) -> None:
    query = db.query(Contact).filter(
        Contact.customer_id == customer_id,
        Contact.is_primary.is_(True),
    )
    if exclude_contact_id is not None:
        query = query.filter(Contact.id != exclude_contact_id)

    for previous_primary in query.all():
        old_primary_value = contact_audit_value(previous_primary)
        previous_primary.is_primary = False
        log_contact_operation(
            db,
            previous_primary,
            SalesOperationType.STATUS_CHANGE,
            operator,
            old_value=old_primary_value,
            new_value=contact_audit_value(previous_primary),
            operation_desc="取消主要联系人",
        )


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

    if not security.check_sales_data_permission(customer, current_user, db, "sales_owner_id"):
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

    # 应用数据权限（通过客户的负责人过滤，已集成完整scope）
    from app.core.sales_permissions import get_sales_data_scope
    from app.services.data_scope import DataScopeService

    scope = get_sales_data_scope(current_user, db)
    if scope == "ALL":
        pass  # 全部可见
    elif scope == "DEPT":
        if current_user.department:
            dept_users = db.query(User).filter(User.department == current_user.department).all()
            dept_user_ids = [u.id for u in dept_users]
            query = query.join(Customer).filter(
                Customer.sales_owner_id.in_(dept_user_ids + [current_user.id])
            )
        else:
            query = query.join(Customer).filter(Customer.sales_owner_id == current_user.id)
    elif scope == "TEAM":
        subordinate_ids = DataScopeService.get_subordinate_ids(db, current_user.id)
        allowed_ids = list(subordinate_ids | {current_user.id})
        query = query.join(Customer).filter(Customer.sales_owner_id.in_(allowed_ids))
    else:
        # OWN, PROJECT, FINANCE_ONLY, NONE
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
        contact.customer, current_user, db, "sales_owner_id"
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

    if not security.check_sales_data_permission(customer, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权为该客户添加联系人")

    # 确保 customer_id 一致
    contact_data = contact_in.model_dump(exclude_unset=True)
    contact_data["customer_id"] = customer_id

    # 如果设置为主要联系人，先取消其他主要联系人
    if contact_data.get("is_primary"):
        _log_primary_contact_demotions(db, customer_id, current_user)

    contact = Contact(**contact_data)
    db.add(contact)
    db.flush()
    log_contact_operation(
        db,
        contact,
        SalesOperationType.CREATE,
        current_user,
        new_value=contact_audit_value(contact),
        operation_desc="创建客户联系人",
    )
    db.commit()
    db.refresh(contact)

    # 加载客户信息
    db.refresh(contact, attribute_names=["customer"])

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
    contact = get_or_404(db, Contact, contact_id, "联系人不存在")

    # 检查权限
    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
    if customer and not security.check_sales_data_permission(
        customer, current_user, db, "sales_owner_id"
    ):
        raise HTTPException(status_code=403, detail="无权修改该联系人")

    # 更新字段
    old_value = contact_audit_value(contact)
    update_data = contact_in.model_dump(exclude_unset=True)

    # 如果设置为主要联系人，先取消其他主要联系人
    if update_data.get("is_primary"):
        _log_primary_contact_demotions(
            db,
            contact.customer_id,
            current_user,
            exclude_contact_id=contact_id,
        )

    for field, value in update_data.items():
        setattr(contact, field, value)

    log_contact_operation(
        db,
        contact,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=contact_audit_value(contact),
        operation_desc="更新客户联系人",
    )
    db.commit()
    db.refresh(contact)

    # 加载客户信息
    db.refresh(contact, attribute_names=["customer"])

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
    contact = get_or_404(db, Contact, contact_id, "联系人不存在")

    # 检查权限
    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
    if customer and not security.check_sales_data_permission(
        customer, current_user, db, "sales_owner_id"
    ):
        if not security.is_admin(current_user):
            raise HTTPException(status_code=403, detail="无权删除该联系人")

    old_value = contact_audit_value(contact)
    db.delete(contact)
    log_contact_operation(
        db,
        contact,
        SalesOperationType.DELETE,
        current_user,
        old_value=old_value,
        new_value={},
        operation_desc="删除客户联系人",
    )
    db.commit()


@router.post("/contacts/{contact_id}/set-primary", response_model=ContactResponse)
def set_primary_contact(
    contact_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    设置为主要联系人
    """
    contact = get_or_404(db, Contact, contact_id, "联系人不存在")

    # 检查权限
    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
    if customer and not security.check_sales_data_permission(
        customer, current_user, db, "sales_owner_id"
    ):
        raise HTTPException(status_code=403, detail="无权修改该联系人")

    # 取消该客户的其他主要联系人，并逐条留痕
    _log_primary_contact_demotions(
        db,
        contact.customer_id,
        current_user,
        exclude_contact_id=contact_id,
    )

    # 设置为主要联系人
    old_value = contact_audit_value(contact)
    contact.is_primary = True
    log_contact_operation(
        db,
        contact,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=old_value,
        new_value=contact_audit_value(contact),
        operation_desc="设置主要联系人",
    )
    db.commit()
    db.refresh(contact)

    # 加载客户信息
    db.refresh(contact, attribute_names=["customer"])

    contact_dict = {
        **{c.name: getattr(contact, c.name) for c in contact.__table__.columns},
        "customer_name": contact.customer.customer_name if contact.customer else None,
    }

    return ContactResponse(**contact_dict)
