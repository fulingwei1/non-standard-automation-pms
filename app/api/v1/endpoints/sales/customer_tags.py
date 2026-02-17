# -*- coding: utf-8 -*-
"""
客户标签管理 - CRUD操作
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api import deps
from app.core import security
from app.models.project.customer import Customer
from app.models.sales.customer_tags import CustomerTag, PredefinedTags
from app.models.user import User
from app.schemas.sales import (
    CustomerTagCreate,
    CustomerTagBatchCreate,
    CustomerTagResponse,
    PredefinedTagsResponse,
)
from app.utils.db_helpers import get_or_404, delete_obj

router = APIRouter()


@router.get("/customer-tags/predefined", response_model=PredefinedTagsResponse)
def get_predefined_tags() -> Any:
    """
    获取预定义标签列表
    """
    return PredefinedTagsResponse(tags=PredefinedTags.all_tags())


@router.get("/customers/{customer_id}/tags", response_model=List[CustomerTagResponse])
def read_customer_tags(
    customer_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取指定客户的标签列表
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权访问该客户的标签")

    # 查询标签
    tags = (
        db.query(CustomerTag)
        .filter(CustomerTag.customer_id == customer_id)
        .order_by(CustomerTag.created_at.desc())
        .all()
    )

    return [
        CustomerTagResponse(**{c.name: getattr(tag, c.name) for c in tag.__table__.columns})
        for tag in tags
    ]


@router.post("/customers/{customer_id}/tags", response_model=CustomerTagResponse, status_code=201)
def create_customer_tag(
    customer_id: int,
    *,
    db: Session = Depends(deps.get_db),
    tag_in: CustomerTagCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为指定客户添加单个标签
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权为该客户添加标签")

    # 确保 customer_id 一致
    tag_data = tag_in.model_dump()
    tag_data["customer_id"] = customer_id

    # 检查标签是否已存在
    existing_tag = db.query(CustomerTag).filter(
        CustomerTag.customer_id == customer_id,
        CustomerTag.tag_name == tag_data["tag_name"]
    ).first()

    if existing_tag:
        raise HTTPException(status_code=400, detail="该客户已有此标签")

    # 创建标签
    tag = CustomerTag(**tag_data)
    db.add(tag)
    
    try:
        db.commit()
        db.refresh(tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="标签创建失败，可能已存在")

    return CustomerTagResponse(**{c.name: getattr(tag, c.name) for c in tag.__table__.columns})


@router.post("/customers/{customer_id}/tags/batch", response_model=List[CustomerTagResponse], status_code=201)
def create_customer_tags_batch(
    customer_id: int,
    *,
    db: Session = Depends(deps.get_db),
    tags_in: CustomerTagBatchCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为指定客户批量添加标签
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        raise HTTPException(status_code=403, detail="无权为该客户添加标签")

    # 获取已有标签
    existing_tags = db.query(CustomerTag.tag_name).filter(
        CustomerTag.customer_id == customer_id
    ).all()
    existing_tag_names = {tag[0] for tag in existing_tags}

    # 过滤掉已存在的标签
    new_tag_names = [name for name in tags_in.tag_names if name not in existing_tag_names]

    if not new_tag_names:
        raise HTTPException(status_code=400, detail="所有标签均已存在")

    # 批量创建标签
    new_tags = []
    for tag_name in new_tag_names:
        tag = CustomerTag(customer_id=customer_id, tag_name=tag_name)
        db.add(tag)
        new_tags.append(tag)

    db.commit()

    # 刷新所有标签
    for tag in new_tags:
        db.refresh(tag)

    return [
        CustomerTagResponse(**{c.name: getattr(tag, c.name) for c in tag.__table__.columns})
        for tag in new_tags
    ]


@router.delete("/customers/{customer_id}/tags/{tag_id}", status_code=204)
def delete_customer_tag(
    customer_id: int,
    tag_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> None:
    """
    删除客户标签
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        if not security.is_admin(current_user):
            raise HTTPException(status_code=403, detail="无权删除该客户的标签")

    # 查找标签
    tag = db.query(CustomerTag).filter(
        CustomerTag.id == tag_id,
        CustomerTag.customer_id == customer_id
    ).first()

    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    delete_obj(db, tag)


@router.delete("/customers/{customer_id}/tags", status_code=204)
def delete_customer_tags_by_name(
    customer_id: int,
    tag_name: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> None:
    """
    根据标签名称删除客户标签
    """
    # 检查客户是否存在及权限
    customer = get_or_404(db, Customer, customer_id, detail="客户不存在")

    if not security.check_sales_data_permission(customer, current_user, db, 'sales_owner_id'):
        if not security.is_admin(current_user):
            raise HTTPException(status_code=403, detail="无权删除该客户的标签")

    # 查找并删除标签
    tag = db.query(CustomerTag).filter(
        CustomerTag.customer_id == customer_id,
        CustomerTag.tag_name == tag_name
    ).first()

    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    delete_obj(db, tag)
