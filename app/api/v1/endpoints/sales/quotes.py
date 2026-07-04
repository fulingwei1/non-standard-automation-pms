# -*- coding: utf-8 -*-
"""
销售报价 API endpoints

NOTE: The pytest suite under `tests/api/test_sales.py` sends a payload with a
nested `version` object and expects endpoints:
- POST /sales/quotes
- POST /sales/quotes/{quote_id}/versions
- POST /sales/quotes/{quote_id}/approve
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.models.sales import Customer, Opportunity, Quote, QuoteItem, QuoteTemplate, QuoteTemplateVersion, QuoteVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

# 导入重构后的服务
from app.services.sales.presale_quote_context import (
    build_quote_values_from_presale_solution,
    build_solution_quote_item,
    resolve_presale_ticket_id_for_quote,
    resolve_presale_solution_for_quote,
)
from app.services.sales.tax_basis import build_tax_breakdown
from app.api.v1.endpoints.sales.utils.quote_item_validation import (
    validate_quote_item_quantity_price,
)
from app.services.sales.quotes_service import QuotesService
from app.common.pagination import PaginationParams, get_pagination_query
from app.utils.db_helpers import get_or_404

router = APIRouter()

TECH_META_FIELDS = [
    "station_count",
    "ct_seconds",
    "uph",
    "fixture_qty",
    "camera_count",
    "light_count",
    "operator_hours",
    "engineering_hours",
    "material_cost",
    "labor_cost",
    "overhead_cost",
    "total_cost",
]


def _to_decimal(value) -> Decimal:
    """安全转换为 Decimal，失败返回 0"""
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning(f"成本字段转换失败: value={value!r}, error={e}")
        return Decimal("0")


def _extract_item_meta(item: dict) -> dict:
    meta = {field: item.get(field) for field in TECH_META_FIELDS if item.get(field) not in (None, "")}

    # 如果没有显式 total_cost，则尝试用成本分量合成
    if "total_cost" not in meta:
        total = _to_decimal(meta.get("material_cost")) + _to_decimal(meta.get("labor_cost")) + _to_decimal(meta.get("overhead_cost"))
        if total > 0:
            meta["total_cost"] = float(total)

    return meta


def _calculate_item_cost(item: dict, meta: dict) -> Decimal:
    explicit_cost = _to_decimal(item.get("cost"))
    total_cost = _to_decimal(meta.get("total_cost"))

    if total_cost > 0:
        return total_cost

    by_parts = _to_decimal(meta.get("material_cost")) + _to_decimal(meta.get("labor_cost")) + _to_decimal(meta.get("overhead_cost"))
    if by_parts > 0:
        return by_parts

    return explicit_cost


def _build_item_remark(raw_remark: Optional[str], meta: dict) -> Optional[str]:
    base = (raw_remark or "").split("[tech-meta]")[0].strip()
    if not meta:
        return base or None

    packed = json.dumps(meta, ensure_ascii=False)
    return f"{base} [tech-meta]{packed}".strip()


def _as_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _parse_date(value, fallback: date) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return fallback


def _generate_quote_code() -> str:
    # quotes.quote_code is limited to 20 chars.
    return f"QFT{datetime.now().strftime('%y%m%d%H%M%S%f')[:17]}"


def _get_template_version(
    db: Session, template: QuoteTemplate, version_id: Optional[int]
) -> Optional[QuoteTemplateVersion]:
    if version_id:
        return (
            db.query(QuoteTemplateVersion)
            .filter(
                QuoteTemplateVersion.id == version_id,
                QuoteTemplateVersion.template_id == template.id,
            )
            .first()
        )
    if template.current_version_id:
        return (
            db.query(QuoteTemplateVersion)
            .filter(QuoteTemplateVersion.id == template.current_version_id)
            .first()
        )
    return (
        db.query(QuoteTemplateVersion)
        .filter(QuoteTemplateVersion.template_id == template.id)
        .order_by(QuoteTemplateVersion.id.desc())
        .first()
    )


@router.post(
    "/quotes/from-template",
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED,
)
def create_quote_from_template(
    template_data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """兼容旧入口：从当前 QuoteTemplate/QuoteTemplateVersion 生成报价草稿。"""
    template_id = template_data.get("template_id")
    if not template_id:
        raise HTTPException(status_code=422, detail="template_id 必填")

    template = db.query(QuoteTemplate).filter(QuoteTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="报价模板不存在")

    version = _get_template_version(db, template, template_data.get("version_id"))
    if not version:
        raise HTTPException(status_code=400, detail="报价模板没有版本，无法生成报价")

    customer_id = template_data.get("customer_id")
    opportunity_id = template_data.get("opportunity_id")
    opportunity = None
    if opportunity_id:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")
        customer_id = customer_id or opportunity.customer_id

    if not customer_id:
        raise HTTPException(status_code=422, detail="customer_id 或 opportunity_id 必填")

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    if not opportunity:
        opportunity = (
            db.query(Opportunity)
            .filter(Opportunity.customer_id == customer.id)
            .order_by(Opportunity.id.desc())
            .first()
        )
    if not opportunity:
        raise HTTPException(status_code=422, detail="opportunity_id 必填")
    if opportunity.customer_id != customer.id:
        raise HTTPException(status_code=400, detail="商机与客户不匹配")

    sections = _as_dict(version.sections)
    pricing_rules = _as_dict(version.pricing_rules)
    items = _as_list(sections.get("items") or pricing_rules.get("items"))

    quote = Quote(
        quote_code=(template_data.get("quote_code") or template_data.get("quote_no") or _generate_quote_code())[:20],
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        valid_until=_parse_date(
            template_data.get("valid_until"), date.today() + timedelta(days=30)
        ),
        owner_id=current_user.id,
        status="DRAFT",
    )
    db.add(quote)
    db.flush()

    total_price = _to_decimal(
        template_data.get("total_price")
        or template_data.get("total_amount")
        or pricing_rules.get("total_price")
        or pricing_rules.get("final_price")
    )
    cost_total = _to_decimal(pricing_rules.get("cost_total") or pricing_rules.get("total_cost"))

    tax_breakdown = build_tax_breakdown(
        {**pricing_rules, **template_data},
        fallback_total=total_price,
    )
    if not total_price and tax_breakdown["amount_with_tax"] > 0:
        total_price = tax_breakdown["amount_with_tax"]

    quote_version = QuoteVersion(
        quote_id=quote.id,
        version_no=str(version.version_no or "V1"),
        total_price=total_price,
        amount_without_tax=tax_breakdown["amount_without_tax"],
        tax_rate=tax_breakdown["tax_rate"],
        tax_amount=tax_breakdown["tax_amount"],
        amount_with_tax=tax_breakdown["amount_with_tax"],
        cost_total=cost_total,
        lead_time_days=pricing_rules.get("lead_time_days"),
        risk_terms=pricing_rules.get("risk_terms"),
        created_by=current_user.id,
    )
    db.add(quote_version)
    db.flush()

    calculated_total = Decimal("0")
    calculated_cost = Decimal("0")
    for item in items:
        if not isinstance(item, dict):
            continue
        qty = _to_decimal(item.get("qty") or item.get("quantity") or 1)
        unit_price = _to_decimal(item.get("unit_price") or item.get("price"))
        item_cost = _to_decimal(item.get("cost") or item.get("unit_cost"))
        calculated_total += qty * unit_price
        calculated_cost += qty * item_cost
        db.add(
            QuoteItem(
                quote_version_id=quote_version.id,
                item_type=item.get("item_type") or item.get("type") or "equipment",
                item_name=item.get("item_name") or item.get("product_name") or item.get("name"),
                specification=item.get("specification"),
                unit=item.get("unit"),
                qty=qty,
                unit_price=unit_price,
                cost=item_cost,
                lead_time_days=item.get("lead_time_days"),
                remark=item.get("remark"),
            )
        )

    if not quote_version.total_price:
        quote_version.total_price = calculated_total
    if not quote_version.amount_with_tax and quote_version.total_price:
        quote_version.amount_with_tax = quote_version.total_price
    if (
        not quote_version.amount_without_tax
        and quote_version.total_price
        and not quote_version.tax_amount
    ):
        quote_version.amount_without_tax = quote_version.total_price
    if not quote_version.cost_total:
        quote_version.cost_total = calculated_cost
    if quote_version.total_price and quote_version.total_price > 0:
        quote_version.gross_margin = (
            (quote_version.total_price - (quote_version.cost_total or Decimal("0")))
            / quote_version.total_price
            * Decimal("100")
        ).quantize(Decimal("0.01"))

    quote.current_version_id = quote_version.id
    db.commit()
    db.refresh(quote)

    return ResponseModel(
        code=201,
        message="已从模板创建报价",
        data={
            "quote_id": quote.id,
            "quote_code": quote.quote_code,
            "template_id": template.id,
            "template_version_id": version.id,
            "opportunity_id": quote.opportunity_id,
            "customer_id": quote.customer_id,
            "current_version_id": quote.current_version_id,
        },
    )


@router.get("/quotes", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_quotes(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取报价列表（已集成数据权限过滤）"""
    service = QuotesService(db)
    return service.get_quotes(
        page=pagination.page,
        page_size=pagination.page_size,
        keyword=keyword,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user
    )


@router.post("/quotes", status_code=status.HTTP_201_CREATED)
def create_quote(
    quote_data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """创建报价"""
    opportunity_id = quote_data.get("opportunity_id")
    customer_id = quote_data.get("customer_id")
    if not opportunity_id or not customer_id:
        raise HTTPException(status_code=422, detail="opportunity_id / customer_id 必填")

    get_or_404(db, Opportunity, opportunity_id, detail="商机不存在")

    version_payload = quote_data.get("version") or {}
    if not version_payload:
        legacy_total = (
            quote_data.get("final_amount")
            or quote_data.get("total_amount")
            or quote_data.get("total_price")
            or 0
        )
        version_payload = {
            "version_no": "V1",
            "total_price": legacy_total,
            "cost_total": quote_data.get("cost_total") or 0,
            "gross_margin": quote_data.get("gross_margin") or quote_data.get("margin_rate") or 0,
            "items": quote_data.get("items") or [],
        }

    presale_solution = resolve_presale_solution_for_quote(
        db,
        quote_data=quote_data,
        version_payload=version_payload,
        opportunity_id=opportunity_id,
        customer_id=customer_id,
    )
    total_price, cost_total, lead_time_days = build_quote_values_from_presale_solution(
        version_payload,
        presale_solution,
    )
    presale_ticket_id = resolve_presale_ticket_id_for_quote(
        quote_data=quote_data,
        version_payload=version_payload,
        presale_solution=presale_solution,
    )
    tax_breakdown = build_tax_breakdown(
        {**quote_data, **version_payload},
        fallback_total=total_price,
    )
    if not total_price and tax_breakdown["amount_with_tax"] > 0:
        total_price = tax_breakdown["amount_with_tax"]
    items = version_payload.get("items") or []
    if presale_solution and not items and (total_price > 0 or cost_total > 0):
        items = [build_solution_quote_item(presale_solution, total_price, cost_total)]

    validated_items = []
    for item in items:
        qty_value = item.get("qty")
        if qty_value in (None, ""):
            qty_value = 1
        qty, unit_price = validate_quote_item_quantity_price(
            qty_value,
            item.get("unit_price"),
        )
        meta = _extract_item_meta(item)
        item_cost = _calculate_item_cost(item, meta)
        validated_items.append((item, qty, unit_price, item_cost, meta))

    quote = Quote(
        quote_code=(
            quote_data.get("quote_code")
            or quote_data.get("quote_no")
            or f"QUOTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )[:20],
        opportunity_id=opportunity_id,
        customer_id=customer_id,
        valid_until=date.fromisoformat(quote_data["valid_until"]) if quote_data.get("valid_until") else None,
        owner_id=current_user.id,
        status="DRAFT",
    )
    db.add(quote)
    db.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no=version_payload.get("version_no") or "V1",
        total_price=total_price,
        amount_without_tax=tax_breakdown["amount_without_tax"],
        tax_rate=tax_breakdown["tax_rate"],
        tax_amount=tax_breakdown["tax_amount"],
        amount_with_tax=tax_breakdown["amount_with_tax"],
        cost_total=cost_total,
        gross_margin=_to_decimal(version_payload.get("gross_margin")),
        lead_time_days=lead_time_days,
        risk_terms=version_payload.get("risk_terms"),
        presale_solution_id=presale_solution.id if presale_solution else None,
        presale_ticket_id=presale_ticket_id,
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    total_price_calc = Decimal("0")
    total_cost_calc = Decimal("0")

    for item, qty, unit_price, item_cost, meta in validated_items:
        db.add(
            QuoteItem(
                quote_version_id=version.id,
                item_type=item.get("item_type"),
                item_name=item.get("item_name"),
                specification=item.get("specification"),
                unit=item.get("unit"),
                qty=qty,
                unit_price=unit_price,
                cost=item_cost,
                lead_time_days=item.get("lead_time_days"),
                remark=_build_item_remark(item.get("remark"), meta),
            )
        )

        total_price_calc += qty * unit_price
        total_cost_calc += qty * item_cost

    version_total_price = _to_decimal(version.total_price)
    version_cost_total = _to_decimal(version.cost_total)
    if not version_total_price:
        version_total_price = total_price_calc
        version.total_price = version_total_price
    if not version.amount_with_tax and version_total_price:
        version.amount_with_tax = version_total_price
    if (
        not version.amount_without_tax
        and version_total_price
        and not version.tax_amount
    ):
        version.amount_without_tax = version_total_price
    if not version_cost_total:
        version_cost_total = total_cost_calc
        version.cost_total = version_cost_total
    if version_total_price > 0:
        version.gross_margin = (
            (version_total_price - version_cost_total)
            / version_total_price
            * Decimal("100")
        ).quantize(Decimal("0.01"))

    quote.current_version_id = version.id
    db.commit()
    db.refresh(quote)

    return {
        "id": quote.id,
        "quote_code": quote.quote_code,
        "opportunity_id": quote.opportunity_id,
        "customer_id": quote.customer_id,
        "solution_id": version.presale_solution_id,
        "presale_solution_id": version.presale_solution_id,
        "presale_ticket_id": version.presale_ticket_id,
        "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
        "status": quote.status,
        "current_version_id": quote.current_version_id,
        "current_version": {
            "id": version.id,
            "version_no": version.version_no,
            "total_price": float(version.total_price or 0),
            "amount_without_tax": float(version.amount_without_tax or 0),
            "tax_rate": float(version.tax_rate or 0),
            "tax_amount": float(version.tax_amount or 0),
            "amount_with_tax": float(version.amount_with_tax or 0),
            "cost_total": float(version.cost_total or 0),
            "gross_margin": float(version.gross_margin or 0),
            "lead_time_days": version.lead_time_days,
            "presale_solution_id": version.presale_solution_id,
            "solution_id": version.presale_solution_id,
            "presale_ticket_id": version.presale_ticket_id,
        },
    }


# 已移除 POST /quotes/{quote_id}/versions —— 与 quote_versions.py 重复，保留 quote_versions.py 中更完整的实现


@router.get("/quotes/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_quote_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    获取报价单统计数据
    注意：此路由必须在 /quotes/{quote_id} 之前注册，避免路径冲突
    """
    from datetime import date as date_type
    from datetime import timedelta

    # 基础查询
    base_query = db.query(Quote)

    # 统计各状态数量
    total = base_query.count()
    draft = base_query.filter(Quote.status == "DRAFT").count()
    in_review = base_query.filter(Quote.status == "IN_REVIEW").count()
    approved = base_query.filter(Quote.status == "APPROVED").count()
    sent = base_query.filter(Quote.status == "SENT").count()
    expired = base_query.filter(Quote.status == "EXPIRED").count()
    rejected = base_query.filter(Quote.status == "REJECTED").count()
    accepted = base_query.filter(Quote.status == "ACCEPTED").count()
    converted = base_query.filter(Quote.status == "CONVERTED").count()

    # 金额统计 - 从当前版本获取总价和毛利率
    all_quotes = base_query.all()
    total_amount = 0
    margins = []
    for q in all_quotes:
        if q.current_version:
            if q.current_version.total_price:
                total_amount += float(q.current_version.total_price)
            if q.current_version.gross_margin:
                margins.append(float(q.current_version.gross_margin))

    avg_amount = total_amount / total if total > 0 else 0
    avg_margin = sum(margins) / len(margins) if margins else 0

    # 转化率
    conversion_rate = round(converted / total * 100, 1) if total > 0 else 0

    # 即将到期（7 天内）
    today = date_type.today()
    expiring_soon = base_query.filter(
        Quote.valid_until is not None,
        Quote.valid_until <= today + timedelta(days=7),
        Quote.valid_until > today,
        Quote.status.in_(["DRAFT", "IN_REVIEW", "APPROVED", "SENT"]),
    ).count()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "draft": draft,
            "inReview": in_review,
            "approved": approved,
            "sent": sent,
            "expired": expired,
            "rejected": rejected,
            "accepted": accepted,
            "converted": converted,
            "totalAmount": round(total_amount, 2),
            "avgAmount": round(avg_amount, 2),
            "avgMargin": round(avg_margin, 2),
            "conversionRate": conversion_rate,
            "expiringSoon": expiring_soon,
        },
    )


# NOTE: POST /quotes/{quote_id}/approve 由 quote_per_id_approval.py 统一实现，
# 那里带有 require_permission("quote:approve") 权限校验与审批任务联动。
# 此处曾有一个无权限校验的“极简审批”实现，因 router 注册顺序在前会遮蔽正式实现，
# 导致任意登录用户都能绕过权限改状态，已移除。请勿在本文件重新添加该路由。

# 其他接口可按需补全...
