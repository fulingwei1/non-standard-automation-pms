# -*- coding: utf-8 -*-
"""AI 报价对账服务：三档报价 vs 最终成交合同金额的定期勾稽。

持续优化环节的数据地基：报出各档偏差、最贴近档位与按档平均绝对偏差，
供经营侧复盘并校准报价规则/提示词。链路：AI 报价(售前工单) → 工单挂的商机 → 已签合同。
实际成本对账待成本归集口径修复后扩展（见 FUNCTIONAL_AUDIT_TRACKER MISC-09/PROJ-11）。
"""
import logging
from typing import Any, Dict, List, Optional

from app.models.presale.core import PresaleSupportTicket
from app.models.presale_ai_quotation import PresaleAIQuotation
from app.models.sales.contracts import Contract

logger = logging.getLogger("ai.calibration")

# 视为"成交"的合同状态
DEAL_STATUSES = ("signed", "executing", "completed")
TIERS = ("basic", "standard", "premium")


def _tier_value(quotation_type: Any) -> str:
    return getattr(quotation_type, "value", str(quotation_type or "")).lower()


def quote_calibration(db, feature_note: Optional[str] = None) -> Dict[str, Any]:
    """全量对账：返回 items（逐工单明细）+ summary（按档平均绝对偏差等）。"""
    quotations = (
        db.query(PresaleAIQuotation).order_by(PresaleAIQuotation.id.asc()).all()
    )
    if not quotations:
        return {"items": [], "summary": {"matched": 0, "unmatched": 0, "mean_abs_deviation": {}}}

    # 同一工单同档多次生成取最新（id 升序遍历，后者覆盖前者）
    tiers_by_ticket: Dict[int, Dict[str, float]] = {}
    for q in quotations:
        tier = _tier_value(q.quotation_type)
        if tier not in TIERS:
            continue
        tiers_by_ticket.setdefault(q.presale_ticket_id, {})[tier] = float(q.total or 0)

    ticket_ids = list(tiers_by_ticket.keys())
    tickets = {
        t.id: t
        for t in db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.id.in_(ticket_ids))
        .all()
    }
    opp_ids = [t.opportunity_id for t in tickets.values() if t.opportunity_id]
    contracts_by_opp: Dict[int, Contract] = {}
    if opp_ids:
        for c in (
            db.query(Contract)
            .filter(Contract.opportunity_id.in_(opp_ids), Contract.status.in_(DEAL_STATUSES))
            .order_by(Contract.id.asc())
            .all()
        ):
            contracts_by_opp[c.opportunity_id] = c  # 同商机多合同取最新

    items: List[Dict[str, Any]] = []
    unmatched = 0
    for ticket_id, tiers in tiers_by_ticket.items():
        ticket = tickets.get(ticket_id)
        contract = contracts_by_opp.get(ticket.opportunity_id) if ticket and ticket.opportunity_id else None
        if not contract or not float(contract.total_amount or 0):
            unmatched += 1
            continue
        amount = float(contract.total_amount)
        deviations = {tier: round((total - amount) / amount, 6) for tier, total in tiers.items()}
        closest = min(deviations, key=lambda t: abs(deviations[t]))
        items.append(
            {
                "presale_ticket_id": ticket_id,
                "opportunity_id": ticket.opportunity_id,
                "contract_id": contract.id,
                "contract_amount": amount,
                "tiers": tiers,
                "deviations": deviations,
                "closest_tier": closest,
            }
        )

    mean_abs: Dict[str, Optional[float]] = {}
    for tier in TIERS:
        values = [abs(r["deviations"][tier]) for r in items if tier in r["deviations"]]
        mean_abs[tier] = round(sum(values) / len(values), 6) if values else None

    closest_distribution: Dict[str, int] = {}
    for r in items:
        closest_distribution[r["closest_tier"]] = closest_distribution.get(r["closest_tier"], 0) + 1

    return {
        "items": items,
        "summary": {
            "matched": len(items),
            "unmatched": unmatched,
            "mean_abs_deviation": mean_abs,
            "closest_tier_distribution": closest_distribution,
        },
    }
