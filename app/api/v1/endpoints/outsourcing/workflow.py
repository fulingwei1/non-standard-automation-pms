# -*- coding: utf-8 -*-
"""
外协订单审批工作流 API

使用统一审批引擎实现外协订单审批流程。
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
from app.services.outsourcing_workflow import OutsourcingWorkflowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outsourcing-orders/workflow", tags=["外协审批工作流"])


# ==================== 请求模型 ====================


class OutsourcingOrderSubmitRequest(BaseModel):
    """外协订单提交审批请求"""

    order_ids: List[int] = Field(..., description="外协订单ID列表")
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


class WithdrawRequest(BaseModel):
    """撤回请求"""

    order_id: int = Field(..., description="外协订单ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_orders_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: OutsourcingOrderSubmitRequest,
    current_user: User = Depends(security.require_permission("outsourcing:create")),
) -> Any:
    """
    提交外协订单审批

    将一个或多个外协订单提交到审批流程。
    """
    service = OutsourcingWorkflowService(db)
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
    current_user: User = Depends(security.require_permission("outsourcing:read")),
) -> Any:
    """
    获取待审批的外协订单列表

    返回当前用户待审批的外协订单任务。
    """
    service = OutsourcingWorkflowService(db)
    result = service.get_pending_tasks(
        user_id=current_user.id, offset=pagination.offset, limit=pagination.limit
    )

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={
            "items": result["items"],
            "total": result["total"],
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(result["total"]),
        },
    )


@router.post("/action", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ApprovalActionRequest,
    current_user: User = Depends(security.require_permission("outsourcing:approve")),
) -> Any:
    """
    执行审批操作

    对单个外协订单进行审批通过或驳回。
    审批通过后自动触发成本归集。
    """
    service = OutsourcingWorkflowService(db)

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
    current_user: User = Depends(security.require_permission("outsourcing:approve")),
) -> Any:
    """
    批量审批操作

    对多个外协订单进行批量审批通过或驳回。
    """
    service = OutsourcingWorkflowService(db)
    result = service.perform_batch_approval(
        task_ids=request.task_ids,
        approver_id=current_user.id,
        action=request.action,
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
    current_user: User = Depends(security.require_permission("outsourcing:read")),
) -> Any:
    """
    查询外协订单审批状态

    获取指定外协订单的审批流程状态和历史。
    """
    service = OutsourcingWorkflowService(db)

    try:
        result = service.get_approval_status(order_id)

        if result.get("approval_instance") is None:
            return ResponseModel(code=200, message="该订单暂无审批记录", data=result)

        return ResponseModel(code=200, message="获取审批状态成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/withdraw", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def withdraw_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: WithdrawRequest,
    current_user: User = Depends(security.require_permission("outsourcing:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的外协订单。
    """
    service = OutsourcingWorkflowService(db)

    try:
        result = service.withdraw_approval(
            order_id=request.order_id, user_id=current_user.id, reason=request.reason
        )

        db.commit()

        return ResponseModel(code=200, message="审批撤回成功", data=result)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "权限" in str(e) or "只能撤回" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("outsourcing:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的外协订单审批历史。
    """
    service = OutsourcingWorkflowService(db)
    result = service.get_approval_history(
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
        status_filter=status_filter,
    )

    total = result["total"]

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={
            "items": result["items"],
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (total + pagination.page_size - 1) // pagination.page_size,
        },
    )
