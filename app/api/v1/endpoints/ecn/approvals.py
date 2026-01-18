# -*- coding: utf-8 -*-
"""
ECN审批管理 API endpoints

包含：审批列表、创建审批、审批通过/驳回、审批矩阵
"""

import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnApproval, EcnApprovalMatrix, EcnLog
from app.models.user import User
from app.schemas.ecn import EcnApprovalCreate, EcnApprovalResponse
from app.services.ecn_notification import (
    notify_approval_assigned,
    notify_approval_result,
)

from .utils import get_user_display_name

router = APIRouter()


@router.get("/ecns/{ecn_id}/approvals", response_model=List[EcnApprovalResponse], status_code=status.HTTP_200_OK)
def read_ecn_approvals(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批记录列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    approvals = db.query(EcnApproval).filter(EcnApproval.ecn_id == ecn_id).order_by(EcnApproval.approval_level, EcnApproval.created_at).all()

    items = []
    for approval in approvals:
        approver_name = get_user_display_name(db, approval.approver_id)

        items.append(EcnApprovalResponse(
            id=approval.id,
            ecn_id=approval.ecn_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            status=approval.status,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))

    return items


@router.post("/ecns/{ecn_id}/approvals", response_model=EcnApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_approval(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    approval_in: EcnApprovalCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建审批记录（系统自动创建或手动创建）
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    if ecn.status not in ["SUBMITTED", "IN_APPROVAL"]:
        raise HTTPException(status_code=400, detail="ECN当前不在审批阶段")

    approval = EcnApproval(
        ecn_id=ecn_id,
        approval_level=approval_in.approval_level,
        approval_role=approval_in.approval_role,
        approver_id=approval_in.approver_id,
        status="PENDING"
    )

    db.add(approval)
    db.commit()
    db.refresh(approval)

    # 发送通知（审批任务分配）
    try:
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if ecn and approval.approver_id:
            notify_approval_assigned(db, ecn, approval, approval.approver_id)
    except Exception as e:
        logger.error(f"Failed to send approval assigned notification: {e}")

    return _build_approval_response(db, approval)


@router.get("/ecn-approvals/{approval_id}", response_model=EcnApprovalResponse, status_code=status.HTTP_200_OK)
def read_ecn_approval(
    approval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批记录详情
    """
    approval = db.query(EcnApproval).filter(EcnApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    return _build_approval_response(db, approval)


@router.put("/ecn-approvals/{approval_id}/approve", response_model=EcnApprovalResponse, status_code=status.HTTP_200_OK)
def approve_ecn(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_comment: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过
    """
    approval = db.query(EcnApproval).filter(EcnApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    if approval.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能审批分配给自己的审批")

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_comment
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"

    # 检查是否所有审批都已完成
    ecn = db.query(Ecn).filter(Ecn.id == approval.ecn_id).first()
    if ecn:
        pending_approvals = db.query(EcnApproval).filter(
            EcnApproval.ecn_id == ecn.id,
            EcnApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新ECN状态
            ecn.status = "APPROVED"
            ecn.approval_result = "APPROVED"
            ecn.approved_at = datetime.now()
            ecn.current_step = "EXECUTION"

            # ECN联动：如果工期影响 > 阈值，自动调整相关任务计划
            try:
                from app.services.progress_integration_service import (
                    ProgressIntegrationService,
                )
                integration_service = ProgressIntegrationService(db)
                result = integration_service.handle_ecn_approved(ecn, threshold_days=3)
                if result['adjusted_tasks'] or result['created_tasks']:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"ECN审批通过，已调整 {len(result['adjusted_tasks'])} 个任务，创建 {len(result['created_tasks'])} 个任务")
            except Exception as e:
                # 联动失败不影响ECN审批，记录日志
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"ECN联动处理失败: {str(e)}", exc_info=True)

            # Sprint 2.3: ECN变更影响交期联动
            if ecn.project_id and ecn.schedule_impact_days and ecn.schedule_impact_days > 0:
                try:
                    from app.services.status_transition_service import (
                        StatusTransitionService,
                    )
                    transition_service = StatusTransitionService(db)
                    transition_service.handle_ecn_schedule_impact(
                        ecn.project_id,
                        ecn.id,
                        ecn.schedule_impact_days
                    )
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"ECN变更影响交期，已更新项目协商交期和风险信息")
                except Exception as e:
                    # 联动失败不影响ECN审批，记录日志
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"ECN交期联动处理失败: {str(e)}", exc_info=True)

            # 记录日志
            log = EcnLog(
                ecn_id=ecn.id,
                log_type="APPROVAL",
                log_action="APPROVED",
                old_status="PENDING_APPROVAL",
                new_status="APPROVED",
                log_content="ECN审批通过",
                created_by=current_user.id
            )
            db.add(log)
            db.add(ecn)

            # ECN审批通过时自动归集变更成本
            if ecn.cost_impact and ecn.cost_impact > 0 and ecn.project_id:
                try:
                    from app.services.cost_collection_service import (
                        CostCollectionService,
                    )
                    CostCollectionService.collect_from_ecn(
                        db, ecn.id, created_by=current_user.id
                    )
                except Exception as e:
                    # 成本归集失败不影响审批流程，只记录错误
                    logger.error(f"Failed to collect cost from ECN {ecn.id}: {e}")

    db.add(approval)
    db.commit()
    db.refresh(approval)

    # 发送通知（审批结果）
    try:
        notify_approval_result(db, ecn, approval, "APPROVED")
    except Exception as e:
        logger.error(f"Failed to send approval result notification: {e}")

    return _build_approval_response(db, approval)


@router.put("/ecn-approvals/{approval_id}/reject", response_model=EcnApprovalResponse, status_code=status.HTTP_200_OK)
def reject_ecn(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    approval = db.query(EcnApproval).filter(EcnApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    if approval.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能审批分配给自己的审批")

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"

    # 更新ECN状态为驳回
    ecn = db.query(Ecn).filter(Ecn.id == approval.ecn_id).first()
    if ecn:
        ecn.status = "REJECTED"
        ecn.approval_result = "REJECTED"
        ecn.approval_note = rejection_reason

        # 记录日志
        log = EcnLog(
            ecn_id=ecn.id,
            log_type="APPROVAL",
            log_action="REJECTED",
            old_status="PENDING_APPROVAL",
            new_status="REJECTED",
            log_content=f"ECN审批驳回: {rejection_reason}",
            created_by=current_user.id
        )
        db.add(log)
        db.add(ecn)

    db.add(approval)
    db.commit()
    db.refresh(approval)

    # 发送通知（审批结果）
    try:
        notify_approval_result(db, ecn, approval, "REJECTED")
    except Exception as e:
        logger.error(f"Failed to send approval result notification: {e}")

    return _build_approval_response(db, approval)


@router.get("/ecn-approval-matrix", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_approval_matrix(
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批规则配置
    """
    query = db.query(EcnApprovalMatrix).filter(EcnApprovalMatrix.is_active == True)

    if ecn_type:
        query = query.filter(EcnApprovalMatrix.ecn_type == ecn_type)

    matrices = query.order_by(EcnApprovalMatrix.approval_level).all()

    return [
        {
            "id": m.id,
            "ecn_type": m.ecn_type,
            "condition_type": m.condition_type,
            "condition_min": float(m.condition_min) if m.condition_min else None,
            "condition_max": float(m.condition_max) if m.condition_max else None,
            "approval_level": m.approval_level,
            "approval_role": m.approval_role
        }
        for m in matrices
    ]


def _build_approval_response(db: Session, approval: EcnApproval) -> EcnApprovalResponse:
    """构建审批响应"""
    approver_name = get_user_display_name(db, approval.approver_id)

    return EcnApprovalResponse(
        id=approval.id,
        ecn_id=approval.ecn_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        status=approval.status,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )
