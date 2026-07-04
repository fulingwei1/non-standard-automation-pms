# -*- coding: utf-8 -*-
"""收尾批：C2排产工时 · C3质量异常 · C4行业分析 · C5战略规划 · C6经营计划分解 ·
工程师能力匹配 · 售前ROI取舍 · 产能决策 · 竞品情报。"""
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services import ai_job_service
from app.services.project_status_normalization import project_delivery_scope_expr

router = APIRouter(prefix="/ai-planning", tags=["AI战略/经营/资源"])


def _ai(prompt, mt=1800):
    from app.services.ai_client_service import AIClientService
    r = AIClientService().generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=mt)
    return ai_job_service._extract_json(r.get("content") or "")


def _req(db, opp_id):
    o = db.execute(text("SELECT opp_name, equipment_type, est_amount, probability, budget_range FROM opportunities WHERE id=:i"), {"i": opp_id}).first()
    if not o:
        raise HTTPException(status_code=404, detail="商机不存在")
    r = db.execute(text("SELECT product_object, ct_seconds, interface_desc, acceptance_criteria FROM opportunity_requirements WHERE opportunity_id=:i"), {"i": opp_id}).first()
    return o, (f"设备:{o[1] or ''}; 产品对象:{r[0] if r else ''}; 节拍:{r[1] if r else ''}秒; 接口:{r[2] if r else ''}; 验收:{r[3] if r else ''}")


class OppRef(BaseModel):
    opportunity_id: int


@router.post("/effort-estimate", response_model=ResponseModel, summary="C2 工时/装配阶段估算")
def effort_estimate(req: OppRef, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    _, ctx = _req(db, req.opportunity_id)
    r = _ai("你是非标自动化项目工程师。根据需求估算各阶段工时与装配指导，严格只输出 JSON：\n"
            '{"stages":[{"stage":"阶段(设计/采购/机加/装配/调试/验收)","man_days":工时人天,"key_points":"关键作业要点"}],'
            '"total_man_days":合计人天,"critical_path":"关键路径提示"}\n\n' + f"需求：{ctx}\n只返回合法 JSON。")
    if not isinstance(r, dict) or not r.get("stages"):
        raise HTTPException(status_code=502, detail="AI 估算失败，请先完善需求")
    return ResponseModel(code=200, message="AI 工时估算完成", data=r)


@router.post("/quality-risk", response_model=ResponseModel, summary="C3 质量风险+备件预测")
def quality_risk(req: OppRef, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    _, ctx = _req(db, req.opportunity_id)
    r = _ai("你是非标自动化质量工程师。预测该设备常见质量风险与应备件，严格只输出 JSON：\n"
            '{"quality_risks":[{"risk":"质量风险点","prevention":"预防措施"}],"spare_parts":["建议常备易损/关键备件"]}\n\n' + f"需求：{ctx}\n只返回合法 JSON。")
    if not isinstance(r, dict) or not (r.get("quality_risks") or r.get("spare_parts")):
        raise HTTPException(status_code=502, detail="AI 质量分析失败")
    return ResponseModel(code=200, message="AI 质量风险分析完成", data=r)


class IndustryReq(BaseModel):
    industry: str = Field(..., min_length=1)


@router.post("/industry-analysis", response_model=ResponseModel, summary="C4 行业分析")
def industry_analysis(req: IndustryReq, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    cnt = db.execute(text("SELECT COUNT(*) FROM opportunities o LEFT JOIN customers c ON c.id=o.customer_id WHERE c.industry LIKE :ind"), {"ind": f"%{req.industry}%"}).scalar() or 0
    won = db.execute(text("SELECT COUNT(*) FROM opportunities o LEFT JOIN customers c ON c.id=o.customer_id WHERE c.industry LIKE :ind AND o.stage='WON'"), {"ind": f"%{req.industry}%"}).scalar() or 0
    r = _ai(f"你是非标自动化行业分析师。结合我方在『{req.industry}』行业内部数据(商机{cnt}个/成交{won}个)做行业分析，严格只输出 JSON：\n"
            '{"trends":["行业趋势/自动化需求驱动"],"opportunities":["机会点"],"threats":["威胁/风险"],"our_position":"我方地位评估","suggestions":["拓展建议"]}\n\n只返回合法 JSON。')
    if not isinstance(r, dict) or not r.get("trends"):
        raise HTTPException(status_code=502, detail="AI 行业分析失败")
    return ResponseModel(code=200, message="AI 行业分析完成", data={"industry": req.industry, "internal_opps": cnt, "won": won, **r})


class StrategyReq(BaseModel):
    situation: str = Field(..., min_length=5, description="当前经营态势/战略议题")


@router.post("/strategy-support", response_model=ResponseModel, summary="C5 战略规划决策支持")
def strategy_support(req: StrategyReq, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    r = _ai("你是企业战略顾问(非标自动化)。针对战略议题给决策支持，严格只输出 JSON：\n"
            '{"options":[{"option":"战略选项","pros":"优势","cons":"风险","resource_need":"资源需求"}],'
            '"recommendation":"推荐方向及理由","csf":["关键成功要素CSF"]}\n\n' + f"战略议题：{req.situation}\n只返回合法 JSON。")
    if not isinstance(r, dict) or not r.get("options"):
        raise HTTPException(status_code=502, detail="AI 战略分析失败")
    return ResponseModel(code=200, message="AI 战略决策支持完成", data=r)


class PlanReq(BaseModel):
    annual_target: float = Field(..., gt=0, description="年度目标营收(元)")


@router.post("/plan-breakdown", response_model=ResponseModel, summary="C6 经营计划分解+可达性校验")
def plan_breakdown(req: PlanReq, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    row = db.execute(text("SELECT COUNT(*), COALESCE(SUM(est_amount),0) FROM opportunities WHERE stage NOT IN ('WON','LOST','CLOSED')")).first()
    won = db.execute(text("SELECT COUNT(*) FROM opportunities WHERE stage='WON'")).scalar() or 0
    lost = db.execute(text("SELECT COUNT(*) FROM opportunities WHERE stage='LOST'")).scalar() or 0
    win_rate = round(won / (won + lost) * 100, 1) if (won + lost) else 0
    pipeline = float(row[1] or 0)
    weighted = pipeline * win_rate / 100
    r = _ai(f"你是经营分析师。年度目标营收¥{req.annual_target:.0f}，当前在手pipeline¥{pipeline:.0f}(赢单率{win_rate}%，加权可期¥{weighted:.0f})。"
            "把目标分解并校验可达性，严格只输出 JSON：\n"
            '{"quarterly":[{"quarter":"Q1","target":金额}],"gap":"目标与加权pipeline的缺口评估","achievable":"高|中|低",'
            '"key_actions":["达成目标的关键动作"]}\n\n只返回合法 JSON。')
    if not isinstance(r, dict) or not r.get("quarterly"):
        raise HTTPException(status_code=502, detail="AI 计划分解失败")
    return ResponseModel(code=200, message="AI 经营计划分解完成",
                         data={"annual_target": req.annual_target, "pipeline": pipeline, "win_rate": win_rate, "weighted_pipeline": weighted, **r})


class TaskReq(BaseModel):
    task_desc: str = Field(..., min_length=4, description="任务/项目描述")


@router.post("/staffing", response_model=ResponseModel, summary="工程师能力匹配/配置建议")
def staffing(req: TaskReq, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    r = _ai("你是非标自动化技术经理。为任务拆解所需能力并给配置建议，严格只输出 JSON：\n"
            '{"required_skills":["所需专业能力(机械/电气/视觉/软件/调试)"],"team_composition":[{"role":"角色","count":人数,"why":"原因"}],'
            '"risk":"人员风险提示"}\n\n' + f"任务：{req.task_desc}\n只返回合法 JSON。")
    if not isinstance(r, dict) or not r.get("required_skills"):
        raise HTTPException(status_code=502, detail="AI 能力匹配失败")
    return ResponseModel(code=200, message="AI 能力匹配完成", data=r)


@router.post("/presale-roi", response_model=ResponseModel, summary="售前投入ROI取舍")
def presale_roi(req: OppRef, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    o, ctx = _req(db, req.opportunity_id)
    value = float(o[2] or 0)
    prob = float(o[3] or 0)
    expected = value * prob / 100 if prob else value * 0.3
    r = _ai(f"你是销售运营。商机『{o[0]}』预计金额¥{value:.0f}，赢率{prob or '未知'}%，加权价值¥{expected:.0f}。需求：{ctx}。"
            "判断是否值得投入售前资源，严格只输出 JSON：\n"
            '{"verdict":"值得投入|谨慎投入|不建议","reason":"理由","suggested_effort":"建议投入程度(轻/中/重)","conditions":["投入的前提条件"]}\n\n只返回合法 JSON。')
    if not isinstance(r, dict) or not r.get("verdict"):
        raise HTTPException(status_code=502, detail="AI ROI分析失败")
    return ResponseModel(code=200, message="AI 售前ROI分析完成", data={"expected_value": expected, **r})


@router.post("/capacity-decision", response_model=ResponseModel, summary="能不能接-产能决策")
def capacity_decision(req: OppRef, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    o, ctx = _req(db, req.opportunity_id)
    delivery_projects = db.query(Project).filter(project_delivery_scope_expr(Project))
    load = delivery_projects.count()
    near_delivery = (
        delivery_projects.filter(
            Project.planned_end_date.isnot(None),
            Project.planned_end_date < date.today() + timedelta(days=45),
        ).count()
    )
    r = _ai(f"你是运营总监。当前在制项目{load}个(其中{near_delivery}个45天内需交付)。新订单需求：{ctx}。"
            "判断能否按期承接，严格只输出 JSON：\n"
            '{"can_take":"能接|有条件接|建议婉拒","bottleneck":["产能瓶颈(设计/装配/调试/长周期件)"],"conditions":["承接前提"],"delivery_risk":"交付风险评估"}\n\n只返回合法 JSON。')
    if not isinstance(r, dict) or not r.get("can_take"):
        raise HTTPException(status_code=502, detail="AI 产能决策失败")
    return ResponseModel(code=200, message="AI 产能决策完成", data={"current_load": load, "near_delivery": near_delivery, **r})


class CompetitorReq(BaseModel):
    competitor_info: str = Field(..., min_length=5, description="竞品信息/丢单原因/对手报价等")


@router.post("/competitor-intel", response_model=ResponseModel, summary="竞品情报聚合分析")
def competitor_intel(req: CompetitorReq, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    lost = db.execute(text("SELECT COUNT(*) FROM opportunities WHERE stage='LOST'")).scalar() or 0
    r = _ai(f"你是竞争情报分析师。我方近期丢单{lost}个。根据竞品信息做分析，严格只输出 JSON：\n"
            '{"competitor_strengths":["对手优势"],"our_gaps":["我方短板"],"price_position":"价格带定位评估","counter_strategy":["应对策略"]}\n\n'
            + f"竞品信息：{req.competitor_info}\n只返回合法 JSON。")
    if not isinstance(r, dict) or not (r.get("counter_strategy") or r.get("our_gaps")):
        raise HTTPException(status_code=502, detail="AI 竞品分析失败")
    return ResponseModel(code=200, message="AI 竞品情报分析完成", data={"lost_count": lost, **r})
