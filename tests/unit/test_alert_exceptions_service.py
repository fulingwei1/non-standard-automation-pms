# -*- coding: utf-8 -*-
"""
Alert Exceptions Service 单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.alert_exceptions.service import AlertExceptionsService
from app.models.alert import ExceptionAction, ExceptionEscalation, ExceptionEvent
from app.models.issue import Issue
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.alert import ExceptionEventCreate


class TestAlertExceptionsService(unittest.TestCase):
    """测试异常告警服务类"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.service = AlertExceptionsService(self.mock_db)
        self.current_user_id = 1

    # ========== get_exception_events() 测试 ==========

    def test_get_exception_events_basic(self):
        """测试基本获取事件列表"""
        # Mock查询
        mock_query = MagicMock()
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        
        # 设置返回值 (offset=0时不调用offset(),只调用limit())
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_event]
        self.mock_db.query.return_value = mock_query

        # 执行测试
        events, total = self.service.get_exception_events(offset=0, limit=10)

        # 验证结果
        self.assertEqual(total, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_no, "EXC-001")

    def test_get_exception_events_with_keyword_filter(self):
        """测试关键词筛选"""
        mock_query = MagicMock()
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        
        # 设置filter返回同一个query对象，使链式调用可以继续
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_event]
        self.mock_db.query.return_value = mock_query

        events, total = self.service.get_exception_events(
            offset=0, limit=10, keyword="测试"
        )

        self.assertEqual(total, 1)

    def test_get_exception_events_with_project_filter(self):
        """测试项目筛选"""
        mock_query = MagicMock()
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_event]
        self.mock_db.query.return_value = mock_query

        events, total = self.service.get_exception_events(
            offset=0, limit=10, project_id=1
        )

        self.assertEqual(total, 1)
        # 验证filter被调用
        mock_query.filter.assert_called()

    def test_get_exception_events_with_all_filters(self):
        """测试所有筛选条件"""
        mock_query = MagicMock()
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_event]
        self.mock_db.query.return_value = mock_query

        events, total = self.service.get_exception_events(
            offset=0,
            limit=10,
            keyword="测试",
            project_id=1,
            event_type="QUALITY",
            severity="CRITICAL",
            status="OPEN",
            responsible_user_id=1,
        )

        self.assertEqual(total, 1)

    def test_get_exception_events_empty_result(self):
        """测试空结果"""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        events, total = self.service.get_exception_events(offset=0, limit=10)

        self.assertEqual(total, 0)
        self.assertEqual(len(events), 0)

    # ========== build_event_list_item() 测试 ==========

    def test_build_event_list_item_complete(self):
        """测试构建完整事件列表项"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.discovered_by = 1
        mock_event.discovered_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_event.created_at = datetime(2024, 1, 1, 9, 0, 0)
        
        # Mock用户查询
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.service.build_event_list_item(mock_event)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["event_no"], "EXC-001")
        self.assertEqual(result["event_title"], "测试异常")
        self.assertEqual(result["discovered_by_name"], "张三")
        self.assertEqual(result["discovered_at"], "2024-01-01T10:00:00")
        self.assertEqual(result["created_at"], "2024-01-01T09:00:00")

    def test_build_event_list_item_without_discovered_by(self):
        """测试没有发现人的情况"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.discovered_by = None

        result = self.service.build_event_list_item(mock_event)

        self.assertIsNone(result["discovered_by_name"])

    def test_build_event_list_item_with_null_dates(self):
        """测试空日期"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.discovered_at = None
        mock_event.due_date = None
        mock_event.created_at = None

        result = self.service.build_event_list_item(mock_event)

        self.assertIsNone(result["discovered_at"])
        self.assertIsNone(result["due_date"])
        self.assertIsNone(result["created_at"])

    def test_build_event_list_item_with_decimal_cost(self):
        """测试成本字段转换"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.cost_impact = Decimal("1234.56")

        result = self.service.build_event_list_item(mock_event)

        self.assertEqual(result["cost_impact"], 1234.56)

    # ========== create_exception_event() 测试 ==========

    def test_create_exception_event_success(self):
        """测试成功创建异常事件"""
        event_in = ExceptionEventCreate(
            source_type="MANUAL",
            project_id=1,
            machine_id=1,
            event_type="QUALITY",
            severity="MAJOR",
            event_title="测试异常",
            event_description="详细描述",
            schedule_impact=2,
            cost_impact=Decimal("1000.00"),
        )

        # Mock项目和设备查询
        mock_project = MagicMock()
        mock_machine = MagicMock()
        
        def mock_query_side_effect(model):
            if model == Project:
                query = MagicMock()
                query.filter.return_value.first.return_value = mock_project
                return query
            elif model == Machine:
                query = MagicMock()
                query.filter.return_value.first.return_value = mock_machine
                return query
            return MagicMock()

        self.mock_db.query.side_effect = mock_query_side_effect

        # 执行测试
        result = self.service.create_exception_event(
            event_in=event_in,
            current_user_id=1,
            event_no="EXC-001",
        )

        # 验证
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_create_exception_event_project_not_found(self):
        """测试项目不存在"""
        event_in = ExceptionEventCreate(
            source_type="MANUAL",
            project_id=999,
            event_type="QUALITY",
            severity="MAJOR",
            event_title="测试异常",
            event_description="详细描述",
        )

        # Mock项目不存在
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.create_exception_event(
                event_in=event_in,
                current_user_id=1,
                event_no="EXC-001",
            )

        self.assertEqual(str(context.exception), "项目不存在")

    def test_create_exception_event_machine_not_found(self):
        """测试设备不存在"""
        event_in = ExceptionEventCreate(
            source_type="MANUAL",
            machine_id=999,
            event_type="QUALITY",
            severity="MAJOR",
            event_title="测试异常",
            event_description="详细描述",
        )

        # Mock设备不存在
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.create_exception_event(
                event_in=event_in,
                current_user_id=1,
                event_no="EXC-001",
            )

        self.assertEqual(str(context.exception), "设备不存在")

    def test_create_exception_event_without_project_machine(self):
        """测试不关联项目和设备"""
        event_in = ExceptionEventCreate(
            source_type="MANUAL",
            event_type="QUALITY",
            severity="MAJOR",
            event_title="测试异常",
            event_description="详细描述",
        )

        result = self.service.create_exception_event(
            event_in=event_in,
            current_user_id=1,
            event_no="EXC-001",
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    # ========== get_exception_event_detail() 测试 ==========

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_get_exception_event_detail_success(self, mock_get_or_404):
        """测试获取详情成功"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.discovered_by = 1
        mock_event.discovered_at = datetime(2024, 1, 1, 10, 0, 0)
        
        # Mock actions
        mock_action = MagicMock()
        mock_action.id = 1
        mock_action.action_type = "COMMENT"
        mock_action.action_content = "测试处理"
        mock_action.old_status = "OPEN"
        mock_action.new_status = "OPEN"
        mock_action.created_by = 1
        mock_action.created_at = datetime(2024, 1, 2, 10, 0, 0)
        
        mock_event.actions.order_by.return_value.all.return_value = [mock_action]
        
        mock_get_or_404.return_value = mock_event

        # Mock用户查询
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.service.get_exception_event_detail(1)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["event_no"], "EXC-001")
        self.assertEqual(result["discovered_by_name"], "张三")
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["action_type"], "COMMENT")
        self.assertEqual(result["actions"][0]["action_user_name"], "张三")

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_get_exception_event_detail_no_discovered_by(self, mock_get_or_404):
        """测试无发现人"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.discovered_by = None
        mock_event.actions.order_by.return_value.all.return_value = []
        
        mock_get_or_404.return_value = mock_event

        result = self.service.get_exception_event_detail(1)

        self.assertIsNone(result["discovered_by_name"])

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_get_exception_event_detail_no_actions(self, mock_get_or_404):
        """测试无处理记录"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.actions.order_by.return_value.all.return_value = []
        
        mock_get_or_404.return_value = mock_event

        result = self.service.get_exception_event_detail(1)

        self.assertEqual(len(result["actions"]), 0)

    # ========== update_exception_status() 测试 ==========

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_update_exception_status_to_resolved(self, mock_get_or_404):
        """测试更新状态为已解决"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.status = "OPEN"
        mock_event.resolved_at = None
        mock_event.resolved_by = None
        
        mock_get_or_404.return_value = mock_event

        result = self.service.update_exception_status(
            event_id=1,
            new_status="RESOLVED",
            current_user_id=1,
        )

        self.assertEqual(mock_event.status, "RESOLVED")
        self.assertIsNotNone(mock_event.resolved_at)
        self.assertEqual(mock_event.resolved_by, 1)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_update_exception_status_to_in_progress(self, mock_get_or_404):
        """测试更新状态为处理中"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.status = "OPEN"
        
        mock_get_or_404.return_value = mock_event

        result = self.service.update_exception_status(
            event_id=1,
            new_status="IN_PROGRESS",
            current_user_id=1,
        )

        self.assertEqual(mock_event.status, "IN_PROGRESS")
        self.mock_db.commit.assert_called_once()

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_update_exception_status_already_resolved(self, mock_get_or_404):
        """测试已经标记过解决时间的情况"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.status = "OPEN"
        mock_event.resolved_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_event.resolved_by = 2
        
        mock_get_or_404.return_value = mock_event

        result = self.service.update_exception_status(
            event_id=1,
            new_status="RESOLVED",
            current_user_id=1,
        )

        # 不应该覆盖已有的解决时间
        self.assertEqual(mock_event.resolved_at, datetime(2024, 1, 1, 10, 0, 0))
        self.assertEqual(mock_event.resolved_by, 2)

    # ========== add_exception_action() 测试 ==========

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_add_exception_action_success(self, mock_get_or_404):
        """测试添加处理记录成功"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.status = "OPEN"
        
        mock_get_or_404.return_value = mock_event

        result = self.service.add_exception_action(
            event_id=1,
            action_type="COMMENT",
            action_content="测试处理",
            current_user_id=1,
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # 验证添加的action参数
        added_action = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_action.event_id, 1)
        self.assertEqual(added_action.action_type, "COMMENT")
        self.assertEqual(added_action.action_content, "测试处理")
        self.assertEqual(added_action.old_status, "OPEN")
        self.assertEqual(added_action.new_status, "OPEN")
        self.assertEqual(added_action.created_by, 1)

    # ========== escalate_exception() 测试 ==========

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_escalate_exception_with_user(self, mock_get_or_404):
        """测试升级到指定用户"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.severity = "MINOR"
        mock_event.responsible_user_id = 1
        
        mock_get_or_404.return_value = mock_event

        result = self.service.escalate_exception(
            event_id=1,
            escalate_to_user_id=2,
            escalate_to_dept="技术部",
            escalation_reason="问题严重，需要升级",
            current_user_id=1,
        )

        # 验证升级记录被添加
        self.assertEqual(self.mock_db.add.call_count, 2)  # escalation + event
        
        # 验证严重程度提升
        self.assertEqual(mock_event.severity, "MAJOR")
        
        # 验证责任人更新
        self.assertEqual(mock_event.responsible_user_id, 2)
        self.assertEqual(mock_event.responsible_dept, "技术部")
        
        self.mock_db.commit.assert_called_once()

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_escalate_exception_severity_upgrade(self, mock_get_or_404):
        """测试严重程度升级逻辑"""
        # MINOR -> MAJOR
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.severity = "MINOR"
        mock_get_or_404.return_value = mock_event

        self.service.escalate_exception(
            event_id=1,
            escalate_to_user_id=2,
            escalate_to_dept=None,
            escalation_reason="升级",
            current_user_id=1,
        )
        self.assertEqual(mock_event.severity, "MAJOR")

        # MAJOR -> CRITICAL
        mock_event2 = self._create_mock_event(2, "EXC-002", "测试异常2")
        mock_event2.severity = "MAJOR"
        mock_get_or_404.return_value = mock_event2

        self.service.escalate_exception(
            event_id=2,
            escalate_to_user_id=2,
            escalate_to_dept=None,
            escalation_reason="升级",
            current_user_id=1,
        )
        self.assertEqual(mock_event2.severity, "CRITICAL")

        # CRITICAL 不再升级
        mock_event3 = self._create_mock_event(3, "EXC-003", "测试异常3")
        mock_event3.severity = "CRITICAL"
        mock_get_or_404.return_value = mock_event3

        self.service.escalate_exception(
            event_id=3,
            escalate_to_user_id=2,
            escalate_to_dept=None,
            escalation_reason="升级",
            current_user_id=1,
        )
        self.assertEqual(mock_event3.severity, "CRITICAL")

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_escalate_exception_without_user(self, mock_get_or_404):
        """测试升级但不指定用户"""
        mock_event = self._create_mock_event(1, "EXC-001", "测试异常")
        mock_event.severity = "MINOR"
        mock_event.responsible_user_id = 1
        
        mock_get_or_404.return_value = mock_event

        result = self.service.escalate_exception(
            event_id=1,
            escalate_to_user_id=None,
            escalate_to_dept="技术部",
            escalation_reason="升级",
            current_user_id=1,
        )

        # 责任人不变
        self.assertEqual(mock_event.responsible_user_id, 1)
        # 部门更新
        self.assertEqual(mock_event.responsible_dept, "技术部")

    # ========== create_exception_from_issue() 测试 ==========

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_create_exception_from_issue_success(self, mock_get_or_404):
        """测试从问题创建异常"""
        mock_issue = MagicMock(spec=Issue)
        mock_issue.id = 1
        mock_issue.issue_title = "测试问题"
        mock_issue.issue_description = "问题描述"
        mock_issue.project_id = 1
        mock_issue.machine_id = 1
        mock_issue.reporter_id = 1
        mock_issue.created_at = datetime(2024, 1, 1, 10, 0, 0)
        
        mock_get_or_404.return_value = mock_issue

        result = self.service.create_exception_from_issue(
            issue_id=1,
            event_type="QUALITY",
            severity="MAJOR",
            current_user_id=1,
            event_no="EXC-001",
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # 验证创建的事件
        added_event = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_event.event_no, "EXC-001")
        self.assertEqual(added_event.source_type, "ISSUE")
        self.assertEqual(added_event.source_id, 1)
        self.assertEqual(added_event.event_title, "问题转异常：测试问题")
        self.assertEqual(added_event.event_description, "问题描述")
        self.assertEqual(added_event.project_id, 1)
        self.assertEqual(added_event.discovered_by, 1)

    @patch('app.services.alert_exceptions.service.get_or_404')
    def test_create_exception_from_issue_without_reporter(self, mock_get_or_404):
        """测试问题无报告人的情况"""
        mock_issue = MagicMock(spec=Issue)
        mock_issue.id = 1
        mock_issue.issue_title = "测试问题"
        mock_issue.issue_description = None
        mock_issue.project_id = 1
        mock_issue.machine_id = None
        mock_issue.reporter_id = None
        mock_issue.created_at = None
        
        mock_get_or_404.return_value = mock_issue

        result = self.service.create_exception_from_issue(
            issue_id=1,
            event_type="QUALITY",
            severity="MAJOR",
            current_user_id=2,
            event_no="EXC-001",
        )

        added_event = self.mock_db.add.call_args[0][0]
        # 使用当前用户作为发现人
        self.assertEqual(added_event.discovered_by, 2)
        # 空描述转为空字符串
        self.assertEqual(added_event.event_description, "")

    # ========== 辅助方法 ==========

    def _create_mock_event(self, event_id, event_no, event_title):
        """创建mock事件对象"""
        mock_event = MagicMock(spec=ExceptionEvent)
        mock_event.id = event_id
        mock_event.event_no = event_no
        mock_event.source_type = "MANUAL"
        mock_event.project_id = 1
        mock_event.machine_id = 1
        mock_event.event_type = "QUALITY"
        mock_event.severity = "MAJOR"
        mock_event.event_title = event_title
        mock_event.status = "OPEN"
        mock_event.discovered_at = None
        mock_event.discovered_by = None
        mock_event.schedule_impact = 0
        mock_event.cost_impact = 0
        mock_event.responsible_user_id = None
        mock_event.due_date = None
        mock_event.is_overdue = False
        mock_event.created_at = None
        
        # Mock关系对象
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_event.project = mock_project
        
        mock_machine = MagicMock()
        mock_machine.machine_name = "测试设备"
        mock_event.machine = mock_machine
        
        return mock_event


if __name__ == "__main__":
    unittest.main()
