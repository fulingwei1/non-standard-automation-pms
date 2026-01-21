"""
API integration tests for critical low-coverage endpoints.
Focuses on modules with < 40% coverage:
- Timesheet API (27.7% coverage)
- Purchase API (41.5% coverage)
- Budget API (43.7% coverage)
- Projects API (44.0% coverage)
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, Employee
from app.models.project import Project
from app.models.timesheet import TimesheetEntry
from app.models.purchase import Supplier
from app.models.budget import Budget


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
            name="Timesheet Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
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

        project = Project(
            project_code="PJ260101002",
            name="Timesheet Test Project 2",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()

        entry = TimesheetEntry(
            project_id=project.id,
            employee_id=employee.id,
            date=datetime.now().date(),
            work_hours=8.0,
            task_description="Test work",
        )
        db_session.add(entry)
        db_session.commit()

        response = client.get(
            f"/api/v1/timesheet/entries?project_id={project.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_update_timesheet_entry(self, db_session: Session):
        """Test updating a timesheet entry."""
        client = TestClient(app)

        employee = Employee(
            real_name="Test Worker 3",
            employee_no="T003",
            department="生产部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="worker3",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "worker3", "password": "testpass"}
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101003",
            name="Timesheet Test Project 3",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()

        entry = TimesheetEntry(
            project_id=project.id,
            employee_id=employee.id,
            date=datetime.now().date(),
            work_hours=4.0,
            task_description="Initial entry",
        )
        db_session.add(entry)
        db_session.commit()

        update_data = {"work_hours": 8.0, "task_description": "Updated entry"}

        response = client.patch(
            f"/api/v1/timesheet/entries/{entry.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        db_session.refresh(entry)
        assert entry.work_hours == 8.0

    def test_delete_timesheet_entry(self, db_session: Session):
        """Test deleting a timesheet entry."""
        client = TestClient(app)

        employee = Employee(
            real_name="Test Worker 4",
            employee_no="T004",
            department="生产部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="worker4",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "worker4", "password": "testpass"}
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101004",
            name="Timesheet Test Project 4",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()

        entry = TimesheetEntry(
            project_id=project.id,
            employee_id=employee.id,
            date=datetime.now().date(),
            work_hours=8.0,
            task_description="Test work",
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        response = client.delete(
            f"/api/v1/timesheet/entries/{entry_id}",
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
            name="Purchase Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S3_PURCHASE,
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
        assert "items" in response.json()

    def test_add_item_to_purchase_order(self, db_session: Session):
        """Test adding items to a purchase order."""
        client = TestClient(app)

        from app.models.material import Material, MaterialCategory

        employee = Employee(
            real_name="Procurement Specialist 3",
            employee_no="P003",
            department="采购部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="procurement3",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "procurement3", "password": "testpass"},
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101006",
            name="Purchase Test Project 2",
            customer_name="Test Customer",
            status=ProjectStatus.S3_PURCHASE,
        )
        db_session.add(project)
        db_session.commit()

        supplier = Supplier(name="Test Supplier 2", code="SUP002")
        db_session.add(supplier)
        db_session.commit()

        category = MaterialCategory(name="标准件", code="STD")
        db_session.add(category)
        db_session.commit()

        material = Material(
            name="Test Material",
            code="MAT-001",
            category_id=category.id,
            supplier_id=supplier.id,
            unit_price=10.50,
            unit="piece",
        )
        db_session.add(material)
        db_session.commit()

        po_data = {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "po_number": "PO-2601-002",
            "order_date": datetime.now().isoformat(),
            "expected_date": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        response = client.post(
            "/api/v1/purchase/orders",
            json=po_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        po_id = response.json()["id"]

        # Add item
        item_data = {
            "purchase_order_id": po_id,
            "material_id": material.id,
            "quantity": 100,
            "unit_price": 10.50,
        }

        response = client.post(
            "/api/v1/purchase/items",
            json=item_data,
            headers={"Authorization": f"Bearer {token}"},
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
            name="Budget Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.S2_DESIGN,
            contract_amount=Decimal("100000.00"),
        )
        db_session.add(project)
        db_session.commit()

        budget_data = {
            "project_id": project.id,
            "budget_amount": Decimal("100000.00"),
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
        }

        response = client.post(
            "/api/v1/budget/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "id" in response.json()

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

    def test_add_budget_item(self, db_session: Session):
        """Test adding items to a budget."""
        client = TestClient(app)

        employee = Employee(
            real_name="Project Manager 3",
            employee_no="M003",
            department="项目管理部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="pm3",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "pm3", "password": "testpass"}
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101008",
            name="Budget Test Project 2",
            customer_name="Test Customer",
            status=ProjectStatus.S2_DESIGN,
            contract_amount=Decimal("150000.00"),
        )
        db_session.add(project)
        db_session.commit()

        budget_data = {
            "project_id": project.id,
            "budget_amount": Decimal("150000.00"),
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
        }

        response = client.post(
            "/api/v1/budget/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        budget_id = response.json()["id"]

        item_data = {
            "budget_id": budget_id,
            "item_name": "Materials",
            "budget_amount": Decimal("50000.00"),
        }

        response = client.post(
            "/api/v1/budget/items",
            json=item_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_update_budget(self, db_session: Session):
        """Test updating a budget."""
        client = TestClient(app)

        employee = Employee(
            real_name="Project Manager 4",
            employee_no="M004",
            department="项目管理部",
            employment_status="active",
        )
        db_session.add(employee)
        db_session.commit()

        user = User(
            username="pm4",
            hashed_password="hashed_pass",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login", json={"username": "pm4", "password": "testpass"}
        )
        token = response.json()["access_token"]

        project = Project(
            project_code="PJ260101009",
            name="Budget Test Project 3",
            customer_name="Test Customer",
            status=ProjectStatus.S2_DESIGN,
            contract_amount=Decimal("120000.00"),
        )
        db_session.add(project)
        db_session.commit()

        budget = Budget(
            project_id=project.id,
            budget_amount=Decimal("120000.00"),
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=90),
        )
        db_session.add(budget)
        db_session.commit()

        update_data = {
            "budget_amount": Decimal("125000.00"),
            "end_date": (datetime.now() + timedelta(days=95)).isoformat(),
        }

        response = client.patch(
            f"/api/v1/budget/budgets/{budget.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
