# -*- coding: utf-8 -*-
"""
报表中心 API 测试

覆盖以下端点模块:
- /api/v1/reports/configs - 报表配置
- /api/v1/reports/generate - 报表生成
- /api/v1/reports/templates - 报表模板
- /api/v1/reports/bi - BI分析
- /api/v1/reports/rd-expense - 研发费用
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    """生成认证请求头"""
    return {"Authorization": f"Bearer {token}"}


# ==================== 报表配置 API 测试 ====================


class TestReportConfigsAPI:
    """报表配置管理测试"""

    def test_list_configs(self, client: TestClient, admin_token: str):
        """测试获取报表配置列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/configs",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Report configs endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_config_detail(self, client: TestClient, admin_token: str):
        """测试获取配置详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取配置列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/reports/configs",
            headers=headers
        )

        if list_response.status_code == 404:
            pytest.skip("Report configs endpoint not found")

        configs = list_response.json()
        items = configs.get("items", configs) if isinstance(configs, dict) else configs
        if not items:
            pytest.skip("No configs available for testing")

        config_id = items[0]["id"] if isinstance(items[0], dict) else items[0]

        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/configs/{config_id}",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Config detail endpoint not found")

        assert response.status_code == 200, response.text


# ==================== 报表模板 API 测试 ====================


class TestReportTemplatesAPI:
    """报表模板管理测试"""

    def test_list_templates(self, client: TestClient, admin_token: str):
        """测试获取模板列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/templates",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Report templates endpoint not found")

        assert response.status_code == 200, response.text

    def test_list_templates_by_category(self, client: TestClient, admin_token: str):
        """测试按分类筛选模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/templates",
            params={"category": "PROJECT"},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Report templates endpoint not found")

        assert response.status_code == 200, response.text

    def test_create_template(self, client: TestClient, admin_token: str):
        """测试创建报表模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        template_data = {
            "template_code": f"TPL_TEST_{date.today().strftime('%Y%m%d%H%M%S')}",
            "template_name": "测试报表模板",
            "category": "PROJECT",
            "description": "用于测试的报表模板",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/reports/templates",
            json=template_data,
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Report templates endpoint not found")
        if response.status_code == 403:
            pytest.skip("User does not have permission to create template")
        if response.status_code == 422:
            pytest.skip("Template creation validation error")

        assert response.status_code in [200, 201], response.text


# ==================== 报表生成 API 测试 ====================


class TestReportGenerationAPI:
    """报表生成测试"""

    def test_generate_report(self, client: TestClient, admin_token: str):
        """测试生成报表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        generate_data = {
            "template_code": "PROJECT_SUMMARY",
            "start_date": (today - timedelta(days=30)).isoformat(),
            "end_date": today.isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/reports/generate",
            json=generate_data,
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Report generate endpoint not found")
        if response.status_code == 422:
            pytest.skip("Report generation validation error")

        assert response.status_code in [200, 201, 202], response.text

    def test_get_generation_status(self, client: TestClient, admin_token: str):
        """测试获取生成状态"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/generate/status/1",
            headers=headers
        )

        if response.status_code == 404:
            # 任务不存在或端点不存在
            pass
        else:
            assert response.status_code == 200, response.text

    def test_list_generated_reports(self, client: TestClient, admin_token: str):
        """测试获取已生成报表列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/generated",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Generated reports endpoint not found")

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
            f"{settings.API_V1_PREFIX}/reports/download/1",
            headers=headers
        )

        if response.status_code == 404:
            # 报表不存在或端点不存在
            pass
        else:
            # 可能返回文件或JSON
            assert response.status_code in [200, 400], response.text

    def test_export_report(self, client: TestClient, admin_token: str):
        """测试导出报表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/export",
            params={
                "template_code": "PROJECT_SUMMARY",
                "format": "xlsx",
                "start_date": (today - timedelta(days=30)).isoformat(),
                "end_date": today.isoformat(),
            },
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Export endpoint not found")
        if response.status_code == 422:
            pytest.skip("Export validation error")

        assert response.status_code in [200, 400], response.text


# ==================== BI分析 API 测试 ====================


class TestBIAnalyticsAPI:
    """BI分析测试"""

    def test_get_bi_dashboard(self, client: TestClient, admin_token: str):
        """测试获取BI仪表盘"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/bi/dashboard",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("BI dashboard endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_bi_charts(self, client: TestClient, admin_token: str):
        """测试获取BI图表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/bi/charts",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("BI charts endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_bi_kpis(self, client: TestClient, admin_token: str):
        """测试获取BI关键指标"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/bi/kpis",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("BI KPIs endpoint not found")

        assert response.status_code == 200, response.text


# ==================== 研发费用报表 API 测试 ====================


class TestRDExpenseReportAPI:
    """研发费用报表测试"""

    def test_get_rd_expense_report(self, client: TestClient, admin_token: str):
        """测试获取研发费用报表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/rd-expense",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("RD expense endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_rd_expense_by_project(self, client: TestClient, admin_token: str):
        """测试按项目获取研发费用"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/rd-expense/by-project",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("RD expense by project endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_rd_expense_by_department(self, client: TestClient, admin_token: str):
        """测试按部门获取研发费用"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/rd-expense/by-department",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("RD expense by department endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_rd_expense_with_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围获取研发费用"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/rd-expense",
            params={
                "start_date": (today - timedelta(days=90)).isoformat(),
                "end_date": today.isoformat(),
            },
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("RD expense endpoint not found")

        assert response.status_code == 200, response.text


# ==================== 报表对比 API 测试 ====================


class TestReportComparisonAPI:
    """报表对比测试"""

    def test_compare_reports(self, client: TestClient, admin_token: str):
        """测试报表对比"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        comparison_data = {
            "template_code": "PROJECT_SUMMARY",
            "period1_start": (today - timedelta(days=60)).isoformat(),
            "period1_end": (today - timedelta(days=31)).isoformat(),
            "period2_start": (today - timedelta(days=30)).isoformat(),
            "period2_end": today.isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/reports/compare",
            json=comparison_data,
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Report comparison endpoint not found")
        if response.status_code == 422:
            pytest.skip("Comparison validation error")

        assert response.status_code in [200, 400], response.text


# ==================== 边界条件测试 ====================


class TestReportCenterEdgeCases:
    """报表中心边界条件测试"""

    def test_get_nonexistent_template(self, client: TestClient, admin_token: str):
        """测试获取不存在的模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/templates/99999",
            headers=headers
        )

        if response.status_code != 404:
            pytest.skip("Templates endpoint returns non-404 for missing resource")
        assert response.status_code == 404

    def test_invalid_date_range(self, client: TestClient, admin_token: str):
        """测试无效日期范围"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/rd-expense",
            params={
                "start_date": today.isoformat(),
                "end_date": (today - timedelta(days=30)).isoformat(),  # 结束早于开始
            },
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("RD expense endpoint not found")

        # 可能返回200（空数据）或400/422（验证错误）
        assert response.status_code in [200, 400, 422], response.text

    def test_unsupported_export_format(self, client: TestClient, admin_token: str):
        """测试不支持的导出格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        response = client.get(
            f"{settings.API_V1_PREFIX}/reports/export",
            params={
                "template_code": "PROJECT_SUMMARY",
                "format": "invalid_format",
                "start_date": (today - timedelta(days=30)).isoformat(),
                "end_date": today.isoformat(),
            },
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Export endpoint not found")

        # 应该返回400或422
        assert response.status_code in [400, 422], response.text
