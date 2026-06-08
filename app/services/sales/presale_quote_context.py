# -*- coding: utf-8 -*-
"""售前方案到报价版本的上下文衔接工具。"""

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.presale import PresaleSolution

logger = logging.getLogger(__name__)

PRESALE_SOLUTION_REMARK_PATTERN = re.compile(r"来源售前方案\s+(\S+)")


def to_decimal(value) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        logger.warning("报价金额字段转换失败: value=%r, error=%s", value, exc)
        return Decimal("0")


def resolve_presale_solution_for_quote(
    db: Session,
    *,
    quote_data: dict,
    version_payload: dict,
    opportunity_id: int,
    customer_id: int,
) -> Optional[PresaleSolution]:
    solution_id = (
        quote_data.get("solution_id")
        or quote_data.get("presale_solution_id")
        or version_payload.get("solution_id")
        or version_payload.get("presale_solution_id")
    )

    if solution_id:
        solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
        if not solution:
            raise HTTPException(status_code=404, detail="售前方案不存在")
        if solution.opportunity_id and solution.opportunity_id != opportunity_id:
            raise HTTPException(status_code=400, detail="售前方案与商机不匹配")
        if solution.customer_id and solution.customer_id != customer_id:
            raise HTTPException(status_code=400, detail="售前方案与客户不匹配")
        return solution

    return (
        db.query(PresaleSolution)
        .filter(
            PresaleSolution.opportunity_id == opportunity_id,
            or_(
                PresaleSolution.status == "APPROVED",
                PresaleSolution.review_status == "APPROVED",
            ),
        )
        .order_by(
            desc(PresaleSolution.review_time),
            desc(PresaleSolution.updated_at),
            desc(PresaleSolution.id),
        )
        .first()
    )


def build_quote_values_from_presale_solution(
    version_payload: dict,
    solution: Optional[PresaleSolution],
) -> tuple[Decimal, Decimal, Optional[int]]:
    total_price = to_decimal(version_payload.get("total_price"))
    cost_total = to_decimal(version_payload.get("cost_total"))
    lead_time_days = version_payload.get("lead_time_days")

    if not solution:
        return total_price, cost_total, lead_time_days

    solution_total_price = to_decimal(solution.suggested_price)
    solution_cost_total = to_decimal(solution.estimated_cost)
    if not total_price and solution_total_price > 0:
        total_price = solution_total_price
    if not cost_total and solution_cost_total > 0:
        cost_total = solution_cost_total
    if not lead_time_days:
        lead_time_days = solution.estimated_duration

    return total_price, cost_total, lead_time_days


def build_solution_quote_item(
    solution: PresaleSolution,
    total_price: Decimal,
    cost_total: Decimal,
) -> dict:
    return {
        "item_type": "SOLUTION",
        "item_name": solution.name,
        "specification": solution.technical_spec,
        "unit": "套",
        "qty": 1,
        "unit_price": total_price,
        "cost": cost_total,
        "lead_time_days": solution.estimated_duration,
        "remark": f"来源售前方案 {solution.solution_no}",
    }


def resolve_presale_context_for_quote_version(
    db: Session,
    quote_version,
) -> tuple[list[PresaleSolution], set[int]]:
    """返回报价版本明确选用的售前方案和工单。

    新数据优先使用 QuoteVersion.presale_solution_id / presale_ticket_id；
    老数据再兼容解析 QuoteItem.remark 里的“来源售前方案 xxx”。
    """
    if not quote_version:
        return [], set()

    solution_ids = set()
    ticket_ids = set()
    if getattr(quote_version, "presale_solution_id", None):
        solution_ids.add(quote_version.presale_solution_id)
    if getattr(quote_version, "presale_ticket_id", None):
        ticket_ids.add(quote_version.presale_ticket_id)

    if not solution_ids:
        from app.models.sales import QuoteItem

        quote_items = (
            db.query(QuoteItem)
            .filter(QuoteItem.quote_version_id == quote_version.id)
            .all()
        )
        solution_nos = set()
        for item in quote_items:
            match = PRESALE_SOLUTION_REMARK_PATTERN.search(item.remark or "")
            if match:
                solution_nos.add(match.group(1))

        if solution_nos:
            solutions = (
                db.query(PresaleSolution)
                .filter(PresaleSolution.solution_no.in_(solution_nos))
                .all()
            )
            ticket_ids.update(
                solution.ticket_id for solution in solutions if solution.ticket_id
            )
            return solutions, ticket_ids

    if not solution_ids:
        return [], ticket_ids

    solutions = (
        db.query(PresaleSolution)
        .filter(PresaleSolution.id.in_(solution_ids))
        .all()
    )
    ticket_ids.update(solution.ticket_id for solution in solutions if solution.ticket_id)
    return solutions, ticket_ids
