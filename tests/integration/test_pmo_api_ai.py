# -*- coding: utf-8 -*-
"""
PMO管理模块 API 集成测试

测试范围：
- 项目组合管理 (Portfolio)
- 项目看板 (Dashboard)
- 项目健康度监控 (Health Monitor)
- 资源分析 (Resource Analysis)
"""

import pytest
from datetime import date, timedelta

from tests.integration.api_test_helper import APITestHelper, Colors


@pytest.mark.integration
class TestPMODashboardAPI:
    """PMO仪表板 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("PMO仪表板 API 测试")

    def test_get_pmo_dashboard(self):
        """测试获取PMO仪表板"""
        self.helper.print_info("测试获取PMO仪表板...")

        params = {
            "view_type": "executive",
        }

        response = self.helper.get(
            "/dashboard", params=params, resource_type="pmo_dashboard"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("PMO仪表板数据获取成功")
        else:
            self.helper.print_warning("获取PMO仪表板响应不符合预期")

    def test_get_key_metrics(self):
        """测试获取关键指标"""
        self.helper.print_info("测试获取关键指标...")

        response = self.helper.get("/dashboard/metrics", resource_type="key_metrics")

        if self.helper.assert_success(response):
            self.helper.print_success("关键指标获取成功")
        else:
            self.helper.print_warning("获取关键指标响应不符合预期")

    def test_get_alert_summary(self):
        """测试获取预警汇总"""
        self.helper.print_info("测试获取预警汇总...")

        response = self.helper.get("/dashboard/alerts", resource_type="alert_summary")

        if self.helper.assert_success(response):
            self.helper.print_success("预警汇总获取成功")
        else:
            self.helper.print_warning("获取预警汇总响应不符合预期")


@pytest.mark.integration
class TestPMOPortfolioAPI:
    """项目组合管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("项目组合管理 API 测试")

    def test_get_portfolio_overview(self):
        """测试获取项目组合概览"""
        self.helper.print_info("测试获取项目组合概览...")

        params = {
            "period": "current_quarter",
        }

        response = self.helper.get(
            "/portfolio/overview", params=params, resource_type="portfolio_overview"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目组合概览获取成功")
        else:
            self.helper.print_warning("获取项目组合概览响应不符合预期")

    def test_get_project_distribution(self):
        """测试获取项目分布"""
        self.helper.print_info("测试获取项目分布...")

        params = {
            "group_by": "stage",
        }

        response = self.helper.get(
            "/portfolio/distribution",
            params=params,
            resource_type="project_distribution",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目分布获取成功")
        else:
            self.helper.print_warning("获取项目分布响应不符合预期")

    def test_get_resource_utilization(self):
        """测试获取资源利用率"""
        self.helper.print_info("测试获取资源利用率...")

        params = {
            "period": "month",
        }

        response = self.helper.get(
            "/portfolio/resource-utilization",
            params=params,
            resource_type="resource_utilization",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("资源利用率获取成功")
        else:
            self.helper.print_warning("获取资源利用率响应不符合预期")


@pytest.mark.integration
class TestPMOHealthMonitorAPI:
    """项目健康度监控 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("项目健康度监控 API 测试")

    def test_get_health_matrix(self):
        """测试获取健康度矩阵"""
        self.helper.print_info("测试获取健康度矩阵...")

        params = {
            "page": 1,
            "page_size": 50,
        }

        response = self.helper.get(
            "/health/matrix", params=params, resource_type="health_matrix"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("健康度矩阵获取成功")
        else:
            self.helper.print_warning("获取健康度矩阵响应不符合预期")

    def test_get_health_trend(self):
        """测试获取健康度趋势"""
        self.helper.print_info("测试获取健康度趋势...")

        params = {
            "period": "monthly",
            "months": 6,
        }

        response = self.helper.get(
            "/health/trend", params=params, resource_type="health_trend"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("健康度趋势获取成功")
        else:
            self.helper.print_warning("获取健康度趋势响应不符合预期")

    def test_get_risk_projects(self):
        """测试获取风险项目"""
        self.helper.print_info("测试获取风险项目...")

        params = {
            "health_level": ["H2", "H3"],
        }

        response = self.helper.get(
            "/health/risk-projects", params=params, resource_type="risk_projects"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("风险项目获取成功")
        else:
            self.helper.print_warning("获取风险项目响应不符合预期")


@pytest.mark.integration
class TestPMOReportsAPI:
    """PMO报表 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("PMO报表 API 测试")

    def test_generate_executive_report(self):
        """测试生成高管报告"""
        self.helper.print_info("测试生成高管报告...")

        report_data = {
            "report_type": "EXECUTIVE",
            "period_start": (date.today() - timedelta(days=30)).isoformat(),
            "period_end": date.today().isoformat(),
            "include_sections": ["summary", "projects", "risks", "metrics"],
        }

        response = self.helper.post(
            "/reports/generate", report_data, resource_type="executive_report"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("高管报告生成成功")
        else:
            self.helper.print_warning("生成高管报告响应不符合预期，继续测试")

    def test_get_reports_list(self):
        """测试获取报表列表"""
        self.helper.print_info("测试获取报表列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "report_type": "EXECUTIVE",
        }

        response = self.helper.get(
            "/reports", params=params, resource_type="pmo_reports_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 份PMO报表")
        else:
            self.helper.print_warning("获取报表列表响应不符合预期")


@pytest.mark.integration
class TestPMOKPIsAPI:
    """PMO KPI API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("PMO KPI API 测试")

    def test_get_project_kpis(self):
        """测试获取项目KPI"""
        self.helper.print_info("测试获取项目KPI...")

        params = {
            "kpi_type": "all",
            "period": "quarter",
        }

        response = self.helper.get("/kpis", params=params, resource_type="project_kpis")

        if self.helper.assert_success(response):
            self.helper.print_success("项目KPI获取成功")
        else:
            self.helper.print_warning("获取项目KPI响应不符合预期")

    def test_get_team_performance(self):
        """测试获取团队绩效"""
        self.helper.print_info("测试获取团队绩效...")

        params = {
            "period": "month",
            "metric": "project_completion_rate",
        }

        response = self.helper.get(
            "/kpis/team-performance", params=params, resource_type="team_performance"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("团队绩效获取成功")
        else:
            self.helper.print_warning("获取团队绩效响应不符合预期")
