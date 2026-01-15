# -*- coding: utf-8 -*-
"""
模板应用 - 自动生成
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
    prefix="/quotes/{quote_id}/apply-template",
    tags=["templates"]
)

# 共 2 个路由

@router.get("/quotes/{quote_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_quote_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批历史
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.QUOTE,
        entity_id=quote_id
    )

    if not record:
        return []

    history_list = workflow_service.get_approval_history(record.id)
    result = []
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        result.append(ApprovalHistoryResponse(**history_dict))

    return result


# ==================== 模板应用 ====================


@router.post("/quotes/{quote_id}/apply-template", response_model=QuoteVersionResponse)
def apply_cost_template_to_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    template_id: int = Query(..., description="成本模板ID"),
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本或创建新版本"),
    adjustments: Optional[str] = Query(None, description="调整项JSON"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用成本模板到报价
    """
    import json

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="成本模板未启用")

    # 获取或创建报价版本
    if version_id:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == version_id).first()
        if not version or version.quote_id != quote_id:
            raise HTTPException(status_code=404, detail="报价版本不存在")
    elif quote.current_version_id:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    else:
        # 创建新版本
        version_no = f"V{len(quote.versions) + 1}"
        version = QuoteVersion(
            quote_id=quote_id,
            version_no=version_no,
            created_by=current_user.id
        )
        db.add(version)
        db.flush()
        quote.current_version_id = version.id

    # 解析模板成本结构
    cost_structure = template.cost_structure if isinstance(template.cost_structure, dict) else json.loads(template.cost_structure) if template.cost_structure else {}

    # 解析调整项
    adj_dict = json.loads(adjustments) if isinstance(adjustments, str) and adjustments else {}

    # 应用模板成本项
    total_cost = Decimal('0')
    total_price = Decimal('0')

    for category in cost_structure.get('categories', []):
        for item_template in category.get('items', []):
            item_name = item_template.get('item_name', '')

            # 检查是否有调整
            if item_name in adj_dict:
                adj = adj_dict[item_name]
                qty = Decimal(str(adj.get('qty', item_template.get('default_qty', 0))))
                unit_price = Decimal(str(adj.get('unit_price', item_template.get('default_unit_price', 0))))
                cost = Decimal(str(adj.get('cost', item_template.get('default_cost', 0))))
            else:
                qty = Decimal(str(item_template.get('default_qty', 0)))
                unit_price = Decimal(str(item_template.get('default_unit_price', 0)))
                cost = Decimal(str(item_template.get('default_cost', 0)))

            # 创建报价明细
            item = QuoteItem(
                quote_version_id=version.id,
                item_type=item_template.get('item_type', category.get('category', '')),
                item_name=item_name,
                specification=item_template.get('specification'),
                unit=item_template.get('unit'),
                qty=float(qty),
                unit_price=float(unit_price),
                cost=float(cost),
                cost_category=category.get('category', ''),
                cost_source='TEMPLATE',
                lead_time_days=item_template.get('lead_time_days')
            )
            db.add(item)

            total_cost += cost * qty
            total_price += unit_price * qty

    # 更新版本信息
    version.cost_template_id = template_id
    version.total_price = float(total_price)
    version.cost_total = float(total_cost)
    if total_price > 0:
        version.gross_margin = float((total_price - total_cost) / total_price * 100)

    # 更新模板使用次数
    template.usage_count = (template.usage_count or 0) + 1

    db.commit()
    db.refresh(version)

    # 返回版本信息
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    version_dict = {
        **{c.name: getattr(version, c.name) for c in version.__table__.columns},
        "created_by_name": version.creator.real_name if version.creator else None,
        "approved_by_name": version.approver.real_name if version.approver else None,
        "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
    }
    return QuoteVersionResponse(**version_dict)



