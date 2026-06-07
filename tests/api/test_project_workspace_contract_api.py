# -*- coding: utf-8 -*-
"""项目工作台前后端契约与交接上下文测试。"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ecn import Ecn
from app.models.material import BomHeader, BomItem, Material
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.production import ProductionPlan, QualityInspection, WorkOrder
from app.models.project import Customer, Project
from app.models.project_delivery import ProjectDeliverySchedule, ProjectDeliveryTask
from app.models.sales import Contract, Opportunity, Quote, QuoteVersion
from app.models.technical_review import TechnicalReview
from app.models.user import User
from app.models.acceptance import AcceptanceOrder


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _route_map(app) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods or []:
                if method not in {"HEAD", "OPTIONS"}:
                    routes.add((method.upper(), route.path))
    return routes


class TestProjectWorkspaceFrontendContractRoutes:
    """核对 frontend/src/services/api/projects.js 中声明的项目工作台路由。"""

    def test_declared_project_workspace_routes_exist(self, client: TestClient):
        routes = _route_map(client.app)
        prefix = settings.API_V1_PREFIX

        expected_routes = {
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/workspace"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/workspace/context"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/downstream-context"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/bonuses"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/meetings"),
            (
                "POST",
                f"{prefix}/project-workspace/projects/{{project_id}}/meetings/{{meeting_id}}/link",
            ),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/issues"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/solutions"),
        }

        missing = sorted(expected_routes - routes)
        assert not missing, f"前端声明但后端未注册的项目工作台路由: {missing}"


class TestProjectListContextFilters:
    """验证项目中心能承接销售/合同/商机上下文筛选。"""

    def test_project_list_filters_by_project_contract_and_opportunity_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PLC-{unique}",
            customer_name=f"项目列表上下文客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPLC{unique[:6]}",
            customer=customer,
            opp_name=f"项目列表上下文商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("680000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        contract = Contract(
            contract_code=f"CTPLC{unique[:6]}",
            contract_name=f"项目列表上下文合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            total_amount=Decimal("680000"),
            signing_date=date.today(),
            status="signed",
            sales_owner_id=admin_user.id,
        )
        db_session.add_all([customer, opportunity, contract])
        db_session.flush()

        matching_project = Project(
            project_code=f"PRJPLC{unique[:6]}",
            project_name=f"项目列表上下文项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            opportunity=opportunity,
            contract=contract,
            stage="S1",
            status="ST01",
            health="H1",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        noise_project = Project(
            project_code=f"PRJPLN{unique[:6]}",
            project_name=f"项目列表噪声项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        db_session.add_all([matching_project, noise_project])
        db_session.flush()
        contract.project_id = matching_project.id
        db_session.commit()

        response = client.get(
            f"{prefix}/projects/",
            params={
                "project_id": matching_project.id,
                "contract_id": contract.id,
                "opportunity_id": opportunity.id,
                "page_size": 100,
                "sort": "created_at_desc",
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["total"] == 1
        assert [item["id"] for item in payload["items"]] == [matching_project.id]
        assert payload["items"][0]["contract_id"] == contract.id
        assert payload["items"][0]["opportunity_id"] == opportunity.id


class TestProjectWorkspaceHandoverContext:
    """验证销售/售前交接信息进入项目工作台。"""

    def test_project_workspace_context_includes_sales_presale_and_cost_baseline(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PW-{unique}",
            customer_name=f"项目交接客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPPW{unique[:6]}",
            customer=customer,
            opp_name=f"项目交接商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("580000"),
            est_margin=Decimal("35.50"),
            expected_close_date=date.today(),
            acceptance_basis="按冻结需求和终验清单验收",
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QTPW{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, opportunity, quote])
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("580000"),
            cost_total=Decimal("360000"),
            gross_margin=Decimal("37.93"),
            binding_status="valid",
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        contract = Contract(
            contract_code=f"CTPW{unique[:6]}",
            contract_name=f"项目交接合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_version.id,
            total_amount=Decimal("580000"),
            signing_date=date.today(),
            delivery_terms="90天交付",
            payment_terms="30/60/10",
            status="signed",
            sales_owner_id=admin_user.id,
        )
        project = Project(
            project_code=f"PRJPW{unique[:6]}",
            project_name=f"项目交接项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            opportunity=opportunity,
            contract=contract,
            project_type="FCT",
            product_category="测试设备",
            industry="电子制造",
            contract_amount=Decimal("580000"),
            budget_amount=Decimal("360000"),
            stage="S1",
            status="ST01",
            health="H1",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-PW-{unique}",
            title=f"项目交接售前工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=None,
            customer_name=customer.customer_name,
            opportunity_id=opportunity.id,
            project_id=None,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            actual_hours=Decimal("18.5"),
            pm_involvement_required=True,
            pm_involvement_risk_level="高",
            pm_involvement_risk_factors=["金额高", "交期紧"],
            pm_assigned=False,
            created_by=admin_user.id,
        )
        db_session.add_all([contract, project, ticket])
        db_session.flush()
        contract.project_id = project.id
        ticket.customer_id = customer.id
        ticket.project_id = project.id

        solution = PresaleSolution(
            solution_no=f"SOL-PW-{unique}",
            name=f"项目交接方案-{unique}",
            solution_type="CUSTOM",
            industry="电子制造",
            test_type="FCT",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            requirement_summary="冻结需求摘要",
            solution_overview="设备方案概要",
            technical_spec="关键技术规格",
            estimated_cost=Decimal("355000"),
            suggested_price=Decimal("580000"),
            estimated_hours=120,
            estimated_duration=45,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()
        assert (
            db_session.query(PresaleSolution)
            .filter(PresaleSolution.project_id == project.id)
            .count()
            == 1
        )

        response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/workspace/context",
            headers=headers,
        )
        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["project"]["id"] == project.id
        assert payload["contract"]["contract_code"] == contract.contract_code
        assert payload["opportunity"]["opp_code"] == opportunity.opp_code
        assert payload["quote"]["quote_code"] == quote.quote_code
        assert payload["quote"]["version"]["cost_total"] == 360000.0
        assert payload["baseline_cost"]["quote_cost_total"] == 360000.0
        assert payload["baseline_cost"]["presale_estimated_cost"] == 355000.0
        assert payload["presale_tickets"][0]["pm_involvement_required"] is True
        assert payload["presale_tickets"][0]["pm_involvement_risk_level"] == "高"
        assert payload["presale_tickets"][0]["pm_involvement_risk_factors"] == ["金额高", "交期紧"]
        assert payload["presale_tickets"][0]["pm_assigned"] is False
        assert payload["presale_solutions"][0]["solution_no"] == solution.solution_no
        assert payload["handover_status"]["ready"] is True
        assert payload["handover_status"]["missing"] == []

    def test_project_workspace_context_includes_project_scoped_presale_solution_without_ticket(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PWS-{unique}",
            customer_name=f"项目方案回流客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        project = Project(
            project_code=f"PRJPWS{unique[:6]}",
            project_name=f"项目方案回流项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            project_type="FCT",
            product_category="测试设备",
            industry="电子制造",
            stage="S1",
            status="ST01",
            health="H1",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        db_session.add_all([customer, project])
        db_session.flush()

        solution = PresaleSolution(
            solution_no=f"SOL-PWS-{unique}",
            name=f"项目上下文方案-{unique}",
            solution_type="CUSTOM",
            industry="电子制造",
            test_type="FCT",
            project_id=project.id,
            customer_id=customer.id,
            requirement_summary="项目上下文补充方案需求",
            solution_overview="从项目工作区进入售前技术后生成",
            technical_spec="FCT测试设备技术方案",
            estimated_cost=Decimal("128000"),
            suggested_price=Decimal("210000"),
            estimated_hours=64,
            estimated_duration=20,
            status="DRAFT",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()

        response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/workspace/context",
            headers=headers,
        )
        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["presale_solutions"][0]["id"] == solution.id
        assert payload["presale_solutions"][0]["solution_no"] == solution.solution_no
        assert payload["presale_solutions"][0]["project_id"] == project.id
        assert payload["presale_solutions"][0]["customer_id"] == customer.id
        assert payload["presale_solutions"][0]["opportunity_id"] is None
        assert payload["baseline_cost"]["presale_estimated_cost"] == 128000.0
        assert payload["baseline_cost"]["presale_suggested_price"] == 210000.0
        assert "presale_solution" not in payload["handover_status"]["missing"]
        assert "baseline_cost" not in payload["handover_status"]["missing"]

    def test_project_workspace_downstream_context_includes_engineering_bom_and_kitting(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PWD-{unique}",
            customer_name=f"后续上下文客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        project = Project(
            project_code=f"PRJDS{unique[:6]}",
            project_name=f"后续上下文项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            project_type="FCT",
            product_category="测试设备",
            industry="电子制造",
            stage="S3",
            status="ST03",
            health="H2",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        db_session.add_all([customer, project])
        db_session.flush()

        review = TechnicalReview(
            review_no=f"RV-PWD-{unique}",
            review_type="PDR",
            review_name=f"后续上下文技术评审-{unique}",
            project_id=project.id,
            project_no=project.project_code,
            status="completed",
            scheduled_date=datetime.now(),
            actual_date=datetime.now(),
            host_id=admin_user.id,
            presenter_id=admin_user.id,
            recorder_id=admin_user.id,
            conclusion="pass_with_condition",
            conclusion_summary="允许进入BOM下发，遗留问题跟踪关闭",
            issue_count_b=1,
            created_by=admin_user.id,
        )
        ecn = Ecn(
            ecn_no=f"ECN-PWD-{unique}",
            ecn_title=f"后续上下文ECN-{unique}",
            ecn_type="DESIGN",
            project_id=project.id,
            priority="HIGH",
            urgency="URGENT",
            cost_impact=Decimal("2500"),
            schedule_impact_days=3,
            status="APPROVED",
            created_by=admin_user.id,
        )
        stocked_material = Material(
            material_code=f"MAT-PWD-A-{unique}",
            material_name="已齐套传感器",
            current_stock=Decimal("5"),
            created_by=admin_user.id,
        )
        shortage_material = Material(
            material_code=f"MAT-PWD-B-{unique}",
            material_name="关键缺料气缸",
            current_stock=Decimal("1"),
            is_key_material=True,
            created_by=admin_user.id,
        )
        db_session.add_all([review, ecn, stocked_material, shortage_material])
        db_session.flush()

        bom = BomHeader(
            bom_no=f"BOM-PWD-{unique}",
            bom_name=f"后续上下文BOM-{unique}",
            project_id=project.id,
            version="V1",
            is_latest=True,
            status="APPROVED",
            total_items=2,
            created_by=admin_user.id,
        )
        db_session.add(bom)
        db_session.flush()
        db_session.add_all(
            [
                BomItem(
                    bom_id=bom.id,
                    item_no=1,
                    material_id=stocked_material.id,
                    material_code=stocked_material.material_code,
                    material_name=stocked_material.material_name,
                    quantity=Decimal("5"),
                    received_qty=Decimal("0"),
                    source_type="PURCHASE",
                    is_key_item=False,
                ),
                BomItem(
                    bom_id=bom.id,
                    item_no=2,
                    material_id=shortage_material.id,
                    material_code=shortage_material.material_code,
                    material_name=shortage_material.material_name,
                    quantity=Decimal("10"),
                    received_qty=Decimal("1"),
                    purchased_qty=Decimal("4"),
                    source_type="PURCHASE",
                    is_key_item=True,
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/downstream-context",
            headers=headers,
        )
        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["project"]["id"] == project.id
        assert payload["engineering"]["technical_reviews"]["total"] == 1
        assert payload["engineering"]["technical_reviews"]["items"][0]["review_no"] == review.review_no
        assert payload["engineering"]["ecns"]["items"][0]["ecn_no"] == ecn.ecn_no
        assert payload["engineering"]["ecns"]["open_count"] == 1
        assert payload["supply_chain"]["bom"]["total"] == 1
        assert payload["supply_chain"]["bom"]["items"][0]["bom_no"] == bom.bom_no
        assert payload["supply_chain"]["kitting"]["kitting_rate"] == 50.0
        assert payload["supply_chain"]["kitting"]["shortage_items"] == 1
        assert payload["supply_chain"]["kitting"]["shortage_details"][0]["material_code"] == shortage_material.material_code
        assert payload["next_actions"][0]["domain"] == "supply_chain"
        assert payload["next_actions"][0]["href"] == f"/material-analysis?project_id={project.id}"

    def test_project_workspace_downstream_context_includes_production_quality_delivery_and_acceptance(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PWF-{unique}",
            customer_name=f"全链路后续客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        project = Project(
            project_code=f"PRJFL{unique[:6]}",
            project_name=f"全链路后续项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            project_type="FCT",
            product_category="测试设备",
            industry="电子制造",
            stage="S5",
            status="ST05",
            health="H2",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        db_session.add_all([customer, project])
        db_session.flush()

        plan = ProductionPlan(
            plan_no=f"PP-PWF-{unique}",
            plan_name=f"全链路生产计划-{unique}",
            plan_type="MASTER",
            project_id=project.id,
            plan_start_date=date.today(),
            plan_end_date=date.today() + timedelta(days=20),
            status="RELEASED",
            progress=40,
            created_by=admin_user.id,
        )
        db_session.add(plan)
        db_session.flush()

        completed_order = WorkOrder(
            work_order_no=f"WO-PWF-A-{unique}",
            task_name="机架装配",
            task_type="ASSEMBLY",
            project_id=project.id,
            production_plan_id=plan.id,
            plan_qty=1,
            completed_qty=1,
            qualified_qty=1,
            status="COMPLETED",
            progress=100,
            created_by=admin_user.id,
        )
        open_order = WorkOrder(
            work_order_no=f"WO-PWF-B-{unique}",
            task_name="电气接线",
            task_type="ASSEMBLY",
            project_id=project.id,
            production_plan_id=plan.id,
            plan_qty=1,
            completed_qty=0,
            defect_qty=1,
            status="IN_PROGRESS",
            progress=40,
            created_by=admin_user.id,
        )
        db_session.add_all([completed_order, open_order])
        db_session.flush()

        inspection_pass = QualityInspection(
            inspection_no=f"QI-PWF-A-{unique}",
            work_order_id=completed_order.id,
            inspection_type="IPQC",
            inspection_date=datetime.now(),
            inspector_id=admin_user.id,
            inspection_qty=1,
            qualified_qty=1,
            defect_qty=0,
            inspection_result="PASS",
            created_by=admin_user.id,
        )
        inspection_fail = QualityInspection(
            inspection_no=f"QI-PWF-B-{unique}",
            work_order_id=open_order.id,
            inspection_type="IPQC",
            inspection_date=datetime.now(),
            inspector_id=admin_user.id,
            inspection_qty=1,
            qualified_qty=0,
            defect_qty=1,
            inspection_result="FAIL",
            defect_type="接线错误",
            defect_description="线号与图纸不一致",
            created_by=admin_user.id,
        )
        acceptance = AcceptanceOrder(
            order_no=f"ACC-PWF-{unique}",
            project_id=project.id,
            acceptance_type="FAT",
            planned_date=date.today() + timedelta(days=25),
            status="IN_PROGRESS",
            total_items=10,
            passed_items=6,
            failed_items=1,
            pass_rate=Decimal("60.00"),
            overall_result="CONDITIONAL",
            created_by=admin_user.id,
        )
        delivery_schedule = ProjectDeliverySchedule(
            schedule_no=f"PDS-PWF-{unique}",
            schedule_name=f"全链路交付排产-{unique}",
            project_id=project.id,
            version="V1.0",
            status="CONFIRMED",
            usage_type="BOTH",
            initiator_id=admin_user.id,
            initiator_name=admin_user.real_name or admin_user.username,
            is_pre_contract=False,
            is_active=True,
        )
        db_session.add_all([inspection_pass, inspection_fail, acceptance, delivery_schedule])
        db_session.flush()

        db_session.add_all(
            [
                ProjectDeliveryTask(
                    schedule_id=delivery_schedule.id,
                    task_no=f"DT-PWF-A-{unique}",
                    task_type="PRODUCTION",
                    task_name="装配完成",
                    planned_start=date.today(),
                    planned_end=date.today() + timedelta(days=10),
                    status="COMPLETED",
                    progress_pct=Decimal("100"),
                ),
                ProjectDeliveryTask(
                    schedule_id=delivery_schedule.id,
                    task_no=f"DT-PWF-B-{unique}",
                    task_type="ACCEPTANCE",
                    task_name="客户预验收",
                    planned_start=date.today() + timedelta(days=12),
                    planned_end=date.today() + timedelta(days=20),
                    has_conflict=True,
                    conflict_details={"reason": "测试工程师资源冲突"},
                    status="IN_PROGRESS",
                    progress_pct=Decimal("30"),
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/downstream-context",
            headers=headers,
        )
        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["production"]["plans"]["total"] == 1
        assert payload["production"]["plans"]["items"][0]["plan_no"] == plan.plan_no
        assert payload["production"]["work_orders"]["total"] == 2
        assert payload["production"]["work_orders"]["open_count"] == 1
        assert payload["production"]["work_orders"]["avg_progress"] == 70.0
        assert payload["quality"]["inspections"]["total"] == 2
        assert payload["quality"]["inspections"]["failed_count"] == 1
        assert payload["quality"]["inspections"]["defect_qty"] == 1
        assert payload["quality"]["inspections"]["items"][0]["inspection_no"] == inspection_fail.inspection_no
        assert payload["delivery"]["schedules"]["total"] == 1
        assert payload["delivery"]["schedules"]["items"][0]["schedule_no"] == delivery_schedule.schedule_no
        assert payload["delivery"]["tasks"]["total"] == 2
        assert payload["delivery"]["tasks"]["conflict_count"] == 1
        assert payload["acceptance"]["orders"]["total"] == 1
        assert payload["acceptance"]["orders"]["open_count"] == 1
        assert payload["acceptance"]["orders"]["items"][0]["order_no"] == acceptance.order_no
        actions_by_domain = {action["domain"]: action for action in payload["next_actions"]}
        action_domains = set(actions_by_domain)
        assert {"production", "quality", "delivery", "acceptance"}.issubset(action_domains)
        assert actions_by_domain["production"]["href"] == f"/work-orders?project_id={project.id}"
        assert actions_by_domain["quality"]["href"] == f"/quality/inspections?project_id={project.id}"
        assert actions_by_domain["delivery"]["href"] == f"/projects/{project.id}/delivery"
        assert actions_by_domain["acceptance"]["href"] == f"/quality/acceptance?project_id={project.id}"
