# -*- coding: utf-8 -*-
"""AS-20: after-sales warranty status must use project warranty sources."""

from datetime import date
from decimal import Decimal

from app.api.v1.endpoints import after_sales
from app.models.after_sales import AfterSalesFieldService
from app.models.project import Customer, Project, ProjectWarranty
from app.models.user import User


def _seed_project(db_session):
    admin = User(
        username="as20-admin",
        password_hash="x",
        real_name="AS20 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS20-CUST", customer_name="AS20 客户")
    db_session.add_all([admin, customer])
    db_session.flush()
    project = Project(
        project_code="AS20-PROJ",
        project_name="AS20 项目",
        customer_id=customer.id,
        pm_id=admin.id,
    )
    db_session.add(project)
    db_session.flush()
    return admin, project


def test_field_service_uses_project_warranty_when_after_sales_warranty_missing(
    db_session,
    monkeypatch,
):
    admin, project = _seed_project(db_session)
    db_session.add(
        ProjectWarranty(
            project_id=project.id,
            warranty_start_date=date(2026, 1, 1),
            warranty_end_date=date(2026, 12, 31),
            warranty_period_months=12,
            warranty_status="ACTIVE",
        )
    )
    db_session.commit()
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)

    result = after_sales.create_field_service(
        project_id=project.id,
        service_type="REPAIR",
        service_content="现场维修",
        planned_date=date(2026, 7, 4),
        db=db_session,
        current_user=admin,
    )

    service = db_session.get(AfterSalesFieldService, result["id"])

    assert result["is_warranty"] is True
    assert result["warranty_source"] == "project_warranty"
    assert service.is_warranty is True


def test_warranty_endpoint_exposes_project_warranty_source(db_session):
    admin, project = _seed_project(db_session)
    db_session.add(
        ProjectWarranty(
            project_id=project.id,
            warranty_start_date=date(2026, 1, 1),
            warranty_end_date=date(2026, 12, 31),
            warranty_period_months=12,
            warranty_status="ACTIVE",
        )
    )
    db_session.commit()

    result = after_sales.get_warranty(
        project_id=project.id,
        db=db_session,
        current_user=admin,
    )

    assert result[0]["source"] == "project_warranty"
    assert result[0]["is_under_warranty"] is True
    assert result[0]["charge_required"] is False


def test_out_of_warranty_field_service_records_billable_fee(
    db_session,
    monkeypatch,
):
    admin, project = _seed_project(db_session)
    project.warranty_start_date = date(2025, 1, 1)
    project.warranty_end_date = date(2025, 12, 31)
    db_session.commit()
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)

    result = after_sales.create_field_service(
        project_id=project.id,
        service_type="REPAIR",
        service_content="过保维修",
        planned_date=date(2026, 7, 4),
        service_fee=Decimal("300.00"),
        travel_cost=Decimal("50.00"),
        db=db_session,
        current_user=admin,
    )

    service = db_session.get(AfterSalesFieldService, result["id"])

    assert result["is_warranty"] is False
    assert result["charge_required"] is True
    assert result["warranty_source"] == "project_core"
    assert service.is_warranty is False
    assert service.service_fee == Decimal("300.00")
    assert service.travel_cost == Decimal("50.00")
    assert service.total_cost == Decimal("350.00")
