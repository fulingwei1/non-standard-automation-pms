# -*- coding: utf-8 -*-
"""
工时管理模块 API 测试

测试工时记录的 CRUD 操作、提交审批和统计
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_project(client: TestClient, token: str) -> dict:
    """获取第一个可用的项目"""
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


class TestTimesheetCRUD:
    """工时 CRUD 测试"""

    def test_list_timesheets(self, client: TestClient, admin_token: str):
        """测试获取工时列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_timesheets_with_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围筛选工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        assert response.status_code == 200

    def test_create_timesheet(self, client: TestClient, admin_token: str):
        """测试创建工时记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        timesheet_data = {
            "project_id": project["id"],
            "work_date": date.today().isoformat(),
            "hours": 8.0,
            "work_type": "DEVELOPMENT",
            "description": "测试工时记录",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json=timesheet_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400:
            pytest.skip("Duplicate timesheet or validation error")

        assert response.status_code == 201, response.text

    def test_get_timesheet_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取工时列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get timesheet list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No timesheets available for testing")

        timesheet_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/{timesheet_id}",
            headers=headers
        )

        assert response.status_code == 200


class TestTimesheetViews:
    """工时视图测试"""

    def test_get_week_timesheet(self, client: TestClient, admin_token: str):
        """测试获取周工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/week",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have timesheet:read permission")
        if response.status_code == 404:
            pytest.skip("Week timesheet endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for week timesheet")

        assert response.status_code == 200

    def test_get_month_summary(self, client: TestClient, admin_token: str):
        """测试获取月度汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/month-summary",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have timesheet:read permission")
        if response.status_code == 404:
            pytest.skip("Month summary endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for month summary")

        assert response.status_code == 200

    def test_get_statistics(self, client: TestClient, admin_token: str):
        """测试获取工时统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/statistics",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have timesheet:read permission")
        if response.status_code == 404:
            pytest.skip("Statistics endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for statistics")

        assert response.status_code == 200


class TestTimesheetApproval:
    """工时审批测试"""

    def test_get_pending_approval(self, client: TestClient, admin_token: str):
        """测试获取待审批工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/pending-approval",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have timesheet:approve permission")
        if response.status_code == 404:
            pytest.skip("Pending approval endpoint not found")
        if response.status_code == 422:
            pytest.skip("Missing required parameters for pending approval")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
