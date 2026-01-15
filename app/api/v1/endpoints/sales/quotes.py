# -*- coding: utf-8 -*-
"""
销售报价 API endpoints (重构版)
"""

from typing import Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.models.user import User
from app.models.sales import Quote
from app.schemas.sales import QuoteCreate, QuoteUpdate, QuoteResponse
from app.schemas.common import PaginatedResponse

# 导入重构后的服务
from app.services.sales.quotes_service import QuotesService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_quotes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取报价列表"""
    service = QuotesService(db)
    return service.get_quotes(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date
    )


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    quote_data: QuoteCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """创建报价"""
    service = QuotesService(db)
    quote = service.create_quote(quote_data, current_user)
    return QuoteResponse.from_orm(quote)


# 其他接口可以根据需要继续实现...