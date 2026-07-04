# -*- coding: utf-8 -*-
"""AS-18: after-sales field services must create and sync dispatch orders."""

from datetime import date

from app.api.v1.endpoints import after_sales
from app.models.after_sales import AfterSalesFieldService
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.project import Customer, Project
from app.models.user import User


def _seed_project(db_session):
    admin = User(
        username="as18-admin",
        password_hash="x",
        real_name="AS18 Admin",
        is_active=True,
        is_superuser=True,
    )
    engineer = User(
        username="as18-engineer",
        password_hash="x",
        real_name="AS18 Engineer",
        is_active=True,
        is_superuser=False,
    )
    customer = Customer(customer_code="AS18-CUST", customer_name="AS18 客户")
    db_session.add_all([admin, engineer, customer])
    db_session.flush()
    project = Project(
        project_code="AS18-PROJ",
        project_name="AS18 项目",
        customer_id=customer.id,
        pm_id=admin.id,
    )
    db_session.add(project)
    db_session.commit()
    return admin, engineer, project


def test_create_field_service_creates_dispatch_order_and_real_warranty_flag(
    db_session,
    monkeypatch,
):
    admin, engineer, project = _seed_project(db_session)
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)

    result = after_sales.create_field_service(
        project_id=project.id,
        service_type="REPAIR",
        service_content="现场维修主轴",
        planned_date=date(2026, 7, 4),
        engineer_id=engineer.id,
        engineer_name=engineer.real_name,
        db=db_session,
        current_user=admin,
    )

    service = db_session.get(AfterSalesFieldService, result["id"])
    dispatch = db_session.get(InstallationDispatchOrder, result["dispatch_order_id"])

    assert service.dispatch_order_id == dispatch.id
    assert service.is_warranty is False
    assert dispatch.project_id == project.id
    assert dispatch.customer_id == project.customer_id
    assert dispatch.task_type == "REPAIR"
    assert dispatch.task_description == "现场维修主轴"
    assert dispatch.assigned_to_id == engineer.id
    assert dispatch.status == "ASSIGNED"


def test_field_service_status_update_syncs_dispatch_order(db_session, monkeypatch):
    admin, engineer, project = _seed_project(db_session)
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)
    created = after_sales.create_field_service(
        project_id=project.id,
        service_type="REPAIR",
        service_content="现场维修传感器",
        planned_date=date(2026, 7, 4),
        engineer_id=engineer.id,
        engineer_name=engineer.real_name,
        db=db_session,
        current_user=admin,
    )

    started = after_sales.update_field_service_status(
        project_id=project.id,
        service_id=created["id"],
        service_status="IN_PROGRESS",
        db=db_session,
        current_user=admin,
    )
    completed = after_sales.update_field_service_status(
        project_id=project.id,
        service_id=created["id"],
        service_status="COMPLETED",
        actual_date=date(2026, 7, 5),
        service_hours=6,
        report_content="已完成现场维修",
        db=db_session,
        current_user=admin,
    )

    service = db_session.get(AfterSalesFieldService, created["id"])
    dispatch = db_session.get(InstallationDispatchOrder, service.dispatch_order_id)

    assert started["status"] == "IN_PROGRESS"
    assert completed["status"] == "COMPLETED"
    assert service.actual_date == date(2026, 7, 5)
    assert service.service_hours == 6
    assert dispatch.status == "COMPLETED"
    assert dispatch.progress == 100
    assert float(dispatch.actual_hours) == 6.0
