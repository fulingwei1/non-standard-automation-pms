# -*- coding: utf-8 -*-
"""C1 ECN影响预测 · 回款催收 · 投标智能。"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services import ai_job_service

router = APIRouter(prefix="/ai-more", tags=["AI变更/资金/投标"])


def _ai(prompt, mt=1600):
    from app.services.ai_client_service import AIClientService
    r = AIClientService().generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.25, max_tokens=mt)
    return ai_job_service._extract_json(r.get("content") or "")


class EcnRef(BaseModel):
    ecn_id: int


@router.post("/ecn-impact", response_model=ResponseModel, summary="C1 ECN变更连锁影响预测")
def ecn_impact(req: EcnRef, db: Session = Depends(deps.get_db),
               current_user: User = Depends(security.get_current_active_user)) -> Any:
    """ECN 变更 → AI 预测对 BOM/成本/工期/其它机台/已下采购的连锁影响 + 处置建议。"""
    e = db.execute(text("SELECT ecn_title, change_description, project_id, machine_id FROM ecn WHERE id=:i"), {"i": req.ecn_id}).first()
    if not e:
        raise HTTPException(status_code=404, detail="ECN不存在")
    mats = db.execute(text("SELECT material_code, material_name, change_type, cost_impact FROM ecn_affected_materials WHERE ecn_id=:i"), {"i": req.ecn_id}).all()
    mtxt = "\n".join(f"- {m[1]}({m[0]}) {m[2]} 成本影响¥{m[3] or 0}" for m in mats) or "（无受影响物料记录）"
    prompt = ("你是非标自动化变更评审专家。评估这个设计变更(ECN)的连锁影响，严格只输出 JSON：\n"
              '{"cost_impact":"成本影响评估","schedule_impact":"工期影响评估","affected_scope":["受牵连的BOM/其它机台/已下采购/在制品"],'
              '"risks":["风险点"],"actions":["处置建议(按优先级)"]}\n\n'
              f"变更：{e[0]} — {e[1] or ''}\n受影响物料：\n{mtxt}\n\n只返回合法 JSON。")
    r = _ai(prompt)
    if not isinstance(r, dict) or not (r.get("actions") or r.get("affected_scope")):
        raise HTTPException(status_code=502, detail="AI 影响预测失败")
    return ResponseModel(code=200, message="AI ECN影响预测完成", data=r)


@router.get("/receivable-risk", response_model=ResponseModel, summary="回款风险+智能催收")
def receivable_risk(db: Session = Depends(deps.get_db),
                    current_user: User = Depends(security.get_current_active_user)) -> Any:
    """扫描未回款合同 → 回款风险清单 + AI 催收策略。改善非标尾款回收。"""
    rows = db.execute(text(
        "SELECT c.id, c.contract_name, c.total_amount, c.received_amount, c.unreceived_amount, c.signing_date, "
        "(SELECT customer_name FROM customers WHERE id=c.customer_id) cust "
        "FROM contracts c WHERE c.unreceived_amount > 0 ORDER BY c.unreceived_amount DESC LIMIT 15")).all()
    items = [{"contract_id": r[0], "name": r[1], "customer": r[6],
              "total": float(r[2] or 0), "received": float(r[3] or 0), "unreceived": float(r[4] or 0),
              "collection_rate": round(float(r[3] or 0) / float(r[2]) * 100, 1) if r[2] else 0} for r in rows]
    # 催收策略（确定性规则，可靠）
    total_unreceived = sum(x["unreceived"] for x in items)
    strategy = ""
    if items:
        low = [x for x in items if x["collection_rate"] < 30]
        big = max(items, key=lambda x: x["unreceived"])
        strategy = (f"优先催收 {big['customer']}（未回¥{big['unreceived']:.0f}，最大敞口）"
                    + (f"；重点关注 {len(low)} 家回款率<30% 的客户" if low else ""))
    return ResponseModel(code=200, message="回款风险分析完成",
                         data={"total_unreceived": total_unreceived, "count": len(items), "strategy": strategy, "items": items})


class BidReq(BaseModel):
    bid_text: str = Field(..., min_length=20, description="招标文件关键内容")


@router.post("/bid-analysis", response_model=ResponseModel, summary="投标智能分析")
def bid_analysis(req: BidReq, db: Session = Depends(deps.get_db),
                 current_user: User = Depends(security.get_current_active_user)) -> Any:
    """招标文件 → AI 提取技术要求/评分标准/废标条款 + 投标建议。"""
    prompt = ("你是非标自动化投标专家。分析招标文件，严格只输出 JSON：\n"
              '{"tech_requirements":["关键技术要求"],"scoring":["评分标准要点"],"disqualify_clauses":["废标/否决条款(务必满足)"],'
              '"our_fit":"我方契合度评估","win_strategy":["投标制胜要点"],"risks":["投标风险"]}\n\n'
              f"招标文件：\n{req.bid_text}\n\n只返回合法 JSON。")
    r = _ai(prompt, mt=2000)
    if not isinstance(r, dict) or not (r.get("tech_requirements") or r.get("scoring")):
        raise HTTPException(status_code=502, detail="AI 投标分析失败")
    return ResponseModel(code=200, message="AI 投标分析完成", data=r)
