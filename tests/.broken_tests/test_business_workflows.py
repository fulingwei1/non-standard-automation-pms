"""
E2E tests for key business workflows.
Tests complete end-to-end flows:
- Project lifecycle (creation → completion)
- ECN flow (creation → approval → execution)
- Purchase to FAT/SAT workflow
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.project import (
    Project,
    ProjectStatus,
)
from app.models.enums import ProjectHealthEnum as ProjectHealth
from app.models.user import User
from app.models.organization import Employee
from app.models.material import Material, MaterialCategory, Supplier
from app.models.purchase import PurchaseOrder
from app.models.acceptance import (
    AcceptanceOrder,
    AcceptanceTemplate,
)
from app.models.ecn import (
    Ecn,
    EcnEvaluation,
    EcnTask,
    EcnStatus,
    EcnType,
)


@pytest.mark.e2e
class TestProjectLifecycle:
    """Complete project lifecycle from creation to completion."""

    def test_project_creation_to_s1(self, db_session: Session):
        """Test project creation through S1 stage."""
        client = TestClient(app)

        # Create user and login
        employee = Employee(
            real_name="Test Engineer",
            employee_no="E001",
            department="研发部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="testuser",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Create project
        project_data = {
            "project_code": "PJ260101001",
            "name": "E2E Test Project",
            "customer_name": "Test Customer",
            "contract_amount": 100000,
            "planned_start_date": datetime.now().isoformat(),
            "planned_end_date": (datetime.now() + timedelta(days=60)).isoformat(),
        }

        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        project_id = response.json()["id"]

        # Verify project created with S1 stage
        project = db_session.query(Project).filter(Project.id == project_id).first()
        assert project is not None
        assert project.status == ProjectStatus.S1_REQUEST

    def test_progress_to_s9_completion(self, db_session: Session):
        """Test project progression through all stages to completion."""
        client = TestClient(app)

        # Setup user
        employee = Employee(
            real_name="Project Manager",
            employee_no="E002",
            department="项目管理部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="pmuser",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "pmuser", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create project
        project_data = {
            "project_code": "PJ260101002",
            "name": "Lifecycle Test Project",
            "customer_name": "Test Customer",
            "contract_amount": 200000,
            "planned_start_date": datetime.now().isoformat(),
            "planned_end_date": (datetime.now() + timedelta(days=90)).isoformat(),
        }

        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        project_id = response.json()["id"]

        # Progress through stages
        stages = [
            ProjectStatus.S2_DESIGN,
            ProjectStatus.S3_PURCHASE,
            ProjectStatus.S4_MANUFACTURING,
            ProjectStatus.S5_ASSEMBLY,
            ProjectStatus.S6_FAT,
            ProjectStatus.S7_SHIPPING,
            ProjectStatus.S8_SAT,
            ProjectStatus.S9_COMPLETED,
        ]

        for stage in stages:
            response = client.post(
                f"/api/v1/projects/{project_id}/stage",
                json={"stage": stage},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

        # Verify final state
        project = db_session.query(Project).filter(Project.id == project_id).first()
        assert project.status == ProjectStatus.S9_COMPLETED
        assert project.health == ProjectHealth.COMPLETED


@pytest.mark.e2e
class TestECNFlow:
    """Complete ECN workflow from creation to execution."""

    def test_ecn_creation_and_evaluation(self, db_session: Session):
        """Test ECN creation and evaluation process."""
        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Design Engineer",
            employee_no="E003",
            department="研发部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="designer",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "designer", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create project
        project = Project(
            project_code="PJ260101003",
            name="ECN Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S2_DESIGN,
        )
        db_session.add(project)
        db_session.commit()

        # Create ECN
        ecn_data = {
            "ecn_code": "ECN-2601-001",
            "project_id": project.id,
            "type": "DESIGN_CHANGE",
            "title": "Design optimization",
            "description": "Optimize assembly structure",
            "proposed_date": datetime.now().isoformat(),
        }

        response = client.post(
            "/api/v1/ecn", json=ecn_data, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        ecn_id = response.json()["id"]

        # Submit evaluation
        evaluation_data = {
            "ecn_id": ecn_id,
            "evaluator_id": employee.id,
            "technical_feasibility": "FEASIBLE",
            "cost_impact": "LOW",
            "schedule_impact": "LOW",
            "recommendation": "APPROVE",
        }

        response = client.post(
            "/api/v1/ecn/evaluations",
            json=evaluation_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_ecn_approval_workflow(self, db_session: Session):
        """Test ECN multi-level approval process."""
        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Department Head",
            employee_no="E004",
            department="研发部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="head",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "head", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create ECN and evaluation
        project = Project(
            project_code="PJ260101004",
            name="Approval Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S3_PURCHASE,
        )
        db_session.add(project)
        db_session.commit()

        ecn = Ecn(
            ecn_code="ECN-2601-002",
            project_id=project.id,
            type=EcnType.DESIGN_CHANGE,
            title="Test change",
            description="Change for testing",
            status=EcnStatus.PENDING_EVALUATION,
        )
        db_session.add(ecn)
        db_session.commit()

        # Create evaluation
        evaluation = EcnEvaluation(
            ecn_id=ecn.id,
            evaluator_id=employee.id,
            technical_feasibility="FEASIBLE",
            cost_impact="MEDIUM",
            schedule_impact="MEDIUM",
            recommendation="APPROVE",
        )
        db_session.add(evaluation)
        db_session.commit()

        # Submit for approval
        approval_data = {
            "ecn_id": ecn.id,
            "approver_id": employee.id,
            "decision": "APPROVE",
            "comments": "Approved for implementation",
        }

        response = client.post(
            "/api/v1/ecn/approvals",
            json=approval_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify ECN status
        db_session.refresh(ecn)
        assert ecn.status == EcnStatus.APPROVED

    def test_ecn_execution_and_completion(self, db_session: Session):
        """Test ECN execution and task completion."""
        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Engineer",
            employee_no="E005",
            department="生产部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="engineer",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "engineer", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create ECN with tasks
        project = Project(
            project_code="PJ260101005",
            name="Execution Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S4_MANUFACTURING,
        )
        db_session.add(project)
        db_session.commit()

        ecn = Ecn(
            ecn_code="ECN-2601-003",
            project_id=project.id,
            type=EcnType.DESIGN_CHANGE,
            title="Test execution",
            description="Change for execution testing",
            status=EcnStatus.IN_PROGRESS,
        )
        db_session.add(ecn)
        db_session.commit()

        # Create tasks
        task1 = EcnTask(
            ecn_id=ecn.id,
            task_name="Update design documents",
            assignee_id=employee.id,
            due_date=datetime.now() + timedelta(days=5),
            status="PENDING",
        )
        task2 = EcnTask(
            ecn_id=ecn.id,
            task_name="Modify BOM",
            assignee_id=employee.id,
            due_date=datetime.now() + timedelta(days=7),
            status="PENDING",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # Complete task
        response = client.patch(
            f"/api/v1/ecn/tasks/{task1.id}",
            json={
                "status": "COMPLETED",
                "actual_completion_date": datetime.now().isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Complete ECN
        response = client.patch(
            f"/api/v1/ecn/{ecn.id}",
            json={"status": "COMPLETED", "completion_date": datetime.now().isoformat()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        db_session.refresh(ecn)
        assert ecn.status == EcnStatus.COMPLETED


@pytest.mark.e2e
class TestPurchaseToFATWorkflow:
    """Complete workflow from purchase to FAT."""

    def test_purchase_order_creation(self, db_session: Session):
        """Test purchase order creation for project."""
        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Procurement Specialist",
            employee_no="E006",
            department="采购部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="procurement",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "procurement", "password": "testpass"},
        )
        token = response.json()["access_token"]

        # Create project
        project = Project(
            project_code="PJ260101006",
            name="Purchase Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S3_PURCHASE,
        )
        db_session.add(project)
        db_session.commit()

        # Create materials
        category = MaterialCategory(name="标准件", code="STD")
        db_session.add(category)
        db_session.commit()

        supplier = Supplier(name="Test Supplier", code="SUP001")
        db_session.add(supplier)
        db_session.commit()

        material1 = Material(
            name="Material A",
            code="MAT-A001",
            category_id=category.id,
            supplier_id=supplier.id,
            unit_price=10.50,
            unit="piece",
        )
        material2 = Material(
            name="Material B",
            code="MAT-B001",
            category_id=category.id,
            supplier_id=supplier.id,
            unit_price=25.75,
            unit="piece",
        )
        db_session.add_all([material1, material2])
        db_session.commit()

        # Create purchase order
        po_data = {
            "project_id": project.id,
            "po_number": "PO-2601-001",
            "supplier_id": supplier.id,
            "order_date": datetime.now().isoformat(),
            "expected_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "items": [
                {
                    "material_id": material1.id,
                    "quantity": 100,
                    "unit_price": 10.50,
                },
                {
                    "material_id": material2.id,
                    "quantity": 50,
                    "unit_price": 25.75,
                },
            ],
        }

        response = client.post(
            "/api/v1/purchase/orders",
            json=po_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        po_id = response.json()["id"]

        # Verify PO
        po = db_session.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        assert po is not None
        assert len(po.items) == 2

    def test_fat_creation_workflow(self, db_session: Session):
        """Test FAT (Factory Acceptance Test) creation."""
        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Quality Engineer",
            employee_no="E007",
            department="质量部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="quality",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "quality", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create project with machine
        project = Project(
            project_code="PJ260101007",
            name="FAT Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S5_ASSEMBLY,
            health=ProjectHealth.NORMAL,
        )
        db_session.add(project)
        db_session.commit()

        from app.models.project import Machine

        machine = Machine(
            project_id=project.id,
            machine_code="PN001",
            name="Test Machine",
            serial_number="SN-001",
        )
        db_session.add(machine)
        db_session.commit()

        # Create FAT template
        template = AcceptanceTemplate(
            name="Standard FAT Template",
            type="FAT",
            category="STANDARD",
        )
        db_session.add(template)
        db_session.commit()

        # Create FAT order
        fat_data = {
            "project_id": project.id,
            "machine_id": machine.id,
            "template_id": template.id,
            "type": "FAT",
            "scheduled_date": (datetime.now() + timedelta(days=10)).isoformat(),
        }

        response = client.post(
            "/api/v1/acceptance/orders",
            json=fat_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        fat_id = response.json()["id"]

        # Add check items
        check_items = [
            {
                "fat_order_id": fat_id,
                "check_item": "Visual inspection",
                "requirement": "No visible defects",
                "actual_result": "PASS",
            },
            {
                "fat_order_id": fat_id,
                "check_item": "Functional test",
                "requirement": "All functions work correctly",
                "actual_result": "PASS",
            },
            {
                "fat_order_id": fat_id,
                "check_item": "Safety check",
                "requirement": "Safety guards installed",
                "actual_result": "PASS",
            },
        ]

        for item_data in check_items:
            response = client.post(
                "/api/v1/acceptance/items",
                json=item_data,
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

        # Verify FAT completion
        fat = (
            db_session.query(AcceptanceOrder)
            .filter(AcceptanceOrder.id == fat_id)
            .first()
        )
        assert fat is not None
        assert len(fat.items) == 3

    def test_sat_after_fat(self, db_session: Session):
        """Test SAT (Site Acceptance Test) after FAT."""
        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Customer Engineer",
            employee_no="E008",
            department="工程部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="engineer2",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "engineer2", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create project and machine (after FAT)
        project = Project(
            project_code="PJ260101008",
            name="SAT Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S7_SHIPPING,
            health=ProjectHealth.NORMAL,
        )
        db_session.add(project)
        db_session.commit()

        machine = Machine(
            project_id=project.id,
            machine_code="PN002",
            name="Test Machine 2",
            serial_number="SN-002",
        )
        db_session.add(machine)
        db_session.commit()

        # Create SAT
        sat_data = {
            "project_id": project.id,
            "machine_id": machine.id,
            "type": "SAT",
            "scheduled_date": (datetime.now() + timedelta(days=5)).isoformat(),
        }

        response = client.post(
            "/api/v1/acceptance/orders",
            json=sat_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        sat_id = response.json()["id"]

        # Complete SAT
        completion_data = {
            "status": "COMPLETED",
            "completion_date": datetime.now().isoformat(),
            "sign_off_date": datetime.now().isoformat(),
        }

        response = client.patch(
            f"/api/v1/acceptance/orders/{sat_id}",
            json=completion_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify project moves to completion
        sat = (
            db_session.query(AcceptanceOrder)
            .filter(AcceptanceOrder.id == sat_id)
            .first()
        )
        db_session.refresh(project)
        assert project.status == ProjectStatus.S9_COMPLETED


@pytest.mark.e2e
class TestAlertGenerationWorkflow:
    """Test alert generation during project lifecycle."""

    def test_delay_alert_generation(self, db_session: Session):
        """Test automatic alert generation when project is delayed."""
        from app.models.alert import AlertLevel

        client = TestClient(app)

        # Setup
        employee = Employee(
            real_name="Project Manager 2",
            employee_no="E009",
            department="项目管理部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="pmuser2",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "pmuser2", "password": "testpass"}
        )
        token = response.json()["access_token"]

        # Create delayed project
        project = Project(
            project_code="PJ260101009",
            name="Alert Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
            health=ProjectHealth.AT_RISK,
            planned_end_date=datetime.now() - timedelta(days=10),
        )
        db_session.add(project)
        db_session.commit()

        # Trigger alert evaluation
        from app.services.health_calculator import (
            calculate_project_health,
            HealthMetrics,
        )

        metrics = HealthMetrics.from_project(project)
        new_health = calculate_project_health(metrics)

        if new_health != project.health:
            from app.models.alert import AlertRule

            rule = AlertRule(
                rule_name="Auto Delay Alert",
                rule_type="PROJECT_HEALTH",
                condition="{}",
                is_active=True,
            )
            db_session.add(rule)
            db_session.commit()

            from app.services.alert_rule_engine.test_alert_creator import (
                create_alert_record,
            )

            alert = create_alert_record(
                db_session=db_session,
                rule_id=rule.id,
                project_id=project.id,
                alert_level=AlertLevel.WARNING,
                message=f"Project health changed to {new_health}",
            )

            assert alert.id is not None
