# -*- coding: utf-8 -*-
"""售前方案协作 API。

完整流程：
  POST /presale-proposals              从智能体结果创建方案（draft）
  POST /presale-proposals/{id}/revise  迭代修改（提建议→agent改方案）
  POST /presale-proposals/{id}/submit  提交审核（draft→pending_review）
  POST /presale-proposals/{id}/review  审核操作（通过/打回）
  GET  /presale-proposals              方案列表（可按状态过滤）
  GET  /presale-proposals/pending      待审队列（售前工程师用）
  GET  /presale-proposals/{id}         方案详情（含迭代历史）
"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.modules.presale.models.presale_proposal import PresaleProposal, PresaleProposalVersion
from app.models.user import User

router = APIRouter(prefix="/presale-proposals", tags=["售前方案协作"])


# ============= 请求模型 =============

class CreateProposalRequest(BaseModel):
    title: str = Field(..., description="方案标题")
    requirement_text: str = Field(..., description="原始需求")
    solution: Dict[str, Any] = Field(..., description="智能体产出的方案JSON")
    metric_id: Optional[int] = None


class ReviseRequest(BaseModel):
    """迭代修改：销售提建议，agent 改方案"""
    change_request: str = Field(..., description="修改建议，如'报价调低10%''加个老化工位''PLC换成西门子'")


class ReviewRequest(BaseModel):
    """审核操作"""
    action: str = Field(..., description="approve(通过) / reject(打回)")
    comment: Optional[str] = Field(None, description="审核意见")


# ============= 端点 =============

@router.post("", summary="从智能体结果创建方案")
def create_proposal(
    request: CreateProposalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """把智能体产出存为可协作的方案（draft 状态）。"""
    proposal = PresaleProposal(
        title=request.title,
        requirement_text=request.requirement_text,
        current_solution=request.solution,
        status="draft",
        metric_id=request.metric_id,
        created_by=current_user.id,
        created_by_name=getattr(current_user, "full_name", None) or current_user.username,
        version_count=1,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    # 存初版
    v1 = PresaleProposalVersion(
        proposal_id=proposal.id, version_no=1,
        change_request="(AI 初稿)", changes_summary="智能体自动生成",
        solution=request.solution,
        operated_by=current_user.id, operated_by_name=proposal.created_by_name,
        operation="create",
    )
    db.add(v1)
    db.commit()
    return {"id": proposal.id, "status": "draft", "message": "方案已创建，可开始迭代修改"}


@router.post("/{proposal_id}/revise", summary="迭代修改方案（销售提建议→agent改）")
def revise_proposal(
    proposal_id: int,
    request: ReviseRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售提修改建议，agent 理解后修改方案的对应部分。

    agent 会：
    1. 理解建议（调价/加设备/换品牌/改工艺等）
    2. 找到方案里对应的部分修改
    3. 返回修改后的方案 + 改了什么的摘要
    """
    proposal = db.query(PresaleProposal).filter(PresaleProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, "方案不存在")
    if proposal.status not in ("draft", "rejected"):
        raise HTTPException(400, f"当前状态 {proposal.status} 不可修改（仅 draft/rejected 可改）")

    # 调 agent 修改方案
    from app.services.presale.presale_agent_orchestrator import _revise_solution_with_ai
    from app.services.ai_client_service import AIClientService

    ai = AIClientService()
    current_solution = proposal.current_solution or {}
    revised, changes_summary = _revise_solution_with_ai(
        ai, current_solution, request.change_request, proposal.requirement_text
    )

    # 更新方案
    new_version = proposal.version_count + 1
    proposal.current_solution = revised
    proposal.version_count = new_version
    proposal.status = "draft"  # 修改后回到 draft
    db.commit()

    # 存版本记录
    v = PresaleProposalVersion(
        proposal_id=proposal.id, version_no=new_version,
        change_request=request.change_request,
        changes_summary=changes_summary,
        solution=revised,
        operated_by=current_user.id,
        operated_by_name=getattr(current_user, "full_name", None) or current_user.username,
        operation="revise",
    )
    db.add(v)
    db.commit()

    return {
        "proposal_id": proposal.id,
        "version_no": new_version,
        "changes_summary": changes_summary,
        "solution": revised,
        "status": "draft",
        "message": f"已根据建议修改方案（第{new_version}版）",
    }


@router.post("/{proposal_id}/submit", summary="提交审核（draft→pending_review）")
def submit_proposal(
    proposal_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售确认方案，提交给售前工程师审核。"""
    proposal = db.query(PresaleProposal).filter(PresaleProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, "方案不存在")
    if proposal.status not in ("draft", "rejected"):
        raise HTTPException(400, f"当前状态 {proposal.status} 不可提交")

    proposal.status = "pending_review"
    db.commit()

    # 存提交记录
    v = PresaleProposalVersion(
        proposal_id=proposal.id, version_no=proposal.version_count,
        change_request="(提交审核)", changes_summary="销售提交审核",
        solution=proposal.current_solution,
        operated_by=current_user.id,
        operated_by_name=getattr(current_user, "full_name", None) or current_user.username,
        operation="submit",
    )
    db.add(v)
    db.commit()

    # 发飞书通知给售前工程师（不阻塞主流程）
    try:
        from app.services.presale.proposal_notifier import notify_review_submitted
        notify_review_submitted(
            proposal_id=proposal.id,
            title=proposal.title,
            submitted_by=getattr(current_user, "full_name", None) or current_user.username,
            version_count=proposal.version_count,
            requirement_text=proposal.requirement_text or "",
        )
    except Exception as notify_err:
        import logging
        logging.getLogger("presale.proposals").warning("审核通知发送失败（不影响提交）: %s", notify_err)

    return {"status": "pending_review", "message": "已提交审核，售前工程师将收到飞书通知"}


@router.post("/{proposal_id}/review", summary="审核操作（通过/打回）")
def review_proposal(
    proposal_id: int,
    request: ReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """售前工程师审核方案：approve（通过定稿）/ reject（打回继续改）。"""
    proposal = db.query(PresaleProposal).filter(PresaleProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, "方案不存在")
    if proposal.status != "pending_review":
        raise HTTPException(400, f"当前状态 {proposal.status} 不可审核（仅 pending_review 可审核）")

    from datetime import datetime
    if request.action == "approve":
        proposal.status = "approved"
    elif request.action == "reject":
        proposal.status = "rejected"
    else:
        raise HTTPException(400, "action 必须是 approve 或 reject")

    proposal.reviewed_by = current_user.id
    proposal.reviewed_by_name = getattr(current_user, "full_name", None) or current_user.username
    proposal.reviewed_at = datetime.now()
    proposal.review_comment = request.comment
    db.commit()

    v = PresaleProposalVersion(
        proposal_id=proposal.id, version_no=proposal.version_count,
        change_request=f"(审核: {request.action})", changes_summary=request.comment or "",
        solution=proposal.current_solution,
        operated_by=current_user.id,
        operated_by_name=proposal.reviewed_by_name,
        operation=request.action,
    )
    db.add(v)
    db.commit()

    action_label = "通过（定稿）" if request.action == "approve" else "打回（继续修改）"
    return {"status": proposal.status, "message": f"已{action_label}"}


@router.get("", summary="方案列表（可按状态过滤）")
def list_proposals(
    status: Optional[str] = Query(None, description="按状态过滤：draft/pending_review/approved/rejected"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    from sqlalchemy import desc
    q = db.query(PresaleProposal)
    if status:
        q = q.filter(PresaleProposal.status == status)
    total = q.count()
    rows = q.order_by(desc(PresaleProposal.id)).limit(limit).all()
    return {"total": total, "items": [r.to_dict() for r in rows]}


@router.get("/pending", summary="待审队列（售前工程师用）")
def pending_queue(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """售前工程师的待审方案队列。"""
    from sqlalchemy import desc
    rows = (
        db.query(PresaleProposal)
        .filter(PresaleProposal.status == "pending_review")
        .order_by(desc(PresaleProposal.id))
        .all()
    )
    return {"total": len(rows), "items": [r.to_dict() for r in rows]}


@router.get("/{proposal_id}", summary="方案详情（含迭代历史）")
def get_proposal(
    proposal_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查方案完整内容 + 所有迭代版本。"""
    from sqlalchemy import asc
    proposal = db.query(PresaleProposal).filter(PresaleProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, "方案不存在")
    versions = (
        db.query(PresaleProposalVersion)
        .filter(PresaleProposalVersion.proposal_id == proposal_id)
        .order_by(asc(PresaleProposalVersion.version_no))
        .all()
    )
    return {
        **proposal.to_dict(),
        "current_solution": proposal.current_solution,
        "versions": [
            {
                "version_no": v.version_no,
                "change_request": v.change_request,
                "changes_summary": v.changes_summary,
                "operation": v.operation,
                "operated_by_name": v.operated_by_name,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ],
    }
