# -*- coding: utf-8 -*-
"""工程/售后类 AI：B1 BOM智能选型 · B4 售后故障诊断 · M3 配置式设计。"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import KnowledgeBase, ServiceTicket
from app.models.service.enums import KnowledgeBaseStatusEnum
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services import ai_job_service

router = APIRouter(prefix="/ai-eng", tags=["AI工程/售后"])
logger = logging.getLogger(__name__)


def _ai(prompt: str, max_tokens: int = 1600):
    from app.services.ai_client_service import AIClientService

    resp = AIClientService().generate_solution(
        prompt=prompt, model="qwen3-coder-plus", temperature=0.25, max_tokens=max_tokens)
    return ai_job_service._extract_json(resp.get("content") or "")


def _opp_requirement(db: Session, opp_id: int) -> str:
    o = db.execute(text("SELECT opp_name, equipment_type, budget_range FROM opportunities WHERE id=:i"), {"i": opp_id}).first()
    if not o:
        raise HTTPException(status_code=404, detail="商机不存在")
    r = db.execute(text("SELECT product_object, ct_seconds, interface_desc, site_constraints, acceptance_criteria "
                        "FROM opportunity_requirements WHERE opportunity_id=:i"), {"i": opp_id}).first()
    return (f"商机:{o[0]}; 设备类型:{o[1] or ''}; 预算:{o[2] or ''}; 产品对象:{r[0] if r else ''}; "
            f"节拍:{r[1] if r else ''}秒; 接口:{r[2] if r else ''}; 现场:{r[3] if r else ''}; 验收:{r[4] if r else ''}")


class OppRef(BaseModel):
    opportunity_id: int


@router.post("/bom-selection", response_model=ResponseModel, summary="B1 BOM智能选型")
def bom_selection(req: OppRef, db: Session = Depends(deps.get_db),
                  current_user: User = Depends(security.get_current_active_user)) -> Any:
    """按需求 AI 推荐标准件选型（相机/PLC/伺服/传感器等品牌型号 + 理由）。"""
    ctx = _opp_requirement(db, req.opportunity_id)
    prompt = ("你是非标自动化选型工程师。根据需求推荐关键标准件选型，严格只输出 JSON 数组：\n"
              '[{"part":"部件类别(如工业相机)","brand_model":"推荐品牌型号","reason":"选型理由","est_price":参考单价}]\n\n'
              f"需求：{ctx}\n\n覆盖视觉/控制(PLC)/运动(伺服/步进)/传感/气动/电源等，8-14项，只返回合法 JSON。")
    r = _ai(prompt)
    r = r if isinstance(r, list) else (r.get("selection") if isinstance(r, dict) else None)
    if not isinstance(r, list) or not r:
        raise HTTPException(status_code=502, detail="AI 选型失败，请先完善需求")
    return ResponseModel(code=200, message="AI 选型完成", data={"selection": r})


class DesignReq(OppRef):
    persist: bool = False  # True 时把方案落库 presale_solution（可迭代/评审/转报价）


def _recent_lessons(db: Session, keyword: str = "") -> list:
    """取历史项目教训（复盘 lessons + 经验库），供方案生成时提醒历史坑。"""
    rows = []
    kw = f"%{keyword}%" if keyword else "%"
    try:
        rows += db.execute(text(
            "SELECT title, COALESCE(improvement_action, description) FROM project_lessons "
            "WHERE title LIKE :k OR description LIKE :k ORDER BY id DESC LIMIT 5"), {"k": kw}).all()
    except Exception:  # noqa: BLE001 - 表缺失时跳过
        pass
    try:
        rows += db.execute(text(
            "SELECT title, COALESCE(recommendation, description) FROM lessons_learned "
            "WHERE title LIKE :k OR description LIKE :k ORDER BY id DESC LIMIT 5"), {"k": kw}).all()
    except Exception:  # noqa: BLE001
        pass
    if keyword and not rows:  # 按设备类型没命中时退回最近教训
        return _recent_lessons(db, "")
    return [(r[0], r[1]) for r in rows if r[0]]


@router.post("/config-design", response_model=ResponseModel, summary="M3 配置式设计")
def config_design(req: DesignReq, db: Session = Depends(deps.get_db),
                  current_user: User = Depends(security.get_current_active_user)) -> Any:
    """按需求从标准模块库推荐模块组合 + 定制项，秒搭方案骨架（工程师只改定制部分）。
    生成时注入历史项目教训（历史坑提醒）；persist=True 时落库售前方案（版本链），进入评审/报价闭环。"""
    import json as _json

    ctx = _opp_requirement(db, req.opportunity_id)
    mods = db.execute(text("SELECT module_name, category, description FROM ai_standard_modules ORDER BY source_count DESC LIMIT 30")).all()
    mod_txt = "\n".join(f"- {m[0]}（{m[1]}）：{m[2] or ''}" for m in mods) or "（模块库为空，请先AI挖模块）"
    opp = db.execute(text("SELECT opp_name, equipment_type, customer_id FROM opportunities WHERE id=:i"),
                     {"i": req.opportunity_id}).first()
    lessons = _recent_lessons(db, (opp[1] or "") if opp else "")
    lesson_txt = "\n".join(f"- {t}：{d or ''}" for t, d in lessons) or "（暂无）"
    prompt = ("你是非标自动化方案设计师。根据需求从【标准模块库】选模块组合搭方案骨架，缺的列为定制项，"
              "并对照【历史项目教训】给出本方案要避开的坑，严格只输出 JSON：\n"
              '{"modules":[{"module_name":"","qty":1,"role":"在方案中承担的功能"}],'
              '"custom_parts":[{"name":"定制项","reason":"为什么要定制"}],"architecture":"方案骨架一句话描述",'
              '"reuse_rate":"标准模块复用率%估计",'
              '"risk_reminders":[{"reminder":"本方案要注意的坑及对策","source":"来自哪条历史教训(没有对应就写经验判断)"}]}\n\n'
              f"需求：{ctx}\n\n可用模块库：\n{mod_txt}\n\n历史项目教训：\n{lesson_txt}\n\n只返回合法 JSON。")
    r = _ai(prompt, 2400)
    if not isinstance(r, dict) or not r.get("modules"):
        raise HTTPException(status_code=502, detail="AI 配置式设计失败，请先完善需求/挖模块")

    # persist=True：落库售前方案（同商机的 AI 方案形成版本链 parent_id/version）
    if req.persist:
        from app.models.presale import PresaleSolution
        from app.utils.domain_codes import presale as presale_codes

        prev = (db.query(PresaleSolution)
                .filter(PresaleSolution.opportunity_id == req.opportunity_id,
                        PresaleSolution.name.like("【AI配置设计】%"))
                .order_by(PresaleSolution.id.desc()).first())
        spec = {k: r.get(k) for k in ("modules", "custom_parts", "architecture", "reuse_rate", "risk_reminders")}
        solution = PresaleSolution(
            solution_no=presale_codes.generate_solution_no(db),
            name=f"【AI配置设计】{(opp[0] if opp else '')[:80]}",
            solution_type="CUSTOM",
            customer_id=(opp[2] if opp else None),
            opportunity_id=req.opportunity_id,
            requirement_summary=ctx[:1000],
            solution_overview=r.get("architecture") or "",
            technical_spec=_json.dumps(spec, ensure_ascii=False),
            status="DRAFT",
            version=f"V{(int((prev.version or 'V1').lstrip('Vv').split('.')[0]) + 1) if prev else 1}",
            parent_id=prev.id if prev else None,
            author_id=current_user.id,
            author_name=getattr(current_user, "real_name", None) or current_user.username,
        )
        db.add(solution)
        db.commit()
        db.refresh(solution)
        r["solution_id"] = solution.id
        r["solution_no"] = solution.solution_no
        r["solution_version"] = solution.version
    return ResponseModel(code=200, message="AI 配置式设计完成", data=r)


class CoverageReq(BaseModel):
    opportunity_id: int
    solution_id: Optional[int] = None  # 缺省用该商机最新的 AI 配置设计方案


@router.post("/requirement-coverage", response_model=ResponseModel, summary="需求-方案符合性矩阵")
def requirement_coverage(req: CoverageReq, db: Session = Depends(deps.get_db),
                         current_user: User = Depends(security.get_current_active_user)) -> Any:
    """逐条需求核对方案覆盖情况（哪个模块满足/满足度），未覆盖项高亮——防漏项返工，验收对照可复用。
    矩阵结果并入方案 technical_spec，随方案沉淀。"""
    import json as _json
    from datetime import datetime as _dt

    from app.models.presale import PresaleSolution

    ctx = _opp_requirement(db, req.opportunity_id)
    q = db.query(PresaleSolution)
    if req.solution_id:
        solution = q.filter(PresaleSolution.id == req.solution_id).first()
    else:
        solution = (q.filter(PresaleSolution.opportunity_id == req.opportunity_id,
                             PresaleSolution.name.like("【AI配置设计】%"))
                    .order_by(PresaleSolution.id.desc()).first())
    if not solution:
        raise HTTPException(status_code=400, detail="未找到方案，请先运行配置式设计并落库（persist=true）")
    try:
        spec = _json.loads(solution.technical_spec or "{}")
    except (ValueError, TypeError):
        spec = {}
    modules = spec.get("modules") or []
    customs = spec.get("custom_parts") or []
    if not modules and not customs:
        raise HTTPException(status_code=400, detail="方案无模块明细，无法核对覆盖")

    mod_txt = "\n".join(f"- 模块 {m.get('module_name')}×{m.get('qty', 1)}：{m.get('role', '')}" for m in modules)
    mod_txt += "\n" + "\n".join(f"- 定制 {c.get('name')}：{c.get('reason', '')}" for c in customs)
    acts = db.execute(text(
        "SELECT topic, content FROM customer_communications WHERE opportunity_id=:i ORDER BY id DESC LIMIT 10"),
        {"i": req.opportunity_id}).all()
    act_txt = "\n".join(f"[{a[0]}] {a[1]}" for a in acts if a[1]) or "（无）"
    prompt = ("你是非标自动化技术评审专家。综合结构化需求与客户沟通原文，把需求拆成尽可能细的可核对条目"
              "（节拍/精度/接口/现场/验收/安全等，5-12条），逐条判断方案是否覆盖，严格只输出 JSON：\n"
              '{"matrix":[{"requirement":"需求条目","covered_by":"满足它的模块/定制项(未覆盖则空)",'
              '"coverage":"满足|部分|未覆盖","note":"说明/差距"}],'
              '"coverage_rate":"覆盖率%","uncovered":["未覆盖需求条目"]}\n\n'
              f"结构化需求：{ctx}\n\n客户沟通原文：\n{act_txt}\n\n方案构成：\n{mod_txt}\n\n只返回合法 JSON。")
    r = _ai(prompt, 2400)
    if not isinstance(r, dict) or not isinstance(r.get("matrix"), list) or not r.get("matrix"):
        raise HTTPException(status_code=502, detail="AI 覆盖核对失败，请稍后重试")

    # 矩阵并入方案 technical_spec，随方案沉淀
    spec["coverage_matrix"] = {
        "matrix": r["matrix"],
        "coverage_rate": r.get("coverage_rate"),
        "uncovered": r.get("uncovered") or [],
        "generated_at": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    solution.technical_spec = _json.dumps(spec, ensure_ascii=False)
    db.add(solution)
    db.commit()

    uncovered = r.get("uncovered") or []
    return ResponseModel(
        code=200,
        message=f"覆盖核对完成：{r.get('coverage_rate') or ''}，未覆盖 {len(uncovered)} 项",
        data={**r, "solution_id": solution.id, "solution_no": solution.solution_no},
    )


class FaultReq(BaseModel):
    symptom: str = Field(..., min_length=2, description="故障现象描述")
    equipment_type: Optional[str] = None


def _fault_search_keyword(req: FaultReq) -> str:
    symptom = (req.symptom or "").strip()
    if len(symptom) <= 80:
        return symptom
    return symptom[:80]


def _fault_context(db: Session, req: FaultReq) -> dict:
    keyword = _fault_search_keyword(req)
    like_keyword = f"%{keyword}%"

    tickets = (
        db.query(ServiceTicket)
        .filter(
            or_(
                ServiceTicket.problem_desc.like(like_keyword),
                ServiceTicket.solution.like(like_keyword),
                ServiceTicket.root_cause.like(like_keyword),
                ServiceTicket.problem_type.like(like_keyword),
            )
        )
        .order_by(ServiceTicket.reported_time.desc(), ServiceTicket.id.desc())
        .limit(5)
        .all()
        if keyword
        else []
    )
    articles = (
        db.query(KnowledgeBase)
        .filter(
            KnowledgeBase.status == KnowledgeBaseStatusEnum.PUBLISHED.value,
            or_(
                KnowledgeBase.title.like(like_keyword),
                KnowledgeBase.content.like(like_keyword),
                KnowledgeBase.category.like(like_keyword),
            ),
        )
        .order_by(KnowledgeBase.helpful_count.desc(), KnowledgeBase.view_count.desc())
        .limit(5)
        .all()
        if keyword
        else []
    )

    ticket_text = "\n".join(
        (
            f"- {ticket.ticket_no} [{ticket.problem_type}/{ticket.status}] "
            f"现象:{ticket.problem_desc or ''}; 根因:{ticket.root_cause or ''}; "
            f"方案:{ticket.solution or ''}"
        )
        for ticket in tickets
    )
    article_text = "\n".join(
        f"- {article.title}（{article.category}）：{(article.content or '')[:300]}"
        for article in articles
    )

    return {
        "history": ticket_text or "（未检索到相似历史工单）",
        "knowledge": article_text or "（未检索到相关服务知识库文章）",
        "sources": {
            "service_tickets": len(tickets),
            "knowledge_base": len(articles),
        },
    }


def _fault_rule_fallback(req: FaultReq, context_sources: dict) -> dict:
    equipment = req.equipment_type or "非标自动化设备"
    return {
        "possible_causes": [
            {
                "cause": f"{equipment} 供电/气源/急停/安全门等基础条件异常",
                "likelihood": "中",
                "check": "先确认电源、气压、急停、安全门、互锁信号和报警码",
            },
            {
                "cause": "PLC/驱动器/传感器信号链异常",
                "likelihood": "中",
                "check": "按输入信号、输出信号、执行机构逐段排查",
            },
        ],
        "steps": [
            "记录报警码、发生工位、发生频次和最近变更",
            "断电挂牌后检查线缆、端子、气源和机械卡滞",
            "上电后用 PLC/驱动器诊断界面逐点核对 I/O 与报警状态",
            "对照历史工单和知识库执行相同故障的验证步骤",
        ],
        "safety": "涉及运动机构、强电、气动夹具时先断电泄压并挂牌，禁止带电拆线。",
        "ai_generated": False,
        "degraded": True,
        "degraded_reason": "AI_DIAGNOSIS_UNAVAILABLE",
        "context_sources": context_sources,
    }


@router.post("/fault-diagnosis", response_model=ResponseModel, summary="B4 售后故障诊断")
def fault_diagnosis(req: FaultReq, db: Session = Depends(deps.get_db),
                    current_user: User = Depends(security.get_current_active_user)) -> Any:
    """现场/售后故障：现象 → AI 给可能原因 + 排查步骤（把老师傅经验做成可问的助手）。"""
    context = _fault_context(db, req)
    prompt = ("你是非标自动化资深调试/售后工程师。根据故障现象给诊断，严格只输出 JSON：\n"
              '{"possible_causes":[{"cause":"可能原因","likelihood":"高|中|低","check":"排查方法"}],'
              '"steps":["按顺序的排查处理步骤"],"safety":"安全注意事项"}\n\n'
              f"设备类型：{req.equipment_type or '非标自动化设备'}\n故障现象：{req.symptom}\n\n"
              f"历史服务工单：\n{context['history']}\n\n"
              f"服务知识库：\n{context['knowledge']}\n\n只返回合法 JSON。")
    try:
        r = _ai(prompt)
    except Exception as exc:  # noqa: BLE001 - AI unavailable should degrade visibly
        logger.warning("AI 故障诊断调用失败，使用规则降级: %s", exc)
        r = None

    if not isinstance(r, dict) or not (r.get("possible_causes") or r.get("steps")):
        fallback = _fault_rule_fallback(req, context["sources"])
        return ResponseModel(code=200, message="AI 故障诊断暂不可用，已返回规则降级建议", data=fallback)
    r["ai_generated"] = True
    r["degraded"] = False
    r["context_sources"] = context["sources"]
    return ResponseModel(code=200, message="AI 故障诊断完成", data=r)


@router.post("/procurement-advice", response_model=ResponseModel, summary="B2 采购智能(交期/替代料)")
def procurement_advice(req: OppRef, db: Session = Depends(deps.get_db),
                       current_user: User = Depends(security.get_current_active_user)) -> Any:
    """按需求识别长周期件 + 交期风险 + 替代料建议（非标长周期件的齐套是交付命门）。"""
    ctx = _opp_requirement(db, req.opportunity_id)
    prompt = ("你是非标自动化采购工程师。根据需求识别关键采购件，评估交期风险并给替代料建议，严格只输出 JSON 数组：\n"
              '[{"part":"部件","lead_time":"预计交期(如4-6周)","risk":"高|中|低","risk_reason":"交期风险原因",'
              '"alternative":"可替代方案/国产替代或空"}]\n\n'
              f"需求：{ctx}\n\n重点关注进口相机/镜头/伺服/PLC/专用治具等长周期件，8-12项，只返回合法 JSON。")
    r = _ai(prompt)
    r = r if isinstance(r, list) else (r.get("items") if isinstance(r, dict) else None)
    if not isinstance(r, list) or not r:
        raise HTTPException(status_code=502, detail="AI 采购分析失败，请先完善需求")
    return ResponseModel(code=200, message="AI 采购分析完成", data={"items": r})


class ProjRef(BaseModel):
    project_id: int


@router.post("/project-review", response_model=ResponseModel, summary="B5 AI项目复盘")
def project_review(req: ProjRef, db: Session = Depends(deps.get_db),
                   current_user: User = Depends(security.get_current_active_user)) -> Any:
    """按项目数据 AI 自动复盘 + 经验教训（让这次踩的坑下次不再踩）。"""
    p = db.execute(text("SELECT project_code, project_name, status, progress_pct, planned_start_date, "
                        "planned_end_date, actual_start_date, actual_end_date, health "
                        "FROM projects WHERE id=:i"), {"i": req.project_id}).first()
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    ctx = (f"项目:{p[1]}({p[0]}); 状态:{p[2]}; 进度:{p[3]}%; 计划:{p[4]}~{p[5]}; 实际:{p[6]}~{p[7]}; 健康:{p[8]}")
    prompt = ("你是非标自动化PMO。根据项目数据做**复盘**，严格只输出 JSON：\n"
              '{"went_well":["做得好的"],"problems":["暴露的问题"],"lessons":["可复用的经验教训"],'
              '"reusable_assets":["可沉淀为标准的模块/方案/流程"],"summary":"一句话复盘结论"}\n\n'
              f"项目数据：{ctx}\n\n结合非标自动化交付规律，只返回合法 JSON。")
    r = _ai(prompt)
    if not isinstance(r, dict) or not (r.get("lessons") or r.get("problems")):
        raise HTTPException(status_code=502, detail="AI 复盘失败")
    return ResponseModel(code=200, message="AI 项目复盘完成", data=r)
