# -*- coding: utf-8 -*-
"""AI Copilot：提升效率与易用性的通用 AI 能力。
1 全局命令栏  2 语义搜索  3 日报/周报  4 一键摘要  5 翻译  6 邮件代写
7 自然语言筛选  8 我的一天(待办聚合)  9 智能表单填充  10 文本润色/规范化  11 操作助手
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services import ai_job_service

router = APIRouter(prefix="/ai-copilot", tags=["AI Copilot(提效/易用)"])


def _ai(prompt, mt=1400, temp=0.3):
    from app.services.ai_client_service import AIClientService
    return (AIClientService().generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=temp, max_tokens=mt).get("content") or "").strip()


def _aij(prompt, mt=1400):
    return ai_job_service._extract_json(_ai(prompt, mt))


# ---- 2 全局语义搜索（命令栏也复用） ----
def _search(db: Session, q: str, limit: int = 8):
    kw = f"%{q}%"
    res = []
    for r in db.execute(text("SELECT id, opp_name, stage FROM opportunities WHERE opp_name LIKE :k OR equipment_type LIKE :k LIMIT :n"), {"k": kw, "n": limit}).all():
        res.append({"type": "商机", "id": r[0], "title": r[1], "sub": r[2], "path": f"/sales/opportunities/{r[0]}"})
    for r in db.execute(text("SELECT id, customer_name, industry FROM customers WHERE customer_name LIKE :k OR industry LIKE :k LIMIT :n"), {"k": kw, "n": limit}).all():
        res.append({"type": "客户", "id": r[0], "title": r[1], "sub": r[2] or "", "path": f"/customers/{r[0]}"})
    for r in db.execute(text("SELECT id, project_name, status FROM projects WHERE project_name LIKE :k LIMIT :n"), {"k": kw, "n": limit}).all():
        res.append({"type": "项目", "id": r[0], "title": r[1], "sub": r[2], "path": f"/projects/{r[0]}"})
    for r in db.execute(text("SELECT id, module_name, category FROM ai_standard_modules WHERE module_name LIKE :k OR description LIKE :k LIMIT :n"), {"k": kw, "n": limit}).all():
        res.append({"type": "模块", "id": r[0], "title": r[1], "sub": r[2] or "", "path": "/engineering/module-library"})
    return res


@router.get("/search", response_model=ResponseModel, summary="全局搜索")
def search(q: str = Query(..., min_length=1), db: Session = Depends(deps.get_db),
           current_user: User = Depends(security.get_current_active_user)) -> Any:
    return ResponseModel(code=200, message="ok", data={"results": _search(db, q)})


# ---- 1 全局命令栏（自然语言 → 导航/问答/搜索） ----
class CommandReq(BaseModel):
    input: str = Field(..., min_length=1)


ROUTES = {
    "销售仪表盘": "/sales/dashboard", "商机": "/sales/opportunities", "客户": "/customers",
    "报价": "/cost-quotes/quotes", "合同": "/sales/contracts", "项目": "/projects",
    "模块库": "/engineering/module-library", "故障诊断": "/service/fault-diagnosis",
    "AI助手": "/ai/assistant", "会议纪要": "/sales/meeting-minutes-ai", "PMO": "/pmo/dashboard",
}


# 命令栏可执行的动作（只打开预填好的新建对话框，不直接写库，由用户确认后创建）
ACTIONS = {
    "create_opportunity": {"path": "/sales/opportunities", "label": "新建商机"},
    "create_customer": {"path": "/sales/customers", "label": "新建客户"},
}


@router.post("/command", response_model=ResponseModel, summary="全局AI命令栏")
def command(body: CommandReq, db: Session = Depends(deps.get_db),
            current_user: User = Depends(security.get_current_active_user)) -> Any:
    q = body.input.strip()
    # 先做实体搜索（命中即优先给导航候选）
    hits = _search(db, q, limit=5)
    prompt = ("你是系统内的AI助手。判断用户输入意图并只输出 JSON：\n"
              '{"intent":"navigate|search|answer|action","page":"若是导航,给最匹配的页面名",'
              '"answer":"若是问答,直接给简短答案",'
              '"action":"若是执行动作,给动作名(create_opportunity|create_customer)",'
              '"hint":"若是执行动作,提取用于预填表单的业务线索(去掉新建/创建等指令词)"}\n'
              "意图判断：用户明确要新建/创建/录入客户或商机时是 action；只是想打开某页面是 navigate；"
              "问数据或问题是 answer；其余是 search。\n"
              f"可导航页面：{list(ROUTES.keys())}\n用户输入：{q}\n只返回合法 JSON。")
    r = _aij(prompt, 500) or {}
    intent = r.get("intent", "search")
    data = {"intent": intent, "hits": hits}
    if intent == "navigate":
        page = r.get("page", "")
        path = ROUTES.get(page) or next((ROUTES[k] for k in ROUTES if k in page or page in k), None)
        data["path"] = path
        data["page"] = page
    elif intent == "answer":
        data["answer"] = r.get("answer", "")
    elif intent == "action":
        action = ACTIONS.get(r.get("action", ""))
        if action:
            data["action"] = r.get("action")
            data["path"] = action["path"]
            data["label"] = action["label"]
            data["hint"] = (r.get("hint") or q).strip()
        else:
            data["intent"] = "search"
    return ResponseModel(code=200, message="ok", data=data)


# ---- 3 日报/周报自动生成 ----
@router.get("/report", response_model=ResponseModel, summary="日报/周报自动生成")
def report(period: str = Query("day", pattern="^(day|week)$"), db: Session = Depends(deps.get_db),
           current_user: User = Depends(security.get_current_active_user)) -> Any:
    days = 1 if period == "day" else 7
    acts = db.execute(text(
        "SELECT topic, content, created_at FROM customer_communications "
        "WHERE created_by=:u AND created_at >= datetime('now', :d) ORDER BY created_at DESC LIMIT 40"),
        {"u": current_user.id, "d": f"-{days} day"}).all()
    if not acts:
        return ResponseModel(code=200, message="ok", data={"report": "（所选周期内暂无活动记录）", "activity_count": 0})
    body = "\n".join(f"- {a[0]}: {a[1]}" for a in acts if a[1])
    rp = _ai(f"你是销售/工程师本人。把下面的活动记录整理成一份简洁的{'日报' if days==1 else '周报'}(分'已完成/进展''下一步计划''需协调'三段)，直接输出正文：\n{body}", mt=1200)
    return ResponseModel(code=200, message="ok", data={"report": rp, "activity_count": len(acts), "period": period})


@router.get("/my-reports", response_model=ResponseModel, summary="我的日报/周报历史")
def my_reports(limit: int = Query(20, le=50), db: Session = Depends(deps.get_db),
               current_user: User = Depends(security.get_current_active_user)) -> Any:
    """查看已推送给我的历史日报/周报。"""
    rows = db.execute(text(
        "SELECT notification_type, title, content, created_at FROM notifications "
        "WHERE user_id=:u AND notification_type IN ('DAILY_REPORT','WEEKLY_REPORT') "
        "ORDER BY created_at DESC LIMIT :n"), {"u": current_user.id, "n": limit}).all()
    reports = [{"period": "week" if r[0] == "WEEKLY_REPORT" else "day",
                "title": r[1], "content": r[2], "created_at": str(r[3])} for r in rows]
    return ResponseModel(code=200, message="ok", data={"total": len(reports), "reports": reports})


# ---- 4 一键摘要 ----
class TextReq(BaseModel):
    text: str = Field(..., min_length=10)


@router.post("/summarize", response_model=ResponseModel, summary="长文本一键摘要")
def summarize(body: TextReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    r = _aij("把下面文本浓缩，严格只输出 JSON：\n"
             '{"summary":"3句话内摘要","key_points":["要点"],"actions":["需跟进事项"]}\n\n' + body.text[:6000])
    if not isinstance(r, dict):
        raise HTTPException(status_code=502, detail="摘要失败")
    return ResponseModel(code=200, message="ok", data=r)


# ---- 5 翻译 ----
class TransReq(BaseModel):
    text: str = Field(..., min_length=1)
    target: str = Field("en", description="en|zh")


@router.post("/translate", response_model=ResponseModel, summary="中英互译(技术语境)")
def translate(body: TransReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    tgt = "英文" if body.target == "en" else "中文"
    r = _ai(f"你是非标自动化行业翻译。把下面内容准确翻译成{tgt}(保留专业术语)，只输出译文：\n{body.text[:4000]}", mt=1500, temp=0.2)
    return ResponseModel(code=200, message="ok", data={"translation": r})


# ---- 6 邮件/沟通代写 ----
class DraftReq(BaseModel):
    purpose: str = Field(..., min_length=2, description="目的,如'催款''跟进报价''道歉延期'")
    context: Optional[str] = ""
    tone: Optional[str] = "专业礼貌"


@router.post("/draft", response_model=ResponseModel, summary="邮件/沟通代写")
def draft(body: DraftReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    r = _ai(f"你是销售/客服。写一封{body.tone}的中文邮件/微信。目的：{body.purpose}。背景：{body.context or '无'}。"
            "直接输出可发送的正文(含称呼与落款占位)。", mt=1200)
    return ResponseModel(code=200, message="ok", data={"draft": r})


# ---- 7 自然语言筛选 ----
class FilterReq(BaseModel):
    entity: str = Field(..., description="opportunities|contracts|projects")
    query: str = Field(..., min_length=1)


@router.post("/nl-filter", response_model=ResponseModel, summary="自然语言→筛选条件")
def nl_filter(body: FilterReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    fields = {
        "opportunities": "stage(DISCOVERY/QUALIFICATION/PROPOSAL/NEGOTIATION/WON/LOST),equipment_type,est_amount,requirement_maturity,assessment_status",
        "contracts": "status,total_amount,received_amount,unreceived_amount,signing_date",
        "projects": "status(EXECUTING/COMPLETED),progress_pct,planned_end_date,health",
    }.get(body.entity, "")
    r = _aij("把自然语言查询转成结构化筛选条件，严格只输出 JSON：\n"
             '{"filters":[{"field":"字段","op":">=|<=|=|!=|contains","value":"值"}],"sort":"排序字段或空","desc":true}\n'
             f"实体『{body.entity}』可用字段：{fields}\n查询：{body.query}\n只返回合法 JSON。")
    if not isinstance(r, dict):
        raise HTTPException(status_code=502, detail="解析失败")
    return ResponseModel(code=200, message="ok", data=r)


# ---- 8 我的一天（个人待办AI聚合） ----
@router.get("/my-day", response_model=ResponseModel, summary="我的一天(待办聚合)")
def my_day(db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    uid = current_user.id
    stale = db.execute(text("SELECT COUNT(*) FROM opportunities WHERE owner_id=:u AND stage NOT IN ('WON','LOST','CLOSED') AND (last_progress_at IS NULL OR last_progress_at < date('now','-14 days'))"), {"u": uid}).scalar() or 0
    my_opps = db.execute(text("SELECT COUNT(*) FROM opportunities WHERE owner_id=:u AND stage NOT IN ('WON','LOST','CLOSED')"), {"u": uid}).scalar() or 0
    unassessed = db.execute(text("SELECT COUNT(*) FROM opportunities WHERE owner_id=:u AND stage NOT IN ('WON','LOST','CLOSED') AND (assessment_status IS NULL OR assessment_status='REQUESTED')"), {"u": uid}).scalar() or 0
    facts = f"我负责在跟商机{my_opps}个，其中{stale}个14天没进展、{unassessed}个缺售前评估。"
    tip = _ai(f"你是我的AI助理。根据：{facts} 用2-3条给出我今天最该先做的事(每条一句话)。直接输出。", mt=400)
    return ResponseModel(code=200, message="ok", data={"my_opportunities": my_opps, "stale": stale, "unassessed": unassessed, "today_focus": tip})


# ---- 9 智能表单填充 ----
class AutofillReq(BaseModel):
    form_type: str = Field(..., description="如 customer|opportunity|quote")
    hint: str = Field(..., min_length=2, description="一句话线索,如'给宁德时代做电池模组视觉检测'")


@router.post("/autofill", response_model=ResponseModel, summary="智能表单填充")
def autofill(body: AutofillReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    schema = {
        "customer": (
            '{"customer_name":"","short_name":"","industry":"","contact_name":"",'
            '"phone":"","address":"","remark":""}'
        ),
        "opportunity": (
            '{"opp_name":"","project_type":"","equipment_type":"","est_amount":0,'
            '"budget_range":"","delivery_window":"","decision_chain":"","acceptance_basis":"",'
            '"requirement":{"product_object":"","ct_seconds":"","interface_desc":"",'
            '"site_constraints":"","acceptance_criteria":""}}'
        ),
        "quote": '{"item_name":"","equipment_type":"","est_cost":0,"note":""}',
    }.get(body.form_type, '{"note":""}')
    r = _aij(
        f"根据线索为『{body.form_type}』表单预填字段，严格只输出 JSON：\n{schema}\n\n"
        f"线索：{body.hint}\n"
        "线索中没提到的字段留空字符串或0，不要编造联系方式等信息。只返回合法 JSON。",
        1200,
    )
    if not isinstance(r, dict):
        raise HTTPException(status_code=502, detail="填充失败")
    return ResponseModel(code=200, message="ok", data={"fields": r})


# ---- 10 文本润色/规范化 ----
@router.post("/polish", response_model=ResponseModel, summary="文本润色/规范化")
def polish(body: TextReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    r = _ai(f"把下面文字改写得更专业、通顺、规范(不改变原意,适合写入CRM/工作汇报)，只输出改写后的文字：\n{body.text[:4000]}", mt=1200, temp=0.3)
    return ResponseModel(code=200, message="ok", data={"polished": r})


# ---- 11 操作助手（怎么做） ----
class HowToReq(BaseModel):
    question: str = Field(..., min_length=2)


@router.post("/how-to", response_model=ResponseModel, summary="操作助手")
def how_to(body: HowToReq, current_user: User = Depends(security.get_current_active_user)) -> Any:
    r = _aij("你是本系统(非标自动化PM系统:客户/商机/报价/合同/项目/BOM/采购/售后)的操作向导。回答用户怎么操作，严格只输出 JSON：\n"
             '{"steps":["操作步骤"],"tip":"小提示"}\n\n' + f"问题：{body.question}\n只返回合法 JSON。")
    if not isinstance(r, dict):
        raise HTTPException(status_code=502, detail="解答失败")
    return ResponseModel(code=200, message="ok", data=r)
