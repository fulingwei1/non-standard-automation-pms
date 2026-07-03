# -*- coding: utf-8 -*-
"""差异化：#7 多模态图纸/现场照片理解(qwen视觉) · #8 对内数字员工RAG知识问答。"""
import base64
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services import ai_job_service

router = APIRouter(prefix="/ai-advanced", tags=["AI差异化(视觉/RAG)"])


@router.post("/analyze-drawing", response_model=ResponseModel, summary="#7 图纸/现场照片AI理解")
async def analyze_drawing(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """上传客户图纸/规格书/产线照片 → qwen 视觉抽取参数、识别工件、判可行性（吃掉看图报价/评审痛点）。"""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片过大(>8MB)，请压缩后上传")
    mime = file.content_type or "image/jpeg"
    if not mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片(png/jpg)")
    b64 = base64.b64encode(raw).decode()
    prompt = (
        "你是非标自动化售前工程师。看这张客户图纸/规格书/现场照片，尽量抽取信息，严格只输出 JSON：\n"
        '{"image_type":"图纸|规格书|现场照片|产品照片","identified":"识别到的工件/设备/产线",'
        '"parameters":[{"name":"参数名","value":"数值/描述"}],"requirements":["可推断的技术要求"],'
        '"feasibility":"自动化可行性初判","questions":["需向客户确认的点"]}\n\n只返回合法 JSON。'
    )
    from app.services.ai_client_service import AIClientService

    resp = AIClientService().analyze_image(prompt, b64, mime=mime)
    if resp.get("error"):
        raise HTTPException(status_code=502, detail=f"视觉分析失败：{resp['error']}")
    parsed = ai_job_service._extract_json(resp.get("content") or "")
    if not isinstance(parsed, dict):
        return ResponseModel(code=200, message="AI 已分析(非结构化)", data={"raw": resp.get("content", "")[:1500]})
    return ResponseModel(code=200, message="AI 图纸理解完成", data=parsed)


class AskReq(BaseModel):
    question: str = Field(..., min_length=2, description="要问的问题")


@router.post("/ask", response_model=ResponseModel, summary="#8 数字员工-内部知识问答(RAG)")
def ask(req: AskReq, db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.get_current_active_user)) -> Any:
    """对内'数字员工'：按问题从内部数据(商机/项目/客户/模块)检索上下文 → AI 基于事实作答。"""
    from app.services.ai_client_service import AIClientService

    q = req.question
    ctx_parts = []
    # 反向匹配：问题中提到的实体即命中（:q LIKE %name%）；同时对设备类型/行业做正向关键词匹配
    P = {"q": q}
    # 标准模块（问题含模块名，或设备/成本类问题时全列出Top）
    for r in db.execute(text("SELECT module_name, description, ref_cost FROM ai_standard_modules "
                             "WHERE :q LIKE '%'||module_name||'%' OR :q LIKE '%模块%' OR :q LIKE '%成本%' "
                             "ORDER BY source_count DESC LIMIT 8"), P).all():
        ctx_parts.append(f"[模块] {r[0]} {r[1] or ''} 参考成本¥{r[2] or 0}")
    # 商机（问题含商机名/设备类型）
    for r in db.execute(text("SELECT opp_name, stage, equipment_type FROM opportunities "
                             "WHERE :q LIKE '%'||equipment_type||'%' OR (equipment_type!='' AND equipment_type IS NOT NULL AND :q LIKE '%'||opp_name||'%') "
                             "LIMIT 6"), P).all():
        ctx_parts.append(f"[商机] {r[0]} 阶段{r[1]} 设备{r[2] or ''}")
    # 客户（问题含客户名/行业）
    for r in db.execute(text("SELECT customer_name, industry FROM customers "
                             "WHERE :q LIKE '%'||customer_name||'%' OR (industry IS NOT NULL AND industry!='' AND :q LIKE '%'||industry||'%') LIMIT 6"), P).all():
        ctx_parts.append(f"[客户] {r[0]} 行业{r[1] or ''}")
    # 项目（问题含项目名）
    for r in db.execute(text("SELECT project_name, status FROM projects WHERE :q LIKE '%'||project_name||'%' LIMIT 5"), P).all():
        ctx_parts.append(f"[项目] {r[0]} 状态{r[1]}")
    context = "\n".join(dict.fromkeys(ctx_parts)) or "（未检索到直接相关的内部记录）"

    prompt = (
        "你是公司内部的'数字员工'知识助手(非标自动化)。**优先根据下面检索到的内部资料作答**，"
        "资料不足时可用行业常识补充但要说明。回答简洁、可执行。\n\n"
        f"【检索到的内部资料】\n{context}\n\n【问题】{q}\n\n直接用中文作答。"
    )
    resp = AIClientService().generate_solution(prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=1500)
    answer = (resp.get("content") or "").strip()
    if not answer:
        raise HTTPException(status_code=502, detail="AI 未能作答，请换个问法")
    return ResponseModel(code=200, message="ok", data={"answer": answer, "sources": ctx_parts, "matched": len(ctx_parts)})
