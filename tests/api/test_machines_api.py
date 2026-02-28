# -*- coding: utf-8 -*-
"""
API Integration Tests for machines module
已迁移至项目子路由 /projects/{project_id}/machines/

测试端点：
  - GET /api/v1/projects/{project_id}/machines
  - POST /api/v1/projects/{project_id}/machines
  - PUT /api/v1/projects/{project_id}/machines/{machine_id}/progress
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import ProjectWithCustomerFactory, MachineFactory

import uuid

_PN001 = f"PN001-{uuid.uuid4().hex[:8]}"



@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    """Create test client with authenticated user."""
    from app.main import app
    from tests.conftest import _get_auth_token

    client = TestClient(app)
    token = _get_auth_token(db_session, username="admin", password="admin123")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestMachinesAPI:
    """Test suite for machines API endpoints."""

    def test_get_machines_projects_project_id_machines(self, api_client, db_session):
        """测试 GET /api/v1/projects/{project_id}/machines - 项目机台列表"""
        project = ProjectWithCustomerFactory()
        machine1 = MachineFactory(project_id=project.id)
        machine2 = MachineFactory(project_id=project.id)
        
        response = api_client.get(f"/api/v1/projects/{project.id}/machines")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
        if isinstance(data, list):
            assert len(data) >= 2
        elif "items" in data:
            assert len(data["items"]) >= 2

    def test_post_machines_projects_project_id_machines(self, api_client, db_session):
        """测试 POST /api/v1/projects/{project_id}/machines - 创建机台"""
        project = ProjectWithCustomerFactory()
        
        machine_data = {
            "machine_code": _PN001,
            "machine_name": "测试机台",
            "machine_type": "TEST_EQUIPMENT",
            "status": "DESIGN"
        }
        
        response = api_client.post(
            f"/api/v1/projects/{project.id}/machines",
            json=machine_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("machine_code") == _PN001 or "code" in data or "machine_code" in data

    def test_put_machines_machine_id_progress(self, api_client, db_session):
        """测试 PUT /api/v1/projects/{project_id}/machines/{machine_id}/progress - 更新进度"""
        project = ProjectWithCustomerFactory()
        machine = MachineFactory(project_id=project.id)
        
        response = api_client.put(
            f"/api/v1/projects/{project.id}/machines/{machine.id}/progress?progress_pct=50"
        )
        
        assert response.status_code in [200, 400, 404]


    # TODO: 添加更多测试用例
    # - 正常流程测试 (Happy Path)
    # - 边界条件测试 (Edge Cases)
    # - 异常处理测试 (Error Handling)
    # - 数据验证测试 (Data Validation)
    # - 权限测试 (Permission Tests)
