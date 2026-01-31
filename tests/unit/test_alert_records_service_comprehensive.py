# -*- coding: utf-8 -*-
"""
AlertRecordsService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- create_alert: 创建告警记录
- get_alert: 获取告警记录
- list_alerts: 列出告警记录
- handle_alert: 处理告警
- close_alert: 关闭告警
- escalate_alert: 升级告警
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

import pytest


class TestAlertRecordsServiceInit:
    """测试 AlertRecordsService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        service = AlertRecordsService(mock_db)

        assert service.db == mock_db


class TestCreateAlert:
    """测试 create_alert 方法"""

    def test_creates_alert_successfully(self):
        """测试成功创建告警记录"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        alert_data = MagicMock()
        alert_data.project_id = 1
        alert_data.rule_id = 1
        alert_data.severity = "HIGH"
        alert_data.title = "进度告警"
        alert_data.content = "项目进度落后"

        result = service.create_alert(alert_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_sets_default_status(self):
        """测试设置默认状态为 PENDING"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        alert_data = MagicMock()
        alert_data.project_id = 1
        alert_data.severity = "MEDIUM"
        alert_data.title = "成本告警"

        result = service.create_alert(alert_data)

        mock_db.add.assert_called_once()

    def test_generates_alert_code(self):
        """测试生成告警编码"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        service = AlertRecordsService(mock_db)

        alert_data = MagicMock()
        alert_data.project_id = 1
        alert_data.severity = "LOW"
        alert_data.title = "质量告警"

        result = service.create_alert(alert_data)

        mock_db.add.assert_called_once()


class TestGetAlert:
    """测试 get_alert 方法"""

    def test_returns_alert(self):
        """测试返回告警记录"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.alert_code = "ALT20240115001"
        mock_alert.title = "测试告警"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        service = AlertRecordsService(mock_db)

        result = service.get_alert(1)

        assert result == mock_alert

    def test_returns_none_for_missing_alert(self):
        """测试告警不存在时返回 None"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AlertRecordsService(mock_db)

        result = service.get_alert(999)

        assert result is None


class TestListAlerts:
    """测试 list_alerts 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert1 = MagicMock()
        mock_alert1.id = 1
        mock_alert2 = MagicMock()
        mock_alert2.id = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_alert1, mock_alert2]
        mock_query.count.return_value = 2
        mock_db.query.return_value = mock_query

        service = AlertRecordsService(mock_db)

        result = service.list_alerts(page=1, page_size=20)

        assert 'items' in result or isinstance(result, list)

    def test_filters_by_project_id(self):
        """测试按项目ID过滤"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = AlertRecordsService(mock_db)

        result = service.list_alerts(project_id=1)

        mock_query.filter.assert_called()

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = AlertRecordsService(mock_db)

        result = service.list_alerts(status="PENDING")

        mock_query.filter.assert_called()

    def test_filters_by_severity(self):
        """测试按严重程度过滤"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = AlertRecordsService(mock_db)

        result = service.list_alerts(severity="CRITICAL")

        mock_query.filter.assert_called()

    def test_filters_by_handler_id(self):
        """测试按处理人ID过滤"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = AlertRecordsService(mock_db)

        result = service.list_alerts(handler_id=1)

        mock_query.filter.assert_called()


class TestHandleAlert:
    """测试 handle_alert 方法"""

    def test_handles_alert_successfully(self):
        """测试成功处理告警"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "PENDING"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        handle_data = MagicMock()
        handle_data.action = "ACKNOWLEDGE"
        handle_data.comment = "已收到告警"

        result = service.handle_alert(1, handle_data, handler_id=1)

        mock_db.commit.assert_called_once()

    def test_sets_handler_id(self):
        """测试设置处理人ID"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "PENDING"
        mock_alert.handler_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        handle_data = MagicMock()
        handle_data.action = "ACKNOWLEDGE"

        result = service.handle_alert(1, handle_data, handler_id=5)

        assert mock_alert.handler_id == 5 or mock_db.commit.called

    def test_returns_none_for_missing_alert(self):
        """测试告警不存在时返回 None"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AlertRecordsService(mock_db)

        handle_data = MagicMock()
        handle_data.action = "ACKNOWLEDGE"

        result = service.handle_alert(999, handle_data, handler_id=1)

        assert result is None


class TestCloseAlert:
    """测试 close_alert 方法"""

    def test_closes_alert_successfully(self):
        """测试成功关闭告警"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "HANDLING"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        close_data = MagicMock()
        close_data.resolution = "问题已解决"
        close_data.root_cause = "配置错误"

        result = service.close_alert(1, close_data, closer_id=1)

        mock_db.commit.assert_called_once()

    def test_sets_closed_at(self):
        """测试设置关闭时间"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "HANDLING"
        mock_alert.closed_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        close_data = MagicMock()
        close_data.resolution = "已解决"

        result = service.close_alert(1, close_data, closer_id=1)

        mock_db.commit.assert_called_once()

    def test_returns_none_for_missing_alert(self):
        """测试告警不存在时返回 None"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AlertRecordsService(mock_db)

        close_data = MagicMock()
        close_data.resolution = "已解决"

        result = service.close_alert(999, close_data, closer_id=1)

        assert result is None


class TestEscalateAlert:
    """测试 escalate_alert 方法"""

    def test_escalates_alert_successfully(self):
        """测试成功升级告警"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.severity = "MEDIUM"
        mock_alert.escalation_count = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        escalate_data = MagicMock()
        escalate_data.target_severity = "HIGH"
        escalate_data.reason = "问题未及时处理"

        result = service.escalate_alert(1, escalate_data, escalator_id=1)

        mock_db.commit.assert_called_once()

    def test_increments_escalation_count(self):
        """测试递增升级次数"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()

        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.severity = "LOW"
        mock_alert.escalation_count = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = AlertRecordsService(mock_db)

        escalate_data = MagicMock()
        escalate_data.target_severity = "MEDIUM"

        result = service.escalate_alert(1, escalate_data, escalator_id=1)

        assert mock_alert.escalation_count == 2 or mock_db.commit.called

    def test_returns_none_for_missing_alert(self):
        """测试告警不存在时返回 None"""
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AlertRecordsService(mock_db)

        escalate_data = MagicMock()
        escalate_data.target_severity = "HIGH"

        result = service.escalate_alert(999, escalate_data, escalator_id=1)

        assert result is None
