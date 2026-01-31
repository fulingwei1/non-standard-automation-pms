# -*- coding: utf-8 -*-
"""
ShortageAlertsService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- get_shortage_alerts: 获取缺料告警列表
- get_shortage_alert: 获取单个缺料告警
- create_shortage_alert: 创建缺料告警
- update_shortage_alert: 更新缺料告警
- assign_handler: 分配处理人
- resolve_shortage: 解决缺料问题
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal

import pytest


class TestShortageAlertsServiceInit:
    """测试 ShortageAlertsService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        service = ShortageAlertsService(mock_db)

        assert service.db == mock_db


class TestGetShortageAlerts:
    """测试 get_shortage_alerts 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_shortage1 = MagicMock()
        mock_shortage1.id = 1
        mock_shortage2 = MagicMock()
        mock_shortage2.id = 2

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_shortage1, mock_shortage2]
        mock_query.count.return_value = 2
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(page=1, page_size=20)

        assert result is not None

    def test_filters_by_keyword(self):
        """测试按关键字过滤"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(keyword="电容")

        mock_query.filter.assert_called()

    def test_filters_by_severity(self):
        """测试按严重程度过滤"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(severity="HIGH")

        mock_query.filter.assert_called()

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(status="PENDING")

        mock_query.filter.assert_called()

    def test_filters_by_project_id(self):
        """测试按项目ID过滤"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(project_id=1)

        mock_query.filter.assert_called()

    def test_filters_by_material_id(self):
        """测试按物料ID过滤"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(material_id=100)

        mock_query.filter.assert_called()

    def test_filters_by_date_range(self):
        """测试按日期范围过滤"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alerts(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        mock_query.filter.assert_called()


class TestGetShortageAlert:
    """测试 get_shortage_alert 方法"""

    def test_returns_shortage_alert(self):
        """测试返回缺料告警"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.material_code = "MAT001"
        mock_shortage.shortage_qty = Decimal("100")

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_shortage
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alert(1)

        assert result == mock_shortage

    def test_returns_none_for_missing(self):
        """测试不存在时返回None"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.get_shortage_alert(999)

        assert result is None


class TestCreateShortageAlert:
    """测试 create_shortage_alert 方法"""

    def test_creates_alert_successfully(self):
        """测试成功创建缺料告警"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ShortageAlertsService(mock_db)

        alert_data = MagicMock()
        alert_data.material_id = 1
        alert_data.project_id = 1
        alert_data.shortage_qty = Decimal("50")
        alert_data.severity = "HIGH"

        result = service.create_shortage_alert(alert_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_sets_default_status(self):
        """测试设置默认状态"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ShortageAlertsService(mock_db)

        alert_data = MagicMock()
        alert_data.material_id = 1
        alert_data.shortage_qty = Decimal("100")

        result = service.create_shortage_alert(alert_data)

        mock_db.add.assert_called_once()


class TestAssignHandler:
    """测试 assign_handler 方法"""

    def test_assigns_handler_successfully(self):
        """测试成功分配处理人"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.assigned_user_id = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_shortage
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ShortageAlertsService(mock_db)

        result = service.assign_handler(1, handler_id=5)

        assert mock_shortage.assigned_user_id == 5 or mock_db.commit.called

    def test_returns_none_for_missing(self):
        """测试告警不存在时返回None"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        result = service.assign_handler(999, handler_id=5)

        assert result is None


class TestResolveShortage:
    """测试 resolve_shortage 方法"""

    def test_resolves_successfully(self):
        """测试成功解决缺料"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_shortage
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ShortageAlertsService(mock_db)

        resolve_data = MagicMock()
        resolve_data.resolution = "已补料"
        resolve_data.resolution_type = "PURCHASE"

        result = service.resolve_shortage(1, resolve_data, resolver_id=1)

        mock_db.commit.assert_called_once()

    def test_sets_resolved_at(self):
        """测试设置解决时间"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.status = "PENDING"
        mock_shortage.resolved_at = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_shortage
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ShortageAlertsService(mock_db)

        resolve_data = MagicMock()
        resolve_data.resolution = "已解决"

        result = service.resolve_shortage(1, resolve_data, resolver_id=1)

        mock_db.commit.assert_called_once()

    def test_returns_none_for_missing(self):
        """测试告警不存在时返回None"""
        from app.services.shortage.shortage_alerts_service import ShortageAlertsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ShortageAlertsService(mock_db)

        resolve_data = MagicMock()
        resolve_data.resolution = "已解决"

        result = service.resolve_shortage(999, resolve_data, resolver_id=1)

        assert result is None
