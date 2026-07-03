# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
import uuid
from unittest.mock import patch

from app.models.material import BomHeader, BomItem
from app.models.production.work_order import WorkOrder
from app.models.project import Customer, Project, ProjectCost
from app.models.purchase import PurchaseOrder
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.vendor import Vendor
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
        "app.services.cost.cost_collection_service.CostAlertService.check_budget_execution",
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
