# -*- coding: utf-8 -*-
"""
报价CRUD - 自动生成
从 sales/quotes.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.sales import (

from app.schemas.sales import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/quotes",
    tags=["quotes_crud"]
)

# 共 4 个路由

# ==================== 报价基础CRUD ====================


@router.get("/quotes", response_model=PaginatedResponse[QuoteResponse])
def read_quotes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    opportunity_id: Optional[int] = Query(None, description="商机ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价列表
    Issue 7.1: 已集成数据权限过滤
    """
    query = db.query(Quote).options(
        joinedload(Quote.opportunity),
        joinedload(Quote.customer),
        joinedload(Quote.owner)
    )

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Quote, 'owner_id')

    if keyword:
        query = query.filter(Quote.quote_code.contains(keyword))

    if status:
        query = query.filter(Quote.status == status)

    if opportunity_id:
        query = query.filter(Quote.opportunity_id == opportunity_id)

    total = query.count()
    offset = (page - 1) * page_size
    quotes = query.order_by(desc(Quote.created_at)).offset(offset).limit(page_size).all()

    quote_responses = []
    for quote in quotes:
        versions = db.query(QuoteVersion).options(
            joinedload(QuoteVersion.creator),
            joinedload(QuoteVersion.approver)
        ).filter(QuoteVersion.quote_id == quote.id).all()
        quote_dict = {
            **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
            "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
            "customer_name": quote.customer.customer_name if quote.customer else None,
            "owner_name": quote.owner.real_name if quote.owner else None,
            "versions": [],
        }
        for v in versions:
            items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
            v_dict = {
                **{c.name: getattr(v, c.name) for c in v.__table__.columns},
                "created_by_name": v.creator.real_name if v.creator else None,
                "approved_by_name": v.approver.real_name if v.approver else None,
                "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
            }
            quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        quote_responses.append(QuoteResponse(**quote_dict))

    return PaginatedResponse(
        items=quote_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
def create_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_in: QuoteCreate,
    skip_g2_validation: bool = Query(False, description="跳过G2验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报价（G2阶段门验证）
    """
    # 检查商机是否存在
    opportunity = db.query(Opportunity).filter(Opportunity.id == quote_in.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # G2验证
    if not skip_g2_validation:
        is_valid, errors = validate_g2_opportunity_to_quote(opportunity)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"G2阶段门验证失败: {', '.join(errors)}"
            )

    quote_data = quote_in.model_dump(exclude={"version"})

    # 如果没有提供编码，自动生成
    if not quote_data.get("quote_code"):
        quote_data["quote_code"] = generate_quote_code(db)
    else:
        existing = db.query(Quote).filter(Quote.quote_code == quote_data["quote_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="报价编码已存在")

    if not quote_data.get("owner_id"):
        quote_data["owner_id"] = current_user.id

    quote = Quote(**quote_data)
    db.add(quote)
    db.flush()

    # 创建报价版本
    if quote_in.version:
        version_data = quote_in.version.model_dump(exclude={"items"})
        version_data["quote_id"] = quote.id
        version_data["created_by"] = current_user.id
        version = QuoteVersion(**version_data)
        db.add(version)
        db.flush()

        quote.current_version_id = version.id

        # 创建报价明细
        if quote_in.version.items:
            for item_data in quote_in.version.items:
                item_dict = item_data.model_dump()
                item_dict["quote_version_id"] = version.id
                item = QuoteItem(**item_dict)
                db.add(item)

    db.commit()
    db.refresh(quote)

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first() if quote.current_version_id else None
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all() if version else []

    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": opportunity.opp_code if opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }

    if version:
        version_dict = {
            **{c.name: getattr(version, c.name) for c in version.__table__.columns},
            "created_by_name": version.creator.real_name if version.creator else None,
            "approved_by_name": version.approver.real_name if version.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"] = [QuoteVersionResponse(**version_dict)]

    return QuoteResponse(**quote_dict)


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def read_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价详情
    """
    quote = db.query(Quote).options(joinedload(Quote.opportunity), joinedload(Quote.customer)).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).all()
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        if v.id == quote.current_version_id:
            quote_dict["current_version"] = QuoteVersionResponse(**v_dict)

    return QuoteResponse(**quote_dict)


@router.put("/quotes/{quote_id}", response_model=QuoteResponse)
def update_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    quote_in: QuoteUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报价
    Issue 7.2: 已集成操作权限检查
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(quote),
        quote.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此报价")

    update_data = quote_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quote, field, value)

    db.commit()
    db.refresh(quote)

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).all()
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        if v.id == quote.current_version_id:
            quote_dict["current_version"] = QuoteVersionResponse(**v_dict)

    return QuoteResponse(**quote_dict)



