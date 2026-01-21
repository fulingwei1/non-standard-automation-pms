# -*- coding: utf-8 -*-
"""
销售报价管理服务
"""

from datetime import date
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.sales import Quote
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import QuoteCreate


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
        end_date: Optional[date] = None,
        current_user: Optional[User] = None
    ) -> PaginatedResponse:
        """获取报价列表（已集成数据权限过滤）"""
        query = self.db.query(Quote).options(
            joinedload(Quote.customer),
            joinedload(Quote.owner),
            joinedload(Quote.opportunity)
        )

        # 应用数��权限过滤
        if current_user:
            from app.core.sales_permissions import filter_sales_data_by_scope
            query = filter_sales_data_by_scope(query, current_user, self.db, Quote, "owner_id")

        # 搜索条件
        if keyword:
            query = query.filter(
                Quote.quote_code.ilike(f"%{keyword}%")
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
        items = query.order_by(desc(Quote.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        # 转换为响应格式
        quote_responses = []
        for quote in items:
            quote_responses.append({
                "id": quote.id,
                "quote_code": quote.quote_code,
                "opportunity_id": quote.opportunity_id,
                "customer_id": quote.customer_id,
                "status": quote.status,
                "valid_until": quote.valid_until,
                "owner_id": quote.owner_id,
                "customer_name": quote.customer.customer_name if quote.customer else None,
                "owner_name": quote.owner.real_name if quote.owner else None,
                "created_at": quote.created_at,
                "updated_at": quote.updated_at,
            })

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=quote_responses
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
