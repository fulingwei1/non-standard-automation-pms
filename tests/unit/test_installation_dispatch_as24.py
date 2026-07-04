# -*- coding: utf-8 -*-
"""AS-24: installation dispatch must sync scheduling occupancy and timesheets."""

from datetime import date, datetime
from decimal import Decimal

from app.api.v1.endpoints.installation_dispatch.workflow import (
    assign_installation_dispatch_order,
    complete_installation_dispatch_order,
    start_installation_dispatch_order,
)
from app.models.engineer_capacity import EngineerTaskAssignment
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.project import Customer, Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.installation_dispatch import (
    InstallationDispatchOrderAssign,
    InstallationDispatchOrderComplete,
    InstallationDispatchOrderStart,
)


def _seed_dispatch_order(db_session):
    engineer = User(
        username="as24-engineer",
        password_hash="x",
        real_name="AS24 Engineer",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS24-CUST", customer_name="AS24 客户")
    db_session.add_all([engineer, customer])
    db_session.flush()
    project = Project(
        project_code="AS24-PROJ",
        project_name="AS24 项目",
        customer_id=customer.id,
        pm_id=engineer.id,
    )
    db_session.add(project)
    db_session.flush()
    order = InstallationDispatchOrder(
        order_no="AS24-DISPATCH",
        project_id=project.id,
        customer_id=customer.id,
        task_type="DEBUGGING",
        task_title="AS24 现场调试",
        task_description="现场调试设备",
        scheduled_date=date(2026, 7, 4),
        estimated_hours=Decimal("8.00"),
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()
    return engineer, project, order


def test_dispatch_start_syncs_engineer_assignment_status(db_session):
    engineer, _project, order = _seed_dispatch_order(db_session)
    assign_installation_dispatch_order(
        db=db_session,
        order_id=order.id,
        assign_in=InstallationDispatchOrderAssign(assigned_to_id=engineer.id),
        current_user=engineer,
    )

    start_installation_dispatch_order(
        db=db_session,
        order_id=order.id,
        start_in=InstallationDispatchOrderStart(start_time=datetime(2026, 7, 4, 9, 0)),
        current_user=engineer,
    )

    assignment = (
        db_session.query(EngineerTaskAssignment)
        .filter(EngineerTaskAssignment.assignment_no == f"IDISPATCH-{order.id}")
        .one()
    )

    assert assignment.status == "IN_PROGRESS"
    assert assignment.actual_start_date == date(2026, 7, 4)


def test_dispatch_complete_syncs_assignment_and_creates_timesheet(db_session):
    engineer, project, order = _seed_dispatch_order(db_session)
    assign_installation_dispatch_order(
        db=db_session,
        order_id=order.id,
        assign_in=InstallationDispatchOrderAssign(assigned_to_id=engineer.id),
        current_user=engineer,
    )
    start_installation_dispatch_order(
        db=db_session,
        order_id=order.id,
        start_in=InstallationDispatchOrderStart(start_time=datetime(2026, 7, 4, 9, 0)),
        current_user=engineer,
    )

    complete_installation_dispatch_order(
        db=db_session,
        order_id=order.id,
        complete_in=InstallationDispatchOrderComplete(
            end_time=datetime(2026, 7, 4, 16, 30),
            actual_hours=Decimal("6.50"),
            execution_notes="完成调试",
        ),
        current_user=engineer,
    )

    assignment = (
        db_session.query(EngineerTaskAssignment)
        .filter(EngineerTaskAssignment.assignment_no == f"IDISPATCH-{order.id}")
        .one()
    )
    timesheet = (
        db_session.query(Timesheet)
        .filter(Timesheet.assign_id == assignment.id, Timesheet.task_id == order.id)
        .one()
    )

    assert assignment.status == "COMPLETED"
    assert assignment.actual_hours == 6.5
    assert assignment.actual_end_date == date(2026, 7, 4)
    db_session.refresh(order)
    assert order.service_record_id is not None
    assert timesheet.user_id == engineer.id
    assert timesheet.project_id == project.id
    assert timesheet.work_date == date(2026, 7, 4)
    assert timesheet.hours == Decimal("6.50")
    assert timesheet.status == "DRAFT"
