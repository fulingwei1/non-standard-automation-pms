# -*- coding: utf-8 -*-
"""
G3组 - 告警记录服务单元测试
目标文件: app/services/alert/alert_records_service.py
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.alert.alert_records_service import AlertRecordsService


class TestAlertRecordsServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        db = MagicMock()
        service = AlertRecordsService(db)
        assert service.db is db


class TestGetAlertRecord:
    """测试获取单个告警记录"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = AlertRecordsService(self.db)

    def test_get_existing_alert(self):
        mock_alert = MagicMock()
        mock_alert.id = 1
        (self.db.query.return_value
            .options.return_value
            .filter.return_value
            .first.return_value) = mock_alert

        result = self.service.get_alert_record(1)
        assert result is mock_alert

    def test_get_nonexistent_alert_returns_none(self):
        (self.db.query.return_value
            .options.return_value
            .filter.return_value
            .first.return_value) = None

        result = self.service.get_alert_record(999)
        assert result is None


class TestAcknowledgeAlert:
    """测试确认告警"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = AlertRecordsService(self.db)

    def test_acknowledge_nonexistent_returns_none(self):
        with patch.object(self.service, "get_alert_record", return_value=None):
            result = self.service.acknowledge_alert(999, MagicMock(), MagicMock())
        assert result is None

    def test_acknowledge_non_pending_raises_400(self):
        mock_alert = MagicMock()
        mock_alert.status = "acknowledged"

        with patch.object(self.service, "get_alert_record", return_value=mock_alert):
            with pytest.raises(HTTPException) as exc_info:
                self.service.acknowledge_alert(1, MagicMock(), MagicMock())
        assert exc_info.value.status_code == 400

    def test_acknowledge_pending_alert_success(self):
        mock_alert = MagicMock()
        mock_alert.status = "pending"

        handle_data = MagicMock()
        handle_data.note = "已收到，正在处理"

        current_user = MagicMock()
        current_user.id = 5

        with patch.object(self.service, "get_alert_record", return_value=mock_alert), \
             patch.object(self.service, "_send_alert_notification") as mock_notify:
            result = self.service.acknowledge_alert(1, handle_data, current_user)

        assert result is mock_alert
        assert mock_alert.status == "acknowledged"
        assert mock_alert.acknowledged_by == 5
        assert mock_alert.acknowledgment_note == "已收到，正在处理"
        mock_notify.assert_called_once_with(mock_alert, "acknowledged")
        self.db.commit.assert_called_once()


class TestResolveAlert:
    """测试解决告警"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = AlertRecordsService(self.db)

    def test_resolve_nonexistent_returns_none(self):
        with patch.object(self.service, "get_alert_record", return_value=None):
            result = self.service.resolve_alert(999, MagicMock(), MagicMock())
        assert result is None

    def test_resolve_invalid_status_raises_400(self):
        mock_alert = MagicMock()
        mock_alert.status = "resolved"  # 已解决不能再次解决

        with patch.object(self.service, "get_alert_record", return_value=mock_alert):
            with pytest.raises(HTTPException) as exc_info:
                self.service.resolve_alert(1, MagicMock(), MagicMock())
        assert exc_info.value.status_code == 400

    def test_resolve_pending_alert_success(self):
        mock_alert = MagicMock()
        mock_alert.status = "pending"

        handle_data = MagicMock()
        handle_data.note = "问题已修复"

        current_user = MagicMock()
        current_user.id = 8

        with patch.object(self.service, "get_alert_record", return_value=mock_alert), \
             patch.object(self.service, "_send_alert_notification") as mock_notify:
            result = self.service.resolve_alert(1, handle_data, current_user)

        assert result is mock_alert
        assert mock_alert.status == "resolved"
        assert mock_alert.resolved_by == 8
        mock_notify.assert_called_once_with(mock_alert, "resolved")

    def test_resolve_acknowledged_alert_success(self):
        mock_alert = MagicMock()
        mock_alert.status = "acknowledged"

        handle_data = MagicMock()
        handle_data.note = "处理完毕"

        current_user = MagicMock()
        current_user.id = 4

        with patch.object(self.service, "get_alert_record", return_value=mock_alert), \
             patch.object(self.service, "_send_alert_notification"):
            result = self.service.resolve_alert(1, handle_data, current_user)

        assert result is mock_alert
        assert mock_alert.status == "resolved"


class TestGetAlertRecords:
    """测试获取告警记录列表"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = AlertRecordsService(self.db)

    def test_get_records_returns_paginated_response(self):
        mock_query = MagicMock()
        self.db.query.return_value.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        with patch("app.services.alert.alert_records_service.apply_keyword_filter",
                   return_value=mock_query), \
             patch("app.services.alert.alert_records_service.apply_pagination",
                   return_value=mock_query), \
             patch("app.services.alert.alert_records_service.get_pagination_params") as mock_pp:
            mock_pp.return_value.page = 1
            mock_pp.return_value.page_size = 20
            mock_pp.return_value.offset = 0
            mock_pp.return_value.limit = 20
            mock_pp.return_value.pages_for_total.return_value = 0

            result = self.service.get_alert_records()

        assert result.total == 0
        assert result.items == []
        assert result.page == 1

    def test_get_records_with_filters(self):
        mock_query = MagicMock()
        self.db.query.return_value.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.all.return_value = []

        with patch("app.services.alert.alert_records_service.apply_keyword_filter",
                   return_value=mock_query), \
             patch("app.services.alert.alert_records_service.apply_pagination",
                   return_value=mock_query), \
             patch("app.services.alert.alert_records_service.get_pagination_params") as mock_pp:
            mock_pp.return_value.page = 1
            mock_pp.return_value.page_size = 20
            mock_pp.return_value.offset = 0
            mock_pp.return_value.limit = 20
            mock_pp.return_value.pages_for_total.return_value = 1

            result = self.service.get_alert_records(
                severity="HIGH", status="pending", project_id=3
            )

        assert result.total == 5
