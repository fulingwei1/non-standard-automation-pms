# -*- coding: utf-8 -*-
"""
验厂资料 API。

流程：销售上传客户验厂清单 → 总监审批 → 通过后 AI 读清单自动准备资料。

POST /audit-packs              销售提交请求（含客户验厂清单）
POST /audit-packs/{id}/review  总监审批（通过后自动生成资料包）
GET  /audit-packs              列表（按状态过滤）
GET  /audit-packs/pending      待审批队列
GET  /audit-packs/{id}         详情（含生成的资料包HTML）
"""
import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.modules.presale.models.audit_pack import AuditPackRequest
from app.models.user import User

router = APIRouter(prefix="/audit-packs", tags=["验厂资料"])


class AuditPackSubmitRequest(BaseModel):
    """销售提交验厂资料请求"""
    customer_name: str = Field(..., description="客户名称")
    customer_industry: Optional[str] = Field(None, description="客户行业")
    project_name: Optional[str] = Field(None, description="关联项目")
    audit_purpose: Optional[str] = Field(None, description="验厂目的（供应商入库/正式验厂/资质审查）")
    checklist_text: str = Field(..., description="客户验厂清单内容（文本）")
    deadline: Optional[str] = Field(None, description="截止日期")


class AuditPackReviewRequest(BaseModel):
    """总监审批"""
    action: str = Field(..., description="approve/reject")
    comment: Optional[str] = None


@router.post("", summary="销售提交验厂资料请求")
def submit_audit_pack(
    request: AuditPackSubmitRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售上传客户验厂清单，提交给销售总监审批。审批通过后 AI 自动准备资料。"""
    pack = AuditPackRequest(
        customer_name=request.customer_name,
        customer_industry=request.customer_industry,
        project_name=request.project_name,
        audit_purpose=request.audit_purpose,
        checklist_text=request.checklist_text,
        deadline=request.deadline,
        status="pending",
        submitted_by=current_user.id,
        submitted_by_name=getattr(current_user, "full_name", None) or current_user.username,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return {"id": pack.id, "status": "pending", "message": f"已提交审批（客户：{request.customer_name}），销售总监审批通过后自动生成资料包"}


@router.post("/{pack_id}/review", summary="总监审批（通过后自动生成资料包）")
def review_audit_pack(
    pack_id: int,
    request: AuditPackReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售总监审批。通过后 AI 读验厂清单自动生成资料包。"""
    pack = db.query(AuditPackRequest).filter(AuditPackRequest.id == pack_id).first()
    if not pack:
        raise HTTPException(404, "请求不存在")
    if pack.status != "pending":
        raise HTTPException(400, f"当前状态 {pack.status} 不可审批")

    pack.reviewed_by = current_user.id
    pack.reviewed_by_name = getattr(current_user, "full_name", None) or current_user.username
    pack.reviewed_at = datetime.now()
    pack.review_comment = request.comment

    if request.action == "approve":
        pack.status = "approved"
        # AI 自动生成资料包
        from app.services.presale.audit_pack_generator import generate_audit_pack
        from app.services.ai_client_service import AIClientService
        ai = AIClientService()
        html = generate_audit_pack(db, ai, pack.checklist_text, pack.customer_name, pack.customer_industry)
        pack.generated_html = html
        pack.generated_at = datetime.now()
        msg = "已审批通过，AI 已自动生成验厂资料包"
    elif request.action == "reject":
        pack.status = "rejected"
        msg = f"已拒绝{'：' + request.comment if request.comment else ''}"
    else:
        raise HTTPException(400, "action 必须是 approve/reject")

    db.commit()
    return {"id": pack.id, "status": pack.status, "message": msg, "has_html": bool(pack.generated_html)}


@router.get("", summary="验厂资料请求列表")
def list_audit_packs(
    status: Optional[str] = Query(None),
    limit: int = Query(20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    q = db.query(AuditPackRequest)
    if status:
        q = q.filter(AuditPackRequest.status == status)
    total = q.count()
    rows = q.order_by(desc(AuditPackRequest.id)).limit(limit).all()
    return {"total": total, "items": [r.to_dict() for r in rows]}


@router.get("/pending", summary="待审批队列（销售总监用）")
def pending_audit_packs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    rows = db.query(AuditPackRequest).filter(
        AuditPackRequest.status == "pending"
    ).order_by(desc(AuditPackRequest.id)).all()
    return {"total": len(rows), "items": [r.to_dict() for r in rows]}


@router.get("/{pack_id}", summary="验厂资料详情（含AI生成的资料包）")
def get_audit_pack(
    pack_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    pack = db.query(AuditPackRequest).filter(AuditPackRequest.id == pack_id).first()
    if not pack:
        raise HTTPException(404, "请求不存在")
    return {
        **pack.to_dict(),
        "checklist_text": pack.checklist_text,
        "generated_html": pack.generated_html,
    }
