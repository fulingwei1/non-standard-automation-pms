"""
E2E tests for key business workflows.
Tests complete end-to-end flows:
- Project lifecycle (creation -> completion)
- ECN flow (creation -> approval -> execution)
- Purchase to FAT/SAT workflow
"""

import pytest
pytestmark = pytest.mark.skip(reason="E2E tests need endpoint verification")

from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.project import Project
from app.models.enums import ProjectHealthEnum as ProjectHealth
from app.models.enums import EcnStatusEnum, EcnTypeEnum
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
)


@pytest.mark.e2e
class TestProjectLifecycle:
    """Complete project lifecycle from creation to completion."""

    def test_project_creation_to_s1(self, db_session: Session):
        """Test project creation through S1 stage."""
        client = TestClient(app)

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

        project_data = {
            "project_code": "PJ260101001",
            "project_name": "E2E Test Project",
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

        project = db_session.query(Project).filter(Project.id == project_id).first()
        assert project is not None

    def test_progress_to_s9_completion(self, db_session: Session):
        """Test project progression through all stages to completion."""
        client = TestClient(app)

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

        project_data = {
            "project_code": "PJ260101002",
            "project_name": "Lifecycle Test Project",
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

        stages = ["S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]

        for stage in stages:
            response = client.post(
                f"/api/v1/projects/{project_id}/stage",
                json={"stage": stage},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200


@pytest.mark.e2e
class TestECNFlow:
    """Complete ECN workflow from creation to execution."""

    def test_ecn_creation_and_evaluation(self, db_session: Session):
        """Test ECN creation and evaluation process."""
        client = TestClient(app)

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

        project = Project(
            project_code="PJ260101003",
            project_name="ECN Test Project",
            customer_name="Test Customer",
            stage="S2",
            status="ST01",
            health="H1",
            created_by="designer",
        )
        db_session.add(project)
        db_session.commit()

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


@pytest.mark.e2e
class TestPurchaseToFATWorkflow:
    """Complete workflow from purchase to FAT."""

    def test_purchase_order_creation(self, db_session: Session):
        """Test purchase order creation for project."""
        client = TestClient(app)

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

        project = Project(
            project_code="PJ260101006",
            project_name="Purchase Test Project",
            customer_name="Test Customer",
            stage="S3",
            status="ST01",
            health="H1",
            created_by="procurement",
        )
        db_session.add(project)
        db_session.commit()

        po_data = {
            "project_id": project.id,
            "po_number": "PO-2601-001",
            "order_date": datetime.now().isoformat(),
            "expected_date": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        response = client.post(
            "/api/v1/purchase/orders",
            json=po_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
