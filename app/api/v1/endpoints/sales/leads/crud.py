# -*- coding: utf-8 -*-
"""
线索基础CRUD操作
包含：列表、创建、详情、更新、删除
"""

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.advantage_product import AdvantageProduct
from app.models.sales import Lead
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sales import (
    LeadCreate,
    LeadResponse,
    LeadUpdate,
)

from ..utils import (
    generate_lead_code,
    get_entity_creator_id,
)

router = APIRouter()


@router.get("/leads", response_model=PaginatedResponse[LeadResponse])
def read_leads(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索列表
    Issue 7.1: 已集成数据权限过滤
    """
    query = db.query(Lead)

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Lead, 'owner_id')

    if keyword:
        query = query.filter(
            or_(
                Lead.lead_code.contains(keyword),
                Lead.customer_name.contains(keyword),
                Lead.contact_name.contains(keyword),
            )
        )

    if status:
        query = query.filter(Lead.status == status)

    if owner_id:
        query = query.filter(Lead.owner_id == owner_id)

    total = query.count()
    offset = (page - 1) * page_size
    # 默认按优先级排序，如果没有优先级则按创建时间排序
    leads = query.order_by(
        desc(Lead.priority_score).nullslast(),
        desc(Lead.created_at)
    ).offset(offset).limit(page_size).all()

    # 填充负责人名称和优势产品信息
    lead_responses = []
    for lead in leads:
        lead_dict = {
            **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
            "owner_name": lead.owner.real_name if lead.owner else None,
        }

        # 获取优势产品详情（简化版，只在列表中显示产品数量）
        if lead.selected_advantage_products:
            try:
                product_ids = json.loads(lead.selected_advantage_products)
                products = db.query(AdvantageProduct).filter(
                    AdvantageProduct.id.in_(product_ids)
                ).all()
                lead_dict["advantage_products"] = [
                    {
                        "id": p.id,
                        "product_code": p.product_code,
                        "product_name": p.product_name,
                        "category_id": p.category_id,
                    }
                    for p in products
                ]
            except (json.JSONDecodeError, Exception):
                lead_dict["advantage_products"] = []

        lead_responses.append(LeadResponse(**lead_dict))

    return PaginatedResponse(
        items=lead_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/leads", response_model=LeadResponse, status_code=201)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: LeadCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建线索
    """
    # 如果没有提供编码，自动生成
    lead_data = lead_in.model_dump()
    if not lead_data.get("lead_code"):
        lead_data["lead_code"] = generate_lead_code(db)
    else:
        # 检查编码是否已存在
        existing = db.query(Lead).filter(Lead.lead_code == lead_data["lead_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="线索编码已存在")

    # 如果没有指定负责人，默认使用当前用户
    if not lead_data.get("owner_id"):
        lead_data["owner_id"] = current_user.id

    # 处理优势产品选择
    selected_products = lead_data.pop("selected_advantage_products", None)
    if selected_products and len(selected_products) > 0:
        # 验证产品ID是否存在
        products = db.query(AdvantageProduct).filter(
            AdvantageProduct.id.in_(selected_products),
            AdvantageProduct.is_active == True
        ).all()

        if len(products) != len(selected_products):
            raise HTTPException(status_code=400, detail="部分优势产品ID不存在或已禁用")

        # 存储为JSON数组
        lead_data["selected_advantage_products"] = json.dumps(selected_products)
        lead_data["is_advantage_product"] = True
        lead_data["product_match_type"] = "ADVANTAGE"
    else:
        # 如果没有选择优势产品，设置为未知
        lead_data["selected_advantage_products"] = None
        lead_data["is_advantage_product"] = False
        lead_data["product_match_type"] = "UNKNOWN"

    lead = Lead(**lead_data)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # 构造响应，包含优势产品详情
    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }

    # 获取优势产品详情
    if lead.selected_advantage_products:
        try:
            product_ids = json.loads(lead.selected_advantage_products)
            products = db.query(AdvantageProduct).filter(
                AdvantageProduct.id.in_(product_ids)
            ).all()
            lead_dict["advantage_products"] = [
                {
                    "id": p.id,
                    "product_code": p.product_code,
                    "product_name": p.product_name,
                    "category_id": p.category_id,
                }
                for p in products
            ]
        except (json.JSONDecodeError, Exception):
            lead_dict["advantage_products"] = []

    return LeadResponse(**lead_dict)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def read_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索详情
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }

    # 获取优势产品详情
    if lead.selected_advantage_products:
        try:
            product_ids = json.loads(lead.selected_advantage_products)
            products = db.query(AdvantageProduct).filter(
                AdvantageProduct.id.in_(product_ids)
            ).all()
            lead_dict["advantage_products"] = [
                {
                    "id": p.id,
                    "product_code": p.product_code,
                    "product_name": p.product_name,
                    "category_id": p.category_id,
                }
                for p in products
            ]
        except (json.JSONDecodeError, Exception):
            lead_dict["advantage_products"] = []

    return LeadResponse(**lead_dict)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    lead_in: LeadUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新线索
    Issue 7.2: 已集成操作权限检查
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(lead),
        lead.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此线索")

    update_data = lead_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }
    return LeadResponse(**lead_dict)


@router.delete("/leads/{lead_id}", response_model=ResponseModel)
def delete_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除线索
    Issue 7.2: 已集成操作权限检查（仅创建人、销售总监、管理员可以删除）
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # Issue 7.2: 检查删除权限
    if not security.check_sales_delete_permission(
        current_user,
        db,
        get_entity_creator_id(lead),
    ):
        raise HTTPException(status_code=403, detail="您没有权限删除此线索")

    db.delete(lead)
    db.commit()

    return ResponseModel(code=200, message="线索已删除")
