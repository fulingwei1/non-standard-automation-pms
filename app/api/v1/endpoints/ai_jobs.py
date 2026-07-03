# -*- coding: utf-8 -*-
"""AI 后台任务端点：提交重的 AI 生成 + 轮询状态/结果。"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
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
