# -*- coding: utf-8 -*-
"""APPR-09: 通用审批超时任务不能停在死代码。"""
from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy.orm import sessionmaker

from app.models.approval import (
    ApprovalActionLog,
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.user import User


def _create_timeout_case(db_session, timeout_action="AUTO_PASS", manager=None):
    initiator = User(
        username=f"appr09_initiator_{timeout_action.lower()}",
        password_hash="x",
        real_name="发起人",
        is_active=True,
    )
    approver = User(
        username=f"appr09_approver_{timeout_action.lower()}",
        password_hash="x",
        real_name="审批人",
        is_active=True,
        reporting_to=manager.id if manager else None,
    )
    db_session.add_all([initiator, approver])
    db_session.flush()

    template = ApprovalTemplate(
        template_code=f"APPR09_{timeout_action}",
        template_name=f"APPR09 {timeout_action}",
        category="TEST",
        entity_type="APPR09_TEST",
        is_active=True,
        is_published=True,
    )
    db_session.add(template)
    db_session.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"APPR09 {timeout_action} Flow",
        is_default=True,
        is_active=True,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"APPR09_{timeout_action}_NODE",
        node_name="超时审批节点",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [approver.id]},
        timeout_hours=1,
        timeout_action=timeout_action,
    )
    db_session.add(node)
    db_session.flush()

    instance = ApprovalInstance(
        instance_no=f"APPR09-{timeout_action}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="APPR09_TEST",
        entity_id=1,
        initiator_id=initiator.id,
        status="PENDING",
        current_node_id=node.id,
        title=f"APPR09 {timeout_action}",
        summary="审批超时测试",
        submitted_at=datetime(2026, 7, 4, 8, 0, 0),
    )
    db_session.add(instance)
    db_session.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=approver.id,
        status="PENDING",
        due_at=datetime(2026, 7, 4, 9, 0, 0),
    )
    db_session.add(task)
    db_session.commit()
    return instance, task, approver


def test_auto_pass_timeout_advances_instance_to_approved(db_session):
    from app.services.approval_engine.engine import ApprovalEngineService

    instance, task, _approver = _create_timeout_case(db_session, "AUTO_PASS")
    service = ApprovalEngineService(db_session)

    with (
        patch.object(service.notify, "notify_approved"),
        patch.object(service, "_call_adapter_callback"),
    ):
        result = service.process_approval_timeouts(now=datetime(2026, 7, 4, 10, 0, 0))

    assert result["status"] == "success"
    assert result["processed_count"] == 1
    assert result["action_counts"]["AUTO_PASS"] == 1

    db_session.refresh(instance)
    db_session.refresh(task)
    assert task.status == "COMPLETED"
    assert task.action == "APPROVE"
    assert instance.status == "APPROVED"
    assert instance.completed_at is not None
    assert (
        db_session.query(ApprovalActionLog)
        .filter(
            ApprovalActionLog.task_id == task.id,
            ApprovalActionLog.action == "TIMEOUT",
        )
        .count()
        == 1
    )


def test_auto_reject_timeout_rejects_instance(db_session):
    from app.services.approval_engine.engine import ApprovalEngineService

    instance, task, _approver = _create_timeout_case(db_session, "AUTO_REJECT")
    service = ApprovalEngineService(db_session)

    with (
        patch.object(service.notify, "notify_rejected"),
        patch.object(service, "_call_adapter_callback"),
    ):
        result = service.process_approval_timeouts(now=datetime(2026, 7, 4, 10, 0, 0))

    assert result["status"] == "success"
    assert result["action_counts"]["AUTO_REJECT"] == 1

    db_session.refresh(instance)
    db_session.refresh(task)
    assert task.status == "COMPLETED"
    assert task.action == "REJECT"
    assert instance.status == "REJECTED"
    assert instance.completed_at is not None


def test_remind_timeout_sends_reminder_without_completing_task(db_session):
    from app.services.approval_engine.engine import ApprovalEngineService

    instance, task, _approver = _create_timeout_case(db_session, "REMIND")
    service = ApprovalEngineService(db_session)

    with patch.object(service.notify, "notify_remind") as notify_remind:
        result = service.process_approval_timeouts(now=datetime(2026, 7, 4, 10, 0, 0))

    assert result["status"] == "success"
    assert result["action_counts"]["REMIND"] == 1
    notify_remind.assert_called_once()

    db_session.refresh(instance)
    db_session.refresh(task)
    assert task.status == "PENDING"
    assert task.remind_count == 1
    assert instance.status == "PENDING"


def test_escalate_timeout_creates_manager_task(db_session):
    from app.services.approval_engine.engine import ApprovalEngineService

    manager = User(
        username="appr09_manager",
        password_hash="x",
        real_name="上级",
        is_active=True,
    )
    db_session.add(manager)
    db_session.flush()

    instance, task, _approver = _create_timeout_case(db_session, "ESCALATE", manager=manager)
    service = ApprovalEngineService(db_session)

    with patch.object(service.notify, "notify_pending") as notify_pending:
        result = service.process_approval_timeouts(now=datetime(2026, 7, 4, 10, 0, 0))

    assert result["status"] == "success"
    assert result["action_counts"]["ESCALATE"] == 1
    notify_pending.assert_called_once()

    db_session.refresh(instance)
    db_session.refresh(task)
    assert task.status == "EXPIRED"
    assert instance.status == "PENDING"

    escalated_task = (
        db_session.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.assignee_id == manager.id,
            ApprovalTask.status == "PENDING",
        )
        .one()
    )
    assert escalated_task.original_assignee_id == task.assignee_id
    assert escalated_task.assignee_type == "TRANSFERRED"


def test_approval_timeout_task_registered_and_out_of_stub():
    from app.utils import scheduled_tasks
    from app.utils.scheduled_tasks import stub_tasks
    from app.utils.scheduler_config import SCHEDULER_TASKS

    assert "process_approval_timeouts" not in stub_tasks.__all__
    assert scheduled_tasks.get_task("process_approval_timeouts") is scheduled_tasks.process_approval_timeouts

    task = next(t for t in SCHEDULER_TASKS if t["id"] == "process_approval_timeouts")
    assert task["enabled"] is True
    assert task["callable"] == "process_approval_timeouts"
    assert "approval_tasks" in task["dependencies_tables"]
    assert "approval_instances" in task["dependencies_tables"]


def test_scheduled_task_scans_overdue_approval_tasks(db_session, monkeypatch):
    from app.models import base as base_module
    from app.utils import scheduled_tasks

    instance, task, _approver = _create_timeout_case(db_session, "AUTO_PASS")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    monkeypatch.setattr(base_module, "get_session", TestingSessionLocal)

    with patch(
        "app.services.approval_engine.notify.basic_notifications.BasicNotificationsMixin.notify_approved"
    ):
        result = scheduled_tasks.process_approval_timeouts(now=datetime(2026, 7, 4, 10, 0, 0))

    assert result["status"] == "success"
    assert result["processed_count"] == 1

    db_session.refresh(instance)
    db_session.refresh(task)
    assert task.action == "APPROVE"
    assert instance.status == "APPROVED"


def test_due_soon_timeout_warning_uses_node_remind_hours(db_session):
    from app.services.approval_engine.engine import ApprovalEngineService

    instance, task, _approver = _create_timeout_case(db_session, "AUTO_PASS")
    task.due_at = datetime(2026, 7, 4, 12, 0, 0)
    task.node.timeout_remind_hours = 3
    db_session.commit()

    service = ApprovalEngineService(db_session)
    with patch.object(service.notify, "notify_timeout_warning") as notify_warning:
        result = service.process_approval_timeout_warnings(now=datetime(2026, 7, 4, 10, 0, 0))

    assert result["status"] == "success"
    assert result["warning_count"] == 1
    notify_warning.assert_called_once_with(task, 2)

    db_session.refresh(instance)
    db_session.refresh(task)
    assert instance.status == "PENDING"
    assert task.status == "PENDING"
    assert task.remind_count == 1
