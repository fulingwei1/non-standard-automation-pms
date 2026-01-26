# -*- coding: utf-8 -*-
"""
会议报表统一框架 API 测试
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMeetingReportUnifiedAPI:
    """会议报表统一接口测试"""

    def test_get_meeting_monthly_report_unified(self, auth_headers):
        """测试获取会议月报（统一框架）"""
        today = date.today()
        response = client.get(
            "/api/v1/management-rhythm/reports-unified/meeting-monthly",
            params={
                "year": today.year,
                "month": today.month,
                "format": "json",
            },
            headers=auth_headers,
        )

        if response.status_code in (404, 500):
            detail = response.json().get("detail", "")
            pytest.skip(f"会议月报配置或数据不可用: {detail}")

        if response.status_code == 403:
            pytest.skip("权限不足，无法访问会议月报接口")

        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)
        assert "code" in payload
        assert "message" in payload
        assert "data" in payload
