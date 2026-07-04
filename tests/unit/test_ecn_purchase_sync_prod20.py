# -*- coding: utf-8 -*-
"""PROD-20: ECN purchase impact propagation."""

from decimal import Decimal

from app.models.ecn import Ecn, EcnAffectedMaterial, EcnAffectedOrder
from app.models.material import Material
from app.models.project import Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.vendor import Vendor
from app.services.ecn.integration.ecn_integration_service import EcnIntegrationService


def _seed_purchase_impact_chain(db_session):
    vendor = Vendor(
        supplier_code="ECN-SUP-001",
        supplier_name="ECN供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
    )
    project = Project(project_code="ECN-PROJ-001", project_name="ECN项目")
    material = Material(
        material_code="MAT-ECN-001",
        material_name="ECN影响物料",
        specification="旧规格",
        source_type="PURCHASE",
    )
    db_session.add_all([vendor, project, material])
    db_session.flush()

    purchase_order = PurchaseOrder(
        order_no="PO-ECN-001",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="ECN测试采购单",
        status="APPROVED",
    )
    db_session.add(purchase_order)
    db_session.flush()
    purchase_item = PurchaseOrderItem(
        order_id=purchase_order.id,
        item_no=1,
        material_id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        specification=material.specification,
        quantity=Decimal("10"),
        unit_price=Decimal("100"),
        amount=Decimal("1000"),
    )
    db_session.add(purchase_item)

    ecn = Ecn(
        ecn_no="ECN-PO-001",
        ecn_title="采购影响ECN",
        ecn_type="MATERIAL_CHANGE",
        project_id=project.id,
        change_reason="客户变更",
        change_description="物料规格调整",
        status="APPROVED",
    )
    db_session.add(ecn)
    db_session.flush()
    affected_material = EcnAffectedMaterial(
        ecn_id=ecn.id,
        material_id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        specification=material.specification,
        change_type="UPDATE",
        old_quantity=Decimal("10"),
        new_quantity=Decimal("12"),
        old_specification="旧规格",
        new_specification="新规格",
        cost_impact=Decimal("200"),
        status="PENDING",
    )
    db_session.add(affected_material)
    db_session.commit()
    return ecn, purchase_order, purchase_item, affected_material


def test_sync_to_purchase_auto_creates_affected_purchase_order(db_session):
    ecn, purchase_order, _purchase_item, _affected_material = _seed_purchase_impact_chain(
        db_session
    )

    result = EcnIntegrationService(db_session).sync_to_purchase(
        ecn.id, current_user_id=7
    )

    affected_order = (
        db_session.query(EcnAffectedOrder)
        .filter_by(ecn_id=ecn.id, order_type="PURCHASE", order_id=purchase_order.id)
        .one()
    )
    assert result["created_count"] == 1
    assert result["change_required_count"] == 1
    assert affected_order.order_no == purchase_order.order_no
    assert affected_order.action_type == "MODIFY"
    assert affected_order.status == "CHANGE_REQUIRED"
    assert "MAT-ECN-001" in affected_order.impact_description


def test_sync_to_purchase_modify_records_review_action_without_closing_order(db_session):
    ecn, purchase_order, _purchase_item, _affected_material = _seed_purchase_impact_chain(
        db_session
    )
    affected_order = EcnAffectedOrder(
        ecn_id=ecn.id,
        order_type="PURCHASE",
        order_id=purchase_order.id,
        order_no=purchase_order.order_no,
        impact_description="物料规格调整影响采购单",
        action_type="MODIFY",
        status="PENDING",
    )
    db_session.add(affected_order)
    db_session.commit()

    result = EcnIntegrationService(db_session).sync_to_purchase(
        ecn.id, current_user_id=9
    )

    db_session.refresh(purchase_order)
    db_session.refresh(affected_order)
    assert result["updated_count"] == 1
    assert result["change_required_count"] == 1
    assert purchase_order.status == "APPROVED"
    assert "ECN-PO-001" in purchase_order.remark
    assert affected_order.status == "CHANGE_REQUIRED"
    assert affected_order.processed_by == 9
    assert affected_order.action_description
    assert "采购需评审" in affected_order.action_description
