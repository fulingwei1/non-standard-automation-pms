# -*- coding: utf-8 -*-
"""
报价cost_calculations管理 - 自动生成
从 sales/quotes.py 拆分
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db
from app.core import security
from app.core.config import settings
from app.models.sales import Quote, QuoteItem
from app.models.user import User
from app.schemas.common import Response
from app.schemas.sales import QuoteItemResponse, QuoteResponse

router = APIRouter()


@router.get("/quotes/cost_calculations", response_model=Response[List[QuoteResponse]])
def get_quote_cost_calculations(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价cost_calculations列表

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前用户

    Returns:
        Response[List[QuoteResponse]]: 报价cost_calculations列表
    """
    try:
        # TODO: 实现cost_calculations查询逻辑
        quotes = db.query(Quote).offset(skip).limit(limit).all()

        return Response.success(
            data=[QuoteResponse.from_orm(quote) for quote in quotes],
            message="报价cost_calculations列表获取成功"
        )
    except Exception as e:
        return Response.error(message=f"获取报价cost_calculations失败: {str(e)}")


@router.post("/quotes/cost_calculations")
def create_quote_cost_calculations(
    quote_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建报价cost_calculations

    Args:
        quote_data: 报价数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        Response: 创建结果
    """
    try:
        # TODO: 实现cost_calculations创建逻辑
        return Response.success(message="报价cost_calculations创建成功")
    except Exception as e:
        return Response.error(message=f"创建报价cost_calculations失败: {str(e)}")
