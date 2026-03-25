# -*- coding: utf-8 -*-
"""
报价单CRUD管理
包含：获取单个报价详情、更新报价、删除报价
注：列表和创建在 quotes.py 中实现
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import delete_obj, get_or_404
from app.utils.json_helpers import safe_json_loads

router = APIRouter()


def _parse_item_tech_meta(remark: str) -> tuple[str, dict]:
    """
    解析报价项备注中的技术元数据

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


@router.get("/quotes/{quote_id}", response_model=ResponseModel)
def get_quote_detail(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价详情

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 报价详情
    """
    quote = db.query(Quote).options(
        joinedload(Quote.opportunity),
        joinedload(Quote.customer),
        joinedload(Quote.owner),
        joinedload(Quote.current_version).joinedload(QuoteVersion.items)
    ).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 数据权限检查
    if not security.check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该报价")

    # 构建响应数据
    current_version = quote.current_version
    items_data = []
    if current_version and current_version.items:
        for item in current_version.items:
            clean_remark, tech_meta = _parse_item_tech_meta(item.remark or "")
            items_data.append({
                "id": item.id,
                "item_type": item.item_type,
                "item_name": item.item_name,
                "specification": item.specification,
                "unit": item.unit,
                "qty": float(item.qty) if item.qty else None,
                "unit_price": float(item.unit_price) if item.unit_price else None,
                "cost": float(item.cost) if item.cost else None,
                "lead_time_days": item.lead_time_days,
                "remark": clean_remark,
                **tech_meta,
            })

    data = {
        "id": quote.id,
        "quote_code": quote.quote_code,
        "opportunity_id": quote.opportunity_id,
        "opportunity_name": (
            getattr(quote.opportunity, "opp_name", None)
            or getattr(quote.opportunity, "name", None)
            if quote.opportunity
            else None
        ),
        "customer_id": quote.customer_id,
        "customer_name": (
            getattr(quote.customer, "customer_name", None)
            or getattr(quote.customer, "name", None)
            if quote.customer
            else None
        ),
        "status": quote.status,
        "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
        "owner_id": quote.owner_id,
        "owner_name": (
            getattr(quote.owner, "real_name", None)
            or getattr(quote.owner, "name", None)
            if quote.owner
            else None
        ),
        "current_version": {
            "id": current_version.id,
            "version_no": current_version.version_no,
            "total_price": float(current_version.total_price) if current_version.total_price else None,
            "cost_total": float(current_version.cost_total) if current_version.cost_total else None,
            "gross_margin": float(current_version.gross_margin) if current_version.gross_margin else None,
            "lead_time_days": current_version.lead_time_days,
            "items": items_data,
        } if current_version else None,
        "created_at": quote.created_at.isoformat() if quote.created_at else None,
        "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
    }

    return ResponseModel(code=200, message="获取报价详情成功", data=data)


@router.put("/quotes/{quote_id}", response_model=ResponseModel)
def update_quote(
    quote_id: int,
    quote_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新报价基本信息

    Args:
        quote_id: 报价ID
        quote_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    # 数据权限检查
    if not security.check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权修改该报价")

    # 可更新字段
    updatable_fields = ["valid_until", "owner_id"]
    for field in updatable_fields:
        if field in quote_data:
            value = quote_data[field]
            if field == "valid_until" and isinstance(value, str):
                from datetime import date
                value = date.fromisoformat(value)
            setattr(quote, field, value)

    db.commit()
    return ResponseModel(code=200, message="报价更新成功", data={"id": quote.id})


@router.delete("/quotes/{quote_id}", response_model=ResponseModel)
def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除报价（软删除或硬删除）

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    # 数据权限检查
    if not security.check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权删除该报价")

    # 检查状态，已审批的不允许删除
    if quote.status in ["APPROVED", "CONTRACTED"]:
        raise HTTPException(status_code=400, detail="已审批或已签约的报价不能删除")

    # 硬删除（级联删除版本和明细）
    delete_obj(db, quote)

    return ResponseModel(code=200, message="报价删除成功")
