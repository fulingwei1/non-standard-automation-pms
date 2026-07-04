# -*- coding: utf-8 -*-
"""AS-08: after-sales spare parts must be real inventory movements."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Numeric

from app.api.v1.endpoints import after_sales
from app.models.after_sales import AfterSalesFieldService, AfterSalesSparePart
from app.models.project import Customer, Project
from app.models.user import User
from app.models.warehouse import Inventory


def _seed_project(db_session):
    user = User(
        username="as08-admin",
        password_hash="x",
        real_name="AS08 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS08-CUST", customer_name="AS08 客户")
    db_session.add_all([user, customer])
    db_session.flush()
    project = Project(
        project_code="AS08-PROJ",
        project_name="AS08 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.commit()
    return user, project


def test_spare_part_cost_columns_are_numeric():
    assert isinstance(AfterSalesSparePart.__table__.c.unit_price.type, Numeric)
    assert isinstance(AfterSalesFieldService.__table__.c.parts_cost.type, Numeric)


def test_spare_part_create_syncs_project_inventory(db_session, monkeypatch):
    user, project = _seed_project(db_session)
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)

    result = after_sales.create_spare_part(
        project_id=project.id,
        part_no="AS08-PART-001",
        part_name="伺服驱动器",
        part_spec="DRV-01",
        quantity=5,
        min_stock=2,
        unit_price=Decimal("120.50"),
        supplier="AS08 供应商",
        db=db_session,
        current_user=user,
    )

    inventory = (
        db_session.query(Inventory)
        .filter(Inventory.material_code == result["part_no"])
        .one()
    )
    assert inventory.quantity == Decimal("5.00")
    assert inventory.available_quantity == Decimal("5.00")
    assert inventory.min_stock == Decimal("2.00")


def test_spare_part_issue_deducts_inventory_and_field_service_cost(
    db_session,
    monkeypatch,
):
    user, project = _seed_project(db_session)
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)

    created = after_sales.create_spare_part(
        project_id=project.id,
        part_no="AS08-PART-002",
        part_name="传感器",
        part_spec="SEN-02",
        quantity=5,
        min_stock=4,
        unit_price=Decimal("30.00"),
        supplier="AS08 供应商",
        db=db_session,
        current_user=user,
    )
    field_service = AfterSalesFieldService(
        project_id=project.id,
        service_no="AS08-FS-001",
        service_type="REPAIR",
        service_content="现场更换传感器",
        planned_date=date(2026, 7, 4),
        status="IN_PROGRESS",
        parts_cost=Decimal("0.00"),
    )
    db_session.add(field_service)
    db_session.commit()

    result = after_sales.issue_spare_part(
        project_id=project.id,
        part_id=created["id"],
        quantity=2,
        field_service_id=field_service.id,
        db=db_session,
        current_user=user,
    )

    part = db_session.get(AfterSalesSparePart, created["id"])
    inventory = (
        db_session.query(Inventory)
        .filter(Inventory.material_code == created["part_no"])
        .one()
    )
    db_session.refresh(field_service)

    assert result["quantity"] == 3
    assert result["inventory_available_quantity"] == 3.0
    assert part.quantity == 3
    assert part.status == "LOW_STOCK"
    assert inventory.available_quantity == Decimal("3.00")
    assert field_service.parts_cost == Decimal("60.00")
