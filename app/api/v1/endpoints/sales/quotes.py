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
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.sales import Opportunity, Quote, QuoteItem, QuoteVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

# 导入重构后的服务
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
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
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
        raise HTTPException(status_code=422, detail="version 必填")

    quote = Quote(
        quote_code=quote_data.get("quote_code") or f"QUOTE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
        total_price=version_payload.get("total_price"),
        cost_total=version_payload.get("cost_total"),
        gross_margin=version_payload.get("gross_margin"),
        lead_time_days=version_payload.get("lead_time_days"),
        risk_terms=version_payload.get("risk_terms"),
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    total_price_calc = Decimal("0")
    total_cost_calc = Decimal("0")

    for item in (version_payload.get("items") or []):
        qty = _to_decimal(item.get("qty"))
        unit_price = _to_decimal(item.get("unit_price"))
        meta = _extract_item_meta(item)
        item_cost = _calculate_item_cost(item, meta)

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

    if not version.total_price:
        version.total_price = total_price_calc
    if not version.cost_total:
        version.cost_total = total_cost_calc
    if version.total_price and version.total_price > 0:
        version.gross_margin = ((version.total_price - (version.cost_total or Decimal("0"))) / version.total_price * Decimal("100")).quantize(Decimal("0.01"))

    quote.current_version_id = version.id
    db.commit()
    db.refresh(quote)

    return {
        "id": quote.id,
        "quote_code": quote.quote_code,
        "opportunity_id": quote.opportunity_id,
        "customer_id": quote.customer_id,
        "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
        "status": quote.status,
        "current_version_id": quote.current_version_id,
    }


# 已移除 POST /quotes/{quote_id}/versions —— 与 quote_versions.py 重复，保留 quote_versions.py 中更完整的实现


@router.post("/quotes/{quote_id}/approve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def approve_quote(
    quote_id: int,
    payload: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    # Minimal approval flow: mark current version approved when requested.
    approved = bool(payload.get("approved", True))
    remark = payload.get("remark")
    if quote.current_version_id:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
        if version and approved:
            version.approved_by = current_user.id
            version.approved_at = datetime.now()
    quote.status = "APPROVED" if approved else "REJECTED"
    db.commit()
    return ResponseModel(code=200, message="报价审批完成", data={"status": quote.status, "remark": remark})

# 其他接口可按需补全...
