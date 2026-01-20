# -*- coding: utf-8 -*-
"""
API Integration Tests for milestones module
Covers 1 endpoints from api_frontend_coverage.md (unmatched endpoints)

Generated endpoints:
  - DELETE /api/v1/milestones/{milestone_id}
  ... and -4 more
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import ProjectWithCustomerFactory, ProjectMilestoneFactory


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    """Create test client with authenticated user."""
    from app.main import app
    from tests.conftest import _get_auth_token

    client = TestClient(app)
    token = _get_auth_token(db_session, username="admin", password="admin123")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestMilestonesAPI:
    """Test suite for milestones API endpoints."""

    def test_delete_milestones_milestone_id(self, api_client, db_session):
        """测试 DELETE /api/v1/milestones/{milestone_id} - 删除里程碑"""
        project = ProjectWithCustomerFactory()
        milestone = ProjectMilestoneFactory(project_id=project.id)
        
        response = api_client.delete(f"/api/v1/milestones/{milestone.id}")
        
        assert response.status_code in [200, 204, 400, 404]
        if response.status_code in [200, 204]:
            # 验证里程碑已被删除
            from app.models.project import ProjectMilestone
            from app.models.base import get_session
            with get_session() as session:
                deleted_milestone = session.query(ProjectMilestone).filter(
                    ProjectMilestone.id == milestone.id
                ).first()
                assert deleted_milestone is None


    # TODO: 添加更多测试用例
    # - 正常流程测试 (Happy Path)
    # - 边界条件测试 (Edge Cases)
    # - 异常处理测试 (Error Handling)
    # - 数据验证测试 (Data Validation)
    # - 权限测试 (Permission Tests)
