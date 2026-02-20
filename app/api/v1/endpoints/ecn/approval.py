# -*- coding: utf-8 -*-
"""
ECN审批工作流 API

使用统一审批引擎实现ECN审批流程。
ECN(工程变更通知)在完成评估后需要提交审批以确认变更。
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.ecn_approval import EcnApprovalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ecns/approval", tags=["ECN审批工作流"])


# ==================== 请求模型 ====================


class EcnSubmitApprovalRequest(BaseModel):
    """ECN提交审批请求"""

    ecn_ids: list[int] = Field(..., description="ECN ID列表")
    urgency: str = Field("NORMAL", description="紧急程度: LOW/NORMAL/HIGH/URGENT")
    comment: Optional[str] = Field(None, description="提交备注")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    task_id: int = Field(..., description="审批任务ID")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class BatchApprovalRequest(BaseModel):
    """批量审批请求"""

    task_ids: list[int] = Field(..., description="审批任务ID列表")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class WithdrawApprovalRequest(BaseModel):
    """撤回审批请求"""

    ecn_id: int = Field(..., description="ECN ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: EcnSubmitApprovalRequest,
    current_user: User = Depends(security.require_permission("ecn:create")),
) -> Any:
    """
    提交ECN审批

    将已完成评估的ECN提交到审批流程。
    适用于：
    - ECN评估完成后提交审批
    - 被驳回的ECN修改后重新提交
    """
    service = EcnApprovalService(db)
    results, errors = service.submit_ecns_for_approval(
        ecn_ids=request.ecn_ids,
        initiator_id=current_user.id,
        urgency=request.urgency,
        comment=request.comment,
    )

    db.commit()

    return ResponseModel(
        code=200,
        message=f"提交完成: 成功 {len(results)} 个, 失败 {len(errors)} 个",
        data={"success": results, "errors": errors},
    )


@router.get("/pending", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_pending_approval_tasks(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    获取待审批的ECN列表

    返回当前用户待审批的ECN任务。
    """
    service = EcnApprovalService(db)
    items, total = service.get_pending_tasks_for_user(
        user_id=current_user.id,
        ecn_type=ecn_type,
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(total),
        },
    )


@router.post("/action", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ApprovalActionRequest,
    current_user: User = Depends(security.require_permission("ecn:approve")),
) -> Any:
    """
    执行审批操作

    对单个ECN进行审批通过或驳回。
    """
    service = EcnApprovalService(db)

    try:
        result = service.perform_approval_action(
            task_id=request.task_id,
            approver_id=current_user.id,
            action=request.action,
            comment=request.comment,
        )

        db.commit()

        return ResponseModel(code=200, message="审批操作成功", data=result)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/batch-action", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def perform_batch_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchApprovalRequest,
    current_user: User = Depends(security.require_permission("ecn:approve")),
) -> Any:
    """
    批量审批操作

    对多个ECN进行批量审批通过或驳回。
    """
    service = EcnApprovalService(db)
    results, errors = service.perform_batch_approval(
        task_ids=request.task_ids,
        approver_id=current_user.id,
        action=request.action,
        comment=request.comment,
    )

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量审批完成: 成功 {len(results)} 个, 失败 {len(errors)} 个",
        data={"success": results, "errors": errors},
    )


@router.get(
    "/status/{ecn_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    查询ECN审批状态

    获取指定ECN的审批流程状态和历史。
    """
    service = EcnApprovalService(db)
    data = service.get_ecn_approval_status(ecn_id)

    return ResponseModel(code=200, message="获取审批状态成功", data=data)


@router.post("/withdraw", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def withdraw_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: WithdrawApprovalRequest,
    current_user: User = Depends(security.require_permission("ecn:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的ECN。
    """
    service = EcnApprovalService(db)

    try:
        result = service.withdraw_ecn_approval(
            ecn_id=request.ecn_id, user_id=current_user.id, reason=request.reason
        )

        db.commit()

        return ResponseModel(code=200, message="审批撤回成功", data=result)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status_filter: Optional[str] = Query(
        None, description="状态筛选: APPROVED/REJECTED"
    ),
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的ECN审批历史。
    """
    service = EcnApprovalService(db)
    items, total = service.get_approval_history_for_user(
        user_id=current_user.id,
        status_filter=status_filter,
        ecn_type=ecn_type,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(total),
        },
    )
