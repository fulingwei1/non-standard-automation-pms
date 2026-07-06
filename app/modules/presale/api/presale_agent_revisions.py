# -*- coding: utf-8 -*-
"""售前智能体结果修订 API。

闭环核心：工程师修改 AI 结果 → 记录字段级 diff → 统计高频修改字段 → 反哺 prompt 改进。

端点：
  POST /presale-agent/revisions          保存修订（自动算 diff）
  GET  /presale-agent/revisions          查修订历史
  GET  /presale-agent/revisions/stats    高频修改字段统计（AI 改进方向）
  GET  /presale-agent/revisions/{id}     查单条修订详情
"""
import json
from collections import Counter
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale_agent_revision import PresaleAgentRevision
from app.models.user import User

router = APIRouter(prefix="/presale-agent", tags=["售前智能体修订"])


# ============= 请求/响应模型 =============

class RevisionCreateRequest(BaseModel):
    """保存修订请求"""

    metric_id: Optional[int] = None
    job_id: Optional[int] = None
    requirement_text: str = Field(..., description="原始需求")
    ai_output: Dict[str, Any] = Field(..., description="AI 原稿（完整 result）")
    revised_output: Dict[str, Any] = Field(..., description="工程师定稿（修改后）")
    revision_note: Optional[str] = Field(None, description="整体修订说明")


class FieldDiffRequest(BaseModel):
    """单字段修改原因（可选，工程师可逐字段写原因）"""

    section: str = Field(..., description="区段，如 solution/quote_range/risks")
    field: str = Field(..., description="字段名")
    reason: Optional[str] = Field(None, description="修改原因")


# ============= 核心逻辑：字段级 diff 计算 =============

def compute_fields_diff(
    ai_output: Dict[str, Any],
    revised_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    对比 AI 原稿和工程师定稿，算出字段级差异。

    策略：
      - steps 下的每个 step，对比关键字段
      - 标量字段（string/number）：值不同就算一处 diff
      - 列表字段（如 risks/subsystems）：长度变化或内容显著不同算 diff
      - 深层嵌套只取关键路径，避免 diff 过碎
    """
    diffs: List[Dict[str, Any]] = []
    ai_steps = (ai_output or {}).get("steps", {})
    rev_steps = (revised_output or {}).get("steps", {})

    # 定义要对比的关键路径（section -> [字段路径]）
    # 路径用点号分隔，如 "solution.architecture"
    COMPARE_PATHS = {
        "understand_requirement": ["parsed.industry", "parsed.equipment_type",
                                    "parsed.key_specs", "parsed.scale"],
        "generate_solution": ["solution.architecture", "solution.key_modules",
                              "solution.test_strategy", "solution.key_equipment"],
        "deep_solution": ["system_architecture", "solution_overview",
                          "subsystems", "equipment_selection", "tiers",
                          "cost_breakdown", "implementation_phases"],
        "quote_range": [],  # 报价区间是数据查询结果，一般不改
        "risk_warnings": ["risks", "acceptance_challenges", "must_confirm"],
        "deep_risk_analysis": ["deep_risks", "supply_chain_warnings", "cost_risks"],
    }

    for section, paths in COMPARE_PATHS.items():
        ai_sec = ai_steps.get(section, {})
        rev_sec = rev_steps.get(section, {})
        if not isinstance(ai_sec, dict) or not isinstance(rev_sec, dict):
            continue
        for path in paths:
            old_val = _get_path(ai_sec, path)
            new_val = _get_path(rev_sec, path)
            if not _values_equal(old_val, new_val):
                diffs.append({
                    "section": section,
                    "field": path,
                    "old_value": _truncate(old_val),
                    "new_value": _truncate(new_val),
                    "reason": None,  # 工程师可后续补充
                })
    return diffs


def _get_path(obj: Dict, path: str):
    """按点号路径取值，如 _get_path(d, 'parsed.industry')。"""
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur


def _values_equal(a, b) -> bool:
    """宽松相等判断（列表比较长度+元素，字符串去空白）。"""
    if a is None and b is None:
        return True
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a.strip() == b.strip()
    return a == b


def _truncate(val, max_len=200):
    """截断长值，避免 diff 记录过大。"""
    if val is None:
        return None
    if isinstance(val, str):
        return val[:max_len] + ("..." if len(val) > max_len else "")
    if isinstance(val, list):
        return [_truncate(v, max_len) for v in val[:5]]
    if isinstance(val, dict):
        return {k: _truncate(v, max_len) for k, v in list(val.items())[:5]}
    return val


# ============= 端点 =============

@router.post("/revisions", summary="保存工程师对 AI 结果的修订")
def create_revision(
    request: RevisionCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """工程师修改 AI 结果后保存。自动计算字段级 diff，便于后续统计改进方向。"""
    # 计算 diff
    fields_diff = compute_fields_diff(request.ai_output, request.revised_output)
    changed_count = len(fields_diff)
    # 改动 >= 3 个字段算大改
    is_major = 1 if changed_count >= 3 else 0

    revision = PresaleAgentRevision(
        metric_id=request.metric_id,
        job_id=request.job_id,
        requirement_text=request.requirement_text,
        ai_output=request.ai_output,
        revised_output=request.revised_output,
        fields_diff=fields_diff,
        revised_by=current_user.id,
        revised_by_name=getattr(current_user, "full_name", None) or current_user.username,
        revision_note=request.revision_note,
        changed_field_count=changed_count,
        is_major_revision=is_major,
        status="CONFIRMED",
    )
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return {
        "id": revision.id,
        "changed_field_count": changed_count,
        "is_major_revision": is_major,
        "fields_diff": fields_diff,
        "message": f"已记录修订（{changed_count} 处修改{'，标记为大改' if is_major else ''}）",
    }


@router.get("/revisions", summary="查修订历史")
def list_revisions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    major_only: bool = Query(False, description="只看大改"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查修订历史列表。"""
    q = db.query(PresaleAgentRevision)
    if major_only:
        q = q.filter(PresaleAgentRevision.is_major_revision == 1)
    total = q.count()
    rows = q.order_by(desc(PresaleAgentRevision.id)).offset(offset).limit(limit).all()
    return {"total": total, "items": [r.to_dict() for r in rows]}


@router.get("/revisions/stats", summary="高频修改字段统计（AI 改进方向）")
def revision_stats(
    days: int = Query(30, ge=1, le=365, description="统计时间窗"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    统计哪些字段最常被工程师修改——这就是 AI 需要改进的方向。

    返回：
      - total_revisions: 修订总次数
      - major_rate: 大改占比
      - top_changed_fields: 高频被改字段 [{section, field, count, sample_diffs}]
      - top_changed_sections: 高频被改区段
    """
    from datetime import datetime, timedelta

    since = datetime.now() - timedelta(days=days)
    rows = (
        db.query(PresaleAgentRevision)
        .filter(PresaleAgentRevision.created_at >= since)
        .all()
    )

    if not rows:
        return {"total_revisions": 0, "message": "暂无修订数据"}

    field_counter = Counter()
    section_counter = Counter()
    field_samples: Dict[str, list] = {}
    major_count = 0

    for r in rows:
        if r.is_major_revision:
            major_count += 1
        for d in (r.fields_diff or []):
            key = f"{d.get('section', '')}.{d.get('field', '')}"
            field_counter[key] += 1
            section_counter[d.get("section", "")] += 1
            if len(field_samples.get(key, [])) < 2:
                field_samples.setdefault(key, []).append({
                    "old": d.get("old_value"),
                    "new": d.get("new_value"),
                })

    return {
        "time_window_days": days,
        "total_revisions": len(rows),
        "major_revisions": major_count,
        "major_rate": round(major_count / len(rows), 2),
        "top_changed_fields": [
            {"field": k, "count": v, "sample_diffs": field_samples.get(k, [])}
            for k, v in field_counter.most_common(15)
        ],
        "top_changed_sections": [
            {"section": k, "count": v}
            for k, v in section_counter.most_common(10)
        ],
        "suggestion": _build_improvement_suggestion(field_counter, len(rows)),
    }


@router.get("/revisions/{revision_id}", summary="查单条修订详情")
def get_revision(
    revision_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查单条修订的完整内容（AI原稿 vs 工程师定稿 vs diff）。"""
    r = db.query(PresaleAgentRevision).filter(PresaleAgentRevision.id == revision_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="修订记录不存在")
    return {
        "id": r.id,
        "metric_id": r.metric_id,
        "job_id": r.job_id,
        "requirement_text": r.requirement_text,
        "ai_output": r.ai_output,
        "revised_output": r.revised_output,
        "fields_diff": r.fields_diff,
        "changed_field_count": r.changed_field_count,
        "is_major_revision": r.is_major_revision,
        "revised_by_name": r.revised_by_name,
        "revision_note": r.revision_note,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _build_improvement_suggestion(field_counter: Counter, total: int) -> str:
    """根据高频修改字段，生成改进建议。"""
    if not field_counter or total == 0:
        return "暂无足够数据"
    top_field, top_count = field_counter.most_common(1)[0]
    rate = top_count / total
    if rate > 0.5:
        return (
            f"「{top_field}」在 {top_count}/{total} 次修订中被修改（{rate:.0%}），"
            f"是 AI 最需要改进的字段。建议优先优化该字段的生成 prompt 或补充相关数据。"
        )
    elif rate > 0.3:
        return f"「{top_field}」被修改 {top_count} 次（{rate:.0%}），有改进空间。"
    else:
        return "修改较分散，AI 整体质量可接受。"
