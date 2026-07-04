# -*- coding: utf-8 -*-
"""B3 · 交付风险预警：扫描执行中项目，结合进度/工期/健康/缺料预测延期风险 + AI 归因。"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.project_status_normalization import project_delivery_scope_expr

router = APIRouter(prefix="/ai-delivery", tags=["AI交付风险"])


@router.get("/risk", response_model=ResponseModel, summary="交付风险预警(执行中项目)")
def delivery_risk(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """扫描执行中项目 → 逾期/进度滞后/缺料/健康度 → 风险清单 + AI 一句话归因。"""
    from app.services.ai_client_service import AIClientService

    rows = (
        db.query(Project)
        .filter(project_delivery_scope_expr(Project))
        .order_by(Project.planned_end_date.asc())
        .limit(200)
        .all()
    )
    risks = []
    for r in rows:
        pid = r.id
        code = r.project_code
        name = r.project_name
        prog = float(r.progress_pct or 0)
        pend = r.planned_end_date
        health = r.health
        mat = r.material_status
        reasons = []
        sev = "low"
        # 逾期
        overdue = False
        if pend:
            row = db.execute(text("SELECT :pe < date('now')"), {"pe": pend}).scalar()
            overdue = bool(row)
            near = db.execute(text("SELECT :pe < date('now','+30 day')"), {"pe": pend}).scalar()
        else:
            near = False
        if overdue and prog < 100:
            reasons.append("已过计划交付日仍未完工"); sev = "high"
        elif near and prog < 70:
            reasons.append("临近交付但进度<70%"); sev = "high" if sev != "high" else sev
        if str(health or "").lower() in ("risk", "poor", "red", "danger"):
            reasons.append("项目健康度差"); sev = "high"
        if mat and any(k in str(mat) for k in ("缺", "SHORT", "shortage", "未齐")):
            reasons.append("物料未齐套/缺料"); sev = "medium" if sev == "low" else sev
        if reasons:
            risks.append({"project_id": pid, "project_code": code, "name": name,
                          "progress": prog, "planned_end": str(pend) if pend else None,
                          "severity": sev, "reasons": reasons})
    risks.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]])

    summary = ""
    try:
        if risks:
            hi = sum(1 for x in risks if x["severity"] == "high")
            resp = AIClientService().generate_solution(
                prompt=f"你是PMO总监。{len(risks)}个执行中项目有交付风险(其中高风险{hi}个)，"
                       f"用一句话(40字内)点出最该先干预什么。只输出这句话。",
                model="qwen3-coder-plus", temperature=0.3, max_tokens=120)
            summary = (resp.get("content") or "").strip().split("\n")[0][:60]
    except Exception:  # noqa: BLE001
        summary = ""
    return ResponseModel(code=200, message=f"发现 {len(risks)} 个交付风险项目",
                         data={"summary": summary, "high_risk": sum(1 for x in risks if x["severity"] == "high"),
                               "total": len(risks), "risks": risks[:20]})
