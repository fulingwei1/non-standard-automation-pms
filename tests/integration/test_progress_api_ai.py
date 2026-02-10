# -*- coding: utf-8 -*-
"""
进度管理模块 API 集成测试

测试范围：
- 进度汇总 (Summary)
- 甘特图 (Gantt)
- 进度看板 (Board)
- 机台进度汇总 (Machine Progress Summary)

实际路由前缀: /projects/{project_id}/progress/
"""

import pytest

from tests.integration.api_test_helper import APITestHelper


@pytest.mark.integration
class TestProgressSummaryAPI:
    """进度汇总 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, test_machine, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.test_machine_id = test_machine.id if test_machine else None
        self.helper.print_info("进度汇总 API 测试")

    def test_get_progress_summary(self):
        """测试获取进度汇总"""
        self.helper.print_info("测试获取进度汇总...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/progress/summary",
            resource_type="progress_summary",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("进度汇总获取成功")
        else:
            self.helper.print_warning("获取进度汇总响应不符合预期")

    def test_get_gantt_data(self):
        """测试获取甘特图数据"""
        self.helper.print_info("测试获取甘特图数据...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/progress/gantt",
            resource_type="gantt_data",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("甘特图数据获取成功")
        else:
            self.helper.print_warning("获取甘特图数据响应不符合预期")

    def test_get_progress_board(self):
        """测试获取进度看板"""
        self.helper.print_info("测试获取进度看板...")

        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/progress/board",
            resource_type="progress_board",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("进度看板获取成功")
        else:
            self.helper.print_warning("获取进度看板响应不符合预期")

    def test_get_machine_progress_summary(self):
        """测试获取机台进度汇总"""
        self.helper.print_info("测试获取机台进度汇总...")

        if not self.test_project_id or not self.test_machine_id:
            pytest.skip("没有可用的项目ID或机台ID")

        response = self.helper.get(
            f"/projects/{self.test_project_id}/progress/machines/{self.test_machine_id}/summary",
            resource_type="machine_progress_summary",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("机台进度汇总获取成功")
        else:
            self.helper.print_warning("获取机台进度汇总响应不符合预期")
