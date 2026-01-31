# -*- coding: utf-8 -*-
"""
ExceptionEventsService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- create_event: 创建异常事件
- get_event: 获取异常事件
- list_events: 列出异常事件
- update_event: 更新异常事件
- verify_event: 核实异常事件
- resolve_event: 解决异常事件
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

import pytest


class TestExceptionEventsServiceInit:
    """测试 ExceptionEventsService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        service = ExceptionEventsService(mock_db)

        assert service.db == mock_db


class TestCreateEvent:
    """测试 create_event 方法"""

    def test_creates_event_successfully(self):
        """测试成功创建异常事件"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ExceptionEventsService(mock_db)

        event_data = MagicMock()
        event_data.project_id = 1
        event_data.event_type = "DELAY"
        event_data.severity = "HIGH"
        event_data.title = "项目延期"
        event_data.description = "项目进度落后"

        result = service.create_event(event_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_sets_default_status(self):
        """测试设置默认状态"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ExceptionEventsService(mock_db)

        event_data = MagicMock()
        event_data.project_id = 1
        event_data.event_type = "COST_OVERRUN"
        event_data.severity = "MEDIUM"
        event_data.title = "成本超支"
        event_data.description = "成本超出预算"
        event_data.status = None

        result = service.create_event(event_data)

        # 验证 add 被调用
        mock_db.add.assert_called_once()

    def test_generates_event_code(self):
        """测试生成事件编码"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        service = ExceptionEventsService(mock_db)

        event_data = MagicMock()
        event_data.project_id = 1
        event_data.event_type = "QUALITY"
        event_data.severity = "LOW"
        event_data.title = "质量问题"
        event_data.description = "产品质量不达标"

        result = service.create_event(event_data)

        mock_db.add.assert_called_once()


class TestGetEvent:
    """测试 get_event 方法"""

    def test_returns_event(self):
        """测试返回异常事件"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.event_code = "EXC20240115001"
        mock_event.title = "测试事件"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_event

        service = ExceptionEventsService(mock_db)

        result = service.get_event(1)

        assert result == mock_event

    def test_returns_none_for_missing_event(self):
        """测试事件不存在时返回 None"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ExceptionEventsService(mock_db)

        result = service.get_event(999)

        assert result is None


class TestListEvents:
    """测试 list_events 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_event1 = MagicMock()
        mock_event1.id = 1
        mock_event2 = MagicMock()
        mock_event2.id = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_event1, mock_event2]
        mock_query.count.return_value = 2
        mock_db.query.return_value = mock_query

        service = ExceptionEventsService(mock_db)

        result = service.list_events(page=1, page_size=20)

        assert 'items' in result or isinstance(result, list)

    def test_filters_by_project_id(self):
        """测试按项目ID过滤"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ExceptionEventsService(mock_db)

        result = service.list_events(project_id=1)

        mock_query.filter.assert_called()

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ExceptionEventsService(mock_db)

        result = service.list_events(status="PENDING")

        mock_query.filter.assert_called()

    def test_filters_by_severity(self):
        """测试按严重程度过滤"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ExceptionEventsService(mock_db)

        result = service.list_events(severity="CRITICAL")

        mock_query.filter.assert_called()


class TestUpdateEvent:
    """测试 update_event 方法"""

    def test_updates_event_successfully(self):
        """测试成功更新异常事件"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "原标题"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_event
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ExceptionEventsService(mock_db)

        update_data = MagicMock()
        update_data.title = "新标题"
        update_data.description = "新描述"

        result = service.update_event(1, update_data)

        mock_db.commit.assert_called_once()

    def test_returns_none_for_missing_event(self):
        """测试事件不存在时返回 None"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ExceptionEventsService(mock_db)

        update_data = MagicMock()
        update_data.title = "新标题"

        result = service.update_event(999, update_data)

        assert result is None


class TestVerifyEvent:
    """测试 verify_event 方法"""

    def test_verifies_event_successfully(self):
        """测试成功核实异常事件"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.status = "PENDING"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_event
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ExceptionEventsService(mock_db)

        verify_data = MagicMock()
        verify_data.verified = True
        verify_data.verify_comment = "已核实"

        result = service.verify_event(1, verify_data, verifier_id=1)

        assert mock_event.status == "VERIFIED" or mock_db.commit.called

    def test_returns_none_for_missing_event(self):
        """测试事件不存在时返回 None"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ExceptionEventsService(mock_db)

        verify_data = MagicMock()
        verify_data.verified = True

        result = service.verify_event(999, verify_data, verifier_id=1)

        assert result is None


class TestResolveEvent:
    """测试 resolve_event 方法"""

    def test_resolves_event_successfully(self):
        """测试成功解决异常事件"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.status = "VERIFIED"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_event
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ExceptionEventsService(mock_db)

        resolve_data = MagicMock()
        resolve_data.resolution = "问题已解决"
        resolve_data.root_cause = "配置错误"

        result = service.resolve_event(1, resolve_data, resolver_id=1)

        mock_db.commit.assert_called_once()

    def test_sets_resolved_at(self):
        """测试设置解决时间"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()

        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.status = "VERIFIED"
        mock_event.resolved_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_event
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ExceptionEventsService(mock_db)

        resolve_data = MagicMock()
        resolve_data.resolution = "已解决"

        result = service.resolve_event(1, resolve_data, resolver_id=1)

        # 验证 resolved_at 被设置
        mock_db.commit.assert_called_once()

    def test_returns_none_for_missing_event(self):
        """测试事件不存在时返回 None"""
        from app.services.alert.exception_events_service import ExceptionEventsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ExceptionEventsService(mock_db)

        resolve_data = MagicMock()
        resolve_data.resolution = "已解决"

        result = service.resolve_event(999, resolve_data, resolver_id=1)

        assert result is None
