# -*- coding: utf-8 -*-
"""
采购订单审批工作流 API

使用统一审批引擎实现采购订单审批流程。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.purchase import PurchaseOrder
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService
from app.common.pagination import PaginationParams, get_pagination_query
from app.utils.db_helpers import get_or_404

router = APIRouter(prefix="/workflow", tags=["采购审批工作流"])


# ==================== 请求模型 ====================


class PurchaseOrderSubmitRequest(BaseModel):
    """采购订单提交审批请求"""

    order_ids: List[int] = Field(..., description="采购订单ID列表")
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

    order_id: int = Field(..., description="采购订单ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_orders_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: PurchaseOrderSubmitRequest,
    current_user: User = Depends(security.require_permission("purchase:create")),
) -> Any:
    """
    提交采购订单审批

    将一个或多个采购订单提交到审批流程。
    """
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for order_id in request.order_ids:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            errors.append({"order_id": order_id, "error": "采购订单不存在"})
            continue

        if order.status not in ["DRAFT", "REJECTED"]:
            errors.append(
                {"order_id": order_id, "error": f"当前状态 '{order.status}' 不允许提交审批"}
            )
            continue

        try:
            instance = engine.submit(
                template_code="PURCHASE_ORDER_APPROVAL",
                entity_type="PURCHASE_ORDER",
                entity_id=order_id,
                form_data={
                    "order_no": order.order_no,
                    "order_title": order.order_title,
                    "amount_with_tax": float(order.amount_with_tax) if order.amount_with_tax else 0,
                    "supplier_id": order.supplier_id,
                    "project_id": order.project_id,
                },
                initiator_id=current_user.id,
                urgency=request.urgency,
            )
            results.append(
                {
                    "order_id": order_id,
                    "order_no": order.order_no,
                    "instance_id": instance.id,
                    "status": "submitted",
                }
            )
        except Exception as e:
            errors.append({"order_id": order_id, "error": str(e)})

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
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """
    获取待审批的采购订单列表

    返回当前用户待审批的采购订单任务。
    """
    engine = ApprovalEngineService(db)
    tasks = engine.get_pending_tasks(
        user_id=current_user.id, entity_type="PURCHASE_ORDER"
    )

    # 分页
    total = len(tasks)
    paginated_tasks = tasks[pagination.offset : pagination.offset + pagination.page_size]

    items = []
    for task in paginated_tasks:
        instance = task.instance
        order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == instance.entity_id)
            .first()
        )

        items.append(
            {
                "task_id": task.id,
                "instance_id": instance.id,
                "order_id": instance.entity_id,
                "order_no": order.order_no if order else None,
                "order_title": order.order_title if order else None,
                "amount_with_tax": float(order.amount_with_tax)
                if order and order.amount_with_tax
                else 0,
                "supplier_name": order.supplier.vendor_name
                if order and order.supplier
                else None,
                "initiator_name": instance.initiator.real_name
                if instance.initiator
                else None,
                "submitted_at": instance.created_at.isoformat()
                if instance.created_at
                else None,
                "urgency": instance.urgency,
                "node_name": task.node.node_name if task.node else None,
            }
        )

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (total + pagination.page_size - 1) // pagination.page_size,
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
    engine = ApprovalEngineService(db)

    try:
        if request.action == "approve":
            result = engine.approve(
                task_id=request.task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
        elif request.action == "reject":
            result = engine.reject(
                task_id=request.task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的操作类型: {request.action}"
            )

        db.commit()

        return ResponseModel(
            code=200,
            message="审批操作成功",
            data={
                "task_id": request.task_id,
                "action": request.action,
                "instance_status": result.status if hasattr(result, "status") else None,
            },
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
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for task_id in request.task_ids:
        try:
            if request.action == "approve":
                engine.approve(
                    task_id=task_id,
                    approver_id=current_user.id,
                    comment=request.comment,
                )
            elif request.action == "reject":
                engine.reject(
                    task_id=task_id,
                    approver_id=current_user.id,
                    comment=request.comment,
                )
            else:
                errors.append({"task_id": task_id, "error": f"不支持的操作: {request.action}"})
                continue

            results.append({"task_id": task_id, "status": "success"})
        except Exception as e:
            errors.append({"task_id": task_id, "error": str(e)})

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
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """
    查询采购订单审批状态

    获取指定采购订单的审批流程状态和历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "PURCHASE_ORDER",
            ApprovalInstance.entity_id == order_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="该订单暂无审批记录",
            data={
                "order_id": order_id,
                "order_no": order.order_no,
                "status": order.status,
                "approval_instance": None,
            },
        )

    # 获取审批任务历史
    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .order_by(ApprovalTask.created_at)
        .all()
    )

    task_history = []
    for task in tasks:
        task_history.append(
            {
                "task_id": task.id,
                "node_name": task.node.node_name if task.node else None,
                "assignee_name": task.assignee.real_name if task.assignee else None,
                "status": task.status,
                "action": task.action,
                "comment": task.comment,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
            }
        )

    return ResponseModel(
        code=200,
        message="获取审批状态成功",
        data={
            "order_id": order_id,
            "order_no": order.order_no,
            "order_status": order.status,
            "instance_id": instance.id,
            "instance_status": instance.status,
            "urgency": instance.urgency,
            "submitted_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "completed_at": instance.completed_at.isoformat()
            if instance.completed_at
            else None,
            "task_history": task_history,
        },
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
    from app.models.approval import ApprovalInstance

    order = get_or_404(db, PurchaseOrder, request.order_id, "采购订单不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "PURCHASE_ORDER",
            ApprovalInstance.entity_id == request.order_id,
            ApprovalInstance.status == "PENDING",
        )
        .first()
    )

    if not instance:
        raise HTTPException(status_code=400, detail="没有进行中的审批流程可撤回")

    if instance.initiator_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能撤回自己提交的审批")

    engine = ApprovalEngineService(db)
    try:
        engine.withdraw(instance_id=instance.id, user_id=current_user.id)
        db.commit()

        return ResponseModel(
            code=200,
            message="审批撤回成功",
            data={
                "order_id": request.order_id,
                "order_no": order.order_no,
                "status": "withdrawn",
            },
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
    from app.models.approval import ApprovalInstance, ApprovalTask

    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalInstance.entity_type == "PURCHASE_ORDER",
            ApprovalTask.status.in_(["APPROVED", "REJECTED"]),
        )
    )

    if status_filter:
        query = query.filter(ApprovalTask.status == status_filter)

    total = query.count()
    tasks = (
        query.order_by(ApprovalTask.completed_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    items = []
    for task in tasks:
        instance = task.instance
        order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == instance.entity_id)
            .first()
        )

        items.append(
            {
                "task_id": task.id,
                "order_id": instance.entity_id,
                "order_no": order.order_no if order else None,
                "order_title": order.order_title if order else None,
                "amount_with_tax": float(order.amount_with_tax)
                if order and order.amount_with_tax
                else 0,
                "action": task.action,
                "status": task.status,
                "comment": task.comment,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
            }
        )

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (total + pagination.page_size - 1) // pagination.page_size,
        },
    )
