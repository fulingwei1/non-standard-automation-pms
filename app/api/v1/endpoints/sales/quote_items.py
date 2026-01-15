# -*- coding: utf-8 -*-
"""
报价明细 - 自动生成
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
    prefix="/quotes/{quote_id}/items",
    tags=["items"]
)

# 共 5 个路由

# ==================== 报价明细管理 ====================


@router.get("/quotes/{quote_id}/items", response_model=List[QuoteItemResponse])
def get_quote_items(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价明细列表
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    return [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items]


@router.post("/quotes/{quote_id}/items", response_model=QuoteItemResponse, status_code=201)
def create_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_in: QuoteItemCreate,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    item = QuoteItem(quote_version_id=target_version_id, **item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.put("/quotes/{quote_id}/items/{item_id}", response_model=QuoteItemResponse)
def update_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_id: int,
    item_in: QuoteItemUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_version_id.in_([v.id for v in quote.versions])
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="报价明细不存在")

    # 更新字段
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(item, field):
            setattr(item, field, value)

    db.add(item)
    db.commit()
    db.refresh(item)

    return QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.delete("/quotes/{quote_id}/items/{item_id}", status_code=200)
def delete_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_version_id.in_([v.id for v in quote.versions])
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="报价明细不存在")

    db.delete(item)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


@router.put("/quotes/{quote_id}/items/batch", response_model=ResponseModel)
def batch_update_quote_items(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    batch_data: QuoteItemBatchUpdate,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新报价明细
    支持更新、新增、删除操作
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    updated_count = 0
    created_count = 0

    # 处理批量更新
    for item_data in batch_data.items:
        item_dict = item_data.model_dump(exclude_unset=True)
        item_id = item_dict.pop('id', None)

        if item_id:
            # 更新现有明细
            item = db.query(QuoteItem).filter(
                QuoteItem.id == item_id,
                QuoteItem.quote_version_id == target_version_id
            ).first()

            if item:
                for field, value in item_dict.items():
                    if hasattr(item, field) and field != 'id':
                        setattr(item, field, value)
                db.add(item)
                updated_count += 1
        else:
            # 创建新明细
            item = QuoteItem(quote_version_id=target_version_id, **item_dict)
            db.add(item)
            created_count += 1

    db.commit()

    # 重新计算成本和毛利率
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    total_price = sum([float(item.qty or 0) * float(item.unit_price or 0) for item in items])
    total_cost = sum([float(item.cost or 0) * float(item.qty or 0) for item in items])
    gross_margin = ((total_price - total_cost) / total_price * 100) if total_price > 0 else 0

    version.total_price = total_price
    version.cost_total = total_cost
    version.gross_margin = gross_margin
    db.add(version)
    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量更新完成，新增 {created_count} 条，更新 {updated_count} 条",
        data={
            "created": created_count,
            "updated": updated_count,
            "total_price": total_price,
            "total_cost": total_cost,
            "gross_margin": gross_margin
        }
    )



