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
from app.models.acceptance import AcceptanceOrder
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService

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
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for order_id in request.order_ids:
        order = (
            db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
        )
        if not order:
            errors.append({"order_id": order_id, "error": "验收单不存在"})
            continue

        # 验证状态：只有已完成或被驳回的验收单可以提交审批
        if order.status not in ["COMPLETED", "REJECTED"]:
            errors.append(
                {
                    "order_id": order_id,
                    "error": f"当前状态 '{order.status}' 不允许提交审批，需要先完成验收",
                }
            )
            continue

        # 验证是否有验收结论
        if not order.overall_result:
            errors.append(
                {"order_id": order_id, "error": "验收单没有验收结论，无法提交审批"}
            )
            continue

        try:
            instance = engine.submit(
                template_code="ACCEPTANCE_ORDER_APPROVAL",
                entity_type="ACCEPTANCE_ORDER",
                entity_id=order_id,
                form_data={
                    "order_no": order.order_no,
                    "acceptance_type": order.acceptance_type,
                    "overall_result": order.overall_result,
                    "pass_rate": float(order.pass_rate) if order.pass_rate else 0,
                    "passed_items": order.passed_items or 0,
                    "failed_items": order.failed_items or 0,
                    "total_items": order.total_items or 0,
                    "project_id": order.project_id,
                    "machine_id": order.machine_id,
                    "conclusion": order.conclusion,
                    "conditions": order.conditions,
                },
                initiator_id=current_user.id,
                urgency=request.urgency,
            )
            results.append(
                {
                    "order_id": order_id,
                    "order_no": order.order_no,
                    "acceptance_type": order.acceptance_type,
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
    pagination=Depends(get_pagination_query),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    current_user: User = Depends(security.require_permission("acceptance:read")),
) -> Any:
    """
    获取待审批的验收单列表

    返回当前用户待审批的验收单任务。
    """
    engine = ApprovalEngineService(db)
    tasks = engine.get_pending_tasks(
        user_id=current_user.id, entity_type="ACCEPTANCE_ORDER"
    )

    # 如果指定了验收类型筛选
    if acceptance_type:
        filtered_tasks = []
        for task in tasks:
            order = (
                db.query(AcceptanceOrder)
                .filter(AcceptanceOrder.id == task.instance.entity_id)
                .first()
            )
            if order and order.acceptance_type == acceptance_type:
                filtered_tasks.append(task)
        tasks = filtered_tasks

    total = len(tasks)
    start = pagination.offset
    end = start + pagination.limit
    paginated_tasks = tasks[start:end]

    items = []
    for task in paginated_tasks:
        instance = task.instance
        order = (
            db.query(AcceptanceOrder)
            .filter(AcceptanceOrder.id == instance.entity_id)
            .first()
        )

        # 获取验收类型中文名
        type_name_map = {"FAT": "出厂验收", "SAT": "现场验收", "FINAL": "终验收"}
        result_name_map = {
            "PASSED": "合格",
            "FAILED": "不合格",
            "CONDITIONAL": "有条件通过",
        }

        items.append(
            {
                "task_id": task.id,
                "instance_id": instance.id,
                "order_id": instance.entity_id,
                "order_no": order.order_no if order else None,
                "acceptance_type": order.acceptance_type if order else None,
                "acceptance_type_name": type_name_map.get(order.acceptance_type)
                if order
                else None,
                "overall_result": order.overall_result if order else None,
                "result_name": result_name_map.get(order.overall_result)
                if order
                else None,
                "pass_rate": float(order.pass_rate)
                if order and order.pass_rate
                else 0,
                "project_name": order.project.project_name
                if order and hasattr(order, "project") and order.project
                else None,
                "machine_code": order.machine.machine_code
                if order and hasattr(order, "machine") and order.machine
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
    current_user: User = Depends(security.require_permission("acceptance:approve")),
) -> Any:
    """
    批量审批操作

    对多个验收单进行批量审批通过或驳回。
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
                errors.append(
                    {"task_id": task_id, "error": f"不支持的操作: {request.action}"}
                )
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
    current_user: User = Depends(security.require_permission("acceptance:read")),
) -> Any:
    """
    查询验收单审批状态

    获取指定验收单的审批流程状态和历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "ACCEPTANCE_ORDER",
            ApprovalInstance.entity_id == order_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="该验收单暂无审批记录",
            data={
                "order_id": order_id,
                "order_no": order.order_no,
                "acceptance_type": order.acceptance_type,
                "status": order.status,
                "approval_instance": None,
            },
        )

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
            "acceptance_type": order.acceptance_type,
            "overall_result": order.overall_result,
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
    request: WithdrawApprovalRequest,
    current_user: User = Depends(security.require_permission("acceptance:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的验收单。
    """
    from app.models.approval import ApprovalInstance

    order = (
        db.query(AcceptanceOrder).filter(AcceptanceOrder.id == request.order_id).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "ACCEPTANCE_ORDER",
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
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("acceptance:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的验收单审批历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalInstance.entity_type == "ACCEPTANCE_ORDER",
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

    type_name_map = {"FAT": "出厂验收", "SAT": "现场验收", "FINAL": "终验收"}
    result_name_map = {
        "PASSED": "合格",
        "FAILED": "不合格",
        "CONDITIONAL": "有条件通过",
    }

    items = []
    for task in tasks:
        instance = task.instance
        order = (
            db.query(AcceptanceOrder)
            .filter(AcceptanceOrder.id == instance.entity_id)
            .first()
        )

        # 如果指定了验收类型筛选
        if acceptance_type and order and order.acceptance_type != acceptance_type:
            continue

        items.append(
            {
                "task_id": task.id,
                "order_id": instance.entity_id,
                "order_no": order.order_no if order else None,
                "acceptance_type": order.acceptance_type if order else None,
                "acceptance_type_name": type_name_map.get(order.acceptance_type)
                if order
                else None,
                "overall_result": order.overall_result if order else None,
                "result_name": result_name_map.get(order.overall_result)
                if order
                else None,
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
            "pages": pagination.pages_for_total(total),
        },
    )
