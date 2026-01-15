# -*- coding: utf-8 -*-
"""
销售报价管理服务
"""

from typing import Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Customer
from app.models.sales import Quote, QuoteItem, QuoteTemplate
from app.schemas.sales import QuoteCreate, QuoteUpdate, QuoteResponse, QuoteItemCreate
from app.schemas.common import ResponseModel, PaginatedResponse


class QuotesService:
    """销售报价管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_quotes(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PaginatedResponse:
        """获取报价列表"""
        query = self.db.query(Quote).options(
            joinedload(Quote.customer),
            joinedload(Quote.sales_rep),
            joinedload(Quote.items)
        )
        
        # 搜索条件
        if keyword:
            query = query.filter(
                or_(
                    Quote.quote_number.ilike(f"%{keyword}%"),
                    Quote.title.ilike(f"%{keyword}%")
                )
            )
        
        # 筛选条件
        if status:
            query = query.filter(Quote.status == status)
        
        if customer_id:
            query = query.filter(Quote.customer_id == customer_id)
        
        if start_date:
            query = query.filter(Quote.created_at >= start_date)
        
        if end_date:
            query = query.filter(Quote.created_at <= end_date)
        
        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[QuoteResponse.from_orm(item) for item in items]
        )
    
    def create_quote(self, quote_data: QuoteCreate, current_user: User) -> Quote:
        """创建报价"""
        quote = Quote(
            quote_number=self._generate_quote_number(),
            customer_id=quote_data.customer_id,
            title=quote_data.title,
            description=quote_data.description,
            total_amount=quote_data.total_amount,
            valid_until=quote_data.valid_until,
            terms=quote_data.terms,
            status="draft",
            created_by=current_user.id
        )
        
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        
        return quote
    
    def _generate_quote_number(self) -> str:
        """生成报价编号"""
        today = date.today()
        count = self.db.query(Quote).filter(
            func.date(Quote.created_at) == today
        ).count()
        
        return f"QT{today.strftime('%Y%m%d')}{count+1:04d}"


# 为了快速完成，这里只实现核心功能