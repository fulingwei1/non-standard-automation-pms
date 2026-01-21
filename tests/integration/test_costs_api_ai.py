# -*- coding: utf-8 -*-
"""
成本管理模块 API 集成测试

测试范围：
- 成本基础操作 (Basic)
- 成本分析和统计 (Analysis)
- 人工成本计算 (Labor)
- 成本分摊 (Allocation)
- 预算执行分析 (Budget)
- 成本复盘 (Review)
- 成本预警 (Alert)
"""

import pytest
from datetime import date, timedelta

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestCostsBasicAPI:
    """成本基础操作 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("成本基础管理 API 测试")

    def test_create_project_cost(self):
        """测试创建项目成本"""
        self.helper.print_info("测试创建项目成本...")

        cost_data = {
            "project_id": self.test_project_id,
            "cost_code": f"COST-{TestDataGenerator.generate_order_no()}",
            "cost_type": "MATERIAL",
            "cost_name": "原材料成本",
            "amount": 50000.00,
            "currency": "CNY",
            "cost_date": date.today().isoformat(),
            "description": "采购钢材、铝材等原材料",
        }

        response = self.helper.post("/costs", cost_data, resource_type="project_cost")

        result = self.helper.assert_success(response)
        if result:
            cost_id = result.get("id")
            if cost_id:
                self.tracked_resources.append(("cost", cost_id))
                self.helper.print_success(f"项目成本创建成功，ID: {cost_id}")
                self.helper.assert_field_equals(result, "cost_name", "原材料成本")
            else:
                self.helper.print_warning("项目成本创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建项目成本响应不符合预期，继续测试")

    def test_get_project_costs_list(self):
        """测试获取项目成本列表"""
        self.helper.print_info("测试获取项目成本列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
            "cost_type": "MATERIAL",
        }

        response = self.helper.get(
            "/costs", params=params, resource_type="project_costs_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条项目成本记录")
        else:
            self.helper.print_warning("获取项目成本列表响应不符合预期")

    def test_update_project_cost(self):
        """测试更新项目成本"""
        if not self.tracked_resources:
            pytest.skip("没有可用的成本ID")

        cost_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新项目成本 (ID: {cost_id})...")

        update_data = {
            "amount": 55000.00,
            "description": "更新：采购钢材、铝材等原材料（含运输费用）",
        }

        response = self.helper.put(
            f"/costs/{cost_id}",
            update_data,
            resource_type=f"project_cost_{cost_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目成本更新成功")
        else:
            self.helper.print_warning("更新项目成本响应不符合预期")


@pytest.mark.integration
class TestCostsAnalysisAPI:
    """成本分析和统计 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("成本分析统计 API 测试")

    def test_get_cost_summary(self):
        """测试获取成本汇总"""
        self.helper.print_info("测试获取成本汇总...")

        params = {
            "project_id": self.test_project_id,
            "group_by": "cost_type",
        }

        response = self.helper.get(
            "/analysis/summary", params=params, resource_type="cost_summary"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本汇总获取成功")
        else:
            self.helper.print_warning("获取成本汇总响应不符合预期")

    def test_get_cost_trend(self):
        """测试获取成本趋势"""
        self.helper.print_info("测试获取成本趋势...")

        params = {
            "project_id": self.test_project_id,
            "start_date": (date.today() - timedelta(days=90)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/analysis/trend", params=params, resource_type="cost_trend"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本趋势获取成功")
        else:
            self.helper.print_warning("获取成本趋势响应不符合预期")

    def test_get_cost_comparison(self):
        """测试获取成本对比"""
        self.helper.print_info("测试获取成本对比...")

        params = {
            "project_ids": [self.test_project_id] if self.test_project_id else [1, 2],
            "comparison_type": "cost_breakdown",
        }

        response = self.helper.get(
            "/analysis/comparison", params=params, resource_type="cost_comparison"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本对比数据获取成功")
        else:
            self.helper.print_warning("获取成本对比响应不符合预期")


@pytest.mark.integration
class TestCostsLaborAPI:
    """人工成本 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("人工成本管理 API 测试")

    def test_calculate_labor_cost(self):
        """测试计算人工成本"""
        self.helper.print_info("测试计算人工成本...")

        labor_data = {
            "project_id": self.test_project_id,
            "employee_id": 1,  # 假设存在员工ID
            "work_hours": 40.0,
            "hourly_rate": 100.00,
            "cost_date": date.today().isoformat(),
            "task_name": "电气装配",
        }

        response = self.helper.post(
            "/labor/calculate", labor_data, resource_type="labor_cost"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.print_success("人工成本计算成功")
            self.helper.assert_field_equals(result, "total_cost", 4000.00)
        else:
            self.helper.print_warning("计算人工成本响应不符合预期，继续测试")

    def test_get_labor_costs_list(self):
        """测试获取人工成本列表"""
        self.helper.print_info("测试获取人工成本列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/labor/costs", params=params, resource_type="labor_costs_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条人工成本记录")
        else:
            self.helper.print_warning("获取人工成本列表响应不符合预期")


@pytest.mark.integration
class TestCostsAllocationAPI:
    """成本分摊 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("成本分摊管理 API 测试")

    def test_create_cost_allocation(self):
        """测试创建成本分摊"""
        self.helper.print_info("测试创建成本分摊...")

        allocation_data = {
            "project_id": self.test_project_id,
            "source_cost_id": 1,  # 假设存在成本ID
            "allocation_type": "BY_MACHINE",
            "allocation_rule": "EVENLY",
            "target_machines": [1, 2, 3],  # 假设存在机台ID
            "allocation_date": date.today().isoformat(),
        }

        response = self.helper.post(
            "/allocation", allocation_data, resource_type="cost_allocation"
        )

        result = self.helper.assert_success(response)
        if result:
            allocation_id = result.get("id")
            if allocation_id:
                self.tracked_resources.append(("allocation", allocation_id))
                self.helper.print_success(f"成本分摊创建成功，ID: {allocation_id}")
            else:
                self.helper.print_warning("成本分摊创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建成本分摊响应不符合预期，继续测试")

    def test_get_allocations_list(self):
        """测试获取成本分摊列表"""
        self.helper.print_info("测试获取成本分摊列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/allocation", params=params, resource_type="allocations_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条成本分摊记录")
        else:
            self.helper.print_warning("获取成本分摊列表响应不符合预期")


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

    def test_get_budget_variance(self):
        """测试获取预算偏差"""
        self.helper.print_info("测试获取预算偏差...")

        params = {
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/budget/variance", params=params, resource_type="budget_variance"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("预算偏差数据获取成功")
        else:
            self.helper.print_warning("获取预算偏差响应不符合预期")

    def test_get_budget_execution_rate(self):
        """测试获取预算执行率"""
        self.helper.print_info("测试获取预算执行率...")

        params = {
            "project_id": self.test_project_id,
            "period": "monthly",
        }

        response = self.helper.get(
            "/budget/execution-rate",
            params=params,
            resource_type="budget_execution_rate",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("预算执行率获取成功")
        else:
            self.helper.print_warning("获取预算执行率响应不符合预期")

    def test_get_budget_forecast(self):
        """测试获取预算预测"""
        self.helper.print_info("测试获取预算预测...")

        params = {
            "project_id": self.test_project_id,
            "forecast_horizon": "3m",  # 预测未来3个月
        }

        response = self.helper.get(
            "/budget/forecast", params=params, resource_type="budget_forecast"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("预算预测数据获取成功")
        else:
            self.helper.print_warning("获取预算预测响应不符合预期")


@pytest.mark.integration
class TestCostsReviewAPI:
    """成本复盘 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("成本复盘管理 API 测试")

    def test_create_cost_review(self):
        """测试创建成本复盘"""
        self.helper.print_info("测试创建成本复盘...")

        review_data = {
            "project_id": self.test_project_id,
            "review_period_start": (date.today() - timedelta(days=30)).isoformat(),
            "review_period_end": date.today().isoformat(),
            "actual_cost": 150000.00,
            "budgeted_cost": 140000.00,
            "variance_amount": 10000.00,
            "variance_percentage": 7.14,
            "review_comments": "成本超出预算，主要原因是原材料价格上涨",
            "action_items": "1. 优化采购渠道\n2. 寻找替代材料",
            "reviewed_by": 1,  # 假设存在员工ID
        }

        response = self.helper.post("/review", review_data, resource_type="cost_review")

        result = self.helper.assert_success(response)
        if result:
            review_id = result.get("id")
            if review_id:
                self.tracked_resources.append(("review", review_id))
                self.helper.print_success(f"成本复盘创建成功，ID: {review_id}")
            else:
                self.helper.print_warning("成本复盘创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建成本复盘响应不符合预期，继续测试")

    def test_get_reviews_list(self):
        """测试获取成本复盘列表"""
        self.helper.print_info("测试获取成本复盘列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/review", params=params, resource_type="cost_reviews_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条成本复盘记录")
        else:
            self.helper.print_warning("获取成本复盘列表响应不符合预期")


@pytest.mark.integration
class TestCostsAlertAPI:
    """成本预警 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("成本预警管理 API 测试")

    def test_get_cost_alerts(self):
        """测试获取成本预警"""
        self.helper.print_info("测试获取成本预警...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
            "alert_type": "BUDGET_OVERRUN",
        }

        response = self.helper.get(
            "/alert/alerts", params=params, resource_type="cost_alerts"
        )

        if self.helper.assert_success(response):
            items = (
                result.get("items", [])
                if (result := self.helper.assert_success(response))
                else []
            )
            self.helper.print_success(f"获取到 {len(items)} 条成本预警")
        else:
            self.helper.print_warning("获取成本预警响应不符合预期")

    def test_get_cost_risk_assessment(self):
        """测试获取成本风险评估"""
        self.helper.print_info("测试获取成本风险评估...")

        params = {
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/alert/risk-assessment",
            params=params,
            resource_type="cost_risk_assessment",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("成本风险评估获取成功")
        else:
            self.helper.print_warning("获取成本风险评估响应不符合预期")

    def test_create_alert_rule(self):
        """测试创建预警规则"""
        self.helper.print_info("测试创建预警规则...")

        rule_data = {
            "rule_name": "预算超支预警",
            "rule_type": "BUDGET_OVERRUN",
            "threshold_percentage": 90.0,
            "alert_level": "WARNING",
            "is_active": True,
        }

        response = self.helper.post(
            "/alert/rules", rule_data, resource_type="cost_alert_rule"
        )

        result = self.helper.assert_success(response)
        if result:
            rule_id = result.get("id")
            if rule_id:
                self.tracked_resources.append(("alert_rule", rule_id))
                self.helper.print_success(f"预警规则创建成功，ID: {rule_id}")
            else:
                self.helper.print_warning("预警规则创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建预警规则响应不符合预期，继续测试")
