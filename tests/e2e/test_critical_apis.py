"""
API integration tests for critical low-coverage endpoints.
Focuses on modules with < 40% coverage:
- Timesheet API (27.7% coverage)
- Purchase API (41.5% coverage)
- Budget API (43.7% coverage)
- Projects API (44.0% coverage)
"""

import pytest
pytestmark = pytest.mark.skip(reason="E2E tests need endpoint verification")

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.organization import Employee
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.vendor import Vendor as Supplier
from app.models.budget import ProjectBudget


class TestTimesheetAPI:
    """Integration tests for timesheet endpoints."""

    def test_create_timesheet_entry(self, db_session: Session):
        """Test creating a new timesheet entry."""
        client = TestClient(app)

        employee = Employee(
            real_name="Test Worker",
            employee_no="T001",
            department="生产部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="worker",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "worker", "password": "testpass"}
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101001",
            project_name="Timesheet Test Project",
            customer_name="Test Customer",
            stage="S1",
            status="ST01",
            health="H1",
            created_by="worker",
        )
        db_session.add(project)
        db_session.commit()

        entry_data = {
            "project_id": project.id,
            "employee_id": employee.id,
            "date": datetime.now().isoformat(),
            "work_hours": 8.0,
            "task_description": "Assembly work",
        }

        response = client.post(
            "/api/v1/timesheet/entries",
            json=entry_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_timesheet_entries(self, db_session: Session):
        """Test retrieving timesheet entries."""
        client = TestClient(app)

        employee = Employee(
            real_name="Test Worker 2",
            employee_no="T002",
            department="生产部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="worker2",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "worker2", "password": "testpass"}
        )
        token = response.json()["access_token"]

        response = client.get(
            "/api/v1/timesheet/entries",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestPurchaseAPI:
    """Integration tests for purchase order endpoints."""

    def test_create_purchase_order(self, db_session: Session):
        """Test creating a new purchase order."""
        client = TestClient(app)

        employee = Employee(
            real_name="Procurement Specialist",
            employee_no="P001",
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
            project_code="PJ260101005",
            project_name="Purchase Test Project",
            customer_name="Test Customer",
            stage="S3",
            status="ST01",
            health="H1",
            created_by="procurement",
        )
        db_session.add(project)
        db_session.commit()

        supplier = Supplier(name="Test Supplier", code="SUP001")
        db_session.add(supplier)
        db_session.commit()

        po_data = {
            "project_id": project.id,
            "supplier_id": supplier.id,
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
        assert "id" in response.json()

    def test_get_purchase_orders(self, db_session: Session):
        """Test retrieving purchase orders."""
        client = TestClient(app)

        employee = Employee(
            real_name="Procurement Specialist 2",
            employee_no="P002",
            department="采购部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="procurement2",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "procurement2", "password": "testpass"},
        )
        token = response.json()["access_token"]

        response = client.get(
            "/api/v1/purchase/orders", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestBudgetAPI:
    """Integration tests for budget endpoints."""

    def test_create_budget(self, db_session: Session):
        """Test creating a project budget."""
        client = TestClient(app)

        employee = Employee(
            real_name="Project Manager",
            employee_no="M001",
            department="项目管理部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="pm",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "pm", "password": "testpass"}
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101007",
            project_name="Budget Test Project",
            customer_name="Test Customer",
            stage="S2",
            status="ST01",
            health="H1",
            created_by="pm",
        )
        db_session.add(project)
        db_session.commit()

        budget_data = {
            "project_id": project.id,
            "budget_amount": 100000.00,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
        }

        response = client.post(
            "/api/v1/budget/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_get_budgets(self, db_session: Session):
        """Test retrieving budgets."""
        client = TestClient(app)

        employee = Employee(
            real_name="Project Manager 2",
            employee_no="M002",
            department="项目管理部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="pm2",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "pm2", "password": "testpass"}
        )
        token = response.json()["access_token"]

        response = client.get(
            "/api/v1/budget/budgets", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
