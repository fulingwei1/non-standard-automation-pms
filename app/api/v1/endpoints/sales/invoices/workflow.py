# -*- coding: utf-8 -*-
"""
发票工作流审批 API endpoints (新版)
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import (
    ApprovalActionEnum,
    ApprovalRecordStatusEnum,
    InvoiceStatusEnum,
    WorkflowTypeEnum,
)
from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.sales import Invoice
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    ApprovalActionRequest,
    ApprovalHistoryResponse,
    ApprovalRecordResponse,
    ApprovalStartRequest,
    ApprovalStatusResponse,
)
from app.services.approval_engine import ApprovalEngineService
from app.services.sales.invoice_operation_audit import (
    invoice_audit_value,
    log_invoice_operation,
)
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_invoice_approval_instance(db: Session, invoice_id: int) -> ApprovalInstance | None:
    return (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == WorkflowTypeEnum.INVOICE.value,
            ApprovalInstance.entity_id == invoice_id,
        )
        .order_by(ApprovalInstance.created_at.desc(), ApprovalInstance.id.desc())
        .first()
    )


def _get_pending_invoice_approval_instance(
    db: Session, invoice_id: int
) -> ApprovalInstance | None:
    return (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == WorkflowTypeEnum.INVOICE.value,
            ApprovalInstance.entity_id == invoice_id,
            ApprovalInstance.status == ApprovalRecordStatusEnum.PENDING.value,
        )
        .order_by(ApprovalInstance.created_at.desc(), ApprovalInstance.id.desc())
        .first()
    )


def _get_invoice_template_code(db: Session, workflow_id: int | None) -> str:
    if workflow_id:
        flow = (
            db.query(ApprovalFlowDefinition)
            .join(ApprovalTemplate, ApprovalTemplate.id == ApprovalFlowDefinition.template_id)
            .filter(
                ApprovalFlowDefinition.id == workflow_id,
                ApprovalFlowDefinition.is_active,
                ApprovalTemplate.entity_type == WorkflowTypeEnum.INVOICE.value,
                ApprovalTemplate.is_active,
            )
            .first()
        )
        if not flow or not flow.template:
            raise HTTPException(status_code=404, detail="发票审批流程不存在")
        return flow.template.template_code

    template = (
        db.query(ApprovalTemplate)
        .filter(
            ApprovalTemplate.entity_type == WorkflowTypeEnum.INVOICE.value,
            ApprovalTemplate.is_active,
        )
        .order_by(ApprovalTemplate.is_published.desc(), ApprovalTemplate.id.desc())
        .first()
    )
    if not template:
        raise HTTPException(status_code=400, detail="未配置发票审批模板")
    return template.template_code


def _invoice_form_data(invoice: Invoice, comment: str | None = None) -> dict[str, Any]:
    data = {
        "invoice_id": invoice.id,
        "invoice_code": invoice.invoice_code,
        "invoice_type": invoice.invoice_type,
        "amount": float(invoice.amount or 0),
        "tax_rate": float(invoice.tax_rate or 0),
        "tax_amount": float(invoice.tax_amount or 0),
        "total_amount": float(invoice.total_amount or 0),
        "contract_id": invoice.contract_id,
        "contract_code": invoice.contract.contract_code if invoice.contract else None,
        "project_id": invoice.project_id,
        "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "buyer_name": invoice.buyer_name,
        "buyer_tax_no": invoice.buyer_tax_no,
    }
    if comment:
        data["comment"] = comment
    return data


def _log_invoice_approval_operation(
    db: Session,
    invoice: Invoice,
    operation_type: str,
    current_user: User,
    *,
    old_value: dict[str, Any],
    operation_desc: str,
    remark: str | None = None,
) -> None:
    db.flush()
    log_invoice_operation(
        db,
        invoice,
        operation_type,
        current_user,
        old_value=old_value,
        new_value=invoice_audit_value(invoice),
        operation_desc=operation_desc,
        remark=remark,
    )


def _get_current_invoice_approval_task(
    db: Session,
    instance_id: int,
    user_id: int,
) -> ApprovalTask:
    task = (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.assignee_id == user_id,
            ApprovalTask.status == ApprovalRecordStatusEnum.PENDING.value,
        )
        .order_by(ApprovalTask.task_order, ApprovalTask.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=403, detail="当前用户没有待处理的发票审批任务")
    return task


def _task_record_response(task: ApprovalTask) -> ApprovalRecordResponse:
    step_name = task.node.node_name if task.node else None
    approved_at = task.completed_at
    return ApprovalRecordResponse(
        id=task.id,
        step_name=step_name,
        approver_id=task.assignee_id,
        approver_name=task.assignee_name
        or (task.assignee.real_name if task.assignee else None),
        status=task.status,
        action=task.action,
        comment=task.comment,
        approved_at=approved_at,
    )


@router.post("/invoices/{invoice_id}/approval/start", response_model=ResponseModel)
def start_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approval_request: Optional[ApprovalStartRequest] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动发票审批流程
    """
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")
    approval_request = approval_request or ApprovalStartRequest()

    existing = _get_pending_invoice_approval_instance(db, invoice_id)
    if existing:
        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={
                "approval_instance_id": existing.id,
                "instance_no": existing.instance_no,
                "status": existing.status,
                "current_node_id": existing.current_node_id,
            },
        )

    workflow_service = ApprovalEngineService(db)
    try:
        old_value = invoice_audit_value(invoice)
        template_code = _get_invoice_template_code(db, approval_request.workflow_id)
        instance = workflow_service.submit(
            template_code=template_code,
            entity_type=WorkflowTypeEnum.INVOICE.value,
            entity_id=invoice_id,
            form_data=_invoice_form_data(invoice, approval_request.comment),
            initiator_id=current_user.id,
            title=None,
            summary=None,
            urgency="NORMAL",
            cc_user_ids=None,
        )
        db.refresh(invoice)
        _log_invoice_approval_operation(
            db,
            invoice,
            SalesOperationType.SUBMIT,
            current_user,
            old_value=old_value,
            operation_desc="提交发票审批",
            remark=approval_request.comment,
        )
        db.commit()

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={
                "approval_instance_id": instance.id,
                "instance_no": instance.instance_no,
                "status": instance.status,
                "current_node_id": instance.current_node_id,
            },
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices/{invoice_id}/approval-status", response_model=ApprovalStatusResponse)
def get_invoice_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批状态
    """
    instance = _get_invoice_approval_instance(db, invoice_id)
    if not instance:
        return ApprovalStatusResponse(
            entity_id=invoice_id,
            entity_type=WorkflowTypeEnum.INVOICE.value,
            workflow_name=None,
            current_step=None,
            current_approver=None,
            status="NOT_STARTED",
            progress=0,
        )

    current_task = (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.status == ApprovalRecordStatusEnum.PENDING.value,
        )
        .order_by(ApprovalTask.task_order, ApprovalTask.id)
        .first()
    )
    total_tasks = db.query(ApprovalTask).filter(ApprovalTask.instance_id == instance.id).count()
    completed_tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id, ApprovalTask.status == "COMPLETED")
        .count()
    )
    progress = int(completed_tasks / total_tasks * 100) if total_tasks else 0

    return ApprovalStatusResponse(
        entity_id=invoice_id,
        entity_type=WorkflowTypeEnum.INVOICE.value,
        workflow_name=instance.flow.flow_name if instance.flow else None,
        current_step=instance.current_node.node_name if instance.current_node else None,
        current_approver=(
            current_task.assignee_name
            or (current_task.assignee.real_name if current_task and current_task.assignee else None)
            if current_task
            else None
        ),
        status=instance.status,
        progress=progress,
    )


@router.post("/invoices/{invoice_id}/approval/action", response_model=ResponseModel)
def invoice_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发票审批操作（通过/驳回/委托/撤回）
    """
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")
    instance = _get_invoice_approval_instance(db, invoice_id)

    if not instance:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    workflow_service = ApprovalEngineService(db)
    old_value = invoice_audit_value(invoice)

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            task = _get_current_invoice_approval_task(db, instance.id, current_user.id)
            task = workflow_service.approve(
                task_id=task.id, approver_id=current_user.id, comment=action_request.comment
            )
            db.refresh(invoice)

            if task.instance.status == ApprovalRecordStatusEnum.APPROVED.value:
                # 审批完成，允许开票
                invoice.status = InvoiceStatusEnum.APPROVED.value
            message = "审批通过"
            response_status = task.instance.status
            operation_type = SalesOperationType.APPROVE
            operation_desc = "发票审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            task = _get_current_invoice_approval_task(db, instance.id, current_user.id)
            task = workflow_service.reject(
                task_id=task.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回",
            )
            db.refresh(invoice)
            invoice.status = InvoiceStatusEnum.REJECTED.value
            message = "审批已驳回"
            response_status = task.instance.status
            operation_type = SalesOperationType.REJECT
            operation_desc = "发票审批驳回"

        elif action_request.action == ApprovalActionEnum.DELEGATE:
            if not action_request.delegate_to_id:
                raise HTTPException(status_code=400, detail="委托操作需要指定委托给的用户ID")

            task = _get_current_invoice_approval_task(db, instance.id, current_user.id)
            delegated_task = workflow_service.transfer(
                task_id=task.id,
                from_user_id=current_user.id,
                to_user_id=action_request.delegate_to_id,
                comment=action_request.comment,
            )
            message = "审批已委托"
            response_status = delegated_task.instance.status
            operation_type = SalesOperationType.TRANSFER
            operation_desc = "发票审批委托"

        elif action_request.action == ApprovalActionEnum.WITHDRAW:
            instance = workflow_service.withdraw(
                instance_id=instance.id,
                initiator_id=current_user.id,
                comment=action_request.comment,
            )
            db.refresh(invoice)
            message = "审批已撤回"
            response_status = instance.status
            operation_type = SalesOperationType.STATUS_CHANGE
            operation_desc = "撤回发票审批"

        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的审批操作: {action_request.action}"
            )

        _log_invoice_approval_operation(
            db,
            invoice,
            operation_type,
            current_user,
            old_value=old_value,
            operation_desc=operation_desc,
            remark=action_request.comment,
        )
        db.commit()

        return ResponseModel(
            code=200,
            message=message,
            data={"approval_instance_id": instance.id, "status": response_status},
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/approve", response_model=ResponseModel, include_in_schema=False)
def approve_invoice_legacy(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approval_request: Optional[dict[str, Any]] = Body(default=None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """旧版发票审批通过入口，转发到统一审批动作。"""
    payload = approval_request or {}
    action_request = ApprovalActionRequest(
        action=ApprovalActionEnum.APPROVE.value,
        comment=payload.get("comment") or payload.get("comments"),
    )
    return invoice_approval_action(
        db=db,
        invoice_id=invoice_id,
        action_request=action_request,
        current_user=current_user,
    )


@router.get("/invoices/{invoice_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_invoice_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批历史
    """
    instance = _get_invoice_approval_instance(db, invoice_id)
    if not instance:
        return []

    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .order_by(ApprovalTask.task_order, ApprovalTask.id)
        .all()
    )
    return [
        ApprovalHistoryResponse(
            entity_id=invoice_id,
            entity_type=WorkflowTypeEnum.INVOICE.value,
            records=[_task_record_response(task) for task in tasks],
        )
    ]
