# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal
import uuid
from unittest.mock import patch

from app.models.ecn import Ecn
from app.models.material import BomHeader, BomItem
from app.models.production.worker import Worker
from app.models.production.work_order import WorkOrder
from app.models.project import Customer, Project, ProjectCost
from app.models.purchase import GoodsReceipt, PurchaseOrder, PurchaseOrderItem
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.vendor import Vendor
from app.api.v1.endpoints.purchase.receipts import cancel_goods_receipt, create_goods_receipt
from app.api.v1.endpoints.finance_reports import _project_cost_total
from app.api.v1.endpoints.settlements import _project_cost_totals
from app.services.budget_analysis_service import BudgetAnalysisService
from app.services.cost.cost_collection_service import CostCollectionService
from app.services.cost.cost_service import CostService


def _suffix() -> str:
    return uuid.uuid4().hex[:8]


def test_collect_project_costs_from_business_documents(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COST-{suffix}",
        customer_name="成本采集测试客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COST-{suffix}",
        supplier_name="成本采集测试供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COST-{suffix}",
        project_name="业务单据成本采集项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        budget_amount=Decimal("3000.00"),
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    worker = Worker(
        worker_no=f"W-COST-{suffix}",
        worker_name="成本采集工人",
        hourly_rate=Decimal("200.00"),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(worker)
    db_session.flush()

    purchase_order = PurchaseOrder(
        order_no=f"PO-COST-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="项目材料采购",
        total_amount=Decimal("1000.00"),
        tax_amount=Decimal("130.00"),
        order_date=date(2026, 6, 1),
        status="RECEIVED",
        created_by=admin.id,
    )
    bom = BomHeader(
        bom_no=f"BOM-COST-{suffix}",
        bom_name="项目发布BOM",
        project_id=project.id,
        status="RELEASED",
        total_amount=Decimal("0"),
        created_by=admin.id,
    )
    work_order = WorkOrder(
        work_order_no=f"WO-COST-{suffix}",
        task_name="项目装配调试",
        task_type="ASSEMBLY",
        project_id=project.id,
        status="COMPLETED",
        actual_hours=Decimal("2.50"),
        standard_hours=Decimal("3.00"),
        plan_end_date=date(2026, 6, 3),
        assigned_to=worker.id,
        created_by=admin.id,
    )
    timesheet = Timesheet(
        timesheet_no=f"TS-COST-{suffix}",
        user_id=admin.id,
        user_name=admin.real_name,
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        work_date=date(2026, 6, 4),
        hours=Decimal("3.00"),
        status="APPROVED",
        work_content="项目现场调试",
        created_by=admin.id,
    )
    db_session.add_all([purchase_order, bom, work_order, timesheet])
    db_session.flush()

    db_session.add_all(
        [
            BomItem(
                bom_id=bom.id,
                item_no=1,
                material_code=f"MAT-A-{suffix}",
                material_name="电气件A",
                quantity=Decimal("2"),
                unit_price=Decimal("150.00"),
                amount=Decimal("300.00"),
            ),
            BomItem(
                bom_id=bom.id,
                item_no=2,
                material_code=f"MAT-B-{suffix}",
                material_name="机构件B",
                quantity=Decimal("1"),
                unit_price=Decimal("200.00"),
                amount=Decimal("200.00"),
            ),
        ]
    )
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ):
        result = CostCollectionService.collect_project_costs(
            db_session, project_id=project.id, created_by=admin.id
        )
        db_session.flush()

        costs = (
            db_session.query(ProjectCost)
            .filter(ProjectCost.project_id == project.id)
            .order_by(ProjectCost.source_type)
            .all()
        )

        assert result["total_collected"] == 4
        assert result["total_amount"] == 2300.0
        assert {(cost.source_module, cost.source_type) for cost in costs} == {
            ("PURCHASE", "PURCHASE_ORDER"),
            ("BOM", "BOM_COST"),
            ("PRODUCTION", "WORK_ORDER"),
            ("TIMESHEET", "LABOR_COST"),
        }
        assert {cost.source_type: cost.cost_basis for cost in costs} == {
            "PURCHASE_ORDER": "ACTUAL",
            "BOM_COST": "PLAN",
            "WORK_ORDER": "ACTUAL",
            "LABOR_COST": "ACTUAL",
        }
        assert {cost.source_type: cost.amount for cost in costs} == {
            "PURCHASE_ORDER": Decimal("1000.00"),
            "BOM_COST": Decimal("500.00"),
            "WORK_ORDER": Decimal("500.00"),
            "LABOR_COST": Decimal("300.00"),
        }

        db_session.refresh(project)
        assert project.actual_cost == Decimal("1800.00")
        assert (
            CostService(db_session).get_cost_breakdown(project.id)["total_cost"]
            == 1800.0
        )
        assert (
            BudgetAnalysisService.get_budget_execution_analysis(db_session, project.id)[
                "actual_cost"
            ]
            == 1800.0
        )
        assert _project_cost_total(project) == 1800.0
        settlement_costs = _project_cost_totals(
            db_session, project.id, project.actual_cost
        )
        assert sum(settlement_costs.values()) == 1800.0

        CostCollectionService.collect_project_costs(
            db_session, project_id=project.id, created_by=admin.id
        )
        db_session.flush()

        assert (
            db_session.query(ProjectCost)
            .filter(ProjectCost.project_id == project.id)
            .count()
            == 4
        )

        assert (
            CostCollectionService.remove_cost_from_source(
                db_session, "BOM", "BOM_COST", bom.id
            )
            is True
        )
        db_session.flush()
        db_session.refresh(project)
        assert project.actual_cost == Decimal("1800.00")


def test_purchase_cost_uses_received_amount_and_receipt_date(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COST-RECEIPT-{suffix}",
        customer_name="采购收货成本客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COST-RECEIPT-{suffix}",
        supplier_name="采购收货成本供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COST-RECEIPT-{suffix}",
        project_name="采购收货成本项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    order = PurchaseOrder(
        order_no=f"PO-COST-RECEIPT-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="部分收货采购",
        total_amount=Decimal("1000.00"),
        received_amount=Decimal("400.00"),
        tax_amount=Decimal("52.00"),
        order_date=date(2026, 6, 1),
        status="RECEIVED",
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()
    receipt = GoodsReceipt(
        receipt_no=f"GR-COST-{suffix}",
        order_id=order.id,
        supplier_id=vendor.id,
        receipt_date=date(2026, 6, 15),
        status="RECEIVED",
        created_by=admin.id,
    )
    db_session.add(receipt)
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ):
        cost = CostCollectionService.collect_from_purchase_order(
            db_session, order.id, created_by=admin.id
        )
        db_session.flush()

    assert cost.amount == Decimal("400.00")
    assert cost.cost_date == date(2026, 6, 15)
    db_session.refresh(project)
    assert project.actual_cost == Decimal("400.00")


def test_purchase_cost_collection_uses_rich_budget_alert_service(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COST-ALERT-{suffix}",
        customer_name="成本预警客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COST-ALERT-{suffix}",
        supplier_name="成本预警供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COST-ALERT-{suffix}",
        project_name="成本预警项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        budget_amount=Decimal("100.00"),
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    order = PurchaseOrder(
        order_no=f"PO-COST-ALERT-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="触发富版预算预警",
        total_amount=Decimal("150.00"),
        received_amount=Decimal("150.00"),
        order_date=date(2026, 6, 1),
        status="RECEIVED",
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ) as mock_alert:
        CostCollectionService.collect_from_purchase_order(
            db_session, order.id, created_by=admin.id
        )
        db_session.flush()

    mock_alert.assert_called_once_with(
        project_id=project.id,
        trigger_source="PURCHASE",
        source_id=order.id,
    )


def test_create_goods_receipt_collects_received_purchase_cost(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COST-RCPT-HOOK-{suffix}",
        customer_name="收货实时归集客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COST-RCPT-HOOK-{suffix}",
        supplier_name="收货实时归集供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COST-RCPT-HOOK-{suffix}",
        project_name="收货实时归集项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    order = PurchaseOrder(
        order_no=f"PO-COST-RCPT-HOOK-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="收货实时归集采购",
        total_amount=Decimal("50.00"),
        tax_amount=Decimal("6.50"),
        order_date=date(2026, 6, 1),
        status="APPROVED",
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()

    order_item = PurchaseOrderItem(
        order_id=order.id,
        item_no=1,
        material_code=f"MAT-RCPT-HOOK-{suffix}",
        material_name="收货归集物料",
        unit="件",
        quantity=Decimal("5.0000"),
        unit_price=Decimal("10.0000"),
        amount=Decimal("50.00"),
    )
    db_session.add(order_item)
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ):
        response = create_goods_receipt(
            {
                "order_id": order.id,
                "receipt_date": "2026-06-20",
                "receipt_type": "NORMAL",
                "items": [
                    {
                        "order_item_id": order_item.id,
                        "delivery_qty": "2",
                        "received_qty": "2",
                    }
                ],
            },
            db=db_session,
            current_user=admin,
        )

    assert response.code == 200
    db_session.expire_all()
    db_order = db_session.get(PurchaseOrder, order.id)
    db_project = db_session.get(Project, project.id)
    cost = (
        db_session.query(ProjectCost)
        .filter(
            ProjectCost.project_id == project.id,
            ProjectCost.source_module == "PURCHASE",
            ProjectCost.source_type == "PURCHASE_ORDER",
            ProjectCost.source_id == order.id,
        )
        .one()
    )
    assert db_order.received_amount == Decimal("20.00")
    assert db_order.status == "PARTIAL_RECEIVED"
    assert db_project.actual_cost == Decimal("20.00")
    assert cost.amount == Decimal("20.00")
    assert cost.cost_date == date(2026, 6, 20)


def test_cancel_goods_receipt_reverses_purchase_cost(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COST-RCPT-CANCEL-{suffix}",
        customer_name="收货作废冲减客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COST-RCPT-CANCEL-{suffix}",
        supplier_name="收货作废冲减供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COST-RCPT-CANCEL-{suffix}",
        project_name="收货作废冲减项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    order = PurchaseOrder(
        order_no=f"PO-COST-RCPT-CANCEL-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="收货后作废采购",
        total_amount=Decimal("50.00"),
        tax_amount=Decimal("6.50"),
        order_date=date(2026, 6, 1),
        status="APPROVED",
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()

    order_item = PurchaseOrderItem(
        order_id=order.id,
        item_no=1,
        material_code=f"MAT-RCPT-CANCEL-{suffix}",
        material_name="作废冲减物料",
        unit="件",
        quantity=Decimal("5.0000"),
        unit_price=Decimal("10.0000"),
        amount=Decimal("50.00"),
    )
    db_session.add(order_item)
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ):
        receipt_response = create_goods_receipt(
            {
                "order_id": order.id,
                "receipt_date": "2026-06-20",
                "items": [
                    {
                        "order_item_id": order_item.id,
                        "delivery_qty": "2",
                        "received_qty": "2",
                    }
                ],
            },
            db=db_session,
            current_user=admin,
        )
        cancel_response = cancel_goods_receipt(
            receipt_response.data["id"],
            {"reason": "供应商送错料"},
            db=db_session,
            current_user=admin,
        )

    assert cancel_response.code == 200
    db_session.expire_all()
    db_order = db_session.get(PurchaseOrder, order.id)
    db_project = db_session.get(Project, project.id)
    db_receipt = db_session.get(GoodsReceipt, receipt_response.data["id"])
    assert db_receipt.status == "CANCELLED"
    assert db_order.received_amount == Decimal("0.00")
    assert db_order.status == "APPROVED"
    assert db_project.actual_cost == Decimal("0.00")
    assert (
        db_session.query(ProjectCost)
        .filter(
            ProjectCost.project_id == project.id,
            ProjectCost.source_type == "PURCHASE_ORDER",
            ProjectCost.source_id == order.id,
        )
        .count()
        == 0
    )


def test_collect_project_costs_includes_partial_received_purchase_order(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COST-PARTIAL-{suffix}",
        customer_name="部分收货成本客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COST-PARTIAL-{suffix}",
        supplier_name="部分收货成本供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COST-PARTIAL-{suffix}",
        project_name="部分收货成本项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    order = PurchaseOrder(
        order_no=f"PO-COST-PARTIAL-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="部分收货扫描采购",
        total_amount=Decimal("50.00"),
        received_amount=Decimal("20.00"),
        tax_amount=Decimal("6.50"),
        order_date=date(2026, 6, 1),
        status="PARTIAL_RECEIVED",
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ):
        result = CostCollectionService.collect_project_costs(
            db_session, project_id=project.id, created_by=admin.id
        )
        db_session.flush()

    assert result["total_collected"] == 1
    assert result["total_amount"] == 20.0
    db_session.refresh(project)
    assert project.actual_cost == Decimal("20.00")


def test_negative_ecn_cost_impact_reduces_project_actual_cost(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    project = Project(
        project_code=f"PJ-COST-ECN-CREDIT-{suffix}",
        project_name="ECN负向成本冲减项目",
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    db_session.add(
        ProjectCost(
            project_id=project.id,
            cost_type="MATERIAL",
            cost_category="PURCHASE",
            cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
            source_module="PURCHASE",
            source_type="PURCHASE_ORDER",
            source_id=999001,
            source_no=f"PO-BASE-{suffix}",
            amount=Decimal("100.00"),
            cost_date=date(2026, 6, 1),
            created_by=admin.id,
        )
    )
    ecn = Ecn(
        ecn_no=f"ECN-CREDIT-{suffix}",
        ecn_title="供应商补偿冲减",
        project_id=project.id,
        cost_impact=Decimal("-30.00"),
        status="APPROVED",
        created_by=admin.id,
    )
    db_session.add(ecn)
    db_session.flush()

    cost = CostCollectionService.collect_from_ecn(
        db_session, ecn.id, created_by=admin.id, cost_date=date(2026, 6, 30)
    )
    db_session.flush()

    assert cost is not None
    assert cost.amount == Decimal("-30.00")
    assert cost.cost_basis == CostCollectionService.COST_BASIS_ACTUAL
    db_session.refresh(project)
    assert project.actual_cost == Decimal("70.00")


def test_normalize_project_cost_records_repairs_legacy_cost_fields(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    project = Project(
        project_code=f"PJ-COST-NORM-{suffix}",
        project_name="存量成本脏值修复项目",
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    purchase_cost = ProjectCost(
        project_id=project.id,
        source_type="PURCHASE_ORDER",
        source_id=1001,
        source_no=f"PO-NORM-{suffix}",
        amount=Decimal("25.00"),
        cost_date=date(2026, 6, 1),
        created_by=admin.id,
    )
    bom_cost = ProjectCost(
        project_id=project.id,
        source_type="BOM_COST",
        source_id=1002,
        source_no=f"BOM-NORM-{suffix}",
        amount=Decimal("80.00"),
        cost_date=date(2026, 6, 1),
        created_by=admin.id,
    )
    db_session.add_all([purchase_cost, bom_cost])
    db_session.flush()

    result = CostCollectionService.normalize_project_cost_records(
        db_session, project_id=project.id
    )
    db_session.flush()

    assert result["updated"] == 2
    assert purchase_cost.cost_type == "MATERIAL"
    assert purchase_cost.cost_category == "PURCHASE"
    assert purchase_cost.cost_basis == CostCollectionService.COST_BASIS_ACTUAL
    assert bom_cost.cost_type == "MATERIAL"
    assert bom_cost.cost_category == "BOM"
    assert bom_cost.cost_basis == CostCollectionService.COST_BASIS_PLAN
    db_session.refresh(project)
    assert project.actual_cost == Decimal("25.00")


def test_in_progress_work_order_is_not_collected_as_actual_cost(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    project = Project(
        project_code=f"PJ-COST-WIP-{suffix}",
        project_name="在制工单成本项目",
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    work_order = WorkOrder(
        work_order_no=f"WO-COST-WIP-{suffix}",
        task_name="仍在加工工单",
        task_type="ASSEMBLY",
        project_id=project.id,
        status="IN_PROGRESS",
        actual_hours=Decimal("2.00"),
        standard_hours=Decimal("3.00"),
        plan_end_date=date(2026, 6, 3),
        created_by=admin.id,
    )
    db_session.add(work_order)
    db_session.flush()

    assert (
        CostCollectionService.collect_from_work_order(db_session, work_order.id)
        is None
    )
    assert (
        db_session.query(ProjectCost)
        .filter(ProjectCost.project_id == project.id)
        .count()
        == 0
    )


def test_completed_work_order_uses_worker_hourly_rate(db_session):
    suffix = _suffix()
    admin = db_session.query(User).filter(User.username == "admin").first()

    project = Project(
        project_code=f"PJ-COST-WORKER-{suffix}",
        project_name="工人费率成本项目",
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    worker = Worker(
        worker_no=f"W-COST-WORKER-{suffix}",
        worker_name="高费率工人",
        hourly_rate=Decimal("350.00"),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add_all([project, worker])
    db_session.flush()

    work_order = WorkOrder(
        work_order_no=f"WO-COST-WORKER-{suffix}",
        task_name="已完成加工工单",
        task_type="ASSEMBLY",
        project_id=project.id,
        status="COMPLETED",
        actual_hours=Decimal("2.00"),
        standard_hours=Decimal("3.00"),
        actual_end_time=datetime(2026, 6, 10, 17, 30),
        plan_end_date=date(2026, 6, 3),
        assigned_to=worker.id,
        created_by=admin.id,
    )
    db_session.add(work_order)
    db_session.flush()

    with patch(
        "app.services.cost.cost_collection_service.BudgetAlertService.check_and_alert",
        return_value=None,
    ):
        cost = CostCollectionService.collect_from_work_order(db_session, work_order.id)
        db_session.flush()

    assert cost.amount == Decimal("700.00")
