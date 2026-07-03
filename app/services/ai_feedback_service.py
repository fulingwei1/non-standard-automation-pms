# -*- coding: utf-8 -*-
"""AI 产出反馈服务：记录采纳/驳回 + 按功能统计采纳率。

统计口径：同一 (feature_key, ref_type, ref_id) 多次反馈只按最新一条计，
避免"先驳回后采纳"被双计；无 ref 的反馈（如对整页建议的泛反馈）逐条计。
"""
import logging
from typing import Any, Dict, List, Optional

from app.models.ai_feedback import VERDICTS, AIOutputFeedback

logger = logging.getLogger("ai.feedback")


def record(
    db,
    feature_key: str,
    verdict: str,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
    reason: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    commit: bool = True,
) -> AIOutputFeedback:
    """落一条反馈。verdict 只认 ADOPTED/REJECTED/PARTIAL。"""
    verdict = (verdict or "").upper()
    if verdict not in VERDICTS:
        raise ValueError(f"无效结论 {verdict!r}，只接受 {'/'.join(VERDICTS)}")
    if not (feature_key or "").strip():
        raise ValueError("feature_key 不能为空")

    feedback = AIOutputFeedback(
        feature_key=feature_key.strip(),
        ref_type=ref_type,
        ref_id=ref_id,
        verdict=verdict,
        reason=reason,
        detail=detail,
        created_by=user_id,
    )
    db.add(feedback)
    if commit:
        db.commit()
        db.refresh(feedback)
    logger.info(
        "[AI反馈] feature=%s verdict=%s ref=%s:%s by=%s",
        feature_key, verdict, ref_type, ref_id, user_id,
    )
    return feedback


def stats(db, feature_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """按 feature_key 汇总采纳统计（同一产出取最新反馈）。"""
    query = db.query(AIOutputFeedback)
    if feature_key:
        query = query.filter(AIOutputFeedback.feature_key == feature_key)
    rows = query.order_by(AIOutputFeedback.id.asc()).all()

    # 有 ref 的按 (feature, ref_type, ref_id) 取最新；无 ref 的逐条计
    latest: Dict[Any, AIOutputFeedback] = {}
    for row in rows:
        if row.ref_id is None:
            latest[("__loose__", row.id)] = row
        else:
            latest[(row.feature_key, row.ref_type, row.ref_id)] = row

    grouped: Dict[str, Dict[str, Any]] = {}
    for row in latest.values():
        bucket = grouped.setdefault(
            row.feature_key,
            {"feature_key": row.feature_key, "total": 0, "adopted": 0, "rejected": 0, "partial": 0},
        )
        bucket["total"] += 1
        if row.verdict == "ADOPTED":
            bucket["adopted"] += 1
        elif row.verdict == "REJECTED":
            bucket["rejected"] += 1
        else:
            bucket["partial"] += 1

    result = []
    for bucket in grouped.values():
        total = bucket["total"]
        bucket["adoption_rate"] = round(bucket["adopted"] / total, 4) if total else 0.0
        result.append(bucket)
    result.sort(key=lambda b: b["feature_key"])
    return result
