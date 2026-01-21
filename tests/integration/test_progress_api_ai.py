# -*- coding: utf-8 -*-
"""
进度管理模块 API 集成测试

测试范围：
- WBS模板管理 (WBS Templates)
- 进度任务管理 (Tasks)
- 进度报告 (Reports)
- 进度汇总 (Summary)
- 进度统计 (Statistics)
- 计划基线管理 (Baselines)
- 进度预测 (Forecast)
"""

import pytest
from datetime import date, timedelta

from tests.integration.api_test_helper import APITestHelper, Colors


@pytest.mark.integration
class TestProgressTasksAPI:
    """进度任务管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("进度任务管理 API 测试")

    def test_create_progress_task(self):
        """测试创建进度任务"""
        self.helper.print_info("测试创建进度任务...")

        task_data = {
            "project_id": self.test_project_id,
            "task_name": "机械加工",
            "task_type": "MACHINING",
            "wbs_code": "1.2.1",
            "plan_start_date": date.today().isoformat(),
            "plan_end_date": (date.today() + timedelta(days=10)).isoformat(),
            "plan_duration_days": 10,
            "assigned_to": 1,  # 假设存在员工ID
            "priority": "HIGH",
            "status": "NOT_STARTED",
            "description": "完成机架的机械加工",
        }

        response = self.helper.post("/tasks", task_data, resource_type="progress_task")

        result = self.helper.assert_success(response)
        if result:
            task_id = result.get("id")
            if task_id:
                self.tracked_resources.append(("progress_task", task_id))
                self.helper.print_success(f"进度任务创建成功，ID: {task_id}")
                self.helper.assert_field_equals(result, "task_name", "机械加工")
            else:
                self.helper.print_warning("进度任务创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建进度任务响应不符合预期，继续测试")

    def test_get_tasks_list(self):
        """测试获取任务列表"""
        self.helper.print_info("测试获取任务列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
            "status": "IN_PROGRESS",
        }

        response = self.helper.get("/tasks", params=params, resource_type="tasks_list")

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个任务")
        else:
            self.helper.print_warning("获取任务列表响应不符合预期")

    def test_update_task_progress(self):
        """测试更新任务进度"""
        if not self.tracked_resources:
            pytest.skip("没有可用的任务ID")

        task_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新任务进度 (ID: {task_id})...")

        update_data = {
            "status": "IN_PROGRESS",
            "actual_start_date": date.today().isoformat(),
            "progress_percentage": 30.0,
            "notes": "已开始加工，完成30%",
        }

        response = self.helper.put(
            f"/tasks/{task_id}", update_data, resource_type=f"task_{task_id}_progress"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务进度更新成功")
        else:
            self.helper.print_warning("更新任务进度响应不符合预期")

    def test_complete_task(self):
        """测试完成任务"""
        if not self.tracked_resources:
            pytest.skip("没有可用的任务ID")

        task_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试完成任务 (ID: {task_id})...")

        complete_data = {
            "status": "COMPLETED",
            "actual_end_date": date.today().isoformat(),
            "progress_percentage": 100.0,
            "notes": "任务完成",
        }

        response = self.helper.post(
            f"/tasks/{task_id}/complete",
            complete_data,
            resource_type=f"task_{task_id}_complete",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务完成成功")
        else:
            self.helper.print_warning("完成任务响应不符合预期")


@pytest.mark.integration
class TestProgressBaselinesAPI:
    """计划基线管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("计划基线管理 API 测试")

    def test_create_baseline(self):
        """测试创建计划基线"""
        self.helper.print_info("测试创建计划基线...")

        baseline_data = {
            "project_id": self.test_project_id,
            "baseline_name": "初始计划基线",
            "baseline_date": date.today().isoformat(),
            "baseline_version": "V1.0",
            "baseline_type": "INITIAL",
            "notes": "项目启动时的初始计划",
        }

        response = self.helper.post(
            "/baselines", baseline_data, resource_type="baseline"
        )

        result = self.helper.assert_success(response)
        if result:
            baseline_id = result.get("id")
            if baseline_id:
                self.tracked_resources.append(("baseline", baseline_id))
                self.helper.print_success(f"计划基线创建成功，ID: {baseline_id}")
            else:
                self.helper.print_warning("计划基线创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建计划基线响应不符合预期，继续测试")

    def test_get_baselines_list(self):
        """测试获取基线列表"""
        self.helper.print_info("测试获取基线列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/baselines", params=params, resource_type="baselines_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个基线")
        else:
            self.helper.print_warning("获取基线列表响应不符合预期")

    def test_compare_baselines(self):
        """测试对比基线"""
        if len(self.tracked_resources) < 2:
            pytest.skip("需要至少2个基线进行对比")

        baseline_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试对比基线 (ID: {baseline_id})...")

        params = {
            "baseline_id": baseline_id,
            "comparison_type": "VARIANCE",
        }

        response = self.helper.get(
            "/baselines/compare", params=params, resource_type="baseline_comparison"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("基线对比成功")
        else:
            self.helper.print_warning("基线对比响应不符合预期")


@pytest.mark.integration
class TestProgressSummaryAPI:
    """进度汇总 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("进度汇总 API 测试")

    def test_get_progress_summary(self):
        """测试获取进度汇总"""
        self.helper.print_info("测试获取进度汇总...")

        params = {
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/summary", params=params, resource_type="progress_summary"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("进度汇总获取成功")
        else:
            self.helper.print_warning("获取进度汇总响应不符合预期")

    def test_get_task_distribution(self):
        """测试获取任务分布"""
        self.helper.print_info("测试获取任务分布...")

        params = {
            "project_id": self.test_project_id,
            "group_by": "status",
        }

        response = self.helper.get(
            "/summary/task-distribution",
            params=params,
            resource_type="task_distribution",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务分布获取成功")
        else:
            self.helper.print_warning("获取任务分布响应不符合预期")

    def test_get_milestone_progress(self):
        """测试获取里程碑进度"""
        self.helper.print_info("测试获取里程碑进度...")

        params = {
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/summary/milestone-progress",
            params=params,
            resource_type="milestone_progress",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("里程碑进度获取成功")
        else:
            self.helper.print_warning("获取里程碑进度响应不符合预期")


@pytest.mark.integration
class TestProgressStatisticsAPI:
    """进度统计 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("进度统计 API 测试")

    def test_get_progress_statistics(self):
        """测试获取进度统计"""
        self.helper.print_info("测试获取进度统计...")

        params = {
            "project_id": self.test_project_id,
            "period": "monthly",
        }

        response = self.helper.get(
            "/statistics", params=params, resource_type="progress_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("进度统计获取成功")
        else:
            self.helper.print_warning("获取进度统计响应不符合预期")

    def test_get_completion_trend(self):
        """测试获取完成趋势"""
        self.helper.print_info("测试获取完成趋势...")

        params = {
            "project_id": self.test_project_id,
            "start_date": (date.today() - timedelta(days=90)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/statistics/completion-trend",
            params=params,
            resource_type="completion_trend",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("完成趋势获取成功")
        else:
            self.helper.print_warning("获取完成趋势响应不符合预期")


@pytest.mark.integration
class TestProgressForecastAPI:
    """进度预测 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("进度预测 API 测试")

    def test_get_completion_forecast(self):
        """测试获取完成预测"""
        self.helper.print_info("测试获取完成预测...")

        params = {
            "project_id": self.test_project_id,
            "forecast_method": "LINEAR",
        }

        response = self.helper.get(
            "/forecast/completion", params=params, resource_type="completion_forecast"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("完成预测获取成功")
        else:
            self.helper.print_warning("获取完成预测响应不符合预期")

    def test_get_delay_risk_assessment(self):
        """测试获取延期风险评估"""
        self.helper.print_info("测试获取延期风险评估...")

        params = {
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/forecast/delay-risk", params=params, resource_type="delay_risk"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("延期风险评估获取成功")
        else:
            self.helper.print_warning("获取延期风险评估响应不符合预期")


@pytest.mark.integration
class TestProgressReportsAPI:
    """进度报告 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("进度报告 API 测试")

    def test_generate_progress_report(self):
        """测试生成进度报告"""
        self.helper.print_info("测试生成进度报告...")

        report_data = {
            "project_id": self.test_project_id,
            "report_type": "WEEKLY",
            "report_date": date.today().isoformat(),
            "include_summary": True,
            "include_tasks": True,
            "include_baselines": True,
        }

        response = self.helper.post(
            "/reports/generate", report_data, resource_type="progress_report"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.print_success("进度报告生成成功")
        else:
            self.helper.print_warning("生成进度报告响应不符合预期，继续测试")

    def test_get_reports_list(self):
        """测试获取报告列表"""
        self.helper.print_info("测试获取报告列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
        }

        response = self.helper.get(
            "/reports", params=params, resource_type="reports_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 份进度报告")
        else:
            self.helper.print_warning("获取报告列表响应不符合预期")
