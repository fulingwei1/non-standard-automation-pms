# -*- coding: utf-8 -*-
"""
销售报价管理服务
"""

from datetime import date
import re
from typing import Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_pagination, build_keyword_conditions
from app.models.sales import Contract, Quote, QuoteVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import QuoteCreate
from app.utils.db_helpers import save_obj


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
            joinedload(Quote.opportunity),
            joinedload(Quote.current_version).joinedload(QuoteVersion.presale_ticket),
            joinedload(Quote.versions),
        )

        # 应用数��权限过滤
        if current_user:
            from app.core.sales_permissions import filter_sales_data_by_scope
            query = filter_sales_data_by_scope(query, current_user, self.db, Quote, "owner_id")

        # 搜索条件：兼容前端展示编号 QT-000123（实际库存 quote_code + id）。
        keyword_conditions = build_keyword_conditions(Quote, keyword, "quote_code")
        display_id = self._parse_display_quote_id(keyword)
        if display_id is not None:
            keyword_conditions.append(Quote.id == display_id)
        if keyword_conditions:
            query = query.filter(or_(*keyword_conditions))

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
        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = query.order_by(desc(Quote.created_at))
        query = apply_pagination(query, pagination.offset, pagination.limit)
        items = query.all()

        # 转换为响应格式
        quote_responses = []
        for quote in items:
            current_version = self._pick_display_version(quote)
            contract_id = None
            if current_version:
                contract_id = (
                    self.db.query(Contract.id)
                    .filter(Contract.quote_id == current_version.id)
                    .order_by(desc(Contract.id))
                    .scalar()
                )
            presale_ticket = current_version.presale_ticket if current_version else None
            version_payload = None
            if current_version:
                version_payload = {
                    "id": current_version.id,
                    "version_no": current_version.version_no,
                    "total_price": float(current_version.total_price or 0),
                    "amount_without_tax": float(current_version.amount_without_tax or 0),
                    "tax_rate": float(current_version.tax_rate or 0),
                    "tax_amount": float(current_version.tax_amount or 0),
                    "amount_with_tax": float(current_version.amount_with_tax or 0),
                    "cost_total": float(current_version.cost_total or 0),
                    "gross_margin": float(current_version.gross_margin or 0),
                    "lead_time_days": current_version.lead_time_days,
                    "delivery_date": current_version.delivery_date,
                    "solution_id": current_version.presale_solution_id,
                    "presale_solution_id": current_version.presale_solution_id,
                    "presale_ticket_id": current_version.presale_ticket_id,
                }

            title = (
                quote.opportunity.opp_name
                if quote.opportunity and quote.opportunity.opp_name
                else quote.quote_code
            )
            quote_responses.append({
                "id": quote.id,
                "quote_code": quote.quote_code,
                "quote_no": f"QT-{quote.id:06d}",
                "opportunity_id": quote.opportunity_id,
                "lead_id": (
                    quote.opportunity.lead_id
                    if quote.opportunity and quote.opportunity.lead_id
                    else (presale_ticket.lead_id if presale_ticket else None)
                ),
                "project_id": presale_ticket.project_id if presale_ticket else None,
                "customer_id": quote.customer_id,
                "solution_id": current_version.presale_solution_id if current_version else None,
                "presale_solution_id": current_version.presale_solution_id if current_version else None,
                "presale_ticket_id": current_version.presale_ticket_id if current_version else None,
                "contract_id": contract_id,
                "status": quote.status,
                "valid_until": quote.valid_until,
                "owner_id": quote.owner_id,
                "customer_name": quote.customer.customer_name if quote.customer else None,
                "owner_name": quote.owner.real_name if quote.owner else None,
                "created_at": quote.created_at,
                "updated_at": quote.updated_at,
                # 兼容前端报价管理页所需字段
                "title": title,
                "type": self._infer_quote_type(title),
                "priority": self._infer_priority(quote.status, quote.valid_until),
                "opportunity_title": quote.opportunity.opp_name if quote.opportunity else None,
                "created_by": quote.owner_id,
                "created_by_name": quote.owner.real_name if quote.owner else None,
                "version": version_payload,
            })

        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total),
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

        save_obj(self.db, quote)

        return quote

    def _generate_quote_number(self) -> str:
        """生成报价编号"""
        today = date.today()
        count = self.db.query(Quote).filter(
            func.date(Quote.created_at) == today
        ).count()

        return f"QT{today.strftime('%Y%m%d')}{count+1:04d}"

    @staticmethod
    def _parse_display_quote_id(keyword: Optional[str]) -> Optional[int]:
        if not keyword:
            return None
        match = re.fullmatch(r"\s*QT-(\d{1,})\s*", keyword, flags=re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _pick_display_version(quote: Quote):
        if quote.current_version:
            return quote.current_version
        if quote.versions:
            return sorted(quote.versions, key=lambda item: item.id or 0, reverse=True)[0]
        return None

    @staticmethod
    def _infer_quote_type(title: str) -> str:
        title_text = (title or "").lower()
        if any(keyword in title_text for keyword in ("维保", "售后", "调试", "培训", "service")):
            return "SERVICE"
        if any(keyword in title_text for keyword in ("标准", "备件", "耗材", "standard")):
            return "STANDARD"
        if any(keyword in title_text for keyword in ("项目", "产线", "工站", "机器人", "输送", "集成")):
            return "PROJECT"
        return "CUSTOM"

    @staticmethod
    def _infer_priority(status: Optional[str], valid_until: Optional[date]) -> str:
        if status in {"REJECTED", "EXPIRED"}:
            return "LOW"
        if status in {"IN_REVIEW", "SUBMITTED"}:
            return "HIGH"
        if valid_until:
            days_left = (valid_until - date.today()).days
            if 0 <= days_left <= 7:
                return "URGENT"
        return "MEDIUM"


# 为了快速完成，这里只实现核心功能
