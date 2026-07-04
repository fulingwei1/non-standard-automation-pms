# -*- coding: utf-8 -*-
"""PROJ-23: final acceptance handover must create real after-sales records."""

from datetime import date
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.after_sales import AfterSalesMaintenance, AfterSalesWarranty
from app.models.project import Customer, Machine, Project
from app.services.project_data_flow_service import ProjectDataFlowService, _add_months


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def _seed_project_for_handover(
    db: Session,
    *,
    warranty_months: int | None = 18,
) -> tuple[Customer, Project, Machine]:
    customer = Customer(
        customer_code=_unique("CUST-PROJ23"),
        customer_name="PROJ-23 售后移交客户",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=_unique("PJ-PROJ23"),
        project_name="PROJ-23 售后移交项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S9",
        status="ST30",
        actual_end_date=date(2026, 7, 1),
        warranty_period_months=warranty_months,
    )
    db.add(project)
    db.flush()

    machine = Machine(
        project_id=project.id,
        machine_code=_unique("M-PROJ23"),
        machine_name="PROJ-23 售后移交机台",
    )
    db.add(machine)
    db.commit()
    return customer, project, machine


def test_transfer_to_after_sales_creates_warranty_and_backfills_project_machine(
    db_session: Session,
):
    customer, project, machine = _seed_project_for_handover(db_session)

    result = ProjectDataFlowService(db_session).transfer_to_after_sales(project.id)

    warranty = (
        db_session.query(AfterSalesWarranty)
        .filter(AfterSalesWarranty.project_id == project.id)
        .one()
    )
    maintenance_count = (
        db_session.query(AfterSalesMaintenance)
        .filter(AfterSalesMaintenance.project_id == project.id)
        .count()
    )

    db_session.refresh(project)
    db_session.refresh(machine)

    assert result["warranty_created"] is True
    assert result["warranty_id"] == warranty.id
    assert result["maintenance_created"] == 4
    assert maintenance_count == 4
    assert warranty.customer_id == customer.id
    assert warranty.status == "ACTIVE"
    assert warranty.warranty_months == 18
    assert warranty.warranty_start == date(2026, 7, 1)
    assert warranty.warranty_end == _add_months(date(2026, 7, 1), 18)
    assert project.warranty_start_date == warranty.warranty_start
    assert project.warranty_end_date == warranty.warranty_end
    assert machine.customer_id == customer.id
    assert "2026-07-01" in (machine.warranty or "")


def test_transfer_to_after_sales_is_idempotent(db_session: Session):
    _, project, _ = _seed_project_for_handover(db_session, warranty_months=None)
    service = ProjectDataFlowService(db_session)

    first = service.transfer_to_after_sales(project.id)
    second = service.transfer_to_after_sales(project.id)

    warranty_count = (
        db_session.query(AfterSalesWarranty)
        .filter(AfterSalesWarranty.project_id == project.id)
        .count()
    )
    maintenance_count = (
        db_session.query(AfterSalesMaintenance)
        .filter(AfterSalesMaintenance.project_id == project.id)
        .count()
    )

    assert first["warranty_created"] is True
    assert second["warranty_created"] is False
    assert warranty_count == 1
    assert maintenance_count == 4
    assert second["skipped_existing"] == 4
