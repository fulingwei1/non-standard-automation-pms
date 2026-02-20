# -*- coding: utf-8 -*-
"""
Alert Exceptions Service 单元测试
目标覆盖率: >= 60%
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.alert_exceptions import AlertExceptionsService
from app.schemas.alert import ExceptionEventCreate


class TestAlertExceptionsService(unittest.TestCase):
    """AlertExceptionsService 单元测试类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = AlertExceptionsService(self.db)

    def test_init(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.db, self.db)

    @patch('app.services.alert_exceptions.service.apply_keyword_filter')
    @patch('app.services.alert_exceptions.service.apply_pagination')
    def test_get_exception_events_basic(self, mock_pagination, mock_filter):
        """测试获取异常事件列表（基础场景）"""
        # Mock 数据
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_pagination.return_value.all.return_value = []

        # 调用方法
        events, total = self.service.get_exception_events(
            offset=0,
            limit=10,
        )

        # 断言
        self.assertEqual(total, 10)
        self.assertEqual(events, [])
        self.db.query.assert_called_once()

    @patch('app.services.alert_exceptions.service.apply_keyword_filter')
    @patch('app.services.alert_exceptions.service.apply_pagination')
    def test_get_exception_events_with_filters(self, mock_pagination, mock_filter):
        """测试获取异常事件列表（带筛选条件）"""
        # Mock 数据
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_pagination.return_value.all.return_value = []

        # 调用方法
        events, total = self.service.get_exception_events(
            offset=0,
            limit=10,
            keyword="test",
            project_id=1,
            event_type="QUALITY",
            severity="CRITICAL",
            status="OPEN",
            responsible_user_id=2,
        )

        # 断言
        self.assertEqual(total, 5)
        # 验证所有筛选条件都被应用
        self.assertEqual(mock_query.filter.call_count, 5)

    def test_build_event_list_item(self):
        """测试构建事件列表项数据"""
        # Mock 事件对象
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.event_no = "EXC-2024-001"
        mock_event.source_type = "MANUAL"
        mock_event.project_id = 1
        mock_event.project.project_name = "测试项目"
        mock_event.machine_id = 1
        mock_event.machine.machine_name = "测试设备"
        mock_event.event_type = "QUALITY"
        mock_event.severity = "CRITICAL"
        mock_event.event_title = "测试异常"
        mock_event.status = "OPEN"
        mock_event.discovered_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_event.discovered_by = 1
        mock_event.schedule_impact = 5
        mock_event.cost_impact = 1000.0
        mock_event.responsible_user_id = 2
        mock_event.due_date = datetime(2024, 1, 10, 10, 0, 0)
        mock_event.is_overdue = False
        mock_event.created_at = datetime(2024, 1, 1, 9, 0, 0)

        # Mock 用户查询
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # 调用方法
        result = self.service.build_event_list_item(mock_event)

        # 断言
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["event_no"], "EXC-2024-001")
        self.assertEqual(result["event_title"], "测试异常")
        self.assertEqual(result["discovered_by_name"], "张三")
        self.assertEqual(result["severity"], "CRITICAL")

    def test_create_exception_event_success(self):
        """测试创建异常事件（成功）"""
        # Mock 项目和设备查询
        mock_project = MagicMock()
        mock_machine = MagicMock()

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Machine':
                mock_query.filter.return_value.first.return_value = mock_machine
            return mock_query

        self.db.query.side_effect = query_side_effect

        # Mock ExceptionEventCreate
        event_in = ExceptionEventCreate(
            source_type="MANUAL",
            event_type="QUALITY",
            severity="CRITICAL",
            event_title="测试异常",
            event_description="测试描述",
            project_id=1,
            machine_id=1,
        )

        # 调用方法
        with patch('app.services.alert_exceptions.service.ExceptionEvent') as MockEvent:
            mock_instance = MagicMock()
            MockEvent.return_value = mock_instance

            result = self.service.create_exception_event(
                event_in=event_in,
                current_user_id=1,
                event_no="EXC-2024-001",
            )

            # 断言
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once()

    def test_create_exception_event_project_not_found(self):
        """测试创建异常事件（项目不存在）"""
        # Mock 项目查询返回 None
        self.db.query.return_value.filter.return_value.first.return_value = None

        event_in = ExceptionEventCreate(
            source_type="MANUAL",
            event_type="QUALITY",
            severity="CRITICAL",
            event_title="测试异常",
            project_id=999,
        )

        # 断言抛出 ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_exception_event(
                event_in=event_in,
                current_user_id=1,
                event_no="EXC-2024-001",
            )

        self.assertIn("项目不存在", str(context.exception))

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_get_exception_event_detail(self, mock_get_or_404):
        """测试获取异常事件详情"""
        # Mock 事件对象
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.event_no = "EXC-2024-001"
        mock_event.status = "OPEN"
        mock_event.discovered_by = 1
        mock_event.project.project_name = "测试项目"
        mock_event.machine.machine_name = "测试设备"
        mock_event.actions.order_by.return_value.all.return_value = []

        mock_get_or_404.return_value = mock_event

        # Mock 用户查询
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # 调用方法
        result = self.service.get_exception_event_detail(event_id=1)

        # 断言
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["event_no"], "EXC-2024-001")
        self.assertEqual(result["status"], "OPEN")
        self.assertEqual(result["discovered_by_name"], "张三")

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_update_exception_status(self, mock_get_or_404):
        """测试更新异常状态"""
        # Mock 事件对象
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.status = "OPEN"
        mock_event.resolved_at = None

        mock_get_or_404.return_value = mock_event

        # 调用方法（更新为已解决）
        result = self.service.update_exception_status(
            event_id=1,
            new_status="RESOLVED",
            current_user_id=1,
        )

        # 断言
        self.assertEqual(result.status, "RESOLVED")
        self.assertIsNotNone(result.resolved_at)
        self.assertEqual(result.resolved_by, 1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_add_exception_action(self, mock_get_or_404):
        """测试添加处理记录"""
        # Mock 事件对象
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.status = "OPEN"

        mock_get_or_404.return_value = mock_event

        # 调用方法
        with patch('app.services.alert_exceptions.service.ExceptionAction') as MockAction:
            mock_action = MagicMock()
            mock_action.id = 1
            MockAction.return_value = mock_action

            result = self.service.add_exception_action(
                event_id=1,
                action_type="COMMENT",
                action_content="测试备注",
                current_user_id=1,
            )

            # 断言
            self.assertEqual(result.id, 1)
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_escalate_exception(self, mock_get_or_404):
        """测试异常升级"""
        # Mock 事件对象
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.severity = "MINOR"
        mock_event.responsible_user_id = 1

        mock_get_or_404.return_value = mock_event

        # 调用方法
        with patch('app.services.alert_exceptions.service.ExceptionEscalation') as MockEscalation:
            result = self.service.escalate_exception(
                event_id=1,
                escalate_to_user_id=2,
                escalate_to_dept="技术部",
                escalation_reason="问题严重",
                current_user_id=1,
            )

            # 断言
            self.assertEqual(result.severity, "MAJOR")  # 严重程度升级
            self.assertEqual(result.responsible_user_id, 2)  # 责任人更新
            self.assertEqual(result.responsible_dept, "技术部")  # 部门更新
            MockEscalation.assert_called_once()  # 创建升级记录
            self.db.commit.assert_called_once()

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_create_exception_from_issue(self, mock_get_or_404):
        """测试从问题创建异常事件"""
        # Mock 问题对象
        mock_issue = MagicMock()
        mock_issue.id = 1
        mock_issue.project_id = 1
        mock_issue.machine_id = 1
        mock_issue.issue_title = "测试问题"
        mock_issue.issue_description = "问题描述"
        mock_issue.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_issue.reporter_id = 1

        mock_get_or_404.return_value = mock_issue

        # 调用方法
        with patch('app.services.alert_exceptions.service.ExceptionEvent') as MockEvent:
            mock_instance = MagicMock()
            MockEvent.return_value = mock_instance

            result = self.service.create_exception_from_issue(
                issue_id=1,
                event_type="QUALITY",
                severity="CRITICAL",
                current_user_id=1,
                event_no="EXC-2024-001",
            )

            # 断言
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once()
            MockEvent.assert_called_once()


if __name__ == '__main__':
    unittest.main()
