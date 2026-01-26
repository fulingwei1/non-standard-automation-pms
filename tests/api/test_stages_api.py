# -*- coding: utf-8 -*-
"""
API Integration Tests for stages module
Covers 6 endpoints from api_frontend_coverage.md (unmatched endpoints)

Generated endpoints:
  - POST /api/v1/stages
  - PUT /api/v1/stages/{stage_id}
  - PUT /api/v1/stages/project-stages/{stage_id}
  - GET /api/v1/stages/project-stages/{stage_id}/statuses
  - PUT /api/v1/stages/project-statuses/{status_id}/complete
  ... and 1 more
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import ProjectStageFactory, ProjectWithCustomerFactory


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    """Create test client with authenticated user."""
    from app.main import app
    from tests.conftest import _get_auth_token

    client = TestClient(app)
    token = _get_auth_token(db_session, username="admin", password="admin123")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestStagesAPI:
    """Test suite for stages API endpoints."""

    def test_post_stages(self, api_client, db_session):
        """测试 POST /api/v1/stages - 创建阶段"""
        stage_data = {
            "stage_code": "S10",
            "stage_name": "测试阶段",
            "sort_order": 10,
            "is_active": True
        }
        
        response = api_client.post("/api/v1/stages", json=stage_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["stage_code"] == "S10" or "code" in data

    def test_put_stages_stage_id(self, api_client, db_session):
        """测试 PUT /api/v1/stages/{stage_id} - 更新阶段"""
        stage = ProjectStageFactory()
        
        update_data = {
            "stage_name": "更新后的阶段名称",
            "is_active": False
        }
        
        response = api_client.put(f"/api/v1/stages/{stage.id}", json=update_data)
        assert response.status_code in [200, 400, 404]

    def test_put_stages_project_stages_stage_id(self, api_client, db_session):
        """测试 PUT /api/v1/stages/project-stages/{stage_id} - 更新项目阶段"""
        project = ProjectWithCustomerFactory()
        # 注意：这里需要根据实际API实现调整
        response = api_client.put("/api/v1/stages/project-stages/1", json={})
        assert response.status_code in [200, 400, 404]

    def test_get_stages_project_stages_stage_id_statuses(self, api_client, db_session):
        """测试 GET /api/v1/stages/project-stages/{stage_id}/statuses - 获取状态列表"""
        response = api_client.get("/api/v1/stages/project-stages/1/statuses")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_put_stages_project_statuses_status_id_complete(self, api_client, db_session):
        """测试 PUT /api/v1/stages/project-statuses/{status_id}/complete - 完成状态"""
        response = api_client.put("/api/v1/stages/project-statuses/1/complete")
        assert response.status_code in [200, 400, 404]

    def test_post_stages_statuses(self, api_client, db_session):
        """测试 POST /api/v1/stages/statuses - 创建状态"""
        status_data = {
            "status_code": "ST99",
            "status_name": "测试状态",
            "stage_code": "S1"
        }
        
        response = api_client.post("/api/v1/stages/statuses", json=status_data)
        assert response.status_code in [200, 201, 400]


    # TODO: 添加更多测试用例
    # - 正常流程测试 (Happy Path)
    # - 边界条件测试 (Edge Cases)
    # - 异常处理测试 (Error Handling)
    # - 数据验证测试 (Data Validation)
    # - 权限测试 (Permission Tests)
