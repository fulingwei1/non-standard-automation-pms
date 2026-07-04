# -*- coding: utf-8 -*-
"""PROD-24: outsourcing actual cost follows qualified inspection quantity."""

from decimal import Decimal

from app.models.outsourcing import OutsourcingOrder, OutsourcingOrderItem
from app.models.project import Project, ProjectCost
from app.models.vendor import Vendor
from app.services.cost.cost_collection_service import CostCollectionService


def _seed_outsourcing_order(
    db_session,
    *,
    quantity: Decimal = Decimal("10"),
    qualified_quantity: Decimal = Decimal("0"),
    unit_price: Decimal = Decimal("100"),
    total_amount: Decimal = Decimal("1000"),
    tax_amount: Decimal = Decimal("130"),
):
    vendor = Vendor(
        supplier_code="OS-COST-P24",
        supplier_name="PROD-24 外协商",
        vendor_type="OUTSOURCING",
        status="ACTIVE",
    )
    project = Project(
        project_code="PJ-OS-COST-P24",
        project_name="PROD-24 外协成本项目",
        actual_cost=Decimal("0"),
    )
    db_session.add_all([vendor, project])
    db_session.flush()

    order = OutsourcingOrder(
        order_no="OS-COST-P24",
        vendor_id=vendor.id,
        project_id=project.id,
        order_type="MACHINING",
        order_title="外协加工成本",
        total_amount=total_amount,
        tax_amount=tax_amount,
        status="APPROVED",
    )
    db_session.add(order)
    db_session.flush()

    item = OutsourcingOrderItem(
        order_id=order.id,
        item_no=1,
        material_code="MAT-OS-COST",
        material_name="外协加工件",
        quantity=quantity,
        unit_price=unit_price,
        amount=total_amount,
        qualified_quantity=qualified_quantity,
        rejected_quantity=quantity - qualified_quantity,
    )
    db_session.add(item)
    db_session.commit()
    return project, order, item


def test_outsourcing_cost_collection_uses_qualified_quantity_ratio(
    monkeypatch,
    db_session,
):
    project, order, _item = _seed_outsourcing_order(
        db_session,
        quantity=Decimal("10"),
        qualified_quantity=Decimal("6"),
        unit_price=Decimal("100"),
        total_amount=Decimal("1000"),
        tax_amount=Decimal("130"),
    )
    monkeypatch.setattr(CostCollectionService, "_check_budget_alert", lambda *args, **kwargs: None)

    cost = CostCollectionService.collect_from_outsourcing_order(db_session, order.id, created_by=7)
    db_session.flush()

    assert cost is not None
    assert cost.amount == Decimal("600.00")
    assert cost.tax_amount == Decimal("78.00")
    assert "合格数量：6.0000/10.0000" in cost.description
    db_session.refresh(project)
    assert project.actual_cost == Decimal("600.00")


def test_outsourcing_cost_collection_removes_existing_cost_when_no_qualified_quantity(
    monkeypatch,
    db_session,
):
    project, order, _item = _seed_outsourcing_order(
        db_session,
        quantity=Decimal("10"),
        qualified_quantity=Decimal("0"),
        total_amount=Decimal("1000"),
        tax_amount=Decimal("130"),
    )
    old_cost = ProjectCost(
        project_id=project.id,
        cost_type="OUTSOURCING",
        cost_category="OUTSOURCING",
        cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
        source_module="OUTSOURCING",
        source_type="OUTSOURCING_ORDER",
        source_id=order.id,
        source_no=order.order_no,
        amount=Decimal("1000"),
        tax_amount=Decimal("130"),
    )
    project.actual_cost = Decimal("1000")
    db_session.add(old_cost)
    db_session.commit()
    monkeypatch.setattr(CostCollectionService, "_check_budget_alert", lambda *args, **kwargs: None)

    cost = CostCollectionService.collect_from_outsourcing_order(db_session, order.id, created_by=7)
    db_session.flush()

    assert cost is None
    assert (
        db_session.query(ProjectCost)
        .filter(ProjectCost.source_module == "OUTSOURCING", ProjectCost.source_id == order.id)
        .count()
        == 0
    )
    db_session.refresh(project)
    assert project.actual_cost == Decimal("0.00")
