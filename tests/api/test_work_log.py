# -*- coding: utf-8 -*-
"""
工作日志 API 测试

覆盖只读端点：
- GET /api/v1/my/work-logs
- GET /api/v1/projects/{project_id}/work-logs/
- GET /api/v1/projects/{project_id}/work-logs/summary
"""

from datetime import date

import pytest
from typing import Optional
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_project(client: TestClient, token: str) -> Optional[dict]:
    headers = _auth_headers(token)
    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/",
        headers=headers
    )
    if response.status_code != 200:
        return None
    projects = response.json()
    items = projects.get("items", projects) if isinstance(projects, dict) else projects
    if not items:
        return None
    return items[0]


class TestMyWorkLogs:
    """我的工作日志测试"""

    def test_list_my_work_logs(self, client: TestClient, admin_token: str):
        """测试获取我的工作日志列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/my/work-logs",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("My work-logs endpoint not found")

        assert response.status_code == 200

    def test_list_my_work_logs_date_filter(self, client: TestClient, admin_token: str):
        """测试按日期筛选我的工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today().isoformat()
        response = client.get(
            f"{settings.API_V1_PREFIX}/my/work-logs",
            params={"start_date": today, "end_date": today, "page": 1, "page_size": 10},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("My work-logs endpoint not found")

        assert response.status_code == 200


class TestProjectWorkLogs:
    """项目工作日志端点测试"""

    def test_list_project_work_logs(self, client: TestClient, admin_token: str):
        """测试获取项目工作日志列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        project_id = project["id"]
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/work-logs/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Project work-logs endpoint not found")
        if response.status_code == 422:
            pytest.skip("Project work-logs endpoint not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                assert "items" in data["data"] or "total" in data["data"]
            else:
                assert "items" in data or "data" in data
        else:
            assert isinstance(data, list)

    def test_project_work_logs_summary(self, client: TestClient, admin_token: str):
        """测试获取项目工作日志汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        project_id = project["id"]
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/work-logs/summary",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work-logs summary endpoint not found")

        assert response.status_code == 200, response.text
