# -*- coding: utf-8 -*-
"""
工时管理模块 API 集成测试

测试范围：
- 工时记录 (Time Entries)
- 工时审批 (Approval)
- 工时统计 (Statistics)
- 工时报表 (Reports)
"""

import pytest
from datetime import date, timedelta

from tests.integration.api_test_helper import APITestHelper, Colors


@pytest.mark.integration
class TestTimesheetEntriesAPI:
    """工时记录 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("工时记录 API 测试")

    def test_create_time_entry(self):
        """测试创建工时记录"""
        self.helper.print_info("测试创建工时记录...")

        entry_data = {
            "project_id": self.test_project_id,
            "employee_id": 1,  # 假设存在员工ID
            "work_date": date.today().isoformat(),
            "task_type": "DESIGN",
            "task_description": "技术方案设计",
            "work_hours": 8.0,
            "break_hours": 1.0,
            "notes": "完成了FCT设备的整体技术方案设计",
        }

        response = self.helper.post("/entries", entry_data, resource_type="time_entry")

        result = self.helper.assert_success(response)
        if result:
            entry_id = result.get("id")
            if entry_id:
                self.tracked_resources.append(("time_entry", entry_id))
                self.helper.print_success(f"工时记录创建成功，ID: {entry_id}")
            else:
                self.helper.print_warning("工时记录创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建工时记录响应不符合预期，继续测试")

    def test_get_entries_list(self):
        """测试获取工时记录列表"""
        self.helper.print_info("测试获取工时记录列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/entries", params=params, resource_type="time_entries_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条工时记录")
        else:
            self.helper.print_warning("获取工时记录列表响应不符合预期")

    def test_update_time_entry(self):
        """测试更新工时记录"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工时记录ID")

        entry_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新工时记录 (ID: {entry_id})...")

        update_data = {
            "work_hours": 9.0,
            "notes": "更新：实际工作了9小时，包含评审时间",
        }

        response = self.helper.put(
            f"/entries/{entry_id}",
            update_data,
            resource_type=f"time_entry_{entry_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工时记录更新成功")
        else:
            self.helper.print_warning("更新工时记录响应不符合预期")

    def test_submit_timesheet(self):
        """测试提交工时表"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工时记录ID")

        self.helper.print_info("测试提交工时表...")

        submit_data = {
            "period_start": (date.today() - timedelta(days=7)).isoformat(),
            "period_end": date.today().isoformat(),
            "entry_ids": [self.tracked_resources[0][1]],
        }

        response = self.helper.post(
            "/timesheet/submit", submit_data, resource_type="timesheet_submit"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工时表提交成功")
        else:
            self.helper.print_warning("提交工时表响应不符合预期")


@pytest.mark.integration
class TestTimesheetApprovalAPI:
    """工时审批 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("工时审批 API 测试")

    def test_get_pending_approvals(self):
        """测试获取待审批工时"""
        self.helper.print_info("测试获取待审批工时...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "PENDING",
        }

        response = self.helper.get(
            "/approvals", params=params, resource_type="pending_approvals"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条待审批工时")
        else:
            self.helper.print_warning("获取待审批工时响应不符合预期")

    def test_approve_timesheet(self):
        """测试审批工时"""
        self.helper.print_info("测试审批工时...")

        approval_data = {
            "timesheet_id": 1,  # 假设存在工时表ID
            "approval_status": "APPROVED",
            "approval_comments": "工时记录准确，审批通过",
            "approved_by": 1,
        }

        response = self.helper.post(
            "/approvals/approve", approval_data, resource_type="timesheet_approve"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工时审批成功")
        else:
            self.helper.print_warning("审批工时响应不符合预期")

    def test_reject_timesheet(self):
        """测试拒绝工时"""
        self.helper.print_info("测试拒绝工时...")

        reject_data = {
            "timesheet_id": 1,  # 假设存在工时表ID
            "approval_status": "REJECTED",
            "rejection_reason": "工时记录有误，请重新核对",
            "rejected_by": 1,
        }

        response = self.helper.post(
            "/approvals/reject", reject_data, resource_type="timesheet_reject"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工时拒绝成功")
        else:
            self.helper.print_warning("拒绝工时响应不符合预期")


@pytest.mark.integration
class TestTimesheetStatisticsAPI:
    """工时统计 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("工时统计 API 测试")

    def test_get_timesheet_summary(self):
        """测试获取工时汇总"""
        self.helper.print_info("测试获取工时汇总...")

        params = {
            "project_id": self.test_project_id,
            "period": "month",
        }

        response = self.helper.get(
            "/statistics/summary", params=params, resource_type="timesheet_summary"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工时汇总获取成功")
        else:
            self.helper.print_warning("获取工时汇总响应不符合预期")

    def test_get_employee_statistics(self):
        """测试获取员工工时统计"""
        self.helper.print_info("测试获取员工工时统计...")

        params = {
            "employee_id": 1,
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/statistics/employee", params=params, resource_type="employee_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("员工工时统计获取成功")
        else:
            self.helper.print_warning("获取员工工时统计响应不符合预期")

    def test_get_project_statistics(self):
        """测试获取项目工时统计"""
        self.helper.print_info("测试获取项目工时统计...")

        params = {
            "project_id": self.test_project_id,
            "group_by": "task_type",
        }

        response = self.helper.get(
            "/statistics/project", params=params, resource_type="project_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目工时统计获取成功")
        else:
            self.helper.print_warning("获取项目工时统计响应不符合预期")


@pytest.mark.integration
class TestTimesheetReportsAPI:
    """工时报表 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("工时报表 API 测试")

    def test_generate_timesheet_report(self):
        """测试生成工时报表"""
        self.helper.print_info("测试生成工时报表...")

        report_data = {
            "project_id": self.test_project_id,
            "report_type": "WEEKLY",
            "period_start": (date.today() - timedelta(days=7)).isoformat(),
            "period_end": date.today().isoformat(),
            "include_details": True,
        }

        response = self.helper.post(
            "/reports/generate", report_data, resource_type="timesheet_report"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工时报表生成成功")
        else:
            self.helper.print_warning("生成工时报表响应不符合预期，继续测试")

    def test_get_reports_list(self):
        """测试获取报表列表"""
        self.helper.print_info("测试获取报表列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "report_type": "WEEKLY",
        }

        response = self.helper.get(
            "/reports", params=params, resource_type="reports_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 份工时报表")
        else:
            self.helper.print_warning("获取报表列表响应不符合预期")
