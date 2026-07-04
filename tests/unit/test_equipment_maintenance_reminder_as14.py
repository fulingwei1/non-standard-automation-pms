# -*- coding: utf-8 -*-
"""AS-14: 设备维保提醒调度与终验后售后保养计划联动。"""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch

from sqlalchemy.orm import sessionmaker

from app.models.alert import AlertRecord
from app.models.production import Equipment, Workshop
from app.models.user import User


def test_equipment_maintenance_reminder_creates_alerts(db_session, monkeypatch):
    from app.models import base as base_module
    from app.utils import scheduled_tasks

    target_date = date(2026, 7, 4)

    manager = User(employee_id=9001, username="maint_mgr", password_hash="x", is_active=True)
    db_session.add(manager)
    db_session.flush()

    workshop = Workshop(
        workshop_code="AS14-WS",
        workshop_name="AS14 车间",
        workshop_type="ASSEMBLY",
        manager_id=manager.id,
        is_active=True,
    )
    db_session.add(workshop)
    db_session.flush()

    due = Equipment(
        equipment_code="AS14-EQ-DUE",
        equipment_name="到期设备",
        workshop_id=workshop.id,
        next_maintenance_date=target_date,
        is_active=True,
    )
    overdue = Equipment(
        equipment_code="AS14-EQ-OVERDUE",
        equipment_name="逾期设备",
        workshop_id=workshop.id,
        next_maintenance_date=target_date - timedelta(days=2),
        is_active=True,
    )
    future = Equipment(
        equipment_code="AS14-EQ-FUTURE",
        equipment_name="远期设备",
        workshop_id=workshop.id,
        next_maintenance_date=target_date + timedelta(days=30),
        is_active=True,
    )
    inactive = Equipment(
        equipment_code="AS14-EQ-INACTIVE",
        equipment_name="停用设备",
        workshop_id=workshop.id,
        next_maintenance_date=target_date,
        is_active=False,
    )
    db_session.add_all([due, overdue, future, inactive])
    db_session.commit()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    monkeypatch.setattr(base_module, "get_session", TestingSessionLocal)

    try:
        import app.services.equipment_maintenance_service as maintenance_service

        monkeypatch.setattr(
            maintenance_service,
            "send_notification_for_alert",
            lambda *args, **kwargs: None,
        )
    except ImportError:
        pass

    result = scheduled_tasks.check_equipment_maintenance_reminder(
        current_date=target_date, days_ahead=7
    )

    assert result["status"] == "success", f"仍是桩返回或未生成提醒: {result}"
    assert result["due_count"] == 2
    assert result["alerts_created"] == 2

    db_session.expire_all()
    alerts = (
        db_session.query(AlertRecord)
        .filter(AlertRecord.target_type == "EQUIPMENT_MAINTENANCE")
        .order_by(AlertRecord.target_no)
        .all()
    )
    assert [alert.target_no for alert in alerts] == ["AS14-EQ-DUE", "AS14-EQ-OVERDUE"]
    assert {alert.handler_id for alert in alerts} == {manager.id}
    assert {alert.alert_level for alert in alerts} == {"WARNING", "CRITICAL"}

    second = scheduled_tasks.check_equipment_maintenance_reminder(
        current_date=target_date, days_ahead=7
    )
    assert second["alerts_created"] == 0
    assert (
        db_session.query(AlertRecord)
        .filter(AlertRecord.target_type == "EQUIPMENT_MAINTENANCE")
        .count()
        == 2
    ), "同一设备未关闭保养提醒应去重，不能每天重复刷屏"


def test_equipment_maintenance_task_enabled_and_out_of_stub():
    from app.utils.scheduled_tasks import stub_tasks
    from app.utils.scheduler_config.production import PRODUCTION_TASKS

    assert "check_equipment_maintenance_reminder" not in stub_tasks.__all__
    task = next(t for t in PRODUCTION_TASKS if t["id"] == "check_equipment_maintenance_reminder")
    assert task["enabled"] is True
    assert "equipment_maintenance_plans" not in task["dependencies_tables"]


def test_final_acceptance_route_triggers_after_sales_maintenance_plan():
    from app.api.v1.endpoints.acceptance import order_workflow

    order = MagicMock(id=7, status="IN_PROGRESS")
    complete_in = SimpleNamespace(
        overall_result="PASSED",
        conclusion="终验通过",
        conditions=None,
    )

    with (
        patch.object(order_workflow, "get_or_404", return_value=order),
        patch.object(order_workflow, "validate_completion_rules"),
        patch.object(order_workflow, "read_acceptance_order", return_value=order),
        patch(
            "app.services.acceptance_completion_service.validate_required_check_items"
        ),
        patch(
            "app.services.acceptance_completion_service.update_acceptance_order_status"
        ),
        patch(
            "app.services.acceptance_completion_service.trigger_invoice_on_acceptance"
        ),
        patch(
            "app.services.acceptance_completion_service.handle_acceptance_status_transition"
        ),
        patch(
            "app.services.acceptance_completion_service.handle_progress_integration"
        ),
        patch(
            "app.services.acceptance_completion_service.check_auto_stage_transition_after_acceptance"
        ),
        patch(
            "app.services.acceptance_completion_service.trigger_warranty_period"
        ),
        patch(
            "app.services.acceptance_completion_service.trigger_bonus_calculation"
        ),
        patch(
            "app.services.acceptance_completion_service.trigger_after_sales_maintenance_plan"
        ) as mocked_after_sales,
    ):
        order_workflow.complete_acceptance(
            db=MagicMock(),
            order_id=7,
            complete_in=complete_in,
            auto_trigger_invoice=True,
            current_user=MagicMock(),
        )

    mocked_after_sales.assert_called_once_with(ANY, order, "PASSED")
