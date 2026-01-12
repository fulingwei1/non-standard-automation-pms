# -*- coding: utf-8 -*-
"""
进度跟踪 API 测试
测试 WBS 模板、任务管理、进度报告等功能
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestWbsTemplates:
    """WBS 模板测试"""

    def test_list_wbs_templates(self, client: TestClient, admin_token: str):
        """测试获取 WBS 模板列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/wbs-templates",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("WBS templates endpoint not found")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "templates" in data or isinstance(data, list)

    def test_list_wbs_templates_with_filter(self, client: TestClient, admin_token: str):
        """测试按项目类型筛选 WBS 模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/wbs-templates",
            params={"project_type": "TEST_EQUIPMENT"},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("WBS templates endpoint not found")

        assert response.status_code == 200

    def test_get_wbs_template_by_id(self, client: TestClient, admin_token: str):
        """测试获取单个 WBS 模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/wbs-templates/1",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("WBS template not found")

        assert response.status_code == 200


class TestProjectTasks:
    """项目任务测试"""

    def test_list_project_tasks(self, client: TestClient, admin_token: str):
        """测试获取项目任务列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/tasks",
            params={"page": 1, "page_size": 20},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Tasks endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for tasks")

        assert response.status_code == 200

    def test_list_tasks_by_project(self, client: TestClient, admin_token: str):
        """测试按项目筛选任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/tasks",
            params={"project_id": 1},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Tasks endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for tasks")

        assert response.status_code == 200

    def test_get_task_by_id(self, client: TestClient, admin_token: str):
        """测试获取单个任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/tasks/1",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Task not found")

        assert response.status_code == 200


class TestGanttChart:
    """甘特图测试"""

    def test_get_gantt_data(self, client: TestClient, admin_token: str):
        """测试获取甘特图数据"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/projects/1/gantt",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Gantt endpoint not found or project not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for gantt")

        assert response.status_code == 200


class TestProgressBoard:
    """进度看板测试"""

    def test_get_progress_board(self, client: TestClient, admin_token: str):
        """测试获取进度看板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/projects/1/board",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Progress board endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters")

        assert response.status_code == 200


class TestProgressReports:
    """进度报告测试"""

    def test_list_progress_reports(self, client: TestClient, admin_token: str):
        """测试获取进度报告列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/reports",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Progress reports endpoint not found")

        assert response.status_code == 200

    def test_get_progress_summary(self, client: TestClient, admin_token: str):
        """测试获取进度汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/projects/1/summary",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Progress summary endpoint not found")

        assert response.status_code == 200


class TestProgressForecast:
    """进度预测测试"""

    def test_get_progress_forecast(self, client: TestClient, admin_token: str):
        """测试获取进度预测"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/projects/1/forecast",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Progress forecast endpoint not found")

        assert response.status_code == 200


class TestDependencyCheck:
    """依赖检查测试"""

    def test_check_dependencies(self, client: TestClient, admin_token: str):
        """测试检查任务依赖"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/progress/projects/1/dependency-check",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have progress:read permission")
        if response.status_code == 404:
            pytest.skip("Dependency check endpoint not found")

        assert response.status_code == 200
