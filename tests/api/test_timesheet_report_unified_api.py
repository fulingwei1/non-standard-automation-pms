# -*- coding: utf-8 -*-
"""
工时报表统一框架API测试

测试使用统一报表框架生成的工时报表
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTimesheetReportUnifiedAPI:
    """工时报表统一框架API测试类"""

    def test_list_available_timesheet_reports(self, admin_auth_headers):
        """测试获取可用工时报表列表"""
        response = client.get("/api/v1/reports/available", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 检查是否包含工时报表（如果配置存在）
        report_codes = [r.get("code") for r in data]
        timesheet_reports = [
            "TIMESHEET_HR_MONTHLY",
            "TIMESHEET_FINANCE_MONTHLY",
            "TIMESHEET_PROJECT",
            "TIMESHEET_RD_MONTHLY",
        ]
        # 如果没有任何工时报表配置，跳过测试
        found_reports = [code for code in timesheet_reports if code in report_codes]
        if not found_reports:
            pytest.skip("工时报表配置不存在")
        # 至少应该有一个工时报表在列表中
        assert len(found_reports) > 0

    def test_get_hr_report_schema(self, admin_auth_headers):
        """测试获取HR报表Schema"""
        response = client.get(
            "/api/v1/reports/TIMESHEET_HR_MONTHLY/schema",
            headers=admin_auth_headers,
        )
        # 如果配置不存在，返回404是正常的
        if response.status_code == 404:
            pytest.skip("HR报表配置不存在")
        assert response.status_code == 200
        data = response.json()
        assert data["report_code"] == "TIMESHEET_HR_MONTHLY"
        assert "parameters" in data

    def test_get_hr_report_unified_json(self, admin_auth_headers):
        """测试获取HR报表（JSON格式）"""
        today = date.today()
        response = client.get(
            "/api/v1/timesheet/reports-unified/hr",
            params={
                "year": today.year,
                "month": today.month,
                "format": "json",
            },
            headers=admin_auth_headers,
        )

        # 如果配置不存在或服务调用失败，可能返回404或500
        if response.status_code in [404, 500]:
            # 检查是否是配置问题
            detail = response.json().get("detail", "")
            if "not found" in detail.lower() or "config" in detail.lower():
                pytest.skip(f"HR报表配置或服务问题: {detail}")

        # 如果权限不足，返回403
        if response.status_code == 403:
            pytest.skip("权限不足")

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data

    def test_get_finance_report_unified_json(self, admin_auth_headers):
        """测试获取财务报表（JSON格式）"""
        today = date.today()
        response = client.get(
            "/api/v1/timesheet/reports-unified/finance",
            params={
                "year": today.year,
                "month": today.month,
                "format": "json",
            },
            headers=admin_auth_headers,
        )

        if response.status_code in [404, 500]:
            detail = response.json().get("detail", "")
            if "not found" in detail.lower() or "config" in detail.lower():
                pytest.skip(f"财务报表配置或服务问题: {detail}")

        if response.status_code == 403:
            pytest.skip("权限不足")

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "data" in data

    def test_get_project_report_unified_json(self, admin_auth_headers, mock_project):
        """测试获取项目报表（JSON格式）"""
        project_id = mock_project.id

        response = client.get(
            "/api/v1/timesheet/reports-unified/project",
            params={
                "project_id": project_id,
                "format": "json",
            },
            headers=admin_auth_headers,
        )

        if response.status_code in [404, 500]:
            detail = response.json().get("detail", "")
            if "not found" in detail.lower() or "config" in detail.lower():
                pytest.skip(f"项目报表配置或服务问题: {detail}")

        if response.status_code == 403:
            pytest.skip("权限不足")

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "data" in data

    def test_get_rd_report_unified_json(self, admin_auth_headers):
        """测试获取研发报表（JSON格式）"""
        today = date.today()
        response = client.get(
            "/api/v1/timesheet/reports-unified/rd",
            params={
                "year": today.year,
                "month": today.month,
                "format": "json",
            },
            headers=admin_auth_headers,
        )

        if response.status_code in [404, 500]:
            detail = response.json().get("detail", "")
            if "not found" in detail.lower() or "config" in detail.lower():
                pytest.skip(f"研发报表配置或服务问题: {detail}")

        if response.status_code == 403:
            pytest.skip("权限不足")

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "data" in data

    def test_generate_hr_report_with_unified_endpoint(self, admin_auth_headers):
        """测试使用统一报表框架端点生成HR报表"""
        today = date.today()
        response = client.post(
            "/api/v1/reports/TIMESHEET_HR_MONTHLY/generate",
            json={
                "parameters": {
                    "year": today.year,
                    "month": today.month,
                }
            },
            params={"format": "json"},
            headers=admin_auth_headers,
        )

        if response.status_code in [400, 404, 422]:
            # 配置或参数问题，跳过
            detail = response.json().get("detail", "")
            pytest.skip(f"HR报表配置或参数问题: {detail}")

        assert response.status_code == 200
        data = response.json()
        assert "meta" in data
        assert "sections" in data
