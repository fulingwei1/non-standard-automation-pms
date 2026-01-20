# -*- coding: utf-8 -*-
"""
报价版本管理
包含：获取报价的所有版本、创建新版本、版本对比
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion, QuoteItem
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/quotes/{quote_id}/versions", response_model=ResponseModel)
def get_quote_versions(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价的所有版本列表

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 版本列表
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(
        QuoteVersion.quote_id == quote_id
    ).order_by(desc(QuoteVersion.created_at)).all()

    versions_data = [{
        "id": v.id,
        "version_no": v.version_no,
        "total_price": float(v.total_price) if v.total_price else None,
        "cost_total": float(v.cost_total) if v.cost_total else None,
        "gross_margin": float(v.gross_margin) if v.gross_margin else None,
        "lead_time_days": v.lead_time_days,
        "delivery_date": v.delivery_date.isoformat() if v.delivery_date else None,
        "approved_by": v.approved_by,
        "approved_at": v.approved_at.isoformat() if v.approved_at else None,
        "is_current": v.id == quote.current_version_id,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    } for v in versions]

    return ResponseModel(
        code=200,
        message="获取版本列表成功",
        data={"quote_id": quote_id, "versions": versions_data}
    )


@router.get("/quotes/{quote_id}/versions/{version_id}", response_model=ResponseModel)
def get_quote_version_detail(
    quote_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价版本详情

    Args:
        quote_id: 报价ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 版本详情
    """
    version = db.query(QuoteVersion).options(
        joinedload(QuoteVersion.items),
        joinedload(QuoteVersion.creator),
        joinedload(QuoteVersion.approver)
    ).filter(
        QuoteVersion.id == version_id,
        QuoteVersion.quote_id == quote_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    items_data = [{
        "id": item.id,
        "item_type": item.item_type,
        "item_name": item.item_name,
        "qty": float(item.qty) if item.qty else None,
        "unit_price": float(item.unit_price) if item.unit_price else None,
        "cost": float(item.cost) if item.cost else None,
        "lead_time_days": item.lead_time_days,
        "remark": item.remark,
    } for item in (version.items or [])]

    data = {
        "id": version.id,
        "quote_id": version.quote_id,
        "version_no": version.version_no,
        "total_price": float(version.total_price) if version.total_price else None,
        "cost_total": float(version.cost_total) if version.cost_total else None,
        "gross_margin": float(version.gross_margin) if version.gross_margin else None,
        "lead_time_days": version.lead_time_days,
        "risk_terms": version.risk_terms,
        "delivery_date": version.delivery_date.isoformat() if version.delivery_date else None,
        "created_by": version.created_by,
        "created_by_name": version.creator.real_name if version.creator else None,
        "approved_by": version.approved_by,
        "approved_by_name": version.approver.real_name if version.approver else None,
        "approved_at": version.approved_at.isoformat() if version.approved_at else None,
        "items": items_data,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }

    return ResponseModel(code=200, message="获取版本详情成功", data=data)


@router.post("/quotes/{quote_id}/versions", response_model=ResponseModel)
def create_quote_version(
    quote_id: int,
    version_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建报价新版本

    Args:
        quote_id: 报价ID
        version_data: 版本数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 生成版本号
    existing_count = db.query(QuoteVersion).filter(
        QuoteVersion.quote_id == quote_id
    ).count()
    version_no = version_data.get("version_no") or f"V{existing_count + 1}"

    # 创建新版本
    version = QuoteVersion(
        quote_id=quote_id,
        version_no=version_no,
        total_price=version_data.get("total_price"),
        cost_total=version_data.get("cost_total"),
        gross_margin=version_data.get("gross_margin"),
        lead_time_days=version_data.get("lead_time_days"),
        risk_terms=version_data.get("risk_terms"),
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    # 创建明细项
    for item in (version_data.get("items") or []):
        db.add(QuoteItem(
            quote_version_id=version.id,
            item_type=item.get("item_type"),
            item_name=item.get("item_name"),
            qty=item.get("qty"),
            unit_price=item.get("unit_price"),
            cost=item.get("cost"),
            lead_time_days=item.get("lead_time_days"),
            remark=item.get("remark"),
        ))

    # 设置为当前版本
    if version_data.get("set_as_current", True):
        quote.current_version_id = version.id

    db.commit()
    db.refresh(version)

    return ResponseModel(
        code=200,
        message="版本创建成功",
        data={"id": version.id, "version_no": version.version_no}
    )


@router.get("/quotes/{quote_id}/versions/compare", response_model=ResponseModel)
def compare_versions(
    quote_id: int,
    version_id_1: int = Query(..., description="版本1 ID"),
    version_id_2: int = Query(..., description="版本2 ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    对比两个版本

    Args:
        quote_id: 报价ID
        version_id_1: 版本1 ID
        version_id_2: 版本2 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 对比结果
    """
    v1 = db.query(QuoteVersion).filter(
        QuoteVersion.id == version_id_1,
        QuoteVersion.quote_id == quote_id
    ).first()
    v2 = db.query(QuoteVersion).filter(
        QuoteVersion.id == version_id_2,
        QuoteVersion.quote_id == quote_id
    ).first()

    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 计算差异
    price_diff = None
    if v1.total_price and v2.total_price:
        price_diff = float(v2.total_price - v1.total_price)

    cost_diff = None
    if v1.cost_total and v2.cost_total:
        cost_diff = float(v2.cost_total - v1.cost_total)

    margin_diff = None
    if v1.gross_margin and v2.gross_margin:
        margin_diff = float(v2.gross_margin - v1.gross_margin)

    data = {
        "version_1": {
            "id": v1.id,
            "version_no": v1.version_no,
            "total_price": float(v1.total_price) if v1.total_price else None,
            "cost_total": float(v1.cost_total) if v1.cost_total else None,
            "gross_margin": float(v1.gross_margin) if v1.gross_margin else None,
        },
        "version_2": {
            "id": v2.id,
            "version_no": v2.version_no,
            "total_price": float(v2.total_price) if v2.total_price else None,
            "cost_total": float(v2.cost_total) if v2.cost_total else None,
            "gross_margin": float(v2.gross_margin) if v2.gross_margin else None,
        },
        "diff": {
            "price_diff": price_diff,
            "cost_diff": cost_diff,
            "margin_diff": margin_diff,
        }
    }

    return ResponseModel(code=200, message="版本对比成功", data=data)
