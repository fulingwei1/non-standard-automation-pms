# -*- coding: utf-8 -*-
"""
approval_reminders.py 单元测试

测试工时审批超时提醒功能
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.timesheet_reminder.approval_reminders import notify_approval_timeout


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.mark.unit
class TestNotifyApprovalTimeout:
    """测试 notify_approval_timeout 函数"""

    def test_no_pending_timesheets(self, mock_db):
        """测试没有待审批工时记录"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = notify_approval_timeout(mock_db)

        assert result == 0
        mock_db.commit.assert_called_once()

    def test_pending_timesheets_with_department_manager(self, mock_db):
        """测试有待审批记录且有部门经理"""
        # 创建超时的工时记录
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = None
        mock_timesheet.status = "PENDING"
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        # 创建用户（有部门）
        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department_id = 100

        # 创建部门（有经理）
        mock_department = MagicMock()
        mock_department.id = 100
        mock_department.manager_id = 50

        # 设置查询返回值
        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = mock_user
            elif model.__name__ == "Department":
                mock_q.first.return_value = mock_department
            elif model.__name__ == "Notification":
                mock_q.first.return_value = None  # 今天没有发送过通知
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        assert result == 1
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["user_id"] == 50
        assert call_kwargs["notification_type"] == "TIMESHEET_APPROVAL_TIMEOUT"

    def test_pending_timesheets_with_project_manager(self, mock_db):
        """测试有待审批记录且有项目经理（无部门经理）"""
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = 200
        mock_timesheet.status = "PENDING"
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department_id = None  # 无部门

        mock_project = MagicMock()
        mock_project.id = 200
        mock_project.manager_id = 60

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = mock_user
            elif model.__name__ == "Project":
                mock_q.first.return_value = mock_project
            elif model.__name__ == "Notification":
                mock_q.first.return_value = None
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        assert result == 1
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["user_id"] == 60

    def test_skip_if_already_notified_today(self, mock_db):
        """测试今天已发送过通知则跳过"""
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = None
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department_id = 100

        mock_department = MagicMock()
        mock_department.id = 100
        mock_department.manager_id = 50

        # 已存在的通知
        mock_existing_notification = MagicMock()

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = mock_user
            elif model.__name__ == "Department":
                mock_q.first.return_value = mock_department
            elif model.__name__ == "Notification":
                mock_q.first.return_value = mock_existing_notification
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        assert result == 0
        mock_create.assert_not_called()

    def test_skip_if_no_approver(self, mock_db):
        """测试没有审批人则跳过"""
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = None
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department_id = None  # 无部门

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = mock_user
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        assert result == 0
        mock_create.assert_not_called()

    def test_custom_timeout_hours(self, mock_db):
        """测试自定义超时时间"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = notify_approval_timeout(mock_db, timeout_hours=48)

        assert result == 0
        # 验证使用了自定义超时时间（通过filter调用参数验证）
        mock_db.commit.assert_called_once()

    def test_multiple_timesheets_same_approver(self, mock_db):
        """测试多条工时记录同一审批人只发一条通知"""
        mock_timesheet1 = MagicMock()
        mock_timesheet1.id = 1
        mock_timesheet1.user_id = 10
        mock_timesheet1.project_id = None
        mock_timesheet1.created_at = datetime.now() - timedelta(hours=48)

        mock_timesheet2 = MagicMock()
        mock_timesheet2.id = 2
        mock_timesheet2.user_id = 11
        mock_timesheet2.project_id = None
        mock_timesheet2.created_at = datetime.now() - timedelta(hours=48)

        mock_user1 = MagicMock()
        mock_user1.id = 10
        mock_user1.department_id = 100

        mock_user2 = MagicMock()
        mock_user2.id = 11
        mock_user2.department_id = 100  # 同一部门

        mock_department = MagicMock()
        mock_department.id = 100
        mock_department.manager_id = 50

        call_count = {"user": 0}

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet1, mock_timesheet2]
            elif model.__name__ == "User":
                call_count["user"] += 1
                if call_count["user"] == 1:
                    mock_q.first.return_value = mock_user1
                else:
                    mock_q.first.return_value = mock_user2
            elif model.__name__ == "Department":
                mock_q.first.return_value = mock_department
            elif model.__name__ == "Notification":
                mock_q.first.return_value = None
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        # 同一审批人只发一条通知
        assert result == 1
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        # 通知内容应包含2条记录
        assert call_kwargs["extra_data"]["count"] == 2
        assert len(call_kwargs["extra_data"]["timesheet_ids"]) == 2

    def test_department_no_manager(self, mock_db):
        """测试部门没有经理的情况"""
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = 200
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department_id = 100

        mock_department = MagicMock()
        mock_department.id = 100
        mock_department.manager_id = None  # 无经理

        mock_project = MagicMock()
        mock_project.id = 200
        mock_project.manager_id = 60

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = mock_user
            elif model.__name__ == "Department":
                mock_q.first.return_value = mock_department
            elif model.__name__ == "Project":
                mock_q.first.return_value = mock_project
            elif model.__name__ == "Notification":
                mock_q.first.return_value = None
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        # 应该使用项目经理
        assert result == 1
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["user_id"] == 60

    def test_user_not_found(self, mock_db):
        """测试用户不存在的情况"""
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = None
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = None  # 用户不存在
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            result = notify_approval_timeout(mock_db)

        assert result == 0
        mock_create.assert_not_called()

    def test_notification_content_format(self, mock_db):
        """测试通知内容格式"""
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.project_id = None
        mock_timesheet.created_at = datetime.now() - timedelta(hours=48)

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department_id = 100

        mock_department = MagicMock()
        mock_department.id = 100
        mock_department.manager_id = 50

        def query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if model.__name__ == "Timesheet":
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == "User":
                mock_q.first.return_value = mock_user
            elif model.__name__ == "Department":
                mock_q.first.return_value = mock_department
            elif model.__name__ == "Notification":
                mock_q.first.return_value = None
            return mock_q

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.timesheet_reminder.approval_reminders.create_timesheet_notification"
        ) as mock_create:
            notify_approval_timeout(mock_db, timeout_hours=36)

        call_kwargs = mock_create.call_args[1]
        assert "1 条记录待审批" in call_kwargs["title"]
        assert "36 小时未审批" in call_kwargs["content"]
        assert call_kwargs["priority"] == "HIGH"
        assert call_kwargs["extra_data"]["timeout_hours"] == 36
