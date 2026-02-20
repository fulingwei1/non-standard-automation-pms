# -*- coding: utf-8 -*-
"""
验收单审批工作流 API

使用统一审批引擎实现验收单审批流程。
验收单在完成检查后需要提交审批以确认验收结果。
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.acceptance_approval import AcceptanceApprovalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/acceptance-orders/approval", tags=["验收审批工作流"])


# ==================== 请求模型 ====================


class AcceptanceSubmitApprovalRequest(BaseModel):
    """验收单提交审批请求"""

    order_ids: List[int] = Field(..., description="验收单ID列表")
    urgency: str = Field("NORMAL", description="紧急程度: LOW/NORMAL/HIGH/URGENT")
    comment: Optional[str] = Field(None, description="提交备注")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    task_id: int = Field(..., description="审批任务ID")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class BatchApprovalRequest(BaseModel):
    """批量审批请求"""

    task_ids: List[int] = Field(..., description="审批任务ID列表")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class WithdrawApprovalRequest(BaseModel):
    """撤回审批请求"""

    order_id: int = Field(..., description="验收单ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: AcceptanceSubmitApprovalRequest,
    current_user: User = Depends(security.require_permission("acceptance:create")),
) -> Any:
    """
    提交验收单审批

    将已完成的验收单提交到审批流程，获取管理层确认。
    适用于：
    - FAT验收通过后提交审批，确认可以发运
    - SAT验收通过后提交审批，确认可以进入质保期
    - 终验收通过后提交审批，确认项目正式完成
    """
    service = AcceptanceApprovalService(db)
    results, errors = service.submit_orders_for_approval(
        order_ids=request.order_ids,
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
    pagination=Depends(get_pagination_query),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    current_user: User = Depends(security.require_permission("acceptance:read")),
) -> Any:
    """
    获取待审批的验收单列表

    返回当前用户待审批的验收单任务。
    """
    service = AcceptanceApprovalService(db)
    items, total = service.get_pending_tasks(
        user_id=current_user.id,
        acceptance_type=acceptance_type,
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
    current_user: User = Depends(security.require_permission("acceptance:approve")),
) -> Any:
    """
    执行审批操作

    对单个验收单进行审批通过或驳回。
    """
    service = AcceptanceApprovalService(db)

    try:
        result = service.perform_approval_action(
            task_id=request.task_id,
            action=request.action,
            approver_id=current_user.id,
            comment=request.comment,
        )
        db.commit()

        return ResponseModel(code=200, message="审批操作成功", data=result)
    except ValueError as e:
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
    current_user: User = Depends(security.require_permission("acceptance:approve")),
) -> Any:
    """
    批量审批操作

    对多个验收单进行批量审批通过或驳回。
    """
    service = AcceptanceApprovalService(db)
    results, errors = service.batch_approval(
        task_ids=request.task_ids,
        action=request.action,
        approver_id=current_user.id,
        comment=request.comment,
    )
    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量审批完成: 成功 {len(results)} 个, 失败 {len(errors)} 个",
        data={"success": results, "errors": errors},
    )


@router.get(
    "/status/{order_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("acceptance:read")),
) -> Any:
    """
    查询验收单审批状态

    获取指定验收单的审批流程状态和历史。
    """
    service = AcceptanceApprovalService(db)

    try:
        data = service.get_approval_status(order_id)
        message = (
            "该验收单暂无审批记录" if data.get("approval_instance") is None else "获取审批状态成功"
        )
        return ResponseModel(code=200, message=message, data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/withdraw", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def withdraw_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: WithdrawApprovalRequest,
    current_user: User = Depends(security.require_permission("acceptance:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的验收单。
    """
    service = AcceptanceApprovalService(db)

    try:
        result = service.withdraw_approval(
            order_id=request.order_id, user_id=current_user.id, reason=request.reason
        )
        db.commit()

        return ResponseModel(code=200, message="审批撤回成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("acceptance:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的验收单审批历史。
    """
    service = AcceptanceApprovalService(db)
    items, total = service.get_approval_history(
        user_id=current_user.id,
        acceptance_type=acceptance_type,
        status_filter=status_filter,
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
