# -*- coding: utf-8 -*-
"""AS-06: SLA legacy policy activation and scheduled warning scan."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from importlib import import_module

from sqlalchemy import text

from app.models.alert import AlertRecord
from app.models.project import Customer, Project
from app.models.service import ServiceTicket
from app.models.sla import SLAMonitor, SLAPolicy
from app.services.sla_service import check_sla_warnings, match_sla_policy
from app.utils.scheduler_config import SCHEDULER_TASKS


def test_null_active_policy_is_matched_from_legacy_data(db_session):
    policy = SLAPolicy(
        policy_name="Legacy default SLA",
        policy_code="AS06-LEGACY",
        problem_type="SOFTWARE",
        urgency="HIGH",
        response_time_hours=4,
        resolve_time_hours=24,
        warning_threshold_percent=80,
        priority=1,
        is_active=None,
    )
    db_session.add(policy)
    db_session.commit()
    db_session.execute(
        text("UPDATE sla_policies SET is_active = NULL WHERE policy_code = :policy_code"),
        {"policy_code": "AS06-LEGACY"},
    )
    db_session.commit()
    db_session.expire_all()

    result = match_sla_policy(db_session, "SOFTWARE", "HIGH")

    assert result is not None
    assert result.policy_code == "AS06-LEGACY"


def test_null_active_policy_warnings_are_returned(db_session):
    customer = Customer(customer_code="AS06-CUST", customer_name="AS06 客户")
    db_session.add(customer)
    db_session.flush()
    project = Project(project_code="AS06-PROJ", project_name="AS06 项目", customer_id=customer.id)
    db_session.add(project)
    db_session.flush()
    ticket = ServiceTicket(
        ticket_no="AS06-TICKET",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="legacy policy warning scan",
        urgency="HIGH",
        reported_by="tester",
        reported_time=datetime(2026, 1, 1, 9, 0),
    )
    db_session.add(ticket)
    policy = SLAPolicy(
        policy_name="Legacy warning SLA",
        policy_code="AS06-WARNING",
        problem_type="SOFTWARE",
        urgency="HIGH",
        response_time_hours=4,
        resolve_time_hours=24,
        warning_threshold_percent=80,
        priority=1,
        is_active=None,
    )
    db_session.add(policy)
    db_session.flush()
    db_session.execute(
        text("UPDATE sla_policies SET is_active = NULL WHERE policy_code = :policy_code"),
        {"policy_code": "AS06-WARNING"},
    )
    monitor = SLAMonitor(
        ticket_id=ticket.id,
        policy_id=policy.id,
        response_deadline=ticket.reported_time + timedelta(hours=4),
        resolve_deadline=ticket.reported_time + timedelta(hours=24),
        response_status="WARNING",
        resolve_status="ON_TIME",
        response_warning_sent=False,
        resolve_warning_sent=False,
    )
    db_session.add(monitor)
    db_session.commit()

    warnings = check_sla_warnings(db_session, datetime(2026, 1, 1, 12, 30))

    assert [warning.id for warning in warnings] == [monitor.id]


def test_sla_warning_scan_task_is_registered_and_resolvable():
    task = next((item for item in SCHEDULER_TASKS if item["id"] == "check_sla_warnings"), None)

    assert task is not None
    assert task["enabled"] is True
    assert "sla_monitors" in task["dependencies_tables"]
    module = import_module(task["module"])

    assert callable(getattr(module, task["callable"]))


def test_sla_warning_scan_task_syncs_tickets_and_creates_alert(db_session, monkeypatch):
    from app.utils.scheduled_tasks import alert_tasks

    customer = Customer(customer_code="AS06-TASK-CUST", customer_name="AS06 任务客户")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="AS06-TASK-PROJ",
        project_name="AS06 任务项目",
        customer_id=customer.id,
    )
    db_session.add(project)
    db_session.flush()
    ticket = ServiceTicket(
        ticket_no="AS06-TASK-TICKET",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="task scan should create SLA warning alert",
        urgency="HIGH",
        reported_by="tester",
        reported_time=datetime(2026, 1, 1, 9, 0),
        status="IN_PROGRESS",
    )
    policy = SLAPolicy(
        policy_name="Legacy task SLA",
        policy_code="AS06-TASK",
        problem_type="SOFTWARE",
        urgency="HIGH",
        response_time_hours=4,
        resolve_time_hours=24,
        warning_threshold_percent=80,
        priority=1,
        is_active=None,
    )
    db_session.add_all([ticket, policy])
    db_session.commit()
    db_session.execute(
        text("UPDATE sla_policies SET is_active = NULL WHERE policy_code = :policy_code"),
        {"policy_code": "AS06-TASK"},
    )
    db_session.commit()

    @contextmanager
    def _session_context():
        yield db_session

    monkeypatch.setattr(alert_tasks, "get_db_session", lambda: _session_context())

    result = alert_tasks.check_sla_warnings_task(current_time=datetime(2026, 1, 1, 12, 30))

    monitor = db_session.query(SLAMonitor).filter(SLAMonitor.ticket_id == ticket.id).one()
    alert = db_session.query(AlertRecord).filter(AlertRecord.target_id == monitor.id).one()
    assert result["tickets_scanned"] == 1
    assert result["alerts_created"] == 1
    assert monitor.response_status == "WARNING"
    assert monitor.response_warning_sent is True
    assert alert.target_type == "SLA_MONITOR"
    assert alert.alert_title == "SLA 响应预警"
