# -*- coding: utf-8 -*-
"""
ExceptionEventsService 增强测试 - 提升覆盖率到60%+
目标：补充异常事件管理、处理流程、升级、通知等核心功能测试
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime, timezone
from fastapi import HTTPException

from app.services.alert.exception_events_service import ExceptionEventsService
from app.models.alert import ExceptionEvent, ExceptionAction, ExceptionEscalation
from app.models.user import User
from app.schemas.alert import (
    ExceptionEventCreate,
    ExceptionEventUpdate,
    ExceptionEventResolve,
    ExceptionEventVerify
)


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ExceptionEventsService(db=mock_db)


@pytest.fixture
def mock_exception_event():
    """创建 Mock 异常事件"""
    event = MagicMock(spec=ExceptionEvent)
    event.id = 1
    event.title = "测试异常"
    event.description = "异常描述"
    event.event_type = "quality_issue"
    event.severity = "medium"
    event.status = "pending"
    event.project_id = 1
    event.reported_by = 1
    event.assigned_to = None
    event.resolved_by = None
    event.verified_by = None
    return event


@pytest.fixture
def mock_user():
    """创建 Mock 用户"""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "test_user"
    return user


class TestExceptionEventsServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self, mock_db):
        """测试正常初始化"""
        service = ExceptionEventsService(db=mock_db)
        assert service.db is mock_db


class TestGetExceptionEvents:
    """测试获取异常事件列表"""

    @patch('app.services.alert.exception_events_service.joinedload')
    @patch('app.services.alert.exception_events_service.apply_keyword_filter')
    @patch('app.services.alert.exception_events_service.apply_pagination')
    @patch('app.services.alert.exception_events_service.get_pagination_params')
    def test_get_exception_events_basic(self, mock_get_params, mock_apply_pagination,
                                       mock_apply_filter, mock_joinedload, service, mock_db):
        """测试基本列表查询"""
        # Setup
        mock_query = MagicMock()
        mock_db.query.return_value.options.return_value = mock_query
        mock_apply_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_apply_pagination.return_value.all.return_value = []
        
        mock_pagination = MagicMock()
        mock_pagination.page = 1
        mock_pagination.page_size = 20
        mock_pagination.offset = 0
        mock_pagination.limit = 20
        mock_pagination.pages_for_total.return_value = 0
        mock_get_params.return_value = mock_pagination
        
        # Execute
        result = service.get_exception_events()
        
        # Assert
        assert result.total == 0

    @patch('app.services.alert.exception_events_service.joinedload')
    @patch('app.services.alert.exception_events_service.apply_keyword_filter')
    @patch('app.services.alert.exception_events_service.apply_pagination')
    @patch('app.services.alert.exception_events_service.get_pagination_params')
    def test_get_exception_events_with_filters(self, mock_get_params, mock_apply_pagination,
                                               mock_apply_filter, mock_joinedload, service, mock_db):
        """测试带筛选条件"""
        mock_query = MagicMock()
        mock_db.query.return_value.options.return_value = mock_query
        mock_apply_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_apply_pagination.return_value.all.return_value = []
        
        mock_pagination = MagicMock()
        mock_pagination.page = 1
        mock_pagination.page_size = 20
        mock_pagination.offset = 0
        mock_pagination.limit = 20
        mock_pagination.pages_for_total.return_value = 1
        mock_get_params.return_value = mock_pagination
        
        result = service.get_exception_events(
            keyword="测试",
            severity="high",
            status="pending",
            event_type="quality_issue",
            project_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert result.total == 5
        assert mock_query.filter.call_count >= 5


class TestGetExceptionEvent:
    """测试获取单个异常事件"""

    @patch('app.services.alert.exception_events_service.joinedload')
    def test_get_exception_event_found(self, mock_joinedload, service, mock_db, mock_exception_event):
        """测试找到异常事件"""
        mock_query = MagicMock()
        mock_db.query.return_value.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_exception_event
        
        result = service.get_exception_event(event_id=1)
        
        assert result == mock_exception_event

    @patch('app.services.alert.exception_events_service.joinedload')
    def test_get_exception_event_not_found(self, mock_joinedload, service, mock_db):
        """测试异常事件不存在"""
        mock_query = MagicMock()
        mock_db.query.return_value.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        result = service.get_exception_event(event_id=999)
        
        assert result is None


class TestCreateExceptionEvent:
    """测试创建异常事件"""

    @patch('app.services.alert.exception_events_service.ExceptionEventsService._send_exception_notification')
    @patch('app.services.alert.exception_events_service.ExceptionEventsService._auto_assign_handler')
    @patch('app.utils.db_helpers.save_obj')
    def test_create_exception_event_basic(self, mock_save_obj, mock_auto_assign,
                                         mock_send_notification, service, mock_db, mock_user):
        """测试基本创建"""
        event_data = ExceptionEventCreate(
            title="测试异常",
            description="异常描述",
            event_type="quality_issue",
            severity="medium",
            project_id=1
        )
        
        result = service.create_exception_event(event_data, mock_user)
        
        assert result.title == "测试异常"
        assert result.reported_by == mock_user.id
        assert result.status == "pending"
        mock_save_obj.assert_called_once()
        mock_auto_assign.assert_called_once()
        mock_send_notification.assert_called_once()

    @patch('app.services.alert.exception_events_service.ExceptionEventsService._send_exception_notification')
    @patch('app.services.alert.exception_events_service.ExceptionEventsService._auto_assign_handler')
    @patch('app.utils.db_helpers.save_obj')
    def test_create_exception_event_with_occurred_at(self, mock_save_obj, mock_auto_assign,
                                                     mock_send_notification, service, mock_db, mock_user):
        """测试指定发生时间"""
        occurred_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        event_data = ExceptionEventCreate(
            title="测试异常",
            description="异常描述",
            event_type="quality_issue",
            severity="high",
            project_id=1,
            occurred_at=occurred_at
        )
        
        result = service.create_exception_event(event_data, mock_user)
        
        assert result.occurred_at == occurred_at


class TestUpdateExceptionEvent:
    """测试更新异常事件"""

    def test_update_exception_event_success(self, service, mock_db, mock_exception_event, mock_user):
        """测试成功更新"""
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        event_data = ExceptionEventUpdate(
            title="更新后的标题",
            severity="high"
        )
        
        result = service.update_exception_event(
            event_id=1,
            event_data=event_data,
            current_user=mock_user
        )
        
        assert result.title == "更新后的标题"
        assert result.severity == "high"
        assert result.updated_by == mock_user.id
        mock_db.commit.assert_called_once()

    def test_update_exception_event_not_found(self, service, mock_db, mock_user):
        """测试更新不存在的事件"""
        service.get_exception_event = MagicMock(return_value=None)
        
        result = service.update_exception_event(
            event_id=999,
            event_data=ExceptionEventUpdate(title="新标题"),
            current_user=mock_user
        )
        
        assert result is None


class TestResolveExceptionEvent:
    """测试解决异常事件"""

    @patch('app.services.alert.exception_events_service.ExceptionEventsService._send_exception_notification')
    def test_resolve_exception_event_success(self, mock_send_notification, service, 
                                            mock_db, mock_exception_event, mock_user):
        """测试成功解决"""
        mock_exception_event.status = "pending"
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        resolve_data = ExceptionEventResolve(
            resolution_method="修复代码",
            resolution_note="问题已解决",
            preventive_measures="增加测试用例"
        )
        
        with patch('app.services.alert.exception_events_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            result = service.resolve_exception_event(
                event_id=1,
                resolve_data=resolve_data,
                current_user=mock_user
            )
        
        assert result.status == "resolved"
        assert result.resolved_by == mock_user.id
        assert result.resolution_method == "修复代码"
        assert result.resolution_note == "问题已解决"
        mock_send_notification.assert_called_once()

    def test_resolve_exception_event_already_resolved(self, service, mock_db, 
                                                     mock_exception_event, mock_user):
        """测试已解决的事件"""
        mock_exception_event.status = "resolved"
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        with pytest.raises(HTTPException) as exc_info:
            service.resolve_exception_event(
                event_id=1,
                resolve_data=ExceptionEventResolve(resolution_method="test"),
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400


class TestVerifyExceptionEvent:
    """测试验证异常事件"""

    def test_verify_exception_event_verified(self, service, mock_db, 
                                            mock_exception_event, mock_user):
        """测试验证通过"""
        mock_exception_event.status = "resolved"
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        verify_data = ExceptionEventVerify(
            is_verified=True,
            verification_note="验证通过"
        )
        
        result = service.verify_exception_event(
            event_id=1,
            verify_data=verify_data,
            current_user=mock_user
        )
        
        assert result.status == "verified"
        assert result.verified_by == mock_user.id
        assert result.verification_note == "验证通过"

    def test_verify_exception_event_reopened(self, service, mock_db,
                                            mock_exception_event, mock_user):
        """测试验证不通过重新打开"""
        mock_exception_event.status = "resolved"
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        verify_data = ExceptionEventVerify(
            is_verified=False,
            verification_note="问题仍然存在"
        )
        
        result = service.verify_exception_event(
            event_id=1,
            verify_data=verify_data,
            current_user=mock_user
        )
        
        assert result.status == "reopened"

    def test_verify_exception_event_wrong_status(self, service, mock_db,
                                                 mock_exception_event, mock_user):
        """测试错误状态无法验证"""
        mock_exception_event.status = "pending"
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        with pytest.raises(HTTPException):
            service.verify_exception_event(
                event_id=1,
                verify_data=ExceptionEventVerify(is_verified=True),
                current_user=mock_user
            )


class TestAddExceptionAction:
    """测试添加异常事件处理动作"""

    @patch('app.utils.db_helpers.save_obj')
    def test_add_exception_action_success(self, mock_save_obj, service, mock_db, mock_user):
        """测试成功添加动作"""
        action_data = {
            "action_type": "repair",
            "description": "修复设备",
            "assigned_to": 2,
            "deadline": datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
        }
        
        result = service.add_exception_action(
            event_id=1,
            action_data=action_data,
            current_user=mock_user
        )
        
        assert result.event_id == 1
        assert result.action_type == "repair"
        assert result.description == "修复设备"
        assert result.created_by == mock_user.id
        assert result.status == "pending"
        mock_save_obj.assert_called_once()


class TestEscalateExceptionEvent:
    """测试升级异常事件"""

    @patch('app.services.alert.exception_events_service.ExceptionEventsService._send_escalation_notification')
    def test_escalate_exception_event_success(self, mock_send_escalation, service,
                                             mock_db, mock_exception_event, mock_user):
        """测试成功升级"""
        service.get_exception_event = MagicMock(return_value=mock_exception_event)
        
        escalation_data = {
            "escalation_level": 2,
            "escalated_to": 10,
            "escalation_reason": "超时未处理"
        }
        
        result = service.escalate_exception_event(
            event_id=1,
            escalation_data=escalation_data,
            current_user=mock_user
        )
        
        assert result.status == "escalated"
        assert result.assigned_to == 10
        mock_db.commit.assert_called_once()
        mock_send_escalation.assert_called_once()

    def test_escalate_exception_event_not_found(self, service, mock_db, mock_user):
        """测试升级不存在的事件"""
        service.get_exception_event = MagicMock(return_value=None)
        
        result = service.escalate_exception_event(
            event_id=999,
            escalation_data={"escalation_level": 2, "escalated_to": 10, "escalation_reason": "test"},
            current_user=mock_user
        )
        
        assert result is None


class TestCreateExceptionFromIssue:
    """测试从问题创建异常事件"""

    @patch('app.utils.db_helpers.save_obj')
    def test_create_exception_from_issue_success(self, mock_save_obj, service, mock_db, mock_user):
        """测试成功从问题创建"""
        # Mock issue
        mock_issue = MagicMock()
        mock_issue.id = 1
        mock_issue.title = "质量问题"
        mock_issue.description = "问题描述"
        mock_issue.severity = "high"
        mock_issue.project_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_issue
        
        result = service.create_exception_from_issue(
            issue_id=1,
            current_user=mock_user
        )
        
        assert "【异常】质量问题" in result.title
        assert result.description == "问题描述"
        assert result.source_issue_id == 1
        mock_save_obj.assert_called_once()

    def test_create_exception_from_issue_not_found(self, service, mock_db, mock_user):
        """测试问题不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_exception_from_issue(
                issue_id=999,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 404


class TestAutoAssignHandler:
    """测试自动分配处理人"""

    def test_auto_assign_to_project_manager(self, service, mock_db, mock_exception_event):
        """测试分配给项目经理"""
        # Mock project with PM
        mock_project = MagicMock()
        mock_project.pm_id = 5
        mock_exception_event.project = mock_project
        mock_exception_event.project_id = 1
        
        service._auto_assign_handler(mock_exception_event)
        
        assert mock_exception_event.responsible_user_id == 5
        assert mock_exception_event.status == "ASSIGNED"

    def test_auto_assign_to_dept_manager(self, service, mock_db, mock_exception_event):
        """测试分配给部门负责人"""
        # No PM, but has department
        mock_exception_event.project = None
        mock_exception_event.project_id = None
        mock_exception_event.responsible_dept = "质量部"
        
        # Mock department user
        mock_dept_user = MagicMock()
        mock_dept_user.id = 7
        mock_db.query.return_value.filter.return_value.first.return_value = mock_dept_user
        
        service._auto_assign_handler(mock_exception_event)
        
        assert mock_exception_event.responsible_user_id == 7

    def test_auto_assign_no_handler_found(self, service, mock_db, mock_exception_event):
        """测试无法找到处理人"""
        mock_exception_event.project = None
        mock_exception_event.project_id = None
        mock_exception_event.responsible_dept = None
        
        service._auto_assign_handler(mock_exception_event)
        
        # Should not raise exception, just log warning


class TestDetermineExceptionSeverity:
    """测试确定异常严重程度"""

    def test_determine_severity_critical(self, service):
        """测试严重级别映射"""
        mock_issue = MagicMock()
        mock_issue.severity = "critical"
        
        result = service._determine_exception_severity(mock_issue)
        
        assert result == "critical"

    def test_determine_severity_high(self, service):
        """测试高级别映射"""
        mock_issue = MagicMock()
        mock_issue.severity = "high"
        
        result = service._determine_exception_severity(mock_issue)
        
        assert result == "high"

    def test_determine_severity_default(self, service):
        """测试默认级别"""
        mock_issue = MagicMock()
        mock_issue.severity = "unknown"
        
        result = service._determine_exception_severity(mock_issue)
        
        assert result == "medium"


class TestSendExceptionNotification:
    """测试发送异常事件通知"""

    @patch('app.services.alert.exception_events_service.get_notification_service')
    def test_send_exception_notification_success(self, mock_get_service, service,
                                                mock_db, mock_exception_event):
        """测试成功发送通知"""
        mock_exception_event.responsible_user_id = 1
        mock_exception_event.reported_by = 2
        mock_exception_event.event_title = "测试异常"
        mock_exception_event.title = "测试异常"
        
        mock_notification_service = MagicMock()
        mock_get_service.return_value = mock_notification_service
        
        service._send_exception_notification(mock_exception_event, "created")
        
        mock_notification_service.send_notification.assert_called()

    @patch('app.services.alert.exception_events_service.get_notification_service')
    def test_send_exception_notification_multiple_recipients(self, mock_get_service, service,
                                                            mock_db, mock_exception_event):
        """测试多个接收人"""
        mock_exception_event.responsible_user_id = 1
        mock_exception_event.reported_by = 2
        mock_exception_event.created_by = 3
        mock_exception_event.event_title = "测试异常"
        mock_exception_event.title = "测试异常"
        
        mock_notification_service = MagicMock()
        mock_get_service.return_value = mock_notification_service
        
        service._send_exception_notification(mock_exception_event, "resolved")
        
        # Should send notification to all recipients
        assert mock_notification_service.send_notification.call_count >= 1


class TestSendEscalationNotification:
    """测试发送升级通知"""

    @patch('app.services.alert.exception_events_service.get_notification_service')
    def test_send_escalation_notification_success(self, mock_get_service, service, 
                                                 mock_db, mock_exception_event):
        """测试成功发送升级通知"""
        mock_escalation = MagicMock()
        mock_escalation.escalation_level = 2
        mock_escalation.escalation_reason = "超时未处理"
        mock_escalation.escalated_to = 10
        
        mock_exception_event.event_title = "测试异常"
        mock_exception_event.title = "测试异常"
        
        mock_notification_service = MagicMock()
        mock_get_service.return_value = mock_notification_service
        
        service._send_escalation_notification(mock_exception_event, mock_escalation)
        
        mock_notification_service.send_notification.assert_called_once()


class TestSimplifiedAliases:
    """测试简化别名方法"""

    @patch('app.services.alert.exception_events_service.ExceptionEventsService.create_exception_event')
    def test_create_event_alias(self, mock_create, service, mock_user):
        """测试 create_event 别名"""
        event_data = MagicMock()
        
        service.create_event(event_data, mock_user)
        
        mock_create.assert_called_once_with(event_data, mock_user)

    @patch('app.services.alert.exception_events_service.ExceptionEventsService.get_exception_event')
    def test_get_event_alias(self, mock_get, service):
        """测试 get_event 别名"""
        service.get_event(1)
        
        mock_get.assert_called_once_with(1)

    @patch('app.services.alert.exception_events_service.ExceptionEventsService.get_exception_events')
    def test_list_events_alias(self, mock_list, service):
        """测试 list_events 别名"""
        service.list_events(page=1, page_size=20, keyword="test")
        
        mock_list.assert_called_once_with(page=1, page_size=20, keyword="test")
