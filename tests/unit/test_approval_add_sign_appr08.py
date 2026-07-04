# -*- coding: utf-8 -*-
"""APPR-08: 前/后加签必须真正进入审批任务流。"""

import uuid

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.user import User
from app.services.approval_engine import ApprovalEngineService


def _user(db: Session, username: str, real_name: str) -> User:
    user = User(
        username=f"{username}-{uuid.uuid4().hex[:6]}",
        password_hash="test",
        real_name=real_name,
        department="系统",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _approval_context(db: Session):
    initiator = _user(db, "initiator", "发起人")
    approver = _user(db, "approver", "原审批人")
    signer = _user(db, "signer", "加签人")

    suffix = uuid.uuid4().hex[:8].upper()
    template = ApprovalTemplate(
        template_code=f"APPR08-{suffix}",
        template_name="APPR08测试模板",
        category="TEST",
        entity_type="APPR08",
        is_active=True,
        is_published=True,
        created_by=initiator.id,
    )
    db.add(template)
    db.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name="APPR08测试流程",
        is_default=True,
        is_active=True,
        created_by=initiator.id,
    )
    db.add(flow)
    db.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"APPR08-NODE-{suffix}",
        node_name="审批节点",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [approver.id]},
        can_add_approver=True,
        is_active=True,
    )
    db.add(node)
    db.flush()

    instance = ApprovalInstance(
        instance_no=f"APPR08-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="APPR08",
        entity_id=1,
        initiator_id=initiator.id,
        status="PENDING",
        current_node_id=node.id,
        current_node_order=node.node_order,
        form_data={},
        title="APPR08测试",
    )
    db.add(instance)
    db.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=approver.id,
        assignee_name=approver.real_name,
        assignee_type="NORMAL",
        status="PENDING",
    )
    db.add(task)
    db.commit()
    return instance, task, approver, signer


def test_before_add_sign_reactivates_original_task_after_signer_approves(
    db_session: Session,
):
    instance, task, approver, signer = _approval_context(db_session)
    engine = ApprovalEngineService(db_session)

    added_tasks = engine.add_approver(
        task_id=task.id,
        operator_id=approver.id,
        approver_ids=[signer.id],
        position="BEFORE",
        comment="前加签",
    )

    db_session.refresh(task)
    added_task = added_tasks[0]
    assert task.status == "SKIPPED"
    assert added_task.status == "PENDING"
    assert added_task.assignee_type == "ADDED_BEFORE"

    engine.approve(added_task.id, signer.id, comment="加签通过")

    db_session.refresh(task)
    db_session.refresh(added_task)
    db_session.refresh(instance)
    assert added_task.status == "COMPLETED"
    assert task.status == "PENDING"
    assert instance.status == "PENDING"

    engine.approve(task.id, approver.id, comment="原审批通过")

    db_session.refresh(instance)
    assert instance.status == "APPROVED"


def test_after_add_sign_activates_signer_after_original_approves(db_session: Session):
    instance, task, approver, signer = _approval_context(db_session)
    engine = ApprovalEngineService(db_session)

    added_tasks = engine.add_approver(
        task_id=task.id,
        operator_id=approver.id,
        approver_ids=[signer.id],
        position="AFTER",
        comment="后加签",
    )

    added_task = added_tasks[0]
    assert task.status == "PENDING"
    assert added_task.status == "SKIPPED"
    assert added_task.assignee_type == "ADDED_AFTER"

    engine.approve(task.id, approver.id, comment="原审批通过")

    db_session.refresh(task)
    db_session.refresh(added_task)
    db_session.refresh(instance)
    assert task.status == "COMPLETED"
    assert added_task.status == "PENDING"
    assert instance.status == "PENDING"

    engine.approve(added_task.id, signer.id, comment="后加签通过")

    db_session.refresh(instance)
    assert instance.status == "APPROVED"
