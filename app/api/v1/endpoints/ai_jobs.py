# -*- coding: utf-8 -*-
"""AI 后台任务端点：提交重的 AI 生成 + 轮询状态/结果。"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.presale_ai_quotation import ThreeTierQuotationRequest
from app.services import ai_job_service

router = APIRouter(prefix="/ai-jobs", tags=["AI后台任务"])


def _job_view(job) -> dict:
    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


@router.post("/three-tier-quotations", summary="提交三档报价(后台任务)")
def submit_three_tier_quotations(
    request: ThreeTierQuotationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """提交后台生成，立即返回 job_id；用 GET /ai-jobs/{job_id} 轮询。"""
    job = ai_job_service.submit(
        db, "three_tier_quotation", request.model_dump(mode="json"), current_user.id
    )
    return {"job_id": job.id, "status": job.status, "poll_url": f"/api/v1/ai-jobs/{job.id}"}


class PresaleAgentRequest(BaseModel):
    """售前智能体请求"""

    requirement_text: str = Field(..., min_length=2, description="客户原始需求")
    customer_id: Optional[int] = Field(None, description="关联客户ID（可选）")
    industry_hint: Optional[str] = Field(None, description="行业提示（可选）")
    equipment_hint: Optional[str] = Field(None, description="设备类型提示（可选）")


@router.post("/presale-agent", summary="提交售前智能体分析(后台任务)")
def submit_presale_agent(
    request: PresaleAgentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """售前智能体：需求理解→弹药检索→方案→BOM→报价区间→风险提示。

    提交后立即返回 job_id，前端轮询 GET /ai-jobs/{job_id}。
    完成后 result 含 steps（6 步产物）+ summary + timings。
    """
    job = ai_job_service.submit(
        db, "presale_agent", request.model_dump(mode="json"), current_user.id
    )
    return {"job_id": job.id, "status": job.status, "poll_url": f"/api/v1/ai-jobs/{job.id}"}


class ClarifyRequest(BaseModel):
    """需求澄清请求"""

    requirement_text: str = Field(..., min_length=1, description="销售本轮输入的需求/回答")
    history: list = Field(default_factory=list, description="历史对话 [{role, content}]")


@router.post("/presale-clarify", summary="需求澄清（多轮对话，评估完整性并追问）")
def presale_clarify(
    request: ClarifyRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """评估客户需求完整性。缺关键信息时返回追问，够完整时 is_complete=true 可生成方案。

    多轮会话：前端传 history 累积上下文，agent 基于已有信息决定还要问什么。
    """
    from app.services.presale.requirement_clarifier import clarify_requirement

    result = clarify_requirement(request.requirement_text, request.history)
    return result


class SalesCoachRequest(BaseModel):
    """销售教练请求"""

    sales_input: str = Field(..., min_length=2, description="销售输入（客户线索/问题/会议记录）")
    mode: str = Field("lead_analysis", description="模式：lead_analysis/meeting_prep/field_qa/review_coaching")
    history: list = Field(default_factory=list, description="对话历史")


@router.post("/sales-coach", summary="销售教练（AI 指导销售获取需求和成长）")
def sales_coach(
    request: SalesCoachRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售教练：像老法师一样指导新手销售。

    四种模式：
    - lead_analysis: 线索解读（刚接到客户，怎么开始）
    - meeting_prep: 会前准备（去见客户前准备什么）
    - field_qa: 现场答疑（客户问技术问题快速回答）
    - review_coaching: 复盘辅导（沟通完总结提升）
    """
    from app.services.presale.sales_coach import coach_sales
    from app.services.ai_client_service import AIClientService

    ai = AIClientService()
    result = coach_sales(db, ai, request.sales_input, request.mode, request.history)
    return result


@router.get("/{job_id}", summary="查询AI后台任务状态/结果")
def get_ai_job(
    job_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    job = ai_job_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _job_view(job)
