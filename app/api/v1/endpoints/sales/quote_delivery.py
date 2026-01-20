# -*- coding: utf-8 -*-
"""
报价交付管理
包含：交付日期设置、交付状态跟踪、交付提醒
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/quotes/{quote_id}/delivery", response_model=ResponseModel)
def get_quote_delivery(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价交付信息

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 交付信息
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 计算交付状态
    today = date.today()
    delivery_status = "NOT_SET"
    days_remaining = None

    if quote.delivery_date:
        if quote.delivery_date < today:
            delivery_status = "OVERDUE"
            days_remaining = (today - quote.delivery_date).days * -1
        elif quote.delivery_date == today:
            delivery_status = "DUE_TODAY"
            days_remaining = 0
        elif quote.delivery_date <= today + timedelta(days=7):
            delivery_status = "DUE_SOON"
            days_remaining = (quote.delivery_date - today).days
        else:
            delivery_status = "ON_TRACK"
            days_remaining = (quote.delivery_date - today).days

    return ResponseModel(
        code=200,
        message="获取交付信息成功",
        data={
            "quote_id": quote_id,
            "delivery_date": quote.delivery_date.isoformat() if quote.delivery_date else None,
            "delivery_status": delivery_status,
            "days_remaining": days_remaining,
            "quote_status": quote.status,
        }
    )


@router.put("/quotes/{quote_id}/delivery", response_model=ResponseModel)
def update_quote_delivery(
    quote_id: int,
    delivery_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新报价交付日期

    Args:
        quote_id: 报价ID
        delivery_data: 交付数据（delivery_date）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    delivery_date_str = delivery_data.get("delivery_date")
    if delivery_date_str:
        quote.delivery_date = date.fromisoformat(delivery_date_str)
    else:
        quote.delivery_date = None

    db.commit()

    return ResponseModel(
        code=200,
        message="交付日期更新成功",
        data={
            "quote_id": quote_id,
            "delivery_date": quote.delivery_date.isoformat() if quote.delivery_date else None
        }
    )


@router.get("/quotes/delivery/upcoming", response_model=ResponseModel)
def get_upcoming_deliveries(
    days: int = Query(7, ge=1, le=90, description="未来几天内"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取即将到期的交付

    Args:
        days: 查询未来多少天内的交付
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 即将交付的报价列表
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    quotes = db.query(Quote).filter(
        Quote.delivery_date != None,
        Quote.delivery_date >= today,
        Quote.delivery_date <= end_date,
        Quote.status.in_(["APPROVED", "SENT", "ACCEPTED"])
    ).order_by(Quote.delivery_date).all()

    items = [{
        "quote_id": q.id,
        "quote_no": q.quote_no,
        "title": q.title,
        "delivery_date": q.delivery_date.isoformat() if q.delivery_date else None,
        "days_remaining": (q.delivery_date - today).days if q.delivery_date else None,
        "status": q.status,
        "customer_id": q.customer_id,
    } for q in quotes]

    return ResponseModel(
        code=200,
        message="获取即将交付列表成功",
        data={"count": len(items), "items": items}
    )


@router.get("/quotes/delivery/overdue", response_model=ResponseModel)
def get_overdue_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取逾期交付的报价

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 逾期报价列表
    """
    today = date.today()

    quotes = db.query(Quote).filter(
        Quote.delivery_date != None,
        Quote.delivery_date < today,
        Quote.status.in_(["APPROVED", "SENT", "ACCEPTED"])
    ).order_by(Quote.delivery_date).all()

    items = [{
        "quote_id": q.id,
        "quote_no": q.quote_no,
        "title": q.title,
        "delivery_date": q.delivery_date.isoformat() if q.delivery_date else None,
        "days_overdue": (today - q.delivery_date).days if q.delivery_date else 0,
        "status": q.status,
        "customer_id": q.customer_id,
    } for q in quotes]

    return ResponseModel(
        code=200,
        message="获取逾期交付列表成功",
        data={"count": len(items), "items": items}
    )


@router.get("/quotes/delivery/calendar", response_model=ResponseModel)
def get_delivery_calendar(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取交付日历视图数据

    Args:
        year: 年份
        month: 月份
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 日历数据
    """
    # 计算月份的起止日期
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    quotes = db.query(Quote).filter(
        Quote.delivery_date != None,
        Quote.delivery_date >= start_date,
        Quote.delivery_date <= end_date
    ).order_by(Quote.delivery_date).all()

    # 按日期分组
    calendar_data = {}
    for q in quotes:
        day = q.delivery_date.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append({
            "quote_id": q.id,
            "quote_no": q.quote_no,
            "title": q.title,
            "status": q.status,
        })

    return ResponseModel(
        code=200,
        message="获取交付日历成功",
        data={
            "year": year,
            "month": month,
            "total_deliveries": len(quotes),
            "calendar": calendar_data
        }
    )
