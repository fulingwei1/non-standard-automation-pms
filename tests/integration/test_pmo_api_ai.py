# -*- coding: utf-8 -*-
"""
PMO管理模块 API 集成测试

测试范围：
- PMO仪表板 (Dashboard/Cockpit)
- PMO会议 (Meetings)
- PMO风险墙 (Risk Wall)
- PMO资源概览 (Resource Overview)
"""

import pytest
from datetime import date, timedelta

from tests.integration.api_test_helper import APITestHelper


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
            "/pmo/dashboard", params=params, resource_type="pmo_dashboard"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("PMO仪表板数据获取成功")
        else:
            self.helper.print_warning("获取PMO仪表板响应不符合预期")

    def test_get_risk_wall(self):
        """测试获取风险墙"""
        self.helper.print_info("测试获取风险墙...")

        response = self.helper.get("/pmo/risk-wall", resource_type="risk_wall")

        if self.helper.assert_success(response):
            self.helper.print_success("风险墙获取成功")
        else:
            self.helper.print_warning("获取风险墙响应不符合预期")

    def test_get_resource_overview(self):
        """测试获取资源概览"""
        self.helper.print_info("测试获取资源概览...")

        response = self.helper.get("/pmo/resource-overview", resource_type="resource_overview")

        if self.helper.assert_success(response):
            self.helper.print_success("资源概览获取成功")
        else:
            self.helper.print_warning("获取资源概览响应不符合预期")


@pytest.mark.integration
class TestPMOMeetingsAPI:
    """PMO会议管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("PMO会议管理 API 测试")

    def test_get_meetings_list(self):
        """测试获取会议列表"""
        self.helper.print_info("测试获取会议列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/pmo/meetings", params=params, resource_type="pmo_meetings_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条会议记录")
        else:
            self.helper.print_warning("获取会议列表响应不符合预期")

    def test_create_meeting(self):
        """测试创建会议"""
        self.helper.print_info("测试创建会议...")

        meeting_data = {
            "meeting_type": "PROJECT_REVIEW",
            "meeting_name": "项目进度评审会",
            "meeting_date": (date.today() + timedelta(days=3)).isoformat(),
            "location": "会议室A",
            "agenda": "1. 项目进度汇报\n2. 风险评估\n3. 下一步计划",
        }

        response = self.helper.post(
            "/pmo/meetings", meeting_data, resource_type="pmo_meeting"
        )

        result = self.helper.assert_success(response)
        if result:
            meeting_id = result.get("id")
            if meeting_id:
                self.tracked_resources.append(("meeting", meeting_id))
                self.helper.print_success(f"会议创建成功，ID: {meeting_id}")
            else:
                self.helper.print_warning("会议创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建会议响应不符合预期，继续测试")


@pytest.mark.integration
class TestPMOInitiationsAPI:
    """PMO项目立项 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("PMO项目立项 API 测试")

    def test_get_initiations_list(self):
        """测试获取项目立项列表"""
        self.helper.print_info("测试获取项目立项列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/pmo/initiations", params=params, resource_type="pmo_initiations_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条项目立项记录")
        else:
            self.helper.print_warning("获取项目立项列表响应不符合预期")


@pytest.mark.integration
class TestPMOWeeklyReportAPI:
    """PMO周报 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("PMO周报 API 测试")

    def test_get_weekly_report(self):
        """测试获取周报"""
        self.helper.print_info("测试获取周报...")

        response = self.helper.get(
            "/pmo/weekly-report", resource_type="pmo_weekly_report"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("周报数据获取成功")
        else:
            self.helper.print_warning("获取周报响应不符合预期")


@pytest.mark.integration
class TestPMORisksAPI:
    """PMO项目风险 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else 1
        self.tracked_resources = []
        self.helper.print_info("PMO项目风险 API 测试")

    def test_get_project_risks(self):
        """测试获取项目风险列表"""
        self.helper.print_info("测试获取项目风险列表...")

        response = self.helper.get(
            f"/pmo/projects/{self.test_project_id}/risks",
            resource_type="pmo_project_risks",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目风险列表获取成功")
        else:
            self.helper.print_warning("获取项目风险列表响应不符合预期")

    def test_create_project_risk(self):
        """测试创建项目风险"""
        self.helper.print_info("测试创建项目风险...")

        risk_data = {
            "risk_name": "供应商交付延迟",
            "risk_category": "SUPPLY_CHAIN",
            "probability": "HIGH",
            "impact": "HIGH",
            "description": "关键物料供应商可能无法按时交付",
            "mitigation_plan": "提前备货，寻找备选供应商",
        }

        response = self.helper.post(
            f"/pmo/projects/{self.test_project_id}/risks",
            risk_data,
            resource_type="pmo_project_risk",
        )

        result = self.helper.assert_success(response)
        if result:
            risk_id = result.get("id")
            if risk_id:
                self.tracked_resources.append(("risk", risk_id))
                self.helper.print_success(f"项目风险创建成功，ID: {risk_id}")
            else:
                self.helper.print_warning("项目风险创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建项目风险响应不符合预期，继续测试")
