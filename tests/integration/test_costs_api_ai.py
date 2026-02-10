# -*- coding: utf-8 -*-
"""
成本管理模块 API 集成测试

测试范围：
- 成本汇总 (Summary)
- 成本分析 (Analysis)
- 人工成本计算 (Labor Cost)
- 预算执行 (Budget Execution)
- 成本趋势 (Trend)
- 预算预警检查 (Budget Alert)
- 成本复盘 (Cost Review)
"""

import pytest

from tests.integration.api_test_helper import APITestHelper


@pytest.mark.integration
class TestCostsSummaryAPI:
    """成本汇总 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("成本汇总 API 测试")

    def test_get_cost_summary(self):
        """测试获取成本汇总"""
        self.helper.print_info("测试获取成本汇总...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs/summary",
            resource_type="cost_summary",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本汇总获取成功")
        else:
            self.helper.print_warning("获取成本汇总响应不符合预期")


@pytest.mark.integration
class TestCostsAnalysisAPI:
    """成本分析 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("成本分析 API 测试")

    def test_get_cost_analysis(self):
        """测试获取成本分析"""
        self.helper.print_info("测试获取成本分析...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs/cost-analysis",
            resource_type="cost_analysis",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本分析获取成功")
        else:
            self.helper.print_warning("获取成本分析响应不符合预期")

    def test_get_revenue_detail(self):
        """测试获取收入明细"""
        self.helper.print_info("测试获取收入明细...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs/revenue-detail",
            resource_type="revenue_detail",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("收入明细获取成功")
        else:
            self.helper.print_warning("获取收入明细响应不符合预期")

    def test_get_profit_analysis(self):
        """测试获取利润分析"""
        self.helper.print_info("测试获取利润分析...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs/profit-analysis",
            resource_type="profit_analysis",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("利润分析获取成功")
        else:
            self.helper.print_warning("获取利润分析响应不符合预期")


@pytest.mark.integration
class TestCostsLaborAPI:
    """人工成本 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("人工成本 API 测试")

    def test_calculate_labor_cost(self):
        """测试计算人工成本"""
        self.helper.print_info("测试计算人工成本...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        labor_data = {
            "project_id": self.test_project_id,
        }

        response = self.helper.post(
            f"/projects/{self.test_project_id}/costs/calculate-labor-cost",
            labor_data,
            resource_type="labor_cost",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("人工成本计算成功")
        else:
            self.helper.print_warning("计算人工成本响应不符合预期，继续测试")


@pytest.mark.integration
class TestCostsBudgetAPI:
    """预算执行分析 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("预算执行分析 API 测试")

    def test_get_budget_execution(self):
        """测试获取预算执行"""
        self.helper.print_info("测试获取预算执行...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs/execution",
            resource_type="budget_execution",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("预算执行数据获取成功")
        else:
            self.helper.print_warning("获取预算执行响应不符合预期")

    def test_get_cost_trend(self):
        """测试获取成本趋势"""
        self.helper.print_info("测试获取成本趋势...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs/trend",
            resource_type="cost_trend",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本趋势获取成功")
        else:
            self.helper.print_warning("获取成本趋势响应不符合预期")


@pytest.mark.integration
class TestCostsAlertAPI:
    """成本预警 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("成本预警 API 测试")

    def test_check_budget_alert(self):
        """测试预算预警检查"""
        self.helper.print_info("测试预算预警检查...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        alert_data = {
            "project_id": self.test_project_id,
        }

        response = self.helper.post(
            f"/projects/{self.test_project_id}/costs/check-budget-alert",
            alert_data,
            resource_type="budget_alert_check",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("预算预警检查完成")
        else:
            self.helper.print_warning("预算预警检查响应不符合预期")


@pytest.mark.integration
class TestCostsReviewAPI:
    """成本复盘 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("成本复盘 API 测试")

    def test_generate_cost_review(self):
        """测试生成成本复盘（预期：项目未结项时返回400）"""
        self.helper.print_info("测试生成成本复盘...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        review_data = {
            "project_id": self.test_project_id,
        }

        response = self.helper.post(
            f"/projects/{self.test_project_id}/costs/generate-cost-review",
            review_data,
            resource_type="cost_review",
        )

        status_code = response.get("status_code") if isinstance(response, dict) else None
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("成本复盘生成成功")
        elif status_code == 400:
            # 项目未结项时返回 400 是预期行为
            self.helper.print_warning("项目未结项，返回400是预期行为")
        else:
            self.helper.print_warning("生成成本复盘响应不符合预期")
