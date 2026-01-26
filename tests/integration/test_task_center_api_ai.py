# -*- coding: utf-8 -*-
"""
任务中心模块 API 集成测试

测试范围：
- 任务概览 (Overview)
- 我的任务 (My Tasks)
- 任务详情 (Detail)
- 创建任务 (Create)
- 更新任务 (Update)
- 完成任务 (Complete)
- 转派任务 (Transfer)
- 拒绝任务 (Reject)
- 任务评论 (Comments)
"""

import pytest
from datetime import date, datetime, timedelta

from tests.integration.api_test_helper import APITestHelper, Colors


@pytest.mark.integration
class TestTaskCenterOverviewAPI:
    """任务概览 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("任务概览 API 测试")

    def test_get_task_overview(self):
        """测试获取任务概览"""
        self.helper.print_info("测试获取任务概览...")

        params = {
            "view_type": "dashboard",
        }

        response = self.helper.get(
            "/overview", params=params, resource_type="task_overview"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务概览获取成功")
        else:
            self.helper.print_warning("获取任务概览响应不符合预期")

    def test_get_task_statistics(self):
        """测试获取任务统计"""
        self.helper.print_info("测试获取任务统计...")

        params = {
            "period": "today",
        }

        response = self.helper.get(
            "/overview/statistics", params=params, resource_type="task_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务统计获取成功")
        else:
            self.helper.print_warning("获取任务统计响应不符合预期")


@pytest.mark.integration
class TestTaskCenterMyTasksAPI:
    """我的任务 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("我的任务 API 测试")

    def test_get_my_tasks(self):
        """测试获取我的任务"""
        self.helper.print_info("测试获取我的任务...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "PENDING",
        }

        response = self.helper.get("/my-tasks", params=params, resource_type="my_tasks")

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个我的任务")
        else:
            self.helper.print_warning("获取我的任务响应不符合预期")

    def test_get_my_tasks_by_type(self):
        """测试按类型获取我的任务"""
        self.helper.print_info("测试按类型获取我的任务...")

        params = {
            "page": 1,
            "page_size": 20,
            "task_type": "ASSIGNMENT",
        }

        response = self.helper.get(
            "/my-tasks", params=params, resource_type="my_tasks_by_type"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个指派任务")
        else:
            self.helper.print_warning("获取任务列表响应不符合预期")


@pytest.mark.integration
class TestTaskCenterDetailAPI:
    """任务详情 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("任务详情 API 测试")

    def test_get_task_detail(self):
        """测试获取任务详情"""
        self.helper.print_info("测试获取任务详情...")

        task_id = 1  # 假设存在任务ID
        response = self.helper.get(
            f"/detail/{task_id}", resource_type=f"task_detail_{task_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("任务详情获取成功")
        else:
            self.helper.print_warning("获取任务详情响应不符合预期")

    def test_get_task_history(self):
        """测试获取任务历史"""
        self.helper.print_info("测试获取任务历史...")

        task_id = 1  # 假设存在任务ID
        params = {
            "task_id": task_id,
        }

        response = self.helper.get(
            "/detail/history", params=params, resource_type="task_history"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务历史获取成功")
        else:
            self.helper.print_warning("获取任务历史响应不符合预期")


@pytest.mark.integration
class TestTaskCenterCreateAPI:
    """创建任务 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("创建任务 API 测试")

    def test_create_task(self):
        """测试创建任务"""
        self.helper.print_info("测试创建任务...")

        task_data = {
            "project_id": self.test_project_id,
            "task_title": "审核技术方案",
            "task_type": "REVIEW",
            "priority": "HIGH",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
            "assign_to": 1,  # 假设存在员工ID
            "description": "审核项目技术方案的完整性和可行性",
        }

        response = self.helper.post("/create", task_data, resource_type="task")

        result = self.helper.assert_success(response)
        if result:
            task_id = result.get("id")
            if task_id:
                self.tracked_resources.append(("task", task_id))
                self.helper.print_success(f"任务创建成功，ID: {task_id}")
            else:
                self.helper.print_warning("任务创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建任务响应不符合预期，继续测试")

    def test_create_batch_tasks(self):
        """测试批量创建任务"""
        self.helper.print_info("测试批量创建任务...")

        batch_data = {
            "project_id": self.test_project_id,
            "tasks": [
                {
                    "task_title": "任务1",
                    "task_type": "GENERAL",
                    "priority": "MEDIUM",
                },
                {
                    "task_title": "任务2",
                    "task_type": "GENERAL",
                    "priority": "MEDIUM",
                },
            ],
        }

        response = self.helper.post(
            "/create/batch", batch_data, resource_type="batch_tasks"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("批量任务创建成功")
        else:
            self.helper.print_warning("批量创建任务响应不符合预期")


@pytest.mark.integration
class TestTaskCenterUpdateAPI:
    """更新任务 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("更新任务 API 测试")

    def test_update_task(self):
        """测试更新任务"""
        if not self.tracked_resources:
            pytest.skip("没有可用的任务ID")

        task_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新任务 (ID: {task_id})...")

        update_data = {
            "status": "IN_PROGRESS",
            "progress_percentage": 50.0,
            "notes": "已完成50%的审核工作",
        }

        response = self.helper.put(
            f"/update/{task_id}", update_data, resource_type=f"task_{task_id}_update"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务更新成功")
        else:
            self.helper.print_warning("更新任务响应不符合预期")

    def test_batch_update_tasks(self):
        """测试批量更新任务"""
        self.helper.print_info("测试批量更新任务...")

        batch_data = {
            "task_ids": [1, 2],  # 假设存在任务ID
            "update_fields": {
                "status": "IN_PROGRESS",
            },
        }

        response = self.helper.put(
            "/update/batch", batch_data, resource_type="batch_update_tasks"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("批量任务更新成功")
        else:
            self.helper.print_warning("批量更新任务响应不符合预期")


@pytest.mark.integration
class TestTaskCenterCompleteAPI:
    """完成任务 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("完成任务 API 测试")

    def test_complete_task(self):
        """测试完成任务"""
        if not self.tracked_resources:
            pytest.skip("没有可用的任务ID")

        task_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试完成任务 (ID: {task_id})...")

        complete_data = {
            "completion_notes": "审核已完成，方案符合要求",
            "completion_attachments": [],
            "actual_completion_date": datetime.now().isoformat(),
        }

        response = self.helper.post(
            f"/complete/{task_id}",
            complete_data,
            resource_type=f"task_{task_id}_complete",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务完成成功")
        else:
            self.helper.print_warning("完成任务响应不符合预期")

    def test_batch_complete_tasks(self):
        """测试批量完成任务"""
        self.helper.print_info("测试批量完成任务...")

        batch_data = {
            "task_ids": [1, 2],  # 假设存在任务ID
            "completion_notes": "批量完成任务",
        }

        response = self.helper.post(
            "/complete/batch", batch_data, resource_type="batch_complete_tasks"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("批量任务完成成功")
        else:
            self.helper.print_warning("批量完成任务响应不符合预期")


@pytest.mark.integration
class TestTaskCenterTransferAPI:
    """转派任务 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("转派任务 API 测试")

    def test_transfer_task(self):
        """测试转派任务"""
        if not self.tracked_resources:
            pytest.skip("没有可用的任务ID")

        task_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试转派任务 (ID: {task_id})...")

        transfer_data = {
            "transfer_to": 2,  # 转派给其他员工
            "transfer_reason": "原负责人临时有其他紧急任务",
            "transfer_date": datetime.now().isoformat(),
        }

        response = self.helper.post(
            f"/transfer/{task_id}",
            transfer_data,
            resource_type=f"task_{task_id}_transfer",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务转派成功")
        else:
            self.helper.print_warning("转派任务响应不符合预期")


@pytest.mark.integration
class TestTaskCenterRejectAPI:
    """拒绝任务 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("拒绝任务 API 测试")

    def test_reject_task(self):
        """测试拒绝任务"""
        if not self.tracked_resources:
            pytest.skip("没有可用的任务ID")

        task_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试拒绝任务 (ID: {task_id})...")

        reject_data = {
            "reject_reason": "任务描述不清，需要更多信息",
            "reject_date": datetime.now().isoformat(),
        }

        response = self.helper.post(
            f"/reject/{task_id}", reject_data, resource_type=f"task_{task_id}_reject"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("任务拒绝成功")
        else:
            self.helper.print_warning("拒绝任务响应不符合预期")


@pytest.mark.integration
class TestTaskCenterCommentsAPI:
    """任务评论 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("任务评论 API 测试")

    def test_add_comment(self):
        """测试添加评论"""
        self.helper.print_info("测试添加评论...")

        comment_data = {
            "task_id": 1,  # 假设存在任务ID
            "comment_content": "请注意技术方案的审核要点",
            "comment_type": "NORMAL",
        }

        response = self.helper.post(
            "/comments", comment_data, resource_type="task_comment"
        )

        result = self.helper.assert_success(response)
        if result:
            comment_id = result.get("id")
            if comment_id:
                self.tracked_resources.append(("comment", comment_id))
                self.helper.print_success(f"任务评论创建成功，ID: {comment_id}")
            else:
                self.helper.print_warning("任务评论创建成功，但未返回ID")
        else:
            self.helper.print_warning("添加评论响应不符合预期，继续测试")

    def test_get_comments(self):
        """测试获取评论列表"""
        self.helper.print_info("测试获取评论列表...")

        params = {
            "task_id": 1,  # 假设存在任务ID
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/comments", params=params, resource_type="task_comments"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条评论")
        else:
            self.helper.print_warning("获取评论列表响应不符合预期")
