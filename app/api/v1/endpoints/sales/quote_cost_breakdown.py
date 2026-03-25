# -*- coding: utf-8 -*-
"""
报价成本明细管理
包含：成本分类明细、成本项管理
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.core.sales_permissions import check_sales_data_permission
from app.models.sales import Quote, QuoteVersion, QuoteItem
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404


def _check_quote_scope(quote: Quote, current_user: User, db: Session) -> None:
    """校验当前用户是否有权访问该报价，无权则抛 403"""
    if not check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该报价的成本数据")
from app.utils.json_helpers import safe_json_loads

router = APIRouter()


def _to_decimal(value) -> Decimal:
    """安全转换为 Decimal，失败返回 0"""
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning(f"成本字段转换失败: value={value!r}, error={e}")
        return Decimal("0")


def _split_remark_meta(remark: Optional[str]) -> tuple[str, dict]:
    """
    解析备注中的技术元数据

    Args:
        remark: 备注字符串，可能包含 [tech-meta] 标记

    Returns:
        (清理后的备注, 技术元数据字典)
    """
    if not remark:
        return "", {}
    if "[tech-meta]" not in remark:
        return remark, {}

    base, raw_meta = remark.split("[tech-meta]", 1)
    # 使用 safe_json_loads 安全解析，失败时返回空字典
    tech_meta = safe_json_loads(
        raw_meta,
        default={},
        field_name="tech_meta",
        log_error=False,  # 不记录日志，因为格式不正确是正常情况
    )
    return base.strip(), tech_meta


def _item_cost_from_meta(item: QuoteItem, tech_meta: dict) -> Decimal:
    total_cost = _to_decimal(tech_meta.get("total_cost"))
    if total_cost > 0:
        return total_cost

    parts = _to_decimal(tech_meta.get("material_cost")) + _to_decimal(tech_meta.get("labor_cost")) + _to_decimal(tech_meta.get("overhead_cost"))
    if parts > 0:
        return parts

    return _to_decimal(item.cost)


@router.get("/quotes/{quote_id}/cost-breakdown", response_model=ResponseModel)
def get_cost_breakdown(
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，默认当前版本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价成本明细分解

    Args:
        quote_id: 报价ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 成本明细
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")
    _check_quote_scope(quote, current_user, db)

    vid = version_id or quote.current_version_id
    if not vid:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == vid
    ).order_by(QuoteItem.id).all()

    # 按类型分组汇总
    categories = {}
    total_cost = Decimal('0')
    total_price = Decimal('0')
    total_material_cost = Decimal('0')
    total_labor_cost = Decimal('0')
    total_overhead_cost = Decimal('0')

    for item in items:
        cat = item.cost_category or item.item_type or "其他"
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "items": [],
                "subtotal_cost": Decimal('0'),
                "subtotal_price": Decimal('0'),
            }

        clean_remark, tech_meta = _split_remark_meta(item.remark)
        item_cost = _item_cost_from_meta(item, tech_meta)
        item_price = (item.qty or Decimal('0')) * (item.unit_price or Decimal('0'))

        material_cost = _to_decimal(tech_meta.get("material_cost"))
        labor_cost = _to_decimal(tech_meta.get("labor_cost"))
        overhead_cost = _to_decimal(tech_meta.get("overhead_cost"))

        categories[cat]["items"].append({
            "id": item.id,
            "item_name": item.item_name,
            "specification": item.specification,
            "qty": float(item.qty) if item.qty else 0,
            "unit": item.unit,
            "unit_price": float(item.unit_price) if item.unit_price else 0,
            "cost": float(item_cost),
            "cost_source": item.cost_source,
            "remark": clean_remark,
            **tech_meta,
        })
        categories[cat]["subtotal_cost"] += item_cost
        categories[cat]["subtotal_price"] += item_price
        total_cost += item_cost
        total_price += item_price

        total_material_cost += material_cost
        total_labor_cost += labor_cost
        total_overhead_cost += overhead_cost

    # 转换为列表并计算占比
    breakdown = []
    for cat_data in categories.values():
        cat_data["subtotal_cost"] = float(cat_data["subtotal_cost"])
        cat_data["subtotal_price"] = float(cat_data["subtotal_price"])
        cat_data["cost_ratio"] = round(cat_data["subtotal_cost"] / float(total_cost) * 100, 2) if total_cost else 0
        breakdown.append(cat_data)

    return ResponseModel(
        code=200,
        message="获取成本明细成功",
        data={
            "quote_id": quote_id,
            "version_id": vid,
            "total_cost": float(total_cost),
            "total_price": float(total_price),
            "gross_margin": round((float(total_price) - float(total_cost)) / float(total_price) * 100, 2) if total_price else 0,
            "cost_structure": {
                "material_cost": float(total_material_cost),
                "labor_cost": float(total_labor_cost),
                "overhead_cost": float(total_overhead_cost),
                "other_cost": float(max(Decimal('0'), total_cost - total_material_cost - total_labor_cost - total_overhead_cost)),
            },
            "breakdown": breakdown
        }
    )


@router.put("/quotes/cost-breakdown/items/{item_id}", response_model=ResponseModel)
def update_cost_item(
    item_id: int,
    item_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新成本明细项

    Args:
        item_id: 明细项ID
        item_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    item = get_or_404(db, QuoteItem, item_id, detail="明细项不存在")

    # 数据权限：通过明细项的版本 → 报价链路校验
    version = db.query(QuoteVersion).filter(QuoteVersion.id == item.quote_version_id).first()
    if version:
        quote = db.query(Quote).filter(Quote.id == version.quote_id).first()
        if quote:
            _check_quote_scope(quote, current_user, db)

    # 可更新字段
    updatable = ["cost", "cost_category", "cost_source", "unit_price", "qty", "remark"]
    for field in updatable:
        if field in item_data:
            setattr(item, field, item_data[field])

    db.commit()

    return ResponseModel(code=200, message="成本明细更新成功", data={"id": item.id})


@router.post("/quotes/{quote_id}/cost-breakdown/recalculate", response_model=ResponseModel)
def recalculate_cost(
    quote_id: int,
    version_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    重新计算报价成本汇总

    Args:
        quote_id: 报价ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 计算结果
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")
    _check_quote_scope(quote, current_user, db)

    vid = version_id or quote.current_version_id
    version = get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == vid).all()

    total_cost = Decimal('0')
    total_price = Decimal('0')

    for item in items:
        _, tech_meta = _split_remark_meta(item.remark)
        item_cost = _item_cost_from_meta(item, tech_meta)
        item.cost = item_cost  # 回写标准成本，便于后续统一读取

        total_cost += item_cost
        if item.qty and item.unit_price:
            total_price += item.qty * item.unit_price

    # 更新版本汇总
    version.cost_total = total_cost
    version.total_price = total_price
    if total_price > 0:
        version.gross_margin = ((total_price - total_cost) / total_price * 100).quantize(Decimal('0.01'))
        version.margin_warning = version.gross_margin < 15
    else:
        version.gross_margin = Decimal('0')

    version.cost_breakdown_complete = True
    db.commit()

    return ResponseModel(
        code=200,
        message="成本重新计算完成",
        data={
            "version_id": vid,
            "total_cost": float(total_cost),
            "total_price": float(total_price),
            "gross_margin": float(version.gross_margin)
        }
    )


@router.post("/quotes/{quote_id}/recalculate", response_model=ResponseModel)
def recalculate_quote_cost(
    quote_id: int,
    version_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """兼容入口：按周计划暴露 /quotes/{id}/recalculate。"""
    return recalculate_cost(
        quote_id=quote_id,
        version_id=version_id,
        db=db,
        current_user=current_user,
    )
