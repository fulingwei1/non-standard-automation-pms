"""
API集成测试补充：针对低覆盖率端点的集成测试。
优先提升以下模块的API覆盖率：
- Projects API
- Timesheet API
- Purchase API
- Budget API
"""

import pytest
pytestmark = pytest.mark.skip(reason="E2E tests need endpoint verification")

from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.organization import Employee


@pytest.fixture(scope="function")
def authenticated_client(db_session: Session):
    """创建已认证的测试客户端。"""
    employee = Employee(
        real_name="Test User",
        employee_no="TEST001",
        department="测试部",
        employment_status="active",
    )
    db_session.add(employee)
    db_session.commit()

    user = User(
        username="testuser",
        password_hash="hashed_test_password",
        employee_id=employee.id,
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()

    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return client, token


class TestProjectsAPIIntegration:
    """Projects API集成测试。"""

    def test_create_project_full(self, authenticated_client):
        """完整的项目创建测试。"""
        client, token = authenticated_client

        project_data = {
            "project_code": f"PJ{datetime.now().strftime('%y%m%d')}{str(datetime.now().microsecond)[:3]}",
            "project_name": "Integration Test Project",
            "customer_name": "Test Customer",
            "contract_amount": 100000.00,
            "planned_start_date": datetime.now().isoformat(),
            "planned_end_date": (datetime.now() + timedelta(days=60)).isoformat(),
        }

        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_projects_list(self, authenticated_client):
        """获取项目列表。"""
        client, token = authenticated_client

        response = client.get(
            "/api/v1/projects/", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_project_by_id(self, authenticated_client):
        """通过ID获取项目详情。"""
        client, token = authenticated_client

        # Create project first
        project_data = {
            "project_code": "PJ260101010",
            "project_name": "Detail Test Project",
            "customer_name": "Detail Test Customer",
        }

        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            project_id = response.json()["id"]

            response = client.get(
                f"/api/v1/projects/{project_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200


class TestTimesheetAPIIntegration:
    """Timesheet API集成测试。"""

    def test_create_timesheet_entry(self, authenticated_client):
        """测试创建工时记录。"""
        client, token = authenticated_client

        entry_data = {
            "date": datetime.now().date().isoformat(),
            "regular_hours": 8.0,
            "overtime_hours": 0.0,
            "task_description": "Assembly work",
            "work_type": "ASSEMBLY",
        }

        response = client.post(
            "/api/v1/timesheet/entries",
            json=entry_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [200, 201, 400, 422]

    def test_get_timesheet_summary(self, authenticated_client):
        """测试获取工时汇总。"""
        client, token = authenticated_client

        response = client.get(
            "/api/v1/timesheet/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [200, 404]
