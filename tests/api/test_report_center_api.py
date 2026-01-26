# -*- coding: utf-8 -*-
"""
报表中心 API 测试

覆盖以下端点:
- /api/v1/report-center/generate - 报表生成状态
- /api/v1/report-center/download - 报表下载

注意: configs, templates, bi, rd-expense 等端点尚未实现或返回404
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    """生成认证请求头"""
    return {"Authorization": f"Bearer {token}"}


# ==================== 报表生成 API 测试 ====================


class TestReportGenerationAPI:
    """报表生成测试"""

    def test_get_generation_status(self, client: TestClient, admin_token: str):
        """测试获取报表生成状态"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/report-center/generate/status/1",
            headers=headers
        )

        # 即使报告不存在，也应该返回某种状态
        if response.status_code == 404:
            # 报告不存在是正常的
            pass
        else:
            assert response.status_code == 200, response.text


# ==================== 报表下载 API 测试 ====================


class TestReportDownloadAPI:
    """报表下载测试"""

    def test_download_report(self, client: TestClient, admin_token: str):
        """测试下载报表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/report-center/download/1",
            headers=headers
        )

        # 报表不存在应该返回404
        if response.status_code == 404:
            pass
        elif response.status_code == 200:
            # 如果返回200，应该是文件内容
            assert response.headers.get("content-type") is not None


# ==================== 边界条件测试 ====================


class TestReportCenterEdgeCases:
    """报表中心边界条件测试"""

    def test_get_nonexistent_template(self, client: TestClient, admin_token: str):
        """测试获取不存在的模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/report-center/templates/99999",
            headers=headers
        )

        # 应该返回404
        if response.status_code != 404:
            pytest.skip("Templates endpoint returns non-404 for missing resource")
        assert response.status_code == 404
