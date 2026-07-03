# -*- coding: utf-8 -*-
"""PRE-10：AI 需求分析结果的下游桥接。

分析记录（PresaleAIRequirementAnalysis）此前只被自身 CRUD 消费：方案生成靠前端重贴文本、
三档报价只认手填 base_requirements、与商机域 ai-enrich-requirement 两套抽取互不相通。
本模块提供三个下游出口：
- build_requirements_payload：方案生成的结构化需求输入；
- compose_requirements_text：三档报价等文本型消费方的需求描述；
- confirm_and_backfill：人工确认分析后，增量回填商机 opportunity_requirements（只填空缺，不覆盖人工值）。
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.models.presale.core import PresaleSupportTicket
from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
from app.models.sales.leads import OpportunityRequirement


def get_analysis(db, analysis_id: int) -> Optional[PresaleAIRequirementAnalysis]:
    return (
        db.query(PresaleAIRequirementAnalysis)
        .filter(PresaleAIRequirementAnalysis.id == analysis_id)
        .first()
    )


def build_requirements_payload(analysis: PresaleAIRequirementAnalysis) -> Dict[str, Any]:
    """把分析记录组装成方案生成可直接消费的需求字典。"""
    payload = {
        "raw_requirement": analysis.raw_requirement,
        "structured_requirement": analysis.structured_requirement or {},
        "equipment_list": analysis.equipment_list or [],
        "process_flow": analysis.process_flow or {},
        "technical_parameters": analysis.technical_parameters or {},
        "acceptance_criteria": analysis.acceptance_criteria or [],
    }
    return {k: v for k, v in payload.items() if v}


def _stringify(item: Any) -> str:
    if isinstance(item, str):
        return item
    return json.dumps(item, ensure_ascii=False)


def compose_requirements_text(analysis: PresaleAIRequirementAnalysis) -> str:
    """把分析记录压成一段需求描述文本（三档报价等文本入参消费方使用）。"""
    parts = [analysis.raw_requirement or ""]
    structured = analysis.structured_requirement or {}
    for label, key in (("项目类型", "project_type"), ("应用行业", "industry")):
        if structured.get(key):
            parts.append(f"{label}：{structured[key]}")
    for label, key in (
        ("核心目标", "core_objectives"),
        ("功能需求", "functional_requirements"),
        ("约束条件", "constraints"),
    ):
        values = structured.get(key) or []
        if values:
            parts.append(f"{label}：" + "；".join(_stringify(v) for v in values))
    tech = analysis.technical_parameters or {}
    if tech:
        parts.append("技术参数：" + json.dumps(tech, ensure_ascii=False))
    acceptance = analysis.acceptance_criteria or []
    if acceptance:
        parts.append("验收标准：" + "；".join(_stringify(v) for v in acceptance))
    return "\n".join(p for p in parts if p).strip()


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def confirm_and_backfill(db, analysis_id: int, user_id: Optional[int]) -> Dict[str, Any]:
    """人工确认分析结果：状态置 approved；工单挂了商机则增量回填商机需求表。

    增量语义：opportunity_requirements 里已有非空值（人工填写）一律不覆盖，
    只补空缺字段；完整分析内容带确认人/时间挂到 extra_json 供溯源。
    """
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise ValueError(f"分析记录 {analysis_id} 不存在")

    analysis.status = "approved"

    ticket = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.id == analysis.presale_ticket_id)
        .first()
    )
    opportunity_id = ticket.opportunity_id if ticket else None
    if not opportunity_id:
        db.commit()
        return {
            "analysis_id": analysis.id,
            "status": "approved",
            "backfilled": False,
            "opportunity_id": None,
            "filled_fields": [],
        }

    structured = analysis.structured_requirement or {}
    tech = analysis.technical_parameters or {}
    acceptance = analysis.acceptance_criteria or []
    candidate = {
        "product_object": tech.get("product_object") or structured.get("project_type"),
        "ct_seconds": _to_int(tech.get("ct_seconds") or tech.get("节拍")),
        "interface_desc": tech.get("interface_desc") or tech.get("接口"),
        "site_constraints": "；".join(_stringify(v) for v in (structured.get("constraints") or []))
        or None,
        "acceptance_criteria": "；".join(_stringify(v) for v in acceptance) or None,
    }

    row = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity_id)
        .first()
    )
    if not row:
        row = OpportunityRequirement(opportunity_id=opportunity_id)
        db.add(row)

    filled = []
    for field, value in candidate.items():
        if value in (None, ""):
            continue
        if getattr(row, field) in (None, ""):
            setattr(row, field, value)
            filled.append(field)

    try:
        extra = json.loads(row.extra_json) if row.extra_json else {}
        if not isinstance(extra, dict):
            extra = {}
    except (ValueError, TypeError):
        extra = {}
    extra["presale_ai_analysis"] = {
        "analysis_id": analysis.id,
        "confidence_score": float(analysis.confidence_score or 0),
        "structured_requirement": structured,
        "technical_parameters": tech,
        "acceptance_criteria": acceptance,
        "confirmed_by": user_id,
        "confirmed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    row.extra_json = json.dumps(extra, ensure_ascii=False)

    db.commit()
    return {
        "analysis_id": analysis.id,
        "status": "approved",
        "backfilled": True,
        "opportunity_id": opportunity_id,
        "filled_fields": filled,
    }
