# -*- coding: utf-8 -*-
"""方案 AI 评审的持久化与处置：G2 闸门的消费来源。

评审结果存 opportunity_requirements.extra_json["ai_solution_review"]：
{reviews, high_risk, resolved, reviewed_at, resolution?}。
人机分工：AI 出风险清单（初步判断），人处置留痕（关键判断+责任承担），
未处置的 HIGH 风险由 G2 闸门拦截（决策流硬约束）。
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.sales import Opportunity
from app.models.sales.leads import OpportunityRequirement
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.services.sales.opportunity_operation_audit import log_opportunity_operation

REVIEW_KEY = "ai_solution_review"
RESOLVE_ACTIONS = ("RESOLVED", "ACCEPT_RISK")


def _load_extra(row: OpportunityRequirement) -> Dict[str, Any]:
    try:
        extra = json.loads(row.extra_json) if row.extra_json else {}
        return extra if isinstance(extra, dict) else {}
    except (ValueError, TypeError):
        return {}


def _requirement_row(db, opportunity_id: int, create: bool = False) -> Optional[OpportunityRequirement]:
    row = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity_id)
        .first()
    )
    if not row and create:
        row = OpportunityRequirement(opportunity_id=opportunity_id)
        db.add(row)
        db.flush()
    return row


def _log_solution_review_operation(
    db,
    opportunity_id: int,
    operation_type: str,
    operator: Optional[User],
    *,
    old_value: Optional[dict[str, Any]],
    new_value: Optional[dict[str, Any]],
    operation_desc: str,
    remark: str,
) -> None:
    if not operator:
        return
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        return
    log_opportunity_operation(
        db,
        opportunity,
        operation_type,
        operator,
        old_value=old_value or {},
        new_value=new_value or {},
        operation_desc=operation_desc,
        remark=remark,
    )


def _review_snapshot(record: Optional[dict[str, Any]]) -> dict[str, Any]:
    return {"solution_review": record if isinstance(record, dict) else None}


def persist_solution_review(
    db,
    opportunity_id: int,
    reviews: List[Dict[str, Any]],
    *,
    current_user: Optional[User] = None,
) -> Dict[str, Any]:
    """评审结果落库（覆盖旧评审，重置处置状态）。"""
    high = sum(
        1 for r in reviews if isinstance(r, dict) and str(r.get("risk_level", "")).upper() == "HIGH"
    )
    record = {
        "reviews": reviews,
        "high_risk": high,
        "resolved": False,
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    row = _requirement_row(db, opportunity_id, create=True)
    extra = _load_extra(row)
    old_record = extra.get(REVIEW_KEY)
    extra[REVIEW_KEY] = record
    row.extra_json = json.dumps(extra, ensure_ascii=False)
    db.flush()
    _log_solution_review_operation(
        db,
        opportunity_id,
        SalesOperationType.UPDATE,
        current_user,
        old_value=_review_snapshot(old_record),
        new_value=_review_snapshot(record),
        operation_desc="保存AI方案评审",
        remark=REVIEW_KEY,
    )
    db.commit()
    return record


def get_solution_review(db, opportunity_id: int) -> Optional[Dict[str, Any]]:
    row = _requirement_row(db, opportunity_id)
    if not row:
        return None
    record = _load_extra(row).get(REVIEW_KEY)
    return record if isinstance(record, dict) else None


def resolve_solution_review(
    db,
    opportunity_id: int,
    action: str,
    note: str,
    user_id: Optional[int],
    *,
    current_user: Optional[User] = None,
) -> Dict[str, Any]:
    """人工处置评审风险：RESOLVED（已消除）或 ACCEPT_RISK（带险推进），必须写明理由。"""
    action = (action or "").upper()
    if action not in RESOLVE_ACTIONS:
        raise ValueError(f"无效处置动作 {action!r}，只接受 {'/'.join(RESOLVE_ACTIONS)}")
    if not (note or "").strip():
        raise ValueError("处置必须写明理由（风险如何消除，或为何带险推进）")

    row = _requirement_row(db, opportunity_id)
    extra = _load_extra(row) if row else {}
    record = extra.get(REVIEW_KEY)
    if not row or not isinstance(record, dict):
        raise ValueError(f"商机 {opportunity_id} 没有待处置的方案评审")

    old_record = json.loads(json.dumps(record, ensure_ascii=False))
    record["resolved"] = True
    record["resolution"] = {
        "action": action,
        "note": note.strip(),
        "resolved_by": user_id,
        "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    extra[REVIEW_KEY] = record
    row.extra_json = json.dumps(extra, ensure_ascii=False)

    # 处置即消费：落 AI 反馈（与本事务一起提交）
    from app.services import ai_feedback_service

    ai_feedback_service.record(
        db,
        feature_key="opportunity_solution_review",
        verdict="ADOPTED",
        ref_type="opportunity",
        ref_id=opportunity_id,
        reason=f"[{action}] {note.strip()}",
        user_id=user_id,
        commit=False,
    )
    db.flush()
    _log_solution_review_operation(
        db,
        opportunity_id,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=_review_snapshot(old_record),
        new_value=_review_snapshot(record),
        operation_desc="处置AI方案评审风险",
        remark=f"{REVIEW_KEY}_resolution",
    )
    db.commit()
    return record


def unresolved_high_risk(db, opportunity_id: int) -> int:
    """G2 消费口：未处置评审中的 HIGH 风险数（无评审返回 0）。"""
    record = get_solution_review(db, opportunity_id)
    if not record or record.get("resolved"):
        return 0
    try:
        return int(record.get("high_risk") or 0)
    except (TypeError, ValueError):
        return 0
