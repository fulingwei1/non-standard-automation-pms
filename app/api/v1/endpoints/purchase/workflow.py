# -*- coding: utf-8 -*-
"""
采购订单审批工作流 API

使用统一审批引擎实现采购订单审批流程。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.approval_workflow import (
    OrderSubmitRequest,
    ApprovalActionRequest,
    BatchApprovalRequest,
    WithdrawRequest,
)
from app.common.pagination import PaginationParams, get_pagination_query
from app.services.purchase_workflow import PurchaseWorkflowService

router = APIRouter(prefix="/workflow", tags=["采购审批工作流"])


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_orders_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: OrderSubmitRequest,
    current_user: User = Depends(security.require_permission("purchase:create")),
) -> Any:
    """
    提交采购订单审批

    将一个或多个采购订单提交到审批流程。
    """
    service = PurchaseWorkflowService(db)
    result = service.submit_orders_for_approval(
        order_ids=request.order_ids,
        initiator_id=current_user.id,
        urgency=request.urgency,
        comment=request.comment,
    )

    db.commit()

    success_count = len(result["success"])
    error_count = len(result["errors"])

    return ResponseModel(
        code=200,
        message=f"提交完成: 成功 {success_count} 个, 失败 {error_count} 个",
        data=result,
    )


@router.get("/pending", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_pending_approval_tasks(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """
    获取待审批的采购订单列表

    返回当前用户待审批的采购订单任务。
    """
    service = PurchaseWorkflowService(db)
    result = service.get_pending_tasks(
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={
            "items": result["items"],
            "total": result["total"],
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (result["total"] + pagination.page_size - 1) // pagination.page_size,
        },
    )


@router.post("/action", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ApprovalActionRequest,
    current_user: User = Depends(security.require_permission("purchase:approve")),
) -> Any:
    """
    执行审批操作

    对单个采购订单进行审批通过或驳回。
    """
    service = PurchaseWorkflowService(db)

    try:
        result = service.perform_approval_action(
            task_id=request.task_id,
            action=request.action,
            approver_id=current_user.id,
            comment=request.comment,
        )

        db.commit()

        return ResponseModel(
            code=200,
            message="审批操作成功",
            data=result,
        )
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
    current_user: User = Depends(security.require_permission("purchase:approve")),
) -> Any:
    """
    批量审批操作

    对多个采购订单进行批量审批通过或驳回。
    """
    service = PurchaseWorkflowService(db)
    result = service.perform_batch_approval(
        task_ids=request.task_ids,
        action=request.action,
        approver_id=current_user.id,
        comment=request.comment,
    )

    db.commit()

    success_count = len(result["success"])
    error_count = len(result["errors"])

    return ResponseModel(
        code=200,
        message=f"批量审批完成: 成功 {success_count} 个, 失败 {error_count} 个",
        data=result,
    )


@router.get(
    "/status/{order_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """
    查询采购订单审批状态

    获取指定采购订单的审批流程状态和历史。
    """
    service = PurchaseWorkflowService(db)
    result = service.get_approval_status(order_id=order_id)

    message = "该订单暂无审批记录" if result.get("approval_instance") is None else "获取审批状态成功"

    return ResponseModel(
        code=200,
        message=message,
        data=result,
    )


@router.post("/withdraw", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def withdraw_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: WithdrawRequest,
    current_user: User = Depends(security.require_permission("purchase:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的采购订单。
    """
    service = PurchaseWorkflowService(db)

    try:
        result = service.withdraw_approval(
            order_id=request.order_id,
            user_id=current_user.id,
            reason=request.reason,
        )

        db.commit()

        return ResponseModel(
            code=200,
            message="审批撤回成功",
            data=result,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的采购订单审批历史。
    """
    service = PurchaseWorkflowService(db)
    result = service.get_approval_history(
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.limit,
        status_filter=status_filter,
    )

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={
            "items": result["items"],
            "total": result["total"],
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (result["total"] + pagination.page_size - 1) // pagination.page_size,
        },
    )
