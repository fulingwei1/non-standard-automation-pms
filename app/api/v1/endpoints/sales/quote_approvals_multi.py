# -*- coding: utf-8 -*-
"""
报价approvals_multi管理 - 自动生成
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
from app.schemas.common import ResponseModel
from app.schemas.sales import QuoteItemResponse, QuoteResponse

router = APIRouter()


@router.get("/quotes/approvals_multi", response_model=ResponseModel[List[QuoteResponse]])
def get_quote_approvals_multi(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价approvals_multi列表

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前用户

    Returns:
        Response[List[QuoteResponse]]: 报价approvals_multi列表
    """
    try:
        # TODO: 实现approvals_multi查询逻辑
        quotes = db.query(Quote).offset(skip).limit(limit).all()

        return ResponseModel(
            code=200,
            message="报价approvals_multi列表获取成功",
            data=[QuoteResponse.model_validate(quote) for quote in quotes]
        )
    except Exception as e:
        return ResponseModel(code=500, message=f"获取报价approvals_multi失败: {str(e)}")


@router.post("/quotes/approvals_multi")
def create_quote_approvals_multi(
    quote_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建报价approvals_multi

    Args:
        quote_data: 报价数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        Response: 创建结果
    """
    try:
        # TODO: 实现approvals_multi创建逻辑
        return ResponseModel(code=200, message="报价approvals_multi创建成功")
    except Exception as e:
        return ResponseModel(code=500, message=f"创建报价approvals_multi失败: {str(e)}")
