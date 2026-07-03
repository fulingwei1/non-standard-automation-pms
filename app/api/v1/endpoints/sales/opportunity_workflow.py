# -*- coding: utf-8 -*-
"""
商机管理 - 工作流操作（阶段门、阶段、评分、赢单、输单）
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import can_set_opportunity_gate
from app.models.enums import OpportunityStageEnum
from app.models.sales import Opportunity, OpportunityRequirement
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import OpportunityRequirementResponse, OpportunityResponse
from app.utils.db_helpers import get_or_404

from .utils import validate_g2_opportunity_to_quote

logger = logging.getLogger(__name__)

router = APIRouter()


class RequestPresaleSupportRequest(BaseModel):
    """从商机申请售前技术支持"""

    urgency: str = Field("NORMAL", description="紧急度: LOW/NORMAL/HIGH/URGENT")
    description: Optional[str] = Field(None, description="需要售前支持的说明")
    expected_date: Optional[str] = Field(None, description="期望完成日期")


@router.post("/opportunities/{opp_id}/request-presale-support", response_model=ResponseModel)
def request_presale_support(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    req: RequestPresaleSupportRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """一键向售前技术支持部申请技术支持：基于本商机创建售前支持工单（需技术初评），
    并把商机标记为“已申请售前评估”。售前完成技术初评后，方可推进立项（见立项关卡）。"""
    from sqlalchemy import text as _t

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    cust_name = ""
    if opp.customer_id:
        row = db.execute(
            _t("SELECT customer_name FROM customers WHERE id=:i"), {"i": opp.customer_id}
        ).first()
        cust_name = row[0] if row else ""

    today = datetime.now().strftime("%Y%m%d")
    seq = (
        db.execute(
            _t("SELECT COUNT(*) FROM presale_support_ticket WHERE ticket_no LIKE :p"),
            {"p": f"PST-{today}-%"},
        ).scalar()
        or 0
    ) + 1
    ticket_no = f"PST-{today}-{seq:03d}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    applicant = getattr(current_user, "real_name", None) or current_user.username

    db.execute(
        _t(
            "INSERT INTO presale_support_ticket "
            "(ticket_no, title, ticket_type, urgency, description, customer_id, customer_name, "
            "opportunity_id, lead_id, applicant_id, applicant_name, apply_time, status, "
            "assessment_required, assessment_status, expected_date, created_by, created_at, updated_at) "
            "VALUES (:no,:title,'SOLUTION',:urg,:desc,:cid,:cname,:oid,:lid,:aid,:aname,:now,'PENDING',"
            "1,'PENDING',:exp,:uid,:now,:now)"
        ),
        {
            "no": ticket_no,
            "title": f"售前技术支持-{opp.opp_name}",
            "urg": req.urgency,
            "desc": req.description or f"商机[{opp.opp_name}]申请售前技术初评",
            "cid": opp.customer_id,
            "cname": cust_name,
            "oid": opp.id,
            "lid": getattr(opp, "lead_id", None),
            "aid": current_user.id,
            "aname": applicant,
            "exp": req.expected_date,
            "uid": current_user.id,
            "now": now,
        },
    )
    # 回填商机：已申请售前评估
    opp.assessment_status = "REQUESTED"
    opp.updated_at = datetime.now()
    db.add(opp)
    db.commit()

    return ResponseModel(
        code=200,
        message="已向售前技术支持部提交技术支持申请，待售前完成技术初评后方可推进立项",
        data={"ticket_no": ticket_no, "opportunity_id": opp.id, "assessment_status": "REQUESTED"},
    )


@router.get("/ai-business-analysis", response_model=ResponseModel)
def ai_business_analysis(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI 经营分析（管理层）：用内部销售数据做市场自我诊断 + AI 洞察建议（纯内部数据，最可靠）。"""
    from sqlalchemy import text as _t

    from app.services.ai_client_service import AIClientService
    from app.services import ai_job_service

    funnel = {r[0]: r[1] for r in db.execute(_t(
        "SELECT stage, COUNT(*) FROM opportunities WHERE stage IS NOT NULL GROUP BY stage")).all()}
    won = funnel.get("WON", 0)
    lost = funnel.get("LOST", 0)
    win_rate = round(won / (won + lost) * 100, 1) if (won + lost) else 0
    industries = [(r[0], r[1]) for r in db.execute(_t(
        "SELECT COALESCE(c.industry,'未分类') ind, COUNT(*) FROM opportunities o "
        "LEFT JOIN customers c ON c.id=o.customer_id GROUP BY ind ORDER BY COUNT(*) DESC LIMIT 6")).all()]
    equip = [(r[0], r[1]) for r in db.execute(_t(
        "SELECT equipment_type, COUNT(*) FROM opportunities WHERE equipment_type IS NOT NULL AND equipment_type!='' "
        "GROUP BY equipment_type ORDER BY COUNT(*) DESC LIMIT 6")).all()]
    avg_margin = db.execute(_t(
        "SELECT AVG(gross_margin) FROM quote_versions WHERE gross_margin IS NOT NULL")).scalar()
    low_margin = db.execute(_t(
        "SELECT COUNT(*) FROM quote_versions WHERE margin_warning=1 OR gross_margin<20")).scalar() or 0

    metrics = {
        "funnel": funnel, "win_rate": win_rate, "won": won, "lost": lost,
        "top_industries": industries, "top_equipment": equip,
        "avg_gross_margin": round(float(avg_margin or 0), 1), "low_margin_quotes": low_margin,
    }
    prompt = (
        "你是非标自动化企业的经营分析师。根据下面的内部销售数据做**市场自我诊断**，严格只输出 JSON：\n"
        '{"strengths":["优势(强在哪些行业/设备/客户)"],"risks":["风险(集中度/流失/低毛利/漏斗断层)"],'
        '"suggestions":["可落地的经营建议"],"headline":"一句话经营现状总结"}\n\n'
        f"数据：{metrics}\n\n只返回合法 JSON。"
    )
    s = {}
    try:
        resp = AIClientService().generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=1500)
        s = ai_job_service._extract_json(resp.get("content") or "") or {}
    except Exception:  # noqa: BLE001
        s = {}
    return ResponseModel(code=200, message="AI 经营分析完成", data={"metrics": metrics, "analysis": s})


@router.get("/opportunities/{opp_id}/similar-cases", response_model=ResponseModel)
def similar_cases(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """相似案例检索：按设备类型找历史同类商机(含成交与报价金额) → 可复用经验/参考报价。
    把'从零画/从零估'变成'有历史可比'。"""
    from sqlalchemy import text as _t

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    et = opp.equipment_type or ""
    rows = db.execute(_t(
        "SELECT o.id, o.opp_name, o.stage, o.est_amount, "
        "(SELECT v.total_price FROM quotes q JOIN quote_versions v ON v.id=q.current_version_id "
        " WHERE q.opportunity_id=o.id LIMIT 1) AS quote_amount "
        "FROM opportunities o WHERE o.equipment_type=:et AND o.id!=:i "
        "ORDER BY (o.stage='WON') DESC, o.updated_at DESC LIMIT 8"), {"et": et, "i": opp_id}).all()
    cases = [{"opportunity_id": r[0], "name": r[1], "stage": r[2],
              "est_amount": float(r[3] or 0), "quote_amount": float(r[4] or 0)} for r in rows]
    won = [c for c in cases if c["stage"] == "WON"]
    tip = ""
    if won:
        amts = [c["quote_amount"] or c["est_amount"] for c in won if (c["quote_amount"] or c["est_amount"])]
        if amts:
            tip = f"同类『{et}』成交 {len(won)} 单，报价参考区间 ¥{min(amts):.0f}–¥{max(amts):.0f}"
    return ResponseModel(code=200, message=f"找到 {len(cases)} 个同类『{et}』案例",
                         data={"equipment_type": et, "reference": tip, "total": len(cases), "cases": cases})


@router.post("/opportunities/{opp_id}/ai-next-action", response_model=ResponseModel)
def ai_next_action(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售推进建议：结合阶段+需求成熟度+售前评估+近期活动 → AI 给下一步推进动作与短板提示。"""
    from sqlalchemy import text as _t

    from app.services.ai_client_service import AIClientService
    from app.services import ai_job_service

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    act_cnt = db.execute(_t("SELECT COUNT(*) FROM customer_communications WHERE opportunity_id=:i"), {"i": opp_id}).scalar() or 0
    ctx = (f"商机:{opp.opp_name}; 当前阶段:{opp.stage}; 需求成熟度:{opp.requirement_maturity or '未评'}; "
           f"售前评估:{opp.assessment_status or '未申请'}; 阶段门:{opp.gate_status or '未过'}; 活动记录数:{act_cnt}; "
           f"预算:{opp.budget_range or '未知'}")
    prompt = (
        "你是销售总监。根据商机现状给出**下一步推进建议**，严格只输出 JSON：\n"
        '{"next_actions":["按优先级的下一步动作"],"gaps":["当前短板/缺口"],"win_tips":["提升赢率的要点"],"stage_advice":"是否可推进到下一阶段及理由"}\n\n'
        f"商机现状：{ctx}\n\n结合非标自动化销售规律，只返回合法 JSON。"
    )
    resp = AIClientService().generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=1200)
    s = ai_job_service._extract_json(resp.get("content") or "")
    if not s:
        raise HTTPException(status_code=502, detail="AI 推进建议生成失败")
    return ResponseModel(code=200, message="AI 推进建议已生成", data=s)


@router.post("/opportunities/{opp_id}/ai-solution-review", response_model=ResponseModel)
def ai_solution_review(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """方案 AI 评审/自检：从需求评估技术可行性风险（节拍可达性/机械干涉/接口兼容/来料假设/验收可测性），
    定稿前抓返工点。非标返工大多来自这些没提前想清楚。"""
    from sqlalchemy import text as _t

    from app.services.ai_client_service import AIClientService
    from app.services import ai_job_service

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    req = db.execute(_t(
        "SELECT product_object, ct_seconds, interface_desc, site_constraints, acceptance_criteria "
        "FROM opportunity_requirements WHERE opportunity_id=:i"), {"i": opp_id}).first()
    ctx = (
        f"设备类型:{opp.equipment_type or ''}; 产品对象:{req[0] if req else ''}; 目标节拍:{req[1] if req else ''}秒; "
        f"接口:{req[2] if req else ''}; 现场:{req[3] if req else ''}; 验收:{req[4] if req else ''}"
    )
    prompt = (
        "你是非标自动化资深方案评审专家。针对下面需求做**方案可行性自检**，找出可能导致返工/失败的风险点，"
        "严格只输出 JSON 数组：\n"
        '[{"aspect":"评审方面","risk_level":"HIGH|MEDIUM|LOW","finding":"具体风险/隐患","suggestion":"规避建议或需向客户确认的点"}]\n\n'
        f"需求：{ctx}\n\n"
        "重点评审：节拍可达性(测试/动作时间能否满足目标节拍)、机械干涉与换型可行性、"
        "接口/协议兼容性、来料状态假设、测量系统能力(能否达到验收GRR/CPK)、现场条件、安全。"
        "6-12 条，按风险从高到低，只返回合法 JSON 数组。"
    )
    resp = AIClientService().generate_solution(
        prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=2000)
    parsed = ai_job_service._extract_json(resp.get("content") or "")
    reviews = parsed if isinstance(parsed, list) else (parsed.get("reviews") if isinstance(parsed, dict) else None)
    if not isinstance(reviews, list) or not reviews:
        raise HTTPException(status_code=502, detail="AI 方案评审失败，请先完善需求")
    high = sum(1 for r in reviews if isinstance(r, dict) and str(r.get("risk_level")).upper() == "HIGH")
    return ResponseModel(code=200, message=f"AI 方案评审完成：{len(reviews)}项，其中高风险{high}项",
                         data={"opportunity_id": opp_id, "high_risk": high, "reviews": reviews})


@router.post("/opportunities/{opp_id}/ai-acceptance-criteria", response_model=ResponseModel)
def ai_acceptance_criteria(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI 验收标准对齐：从已结构化的需求自动生成**可测量**的验收标准（指标/目标值/测量方法/判定），
    销售-售前-客户提前锁定 → 少扯皮、尾款好收。生成结果回填需求表。"""
    import json as _json
    from datetime import datetime as _dt

    from sqlalchemy import text as _t

    from app.services.ai_client_service import AIClientService
    from app.services import ai_job_service

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    req = db.execute(_t(
        "SELECT product_object, ct_seconds, interface_desc, site_constraints, acceptance_criteria "
        "FROM opportunity_requirements WHERE opportunity_id=:i"), {"i": opp_id}).first()
    ctx = (
        f"设备类型:{opp.equipment_type or ''}; 产品对象:{req[0] if req else ''}; 节拍:{req[1] if req else ''}秒; "
        f"接口:{req[2] if req else ''}; 现场:{req[3] if req else ''}; 客户已提验收:{req[4] if req else ''}"
    )
    prompt = (
        "你是非标自动化验收专家。根据需求生成**可测量、可判定**的验收标准（避免'满足要求'这种模糊表述），"
        "严格只输出 JSON 数组：\n"
        '[{"item":"验收指标","target":"目标值(量化)","method":"测量方法","criteria":"判定标准"}]\n\n'
        f"需求：{ctx}\n\n"
        "覆盖：功能测试项、节拍、良率/误判率、测量系统能力(GRR/CPK)、机型兼容与换型、"
        "接口/数据对接、稼动率、安全、可维护性等。8-14 条，只返回合法 JSON 数组。"
    )
    resp = AIClientService().generate_solution(
        prompt=prompt, model="qwen3-coder-plus", temperature=0.25, max_tokens=2000)
    parsed = ai_job_service._extract_json(resp.get("content") or "")
    criteria = parsed if isinstance(parsed, list) else (parsed.get("criteria") if isinstance(parsed, dict) else None)
    if not isinstance(criteria, list) or not criteria:
        raise HTTPException(status_code=502, detail="AI 生成验收标准失败，请先完善需求")

    # 回填：格式化文本 + 结构化 extra_json
    lines = [f"{i+1}. {c.get('item','')}：{c.get('target','')}（{c.get('method','')}；判定：{c.get('criteria','')}）"
             for i, c in enumerate(criteria) if isinstance(c, dict)]
    text_criteria = "\n".join(lines)
    now = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    if req:
        db.execute(_t("UPDATE opportunity_requirements SET acceptance_criteria=:ac, extra_json=:ej, updated_at=:now "
                      "WHERE opportunity_id=:i"),
                   {"ac": text_criteria, "ej": _json.dumps({"acceptance_criteria": criteria}, ensure_ascii=False), "now": now, "i": opp_id})
    else:
        db.execute(_t("INSERT INTO opportunity_requirements(opportunity_id, acceptance_criteria, extra_json, created_at, updated_at) "
                      "VALUES(:i,:ac,:ej,:now,:now)"),
                   {"i": opp_id, "ac": text_criteria, "ej": _json.dumps({"acceptance_criteria": criteria}, ensure_ascii=False), "now": now})
    opp.acceptance_basis = text_criteria[:500]
    db.add(opp)
    db.commit()

    return ResponseModel(code=200, message="AI 已生成可测量验收标准（可微调后与客户/售前对齐）",
                         data={"opportunity_id": opp_id, "count": len(criteria), "acceptance_criteria": criteria})


@router.post("/opportunities/{opp_id}/ai-quote-estimate", response_model=ResponseModel)
def ai_quote_estimate(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI 智能报价估算：读商机需求 + 标准模块库 → AI 推荐模块组合累加成本 + 风险加成 + 类比历史 → 报价与毛利。
    体现"报价从整机拍脑袋升级为模块累加+历史类比+风险加成"，且需求/成本自动带出。"""
    from sqlalchemy import text as _t

    from app.services.ai_client_service import AIClientService
    from app.services import ai_job_service

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    req = db.execute(_t(
        "SELECT product_object, ct_seconds, interface_desc, site_constraints, acceptance_criteria "
        "FROM opportunity_requirements WHERE opportunity_id=:i"), {"i": opp_id}).first()
    req_txt = (
        f"设备类型:{opp.equipment_type or ''}; 产品对象:{req[0] if req else ''}; 节拍:{req[1] if req else ''}秒; "
        f"接口:{req[2] if req else ''}; 现场:{req[3] if req else ''}; 验收:{req[4] if req else ''}; "
        f"预算:{opp.budget_range or ''}; 成熟度:{opp.requirement_maturity or ''}"
    )
    mods = db.execute(_t(
        "SELECT module_name, category, ref_cost, description FROM ai_standard_modules ORDER BY source_count DESC LIMIT 30")).all()
    mod_txt = "\n".join(f"- {m[0]}（{m[1]}，参考成本¥{float(m[2] or 0):.0f}）：{m[3] or ''}" for m in mods) or "（模块库为空，请先在模块库执行AI挖掘）"

    prompt = (
        "你是非标自动化报价工程师。根据【需求】和【可用标准模块库】，做模块级报价估算，严格只输出 JSON：\n"
        '{"recommended_modules":[{"module_name":"","qty":1,"unit_cost":0,"subtotal":0}],'
        '"custom_items":[{"name":"定制项","cost":0}],'
        '"material_cost":材料总成本,"risk_factor":"风险加成百分比如15","risk_reason":"加成原因(需求不清/新工艺/长周期件等)",'
        '"suggested_cost":含风险总成本,"suggested_gross_margin":"建议毛利率如35","suggested_price":建议报价,'
        '"basis":"报价依据一句话(模块累加+类比)"}\n\n'
        f"【需求】{req_txt}\n\n【可用标准模块库】\n{mod_txt}\n\n"
        "要求：优先用标准模块累加，缺的部分列为定制项；需求越不清晰风险加成越高；只返回合法 JSON。"
    )
    resp = AIClientService().generate_solution(
        prompt=prompt, model="qwen3-coder-plus", temperature=0.25, max_tokens=1800)
    est = ai_job_service._extract_json(resp.get("content") or "")
    if not est:
        raise HTTPException(status_code=502, detail="AI 报价估算失败，请稍后重试")
    return ResponseModel(code=200, message="AI 报价估算完成（模块累加+风险加成，仅供参考可微调）", data=est)


@router.get("/ai-briefing", response_model=ResponseModel)
def ai_sales_briefing(
    *,
    db: Session = Depends(deps.get_db),
    owner_id: Optional[int] = Query(None, description="按负责人过滤(不传=全部)"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI 经营简报：主动扫描需要关注的异常，生成分类行动清单（数据主动找人）。
    检测用确定性SQL（可靠），AI 只做"今日重点"一句话总结。"""
    from sqlalchemy import text as _t

    own = "AND o.owner_id = :oid" if owner_id else ""
    p = {"oid": owner_id} if owner_id else {}
    alerts = []

    def rows(sql):
        return db.execute(_t(sql), p).all()

    # 1) 商机停滞（14天无进展或从未记录进展）
    r = rows(f"SELECT o.id,o.opp_name FROM opportunities o WHERE o.stage NOT IN ('WON','LOST','CLOSED') "
             f"AND (o.last_progress_at IS NULL OR o.last_progress_at < date('now','-14 days')) {own} "
             f"ORDER BY o.updated_at ASC LIMIT 10")
    if r:
        cnt = db.execute(_t(f"SELECT COUNT(*) FROM opportunities o WHERE o.stage NOT IN ('WON','LOST','CLOSED') "
                            f"AND (o.last_progress_at IS NULL OR o.last_progress_at < date('now','-14 days')) {own}"), p).scalar()
        alerts.append({"type": "商机停滞", "severity": "high", "count": cnt,
                       "action": "尽快跟进或记一条活动", "items": [{"opportunity_id": x[0], "name": x[1]} for x in r]})

    # 2) 需求不清（成熟度低/未评）→ 建议用AI完善需求(A1)
    r = rows(f"SELECT o.id,o.opp_name FROM opportunities o WHERE o.stage NOT IN ('WON','LOST','CLOSED') "
             f"AND (o.requirement_maturity IS NULL OR o.requirement_maturity <= 2) {own} "
             f"ORDER BY o.updated_at DESC LIMIT 10")
    if r:
        cnt = db.execute(_t(f"SELECT COUNT(*) FROM opportunities o WHERE o.stage NOT IN ('WON','LOST','CLOSED') "
                            f"AND (o.requirement_maturity IS NULL OR o.requirement_maturity <= 2) {own}"), p).scalar()
        alerts.append({"type": "需求不清", "severity": "medium", "count": cnt,
                       "action": "点『AI 完善需求』或补录活动", "items": [{"opportunity_id": x[0], "name": x[1]} for x in r]})

    # 3) 售前评估缺失（未申请/未完成）→ 建议一键申请售前支持(②)
    r = rows(f"SELECT o.id,o.opp_name FROM opportunities o WHERE o.stage NOT IN ('WON','LOST','CLOSED') "
             f"AND (o.assessment_status IS NULL OR o.assessment_status='REQUESTED') {own} "
             f"ORDER BY o.updated_at DESC LIMIT 10")
    if r:
        cnt = db.execute(_t(f"SELECT COUNT(*) FROM opportunities o WHERE o.stage NOT IN ('WON','LOST','CLOSED') "
                            f"AND (o.assessment_status IS NULL OR o.assessment_status='REQUESTED') {own}"), p).scalar()
        alerts.append({"type": "售前评估缺失", "severity": "medium", "count": cnt,
                       "action": "一键申请售前技术支持", "items": [{"opportunity_id": x[0], "name": x[1]} for x in r]})

    # 4) 低毛利报价（margin_warning 或毛利<20%）
    try:
        r = db.execute(_t(
            "SELECT q.id, o.opp_name, v.gross_margin FROM quotes q "
            "JOIN quote_versions v ON v.id=q.current_version_id "
            "LEFT JOIN opportunities o ON o.id=q.opportunity_id "
            "WHERE (v.margin_warning=1 OR v.gross_margin < 20) LIMIT 10")).all()
        if r:
            alerts.append({"type": "低毛利报价", "severity": "high", "count": len(r),
                           "action": "复核成本/让利空间", "items": [{"quote_id": x[0], "name": x[1], "gross_margin": float(x[2] or 0)} for x in r]})
    except Exception:  # noqa: BLE001
        pass

    # AI 今日重点（失败不影响简报）
    summary = ""
    try:
        if alerts:
            from app.services.ai_client_service import AIClientService
            brief = "；".join(f"{a['type']}{a['count']}个" for a in alerts)
            resp = AIClientService().generate_solution(
                prompt=f"你是销售总监助理。用一句话(40字内)点出今日销售最该先处理什么：{brief}。只输出这句话。",
                model="qwen3-coder-plus", temperature=0.3, max_tokens=120)
            summary = (resp.get("content") or "").strip().split("\n")[0][:60]
    except Exception:  # noqa: BLE001
        summary = ""

    return ResponseModel(code=200, message="经营简报生成成功",
                         data={"summary": summary, "alert_types": len(alerts), "alerts": alerts})


@router.post("/opportunities/{opp_id}/ai-enrich-requirement", response_model=ResponseModel)
def ai_enrich_requirement(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI 一键完善商机需求：汇总商机描述+已录入的活动/会议纪要 → AI 抽取结构化需求，
    自动回填商机与需求表（销售不用手填）。体现"数据带出/AI计算、少录入"。"""
    from sqlalchemy import text as _t

    from app.services.ai_client_service import AIClientService
    from app.services import ai_job_service

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    # 汇总上下文：商机名 + 已录入活动/纪要内容
    acts = db.execute(
        _t("SELECT topic, content FROM customer_communications WHERE opportunity_id=:i ORDER BY id DESC LIMIT 20"),
        {"i": opp_id},
    ).all()
    context = f"商机：{opp.opp_name}\n已有设备类型：{opp.equipment_type or ''}\n"
    context += "\n".join(f"[{a[0]}] {a[1]}" for a in acts if a[1]) or "（暂无活动记录）"

    prompt = (
        "你是非标自动化售前工程师。根据下面的商机与销售活动记录，抽取结构化技术需求，严格只输出 JSON：\n"
        '{"product_object":"被测/被加工对象","equipment_type":"设备类型如ICT测试/FCT测试/视觉检测",'
        '"ct_seconds":节拍秒数或null,"interface_desc":"接口/通信协议如MES/PLC",'
        '"site_constraints":"现场约束","acceptance_criteria":"验收标准如GRR<10%/CPK>=1.33/节拍/误判率",'
        '"safety_requirement":"安全要求","budget":"预算或空","delivery_window":"交期或空",'
        '"key_demands":["关键诉求"],"competitors":["竞品"],'
        '"requirement_maturity":"HIGH|MEDIUM|LOW(信息越全越高)"}\n\n'
        f"{context}\n\n只返回合法 JSON。缺失字段给空字符串或 null。"
    )
    ai = AIClientService()
    resp = ai.generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.2, max_tokens=1200)
    s = ai_job_service._extract_json(resp.get("content") or "")
    if not s:
        raise HTTPException(status_code=502, detail="AI 未能解析需求，请稍后重试或补充活动记录")

    def _j(v):
        return "、".join(v) if isinstance(v, list) else (v or "")

    # 回填商机
    if s.get("equipment_type"):
        opp.equipment_type = s["equipment_type"]
    if s.get("budget"):
        opp.budget_range = str(s["budget"])
    if s.get("delivery_window"):
        opp.delivery_window = str(s["delivery_window"])
    if s.get("acceptance_criteria"):
        opp.acceptance_basis = s["acceptance_criteria"]
    if s.get("requirement_maturity"):
        # 商机成熟度全链统一 1-5 整数口径（模型/Schema/编辑框均为 int，写字符串会导致详情接口 500）
        opp.requirement_maturity = MATURITY_LEVELS.get(
            str(s["requirement_maturity"]).upper(), opp.requirement_maturity
        )
    opp.updated_at = datetime.now()
    db.add(opp)

    # 回填需求表（upsert）
    exists = db.execute(_t("SELECT id FROM opportunity_requirements WHERE opportunity_id=:i"), {"i": opp_id}).first()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ct = s.get("ct_seconds")
    try:
        ct = int(ct) if ct not in (None, "", "null") else None
    except (TypeError, ValueError):
        ct = None
    fields = {
        "po": s.get("product_object") or "", "ct": ct, "ifc": s.get("interface_desc") or "",
        "sc": s.get("site_constraints") or "", "ac": s.get("acceptance_criteria") or "",
        "sr": s.get("safety_requirement") or "", "i": opp_id, "now": now,
    }
    if exists:
        db.execute(_t(
            "UPDATE opportunity_requirements SET product_object=:po, ct_seconds=:ct, interface_desc=:ifc, "
            "site_constraints=:sc, acceptance_criteria=:ac, safety_requirement=:sr, updated_at=:now "
            "WHERE opportunity_id=:i"), fields)
    else:
        db.execute(_t(
            "INSERT INTO opportunity_requirements(opportunity_id, product_object, ct_seconds, interface_desc, "
            "site_constraints, acceptance_criteria, safety_requirement, created_at, updated_at) "
            "VALUES(:i,:po,:ct,:ifc,:sc,:ac,:sr,:now,:now)"), fields)
    db.commit()

    return ResponseModel(
        code=200,
        message="AI 已根据活动/纪要完善商机需求（可再核对微调）",
        data={
            "opportunity_id": opp_id,
            "equipment_type": opp.equipment_type,
            "budget_range": opp.budget_range,
            "requirement_maturity": opp.requirement_maturity,
            "requirement": {
                "product_object": fields["po"], "ct_seconds": ct,
                "interface_desc": fields["ifc"], "acceptance_criteria": fields["ac"],
                "site_constraints": fields["sc"], "safety_requirement": fields["sr"],
            },
            "key_demands": _j(s.get("key_demands")),
            "competitors": _j(s.get("competitors")),
        },
    )


@router.post("/opportunities/{opp_id}/requirement-document", response_model=ResponseModel)
async def upload_requirement_document(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    file: UploadFile = File(..., description="客户需求文档 .pdf/.docx/.txt/.md"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """一步式需求文档入口：上传客户需求文档（PDF/Word）→ 提取文本落为本商机活动记录 →
    直接跑 AI 需求抽取回填。原文件存档并登记到需求附件。"""
    import json as _json
    import re as _re
    from pathlib import Path

    from sqlalchemy import text as _t

    from app.core.config import settings

    from .activity_minutes import _extract_text_from_file

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大(>15MB)，请压缩后上传")
    text_content = _extract_text_from_file(file.filename, raw)
    if len(text_content.strip()) < 30:
        raise HTTPException(status_code=400, detail="文档内容过短或未提取到有效文本")

    # 原文件存档
    now_dt = datetime.now()
    safe_name = _re.sub(r"[^\w.-]", "_", file.filename or "requirement.doc")[-80:]
    save_dir = Path(settings.UPLOAD_DIR) / "requirement_docs"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"opp{opp_id}_{now_dt.strftime('%Y%m%d%H%M%S')}_{safe_name}"
    save_path.write_bytes(raw)

    # 落为活动记录（进入需求抽取链的统一数据源）
    cust_name = ""
    if opp.customer_id:
        row = db.execute(_t("SELECT customer_name FROM customers WHERE id=:i"), {"i": opp.customer_id}).first()
        cust_name = row[0] if row else ""
    today = now_dt.strftime("%Y%m%d")
    seq = (db.execute(_t("SELECT COUNT(*) FROM customer_communications WHERE communication_no LIKE :p"),
                      {"p": f"COMM-{today}-%"}).scalar() or 0) + 1
    comm_no = f"COMM-{today}-{seq:03d}"
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    db.execute(_t(
        "INSERT INTO customer_communications(communication_no, communication_type, customer_name, "
        "communication_date, topic, subject, content, customer_id, opportunity_id, created_by, created_at, updated_at) "
        "VALUES(:no,'DOCUMENT',:cname,date('now'),:topic,:topic,:content,:cid,:oid,:uid,:now,:now)"),
        {"no": comm_no, "cname": cust_name or "（未关联客户）", "topic": f"需求文档-{file.filename}",
         "content": text_content[:20000], "cid": opp.customer_id, "oid": opp_id,
         "uid": current_user.id, "now": now})

    # 登记到需求附件（opportunity_requirements.attachments，JSON 列表）
    req_row = db.execute(_t("SELECT id, attachments FROM opportunity_requirements WHERE opportunity_id=:i"),
                         {"i": opp_id}).first()
    try:
        attachments = _json.loads(req_row[1]) if req_row and req_row[1] else []
        if not isinstance(attachments, list):
            attachments = []
    except (ValueError, TypeError):
        attachments = []
    attachments.append({"filename": file.filename, "path": str(save_path), "size": len(raw),
                        "communication_no": comm_no, "uploaded_at": now, "uploaded_by": current_user.id})
    if req_row:
        db.execute(_t("UPDATE opportunity_requirements SET attachments=:a, updated_at=:now WHERE opportunity_id=:i"),
                   {"a": _json.dumps(attachments, ensure_ascii=False), "now": now, "i": opp_id})
    else:
        db.execute(_t("INSERT INTO opportunity_requirements(opportunity_id, attachments, created_at, updated_at) "
                      "VALUES(:i,:a,:now,:now)"), {"i": opp_id, "a": _json.dumps(attachments, ensure_ascii=False), "now": now})
    db.commit()

    # 一步式：直接跑 AI 需求抽取回填（失败不吞上传结果）
    enrichment, enrich_error = None, None
    try:
        enrichment = ai_enrich_requirement(db=db, opp_id=opp_id, current_user=current_user).data
    except HTTPException as e:
        enrich_error = e.detail
    except Exception as e:  # noqa: BLE001
        enrich_error = str(e)[:150]

    return ResponseModel(
        code=200,
        message=("需求文档已入库并完成 AI 需求抽取" if enrichment
                 else f"需求文档已入库，但 AI 抽取失败：{enrich_error}（可稍后点『AI 完善需求』重试）"),
        data={"opportunity_id": opp_id, "filename": file.filename, "extracted_chars": len(text_content),
              "communication_no": comm_no, "attachment_count": len(attachments), "enrichment": enrichment},
    )


# 商机成熟度统一 1-5 整数口径（AI 定性判级 → 数值；5 留给人工确认完备）
MATURITY_LEVELS = {"HIGH": 4, "MEDIUM": 3, "LOW": 2}

# 非标需求十要素（需求澄清 rubric）：filled=10 / partial=5 / missing=0，总分 0-100
REQUIREMENT_GAP_ELEMENTS = [
    ("product_object", "被测/被加工对象"),
    ("cycle_time", "节拍/产能"),
    ("accuracy", "精度/良率/误判率指标"),
    ("interface", "接口与通信(MES/PLC/上下游)"),
    ("site", "现场约束(空间/水电气/净高)"),
    ("acceptance", "验收标准与方法"),
    ("safety", "安全与合规要求"),
    ("budget", "预算"),
    ("delivery", "交期窗口"),
    ("volume", "产品品种/换型与扩展性"),
]


@router.post("/opportunities/{opp_id}/ai-requirement-gaps", response_model=ResponseModel)
def ai_requirement_gaps(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """需求澄清助手：按非标十要素逐项评估信息完备度（附证据原文），生成下次拜访追问清单。
    成熟度改为 rubric 确定性计分（不再由 AI 拍脑袋），治"需求不清晰致失败"的根因。"""
    import json as _json

    from sqlalchemy import text as _t

    from app.services import ai_job_service
    from app.services.ai_client_service import AIClientService

    opp = get_or_404(db, Opportunity, opp_id, "商机不存在")
    req_row = db.execute(
        _t("SELECT product_object, ct_seconds, interface_desc, site_constraints, "
           "acceptance_criteria, safety_requirement, extra_json FROM opportunity_requirements "
           "WHERE opportunity_id=:i"), {"i": opp_id}).first()
    acts = db.execute(
        _t("SELECT topic, content FROM customer_communications WHERE opportunity_id=:i ORDER BY id DESC LIMIT 20"),
        {"i": opp_id}).all()

    context = (
        f"商机：{opp.opp_name}\n设备类型：{opp.equipment_type or ''}\n预算：{opp.budget_range or ''}\n"
        f"交期：{opp.delivery_window or ''}\n验收依据：{opp.acceptance_basis or ''}\n"
    )
    if req_row:
        context += (
            f"已录需求：对象={req_row[0] or ''} 节拍={req_row[1] or ''} 接口={req_row[2] or ''} "
            f"现场={req_row[3] or ''} 验收={req_row[4] or ''} 安全={req_row[5] or ''}\n"
        )
    context += "销售活动/纪要：\n" + ("\n".join(f"[{a[0]}] {a[1]}" for a in acts if a[1]) or "（暂无）")

    elements_spec = "\n".join(f"- {k}：{label}" for k, label in REQUIREMENT_GAP_ELEMENTS)
    prompt = (
        "你是非标自动化售前技术专家。逐项评估下面商机的需求信息完备度，严格只输出 JSON：\n"
        '{"elements":[{"key":"要素key","status":"filled|partial|missing","confidence":0到100,'
        '"evidence":"支撑该判断的原文摘录(没有则空)","question":"若不完备,给销售下次拜访的具体追问话术(完备则空)"}]}\n'
        f"必须覆盖以下 {len(REQUIREMENT_GAP_ELEMENTS)} 个要素（key 逐一对应）：\n{elements_spec}\n\n"
        "判定标准：有明确数值/结论=filled；提到但含糊=partial；完全没提=missing。追问话术要具体可直接照着问。\n\n"
        f"{context}\n\n只返回合法 JSON。"
    )
    ai = AIClientService()
    resp = ai.generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.2, max_tokens=2000)
    s = ai_job_service._extract_json(resp.get("content") or "")
    raw_elements = (s or {}).get("elements")
    if not isinstance(raw_elements, list) or not raw_elements:
        raise HTTPException(status_code=502, detail="AI 未能完成需求缺口分析，请稍后重试")

    # 对齐十要素 + rubric 确定性计分
    by_key = {str(e.get("key")): e for e in raw_elements if isinstance(e, dict)}
    score_map = {"filled": 10, "partial": 5, "missing": 0}
    elements, score, questions = [], 0, []
    for key, label in REQUIREMENT_GAP_ELEMENTS:
        e = by_key.get(key) or {}
        status = e.get("status") if e.get("status") in score_map else "missing"
        score += score_map[status]
        item = {
            "key": key, "label": label, "status": status,
            "confidence": int(e.get("confidence") or 0),
            "evidence": (e.get("evidence") or "")[:300],
            "question": (e.get("question") or "")[:300],
        }
        elements.append(item)
        if status != "filled" and item["question"]:
            questions.append(item["question"])
    maturity = "HIGH" if score >= 75 else ("MEDIUM" if score >= 45 else "LOW")

    # 回写商机成熟度（rubric 分数 → 1-5 整数口径），缺口分析存 opportunity_requirements.extra_json
    opp.requirement_maturity = MATURITY_LEVELS[maturity]
    opp.updated_at = datetime.now()
    db.add(opp)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gap_payload = {"elements": elements, "score": score, "maturity": maturity, "generated_at": now}
    try:
        extra = _json.loads(req_row[6]) if req_row and req_row[6] else {}
        if not isinstance(extra, dict):
            extra = {}
    except (ValueError, TypeError):
        extra = {}
    extra["gap_analysis"] = gap_payload
    extra_str = _json.dumps(extra, ensure_ascii=False)
    if req_row:
        db.execute(_t("UPDATE opportunity_requirements SET extra_json=:e, updated_at=:now WHERE opportunity_id=:i"),
                   {"e": extra_str, "now": now, "i": opp_id})
    else:
        db.execute(_t("INSERT INTO opportunity_requirements(opportunity_id, extra_json, created_at, updated_at) "
                      "VALUES(:i,:e,:now,:now)"), {"i": opp_id, "e": extra_str, "now": now})
    db.commit()

    return ResponseModel(
        code=200,
        message=f"需求完备度 {score}/100（{maturity}），待澄清 {len(questions)} 项",
        data={**gap_payload, "questions": questions},
    )


class OpportunityGateSubmitRequest(BaseModel):
    """商机阶段门提交请求（轻量版，用于 gate_status 更新）"""

    model_config = ConfigDict(populate_by_name=True)

    gate_status: str = Field(..., description="阶段门状态：PASS/REJECT")


@router.post("/opportunities/{opp_id}/gate", response_model=ResponseModel)
def submit_opportunity_gate(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    gate_request: OpportunityGateSubmitRequest,
    gate_type: str = Query("G2", description="阶段门类型: G1, G2, G3, G4"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交商机阶段门（带自动验证）
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not can_set_opportunity_gate(db, current_user, opportunity):
        raise HTTPException(status_code=403, detail="无权限设置商机阶段门")

    # 根据阶段门类型进行验证
    validation_errors = []
    if gate_type == "G2":
        is_valid, errors = validate_g2_opportunity_to_quote(opportunity)
        if not is_valid:
            validation_errors = errors

    if validation_errors and gate_request.gate_status == "PASS":
        raise HTTPException(
            status_code=400, detail=f"{gate_type}阶段门验证失败: {', '.join(validation_errors)}"
        )

    opportunity.gate_status = gate_request.gate_status
    if gate_request.gate_status == "PASS":
        opportunity.gate_passed_at = datetime.now()
    opportunity.updated_by = current_user.id

    db.commit()

    return ResponseModel(
        code=200,
        message=f"{gate_type}阶段门{'通过' if gate_request.gate_status == 'PASS' else '拒绝'}",
        data={"validation_errors": validation_errors} if validation_errors else None,
    )


@router.put("/opportunities/{opp_id}/stage", response_model=OpportunityResponse)
def update_opportunity_stage(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    stage: str = Query(..., description="新阶段"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新商机阶段
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    valid_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    if stage not in valid_stages:
        raise HTTPException(
            status_code=400, detail=f"无效的阶段，必须是: {', '.join(valid_stages)}"
        )

    opportunity.stage = stage
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/score", response_model=OpportunityResponse)
def update_opportunity_score(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    score: int = Query(..., ge=0, le=100, description="评分"),
    score_remark: Optional[str] = Query(None, description="评分说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商机评分（准入评估）
    评分范围：0-100分
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    opportunity.score = score

    # 根据评分自动更新风险等级
    if score >= 80:
        opportunity.risk_level = "LOW"
    elif score >= 60:
        opportunity.risk_level = "MEDIUM"
    else:
        opportunity.risk_level = "HIGH"
    opportunity.updated_by = current_user.id

    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/win", response_model=OpportunityResponse)
def win_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    赢单
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    opportunity.stage = "WON"
    opportunity.gate_status = "PASS"
    opportunity.gate_passed_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/lose", response_model=OpportunityResponse)
def lose_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    lose_reason: Optional[str] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    输单
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    opportunity.stage = "LOST"
    if lose_reason:
        opportunity.lose_reason = lose_reason
    opportunity.lost_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    return _build_opportunity_response(db, opportunity)


# ==================== 新增高频 API ====================

# 阶段推进顺序
STAGE_ORDER = [
    OpportunityStageEnum.DISCOVERY.value,
    OpportunityStageEnum.QUALIFICATION.value,
    OpportunityStageEnum.PROPOSAL.value,
    OpportunityStageEnum.NEGOTIATION.value,
    OpportunityStageEnum.CLOSING.value,
]


class OpportunityAdvanceRequest(BaseModel):
    """商机阶段推进请求"""

    model_config = ConfigDict(populate_by_name=True)

    target_stage: Optional[str] = Field(
        default=None, description="目标阶段（留空自动推进到下一阶段）"
    )
    remark: Optional[str] = Field(default=None, description="推进备注")


class OpportunityLossRequest(BaseModel):
    """商机输单请求"""

    model_config = ConfigDict(populate_by_name=True)

    loss_reason: str = Field(..., min_length=1, description="输单原因（必填）")
    competitor: Optional[str] = Field(default=None, description="竞争对手")
    remark: Optional[str] = Field(default=None, description="备注")


def _build_opportunity_response(db: Session, opportunity: Opportunity) -> OpportunityResponse:
    """构建商机响应对象"""
    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )
    return OpportunityResponse(**opp_dict)


@router.post("/opportunities/{opp_id}/advance", response_model=ResponseModel)
def advance_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: OpportunityAdvanceRequest = Body(default=OpportunityAdvanceRequest()),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    推进商机阶段

    自动推进到下一阶段，或指定目标阶段。
    不能从 WON/LOST 推进，也不能跳过阶段倒退。
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    # 数据权限检查
    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    current_stage = opportunity.stage
    if current_stage in ("WON", "LOST"):
        raise HTTPException(status_code=400, detail=f"商机已{('赢单' if current_stage == 'WON' else '输单')}，无法继续推进")

    if request.target_stage:
        target = request.target_stage
        # 验证目标阶段有效
        valid_targets = STAGE_ORDER + ["WON"]
        if target not in valid_targets:
            raise HTTPException(
                status_code=400, detail=f"无效的目标阶段，可选: {', '.join(valid_targets)}"
            )
        # 不能倒退
        if current_stage in STAGE_ORDER and target in STAGE_ORDER:
            if STAGE_ORDER.index(target) <= STAGE_ORDER.index(current_stage):
                raise HTTPException(status_code=400, detail="不能倒退阶段")
    else:
        # 自动推进到下一阶段
        if current_stage not in STAGE_ORDER:
            raise HTTPException(
                status_code=400, detail=f"当前阶段 {current_stage} 不支持自动推进"
            )
        idx = STAGE_ORDER.index(current_stage)
        if idx >= len(STAGE_ORDER) - 1:
            # CLOSING 之后需要明确 win 或 loss
            raise HTTPException(
                status_code=400,
                detail="已在最后阶段(CLOSING)，请使用赢单或输单接口",
            )
        target = STAGE_ORDER[idx + 1]

    old_stage = opportunity.stage
    opportunity.stage = target
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    logger.info(f"商机 {opp_id} 阶段推进: {old_stage} → {target}, 操作人: {current_user.id}")

    return ResponseModel(
        code=200,
        message=f"商机阶段已从 {old_stage} 推进到 {target}",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": target,
        },
    )


@router.post("/opportunities/{opp_id}/win", response_model=ResponseModel)
def win_opportunity_post(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    remark: Optional[str] = Body(default=None, embed=True),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记赢单
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    if opportunity.stage == "WON":
        raise HTTPException(status_code=400, detail="商机已是赢单状态")
    if opportunity.stage == "LOST":
        raise HTTPException(status_code=400, detail="商机已输单，无法标记赢单")

    old_stage = opportunity.stage
    opportunity.stage = "WON"
    opportunity.gate_status = "PASS"
    opportunity.gate_passed_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    logger.info(f"商机 {opp_id} 赢单: {old_stage} → WON, 操作人: {current_user.id}")

    return ResponseModel(
        code=200,
        message="商机已标记为赢单",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": "WON",
        },
    )


@router.post("/opportunities/{opp_id}/lose", response_model=ResponseModel)
def lose_opportunity_post_compat(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: dict = Body(default={}),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """兼容旧路径：POST /opportunities/{opp_id}/lose。"""
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    if opportunity.stage == "LOST":
        return ResponseModel(
            code=200,
            message="商机已是输单状态",
            data={"opportunity_id": opp_id, "new_stage": "LOST"},
        )
    if opportunity.stage == "WON":
        return ResponseModel(
            code=200,
            message="商机已赢单，未改为输单",
            data={"opportunity_id": opp_id, "new_stage": "WON", "unchanged": True},
        )

    reason = (
        request.get("loss_reason")
        or request.get("lose_reason")
        or request.get("reason")
        or "未填写输单原因"
    )
    old_stage = opportunity.stage
    opportunity.stage = "LOST"
    opportunity.lose_reason = reason
    opportunity.lost_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()

    return ResponseModel(
        code=200,
        message="商机已标记为输单",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": "LOST",
            "loss_reason": reason,
            "competitor": request.get("competitor"),
        },
    )


@router.post("/opportunities/{opp_id}/loss", response_model=ResponseModel)
def loss_opportunity_post(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: OpportunityLossRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记输单（需填写原因）
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    if opportunity.stage == "LOST":
        raise HTTPException(status_code=400, detail="商机已是输单状态")
    if opportunity.stage == "WON":
        raise HTTPException(status_code=400, detail="商机已赢单，无法标记输单")

    old_stage = opportunity.stage
    opportunity.stage = "LOST"
    opportunity.lose_reason = request.loss_reason
    opportunity.lost_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    logger.info(
        f"商机 {opp_id} 输单: {old_stage} → LOST, 原因: {request.loss_reason}, 操作人: {current_user.id}"
    )

    return ResponseModel(
        code=200,
        message="商机已标记为输单",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": "LOST",
            "loss_reason": request.loss_reason,
        },
    )
