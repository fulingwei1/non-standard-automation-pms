# -*- coding: utf-8 -*-
"""
报价版本 - 自动生成
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
    prefix="/quotes/{quote_id}/versions",
    tags=["versions"]
)

# 共 2 个路由

# ==================== 报价版本管理 ====================


@router.get("/quotes/{quote_id}/versions", response_model=List[QuoteVersionResponse])
def get_quote_versions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价的所有版本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote_id).order_by(desc(QuoteVersion.created_at)).all()

    version_responses = []
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        version_responses.append(QuoteVersionResponse(**v_dict))

    return version_responses


@router.post("/quotes/{quote_id}/versions", response_model=QuoteVersionResponse, status_code=201)
def create_quote_version(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_in: QuoteVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报价版本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version_data = version_in.model_dump()
    version_data["quote_id"] = quote_id
    version_data["created_by"] = current_user.id
    version = QuoteVersion(**version_data)
    db.add(version)
    db.flush()

    # 创建报价明细
    if version_in.items:
        for item_data in version_in.items:
            item = QuoteItem(quote_version_id=version.id, **item_data.model_dump())
            db.add(item)

    db.commit()
    db.refresh(version)

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    version_dict = {
        **{c.name: getattr(version, c.name) for c in version.__table__.columns},
        "created_by_name": version.creator.real_name if version.creator else None,
        "approved_by_name": version.approver.real_name if version.approver else None,
        "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
    }
    return QuoteVersionResponse(**version_dict)



