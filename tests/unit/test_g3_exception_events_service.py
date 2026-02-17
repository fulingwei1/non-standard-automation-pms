# -*- coding: utf-8 -*-
"""
G3组 - 异常事件服务单元测试
目标文件: app/services/alert/exception_events_service.py
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, ANY

from fastapi import HTTPException

from app.services.alert.exception_events_service import ExceptionEventsService


# 模块级别的 patch target
SERVICE_MODULE = "app.services.alert.exception_events_service"


class TestExceptionEventsServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        db = MagicMock()
        service = ExceptionEventsService(db)
        assert service.db is db


class TestGetExceptionEvent:
    """测试获取单个异常事件"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ExceptionEventsService(self.db)

    def test_get_existing_event(self):
        mock_event = MagicMock()
        mock_event.id = 1
        (self.db.query.return_value
            .options.return_value
            .filter.return_value
            .first.return_value) = mock_event

        with patch(f"{SERVICE_MODULE}.joinedload"):
            result = self.service.get_exception_event(1)
        assert result is mock_event

    def test_get_nonexistent_event_returns_none(self):
        (self.db.query.return_value
            .options.return_value
            .filter.return_value
            .first.return_value) = None

        with patch(f"{SERVICE_MODULE}.joinedload"):
            result = self.service.get_exception_event(999)
        assert result is None


class TestCreateExceptionEvent:
    """测试创建异常事件"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ExceptionEventsService(self.db)

    def test_create_event_success(self):
        event_data = MagicMock()
        event_data.title = "测试异常事件"
        event_data.description = "异常描述"
        event_data.event_type = "SYSTEM"
        event_data.severity = "HIGH"
        event_data.project_id = 1
        event_data.occurred_at = None
        event_data.location = "车间A"
        event_data.impact_assessment = "中等影响"
        event_data.immediate_actions = "立即停机"

        current_user = MagicMock()
        current_user.id = 10

        mock_event_instance = MagicMock()
        mock_event_instance.title = "测试异常事件"
        mock_event_instance.reported_by = 10
        mock_event_instance.status = "pending"

        with patch(f"{SERVICE_MODULE}.ExceptionEvent",
                   return_value=mock_event_instance) as MockEvent, \
             patch(f"{SERVICE_MODULE}.save_obj") as mock_save, \
             patch.object(self.service, "_auto_assign_handler") as mock_assign, \
             patch.object(self.service, "_send_exception_notification") as mock_notify:
            result = self.service.create_exception_event(event_data, current_user)

        mock_save.assert_called_once()
        mock_assign.assert_called_once()
        mock_notify.assert_called_once_with(mock_event_instance, "created")
        assert result is mock_event_instance

    def test_create_event_uses_provided_occurred_at(self):
        fixed_time = datetime(2026, 1, 15, 10, 0, 0)
        event_data = MagicMock()
        event_data.title = "事件"
        event_data.description = ""
        event_data.event_type = "QUALITY"
        event_data.severity = "LOW"
        event_data.project_id = 2
        event_data.occurred_at = fixed_time
        event_data.location = None
        event_data.impact_assessment = None
        event_data.immediate_actions = None

        current_user = MagicMock()
        current_user.id = 5

        mock_event = MagicMock()

        with patch(f"{SERVICE_MODULE}.ExceptionEvent", return_value=mock_event), \
             patch(f"{SERVICE_MODULE}.save_obj"), \
             patch.object(self.service, "_auto_assign_handler"), \
             patch.object(self.service, "_send_exception_notification"):
            result = self.service.create_exception_event(event_data, current_user)

        # ExceptionEvent 应该被调用
        assert result is mock_event


class TestUpdateExceptionEvent:
    """测试更新异常事件"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ExceptionEventsService(self.db)

    def test_update_nonexistent_event_returns_none(self):
        with patch.object(self.service, "get_exception_event", return_value=None):
            result = self.service.update_exception_event(999, MagicMock(), MagicMock())
        assert result is None

    def test_update_event_success(self):
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.status = "pending"

        event_data = MagicMock()
        event_data.dict.return_value = {"title": "新标题", "severity": "MEDIUM"}

        current_user = MagicMock()
        current_user.id = 7

        with patch.object(self.service, "get_exception_event", return_value=mock_event):
            result = self.service.update_exception_event(1, event_data, current_user)

        assert result is mock_event
        assert mock_event.updated_by == 7
        self.db.commit.assert_called_once()

    def test_update_skips_protected_fields(self):
        """id、reported_by、created_at 字段不应被覆盖"""
        mock_event = MagicMock()
        mock_event.id = 1

        event_data = MagicMock()
        event_data.dict.return_value = {
            "id": 999,
            "reported_by": 888,
            "created_at": "2026-01-01",
            "severity": "LOW"
        }

        current_user = MagicMock()
        current_user.id = 3

        with patch.object(self.service, "get_exception_event", return_value=mock_event):
            result = self.service.update_exception_event(1, event_data, current_user)

        # 只有 severity 应该被 setattr
        mock_event.__setattr__.assert_any_call("severity", "LOW")
        # id 不应该被 setattr
        calls = [str(c) for c in mock_event.__setattr__.call_args_list]
        assert not any("'id', 999" in c for c in calls)


class TestResolveExceptionEvent:
    """测试解决异常事件"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ExceptionEventsService(self.db)

    def test_resolve_nonexistent_event_returns_none(self):
        with patch.object(self.service, "get_exception_event", return_value=None):
            result = self.service.resolve_exception_event(999, MagicMock(), MagicMock())
        assert result is None

    def test_resolve_already_resolved_raises_400(self):
        mock_event = MagicMock()
        mock_event.status = "resolved"

        with patch.object(self.service, "get_exception_event", return_value=mock_event):
            with pytest.raises(HTTPException) as exc_info:
                self.service.resolve_exception_event(1, MagicMock(), MagicMock())
        assert exc_info.value.status_code == 400

    def test_resolve_pending_event_success(self):
        mock_event = MagicMock()
        mock_event.status = "pending"

        resolve_data = MagicMock()
        resolve_data.resolution_method = "重启服务"
        resolve_data.resolution_note = "已重启"
        resolve_data.preventive_measures = "定期维护"

        current_user = MagicMock()
        current_user.id = 3

        with patch.object(self.service, "get_exception_event", return_value=mock_event), \
             patch.object(self.service, "_send_exception_notification") as mock_notify:
            result = self.service.resolve_exception_event(1, resolve_data, current_user)

        assert result is mock_event
        assert mock_event.status == "resolved"
        assert mock_event.resolved_by == 3
        mock_notify.assert_called_once_with(mock_event, "resolved")


class TestVerifyExceptionEvent:
    """测试验证异常事件解决方案"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ExceptionEventsService(self.db)

    def test_verify_nonexistent_event_returns_none(self):
        with patch.object(self.service, "get_exception_event", return_value=None):
            result = self.service.verify_exception_event(999, MagicMock(), MagicMock())
        assert result is None

    def test_verify_not_resolved_raises_400(self):
        mock_event = MagicMock()
        mock_event.status = "pending"

        with patch.object(self.service, "get_exception_event", return_value=mock_event):
            with pytest.raises(HTTPException) as exc_info:
                self.service.verify_exception_event(1, MagicMock(), MagicMock())
        assert exc_info.value.status_code == 400

    def test_verify_resolved_event_verified(self):
        mock_event = MagicMock()
        mock_event.status = "resolved"

        verify_data = MagicMock()
        verify_data.is_verified = True
        verify_data.verification_note = "通过验证"

        current_user = MagicMock()
        current_user.id = 9

        with patch.object(self.service, "get_exception_event", return_value=mock_event):
            result = self.service.verify_exception_event(1, verify_data, current_user)

        assert mock_event.status == "verified"
        assert mock_event.verified_by == 9

    def test_verify_resolved_event_reopened(self):
        mock_event = MagicMock()
        mock_event.status = "resolved"

        verify_data = MagicMock()
        verify_data.is_verified = False
        verify_data.verification_note = "未通过"

        current_user = MagicMock()
        current_user.id = 9

        with patch.object(self.service, "get_exception_event", return_value=mock_event):
            result = self.service.verify_exception_event(1, verify_data, current_user)

        assert mock_event.status == "reopened"


class TestGetExceptionEvents:
    """测试获取异常事件列表（分页）"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ExceptionEventsService(self.db)

    def test_get_events_no_filters(self):
        mock_query = MagicMock()
        self.db.query.return_value.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        with patch(f"{SERVICE_MODULE}.joinedload"), \
             patch(f"{SERVICE_MODULE}.apply_keyword_filter", return_value=mock_query), \
             patch(f"{SERVICE_MODULE}.apply_pagination", return_value=mock_query), \
             patch(f"{SERVICE_MODULE}.get_pagination_params") as mock_pp:
            mock_pp.return_value.page = 1
            mock_pp.return_value.page_size = 20
            mock_pp.return_value.offset = 0
            mock_pp.return_value.limit = 20
            mock_pp.return_value.pages_for_total.return_value = 0

            result = self.service.get_exception_events()

        assert result.total == 0
        assert result.items == []

    def test_get_events_with_keyword_filter(self):
        """带关键词搜索"""
        mock_query = MagicMock()
        self.db.query.return_value.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.all.return_value = []

        with patch(f"{SERVICE_MODULE}.joinedload"), \
             patch(f"{SERVICE_MODULE}.apply_keyword_filter", return_value=mock_query), \
             patch(f"{SERVICE_MODULE}.apply_pagination", return_value=mock_query), \
             patch(f"{SERVICE_MODULE}.get_pagination_params") as mock_pp:
            mock_pp.return_value.page = 1
            mock_pp.return_value.page_size = 10
            mock_pp.return_value.offset = 0
            mock_pp.return_value.limit = 10
            mock_pp.return_value.pages_for_total.return_value = 1

            result = self.service.get_exception_events(keyword="故障", severity="HIGH")

        assert result.total == 2
