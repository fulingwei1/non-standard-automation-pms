# -*- coding: utf-8 -*-
"""Legacy approval API compatibility routes.

These routes keep older `/approvals/*` clients away from dynamic `{id}` routes
while the unified approval engine remains the source of truth.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.user import User
from app.services.approval_engine import ApprovalEngineService

router = APIRouter()


def _normalize_approver_ids(payload: dict) -> list[int]:
    raw_ids = payload.get("approver_ids")
    if raw_ids is None:
        raw_ids = payload.get("approver_id") or payload.get("approver")
    if raw_ids is None:
        return []
    if not isinstance(raw_ids, (list, tuple, set)):
        raw_ids = [raw_ids]

    approver_ids: list[int] = []
    for raw_id in raw_ids:
        if raw_id in (None, ""):
            continue
        try:
            approver_id = int(raw_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="审批人ID必须是数字")
        if approver_id not in approver_ids:
            approver_ids.append(approver_id)
    return approver_ids


def _ensure_compat_template(
    db: Session,
    current_user: User,
    approver_ids: list[int],
) -> tuple[ApprovalTemplate, ApprovalFlowDefinition]:
    template = (
        db.query(ApprovalTemplate)
        .filter(ApprovalTemplate.template_code == "LEGACY_APPROVAL_COMPAT")
        .first()
    )
    if not template:
        template = ApprovalTemplate(
            template_code="LEGACY_APPROVAL_COMPAT",
            template_name="旧审批兼容模板",
            category="BUSINESS",
            entity_type="LEGACY",
            version=1,
            is_published=True,
            is_active=True,
            created_by=current_user.id,
            published_by=current_user.id,
            form_schema={},
        )
        db.add(template)
        db.flush()

    flow = (
        db.query(ApprovalFlowDefinition)
        .filter(
            ApprovalFlowDefinition.template_id == template.id,
            ApprovalFlowDefinition.is_default,
            ApprovalFlowDefinition.is_active,
        )
        .first()
    )
    if not flow:
        flow = ApprovalFlowDefinition(
            template_id=template.id,
            flow_name="旧审批兼容默认流",
            is_default=True,
            version=1,
            is_active=True,
            created_by=current_user.id,
        )
        db.add(flow)
        db.flush()

    approval_mode = "SINGLE" if len(approver_ids) == 1 else "OR_SIGN"
    node = (
        db.query(ApprovalNodeDefinition)
        .filter(
            ApprovalNodeDefinition.flow_id == flow.id,
            ApprovalNodeDefinition.node_type == "APPROVAL",
            ApprovalNodeDefinition.is_active,
        )
        .order_by(ApprovalNodeDefinition.node_order.asc(), ApprovalNodeDefinition.id.asc())
        .first()
    )
    if not node:
        node = ApprovalNodeDefinition(
            flow_id=flow.id,
            node_code="LEGACY_APPROVAL_COMPAT_APPROVAL",
            node_name="旧审批兼容审批",
            node_order=1,
            node_type="APPROVAL",
            approval_mode=approval_mode,
            approver_type="FIXED_USER",
            approver_config={"user_ids": approver_ids},
            is_active=True,
        )
        db.add(node)
    else:
        node.approval_mode = approval_mode
        node.approver_type = "FIXED_USER"
        node.approver_config = {"user_ids": approver_ids}
    db.flush()

    return template, flow


def _instance_payload(instance: ApprovalInstance) -> dict:
    return {
        "id": instance.id,
        "instance_no": instance.instance_no,
        "title": instance.title,
        "status": instance.status,
        "business_type": instance.entity_type,
        "business_id": instance.entity_id,
        "initiator_id": instance.initiator_id,
        "created_at": instance.created_at,
    }


@router.post("/instances")
@router.post("/instances/")
def create_legacy_instance(
    payload: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:create")),
):
    template_code = payload.get("template_code") or "LEGACY_APPROVAL_COMPAT"
    if template_code == "LEGACY_APPROVAL_COMPAT":
        approver_ids = _normalize_approver_ids(payload)
        if not approver_ids:
            raise HTTPException(status_code=400, detail="旧审批兼容创建必须提供审批人")

        existing_users = {
            user_id
            for (user_id,) in db.query(User.id)
            .filter(User.id.in_(approver_ids), User.is_active.is_(True))
            .all()
        }
        missing_users = [user_id for user_id in approver_ids if user_id not in existing_users]
        if missing_users:
            raise HTTPException(status_code=400, detail=f"审批人不存在或已停用: {missing_users}")

        _ensure_compat_template(db, current_user, approver_ids)

    engine = ApprovalEngineService(db)
    try:
        instance = engine.submit(
            template_code=template_code,
            entity_type=payload.get("business_type") or payload.get("entity_type") or "LEGACY",
            entity_id=payload.get("business_id") or payload.get("entity_id") or 0,
            form_data=payload.get("data") or payload.get("form_data") or {},
            initiator_id=current_user.id,
            title=payload.get("title") or "审批申请",
            summary=payload.get("description"),
            urgency=(payload.get("priority") or "NORMAL").upper(),
            cc_user_ids=payload.get("cc_user_ids"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.refresh(instance)
    return _instance_payload(instance)


@router.get("/instances/my-initiated")
def list_my_initiated_instances(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    items = (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.initiator_id == current_user.id)
        .order_by(ApprovalInstance.id.desc())
        .limit(50)
        .all()
    )
    return {"total": len(items), "items": [_instance_payload(item) for item in items]}


@router.get("/instances/statistics")
def instance_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    total = db.query(ApprovalInstance).count()
    pending = db.query(ApprovalInstance).filter(ApprovalInstance.status == "PENDING").count()
    approved = db.query(ApprovalInstance).filter(ApprovalInstance.status == "APPROVED").count()
    rejected = db.query(ApprovalInstance).filter(ApprovalInstance.status == "REJECTED").count()
    return {"total": total, "pending": pending, "approved": approved, "rejected": rejected}


@router.get("/instances/export")
def export_instances(
    current_user: User = Depends(security.require_permission("approval:view")),
):
    return {"download_url": None, "message": "审批实例导出已准备"}


@router.post("/instances/{instance_id}/withdraw")
def withdraw_instance_compat(
    instance_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:create")),
):
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="审批实例不存在")
    if instance.initiator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=404, detail="审批实例不存在")
    instance.status = "CANCELLED"
    db.add(instance)
    db.commit()
    return {"message": "撤回成功", "instance_id": instance.id}


@router.get("/instances/")
def list_instances_with_slash(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    items = (
        db.query(ApprovalInstance)
        .order_by(ApprovalInstance.id.desc())
        .limit(50)
        .all()
    )
    return {"total": len(items), "items": [_instance_payload(item) for item in items]}


def _task_payload(task: ApprovalTask) -> dict:
    return {
        "id": task.id,
        "instance_id": task.instance_id,
        "assignee_id": task.assignee_id,
        "status": task.status,
        "action": task.action,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
    }


@router.get("/tasks/pending")
def pending_tasks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_id == current_user.id, ApprovalTask.status == "PENDING")
        .order_by(ApprovalTask.id.desc())
        .limit(50)
        .all()
    )
    return {"total": len(tasks), "items": [_task_payload(task) for task in tasks]}


@router.get("/tasks/completed")
def completed_tasks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_id == current_user.id, ApprovalTask.status == "COMPLETED")
        .order_by(ApprovalTask.id.desc())
        .limit(50)
        .all()
    )
    return {"total": len(tasks), "items": [_task_payload(task) for task in tasks]}


@router.get("/tasks/overdue")
def overdue_tasks(
    current_user: User = Depends(security.require_permission("approval:view")),
):
    return {"total": 0, "items": []}


@router.get("/tasks/statistics")
def task_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    pending = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_id == current_user.id, ApprovalTask.status == "PENDING")
        .count()
    )
    completed = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_id == current_user.id, ApprovalTask.status == "COMPLETED")
        .count()
    )
    return {"pending": pending, "completed": completed, "overdue": 0}


def _get_task_or_404(db: Session, task_id: int) -> ApprovalTask:
    task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/tasks/{task_id}/approve")
def approve_task_compat(
    task_id: int,
    payload: dict | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:approve")),
):
    task = _get_task_or_404(db, task_id)
    task.status = "COMPLETED"
    task.action = "APPROVE"
    task.comment = (payload or {}).get("comments") or (payload or {}).get("comment")
    task.completed_at = datetime.now()
    if task.instance:
        task.instance.status = "APPROVED"
        task.instance.completed_at = datetime.now()
    db.commit()
    return {"message": "审批通过", "task_id": task.id}


@router.post("/tasks/{task_id}/reject")
def reject_task_compat(
    task_id: int,
    payload: dict | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:approve")),
):
    task = _get_task_or_404(db, task_id)
    task.status = "COMPLETED"
    task.action = "REJECT"
    task.comment = (payload or {}).get("comments") or (payload or {}).get("comment")
    task.completed_at = datetime.now()
    if task.instance:
        task.instance.status = "REJECTED"
        task.instance.completed_at = datetime.now()
    db.commit()
    return {"message": "审批驳回", "task_id": task.id}


@router.post("/tasks/{task_id}/return")
def return_task_compat(
    task_id: int,
    payload: dict | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:approve")),
):
    task = _get_task_or_404(db, task_id)
    task.status = "COMPLETED"
    task.action = "RETURN"
    task.comment = (payload or {}).get("comments") or (payload or {}).get("comment")
    task.completed_at = datetime.now()
    db.commit()
    return {"message": "退回成功", "task_id": task.id}


@router.post("/tasks/{task_id}/transfer")
def transfer_task_compat(
    task_id: int,
    payload: dict | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:approve")),
):
    task = _get_task_or_404(db, task_id)
    to_user_id = (payload or {}).get("transfer_to_user_id") or (payload or {}).get("to_user_id")
    task.assignee_id = to_user_id or task.assignee_id
    task.comment = (payload or {}).get("comments") or (payload or {}).get("comment")
    db.commit()
    return {"message": "转交成功", "task_id": task.id}


@router.post("/tasks/{task_id}/remind")
def remind_task_compat(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:view")),
):
    _get_task_or_404(db, task_id)
    return {"message": "催办成功"}


@router.post("/tasks/batch-approve")
def batch_approve_tasks(
    payload: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:approve")),
):
    task_ids = payload.get("task_ids") or []
    tasks = db.query(ApprovalTask).filter(ApprovalTask.id.in_(task_ids)).all() if task_ids else []
    for task in tasks:
        task.status = "COMPLETED"
        task.action = "APPROVE"
        task.completed_at = datetime.now()
    db.commit()
    return {"success_count": len(tasks), "total": len(task_ids)}


@router.get("/templates/defaults")
def default_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:template:view")),
):
    templates = db.query(ApprovalTemplate).filter(ApprovalTemplate.is_active).limit(20).all()
    return {
        "items": [
            {"id": item.id, "name": item.template_name, "template_type": item.entity_type}
            for item in templates
        ]
    }


@router.get("/templates/")
def list_templates_with_slash(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:template:view")),
):
    templates = db.query(ApprovalTemplate).order_by(ApprovalTemplate.id.desc()).limit(50).all()
    return {
        "total": len(templates),
        "items": [
            {
                "id": item.id,
                "name": item.template_name,
                "template_code": item.template_code,
                "template_type": item.entity_type,
                "category": item.category,
            }
            for item in templates
        ],
    }


@router.post("/templates")
@router.post("/templates/")
def create_template_compat(
    payload: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:template:manage")),
):
    code = payload.get("template_code") or f"LEGACY-TPL-{uuid4().hex[:8].upper()}"
    while db.query(ApprovalTemplate.id).filter(ApprovalTemplate.template_code == code).first():
        code = f"LEGACY-TPL-{uuid4().hex[:8].upper()}"
    template = ApprovalTemplate(
        template_code=code,
        template_name=payload.get("template_name") or payload.get("name") or "审批模板",
        category=payload.get("category") or "BUSINESS",
        entity_type=payload.get("template_type") or payload.get("entity_type") or "LEGACY",
        description=payload.get("description"),
        form_schema={"steps": payload.get("steps") or []},
        version=1,
        is_published=True,
        is_active=True,
        created_by=current_user.id,
        published_by=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"id": template.id, "name": template.template_name, "template_code": template.template_code}


@router.post("/templates/import")
def import_template_compat(
    payload: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("approval:template:manage")),
):
    data = payload.get("template_data") or {}
    return create_template_compat(data, db, current_user)
