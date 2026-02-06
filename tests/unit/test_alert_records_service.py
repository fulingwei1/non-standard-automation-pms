# -*- coding: utf-8 -*-
"""
Tests for alert_records_service
Covers: app/services/alert/alert_records_service.py
"""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.alert import AlertRecord, AlertRule, AlertNotification
from app.models.user import User
from app.schemas.alert import AlertRecordHandle
from app.schemas.common import PaginatedResponse


class TestAlertRecordsServiceInit:
    """Test suite for service initialization."""

    def test_init_service(self):
        from app.services.alert.alert_records_service import AlertRecordsService

        mock_session = Mock(spec=Session)
        service = AlertRecordsService(mock_session)

        assert service.db == mock_session


class TestGetAlertRecords:
    """Test suite for get_alert_records method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_get_alert_records_default_params(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.join = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=0)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        db_session.query = Mock(return_value=mock_query)

        result = service.get_alert_records()

        assert isinstance(result, PaginatedResponse)
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 20
        assert result.items == []

    def test_get_alert_records_with_keyword(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=0)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        db_session.query = Mock(return_value=mock_query)

        service.get_alert_records(keyword="测试")

        # Verify filter was called for keyword search
        assert mock_query.filter.called

    def test_get_alert_records_with_all_filters(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.join = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=5)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        db_session.query = Mock(return_value=mock_query)

        result = service.get_alert_records(
            page=2,
            page_size=10,
            keyword="test",
            severity="high",
            status="pending",
            rule_type="schedule",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            project_id=100
        )

        assert result.page == 2
        assert result.page_size == 10
        assert result.total == 5

    def test_get_alert_records_pagination(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=50)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        db_session.query = Mock(return_value=mock_query)

        result = service.get_alert_records(page=3, page_size=10)

        # Verify offset calculation: (page - 1) * page_size = (3-1) * 10 = 20
        mock_query.offset.assert_called_with(20)
        mock_query.limit.assert_called_with(10)


class TestGetAlertRecord:
    """Test suite for get_alert_record method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_get_alert_record_found(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.title = "Test Alert"

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_alert)
        db_session.query = Mock(return_value=mock_query)

        result = service.get_alert_record(1)

        assert result == mock_alert
        assert result.id == 1

    def test_get_alert_record_not_found(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        db_session.query = Mock(return_value=mock_query)

        result = service.get_alert_record(999)

        assert result is None


class TestAcknowledgeAlert:
    """Test suite for acknowledge_alert method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def current_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        return user

    def test_acknowledge_alert_success(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "pending"
        mock_alert.title = "Test Alert"

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            with patch.object(service, '_send_alert_notification'):
                handle_data = Mock(spec=AlertRecordHandle)
                handle_data.note = "确认处理"

                result = service.acknowledge_alert(1, handle_data, current_user)

                assert result.status == "acknowledged"
                assert result.acknowledged_by == current_user.id
                assert result.acknowledgment_note == "确认处理"
                db_session.commit.assert_called()

    def test_acknowledge_alert_not_found(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        with patch.object(service, 'get_alert_record', return_value=None):
            handle_data = Mock(spec=AlertRecordHandle)
            handle_data.note = "test"

            result = service.acknowledge_alert(999, handle_data, current_user)

            assert result is None

    def test_acknowledge_alert_wrong_status(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "resolved"  # Wrong status

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            handle_data = Mock(spec=AlertRecordHandle)
            handle_data.note = "test"

            with pytest.raises(HTTPException) as exc_info:
                service.acknowledge_alert(1, handle_data, current_user)

            assert exc_info.value.status_code == 400
            assert "待处理状态" in exc_info.value.detail


class TestResolveAlert:
    """Test suite for resolve_alert method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def current_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user

    def test_resolve_alert_from_pending(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "pending"
        mock_alert.title = "Test"

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            with patch.object(service, '_send_alert_notification'):
                handle_data = Mock(spec=AlertRecordHandle)
                handle_data.note = "已解决"

                result = service.resolve_alert(1, handle_data, current_user)

                assert result.status == "resolved"
                assert result.resolved_by == current_user.id

    def test_resolve_alert_from_acknowledged(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "acknowledged"
        mock_alert.title = "Test"

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            with patch.object(service, '_send_alert_notification'):
                handle_data = Mock(spec=AlertRecordHandle)
                handle_data.note = "已解决"

                result = service.resolve_alert(1, handle_data, current_user)

                assert result.status == "resolved"

    def test_resolve_alert_wrong_status(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "closed"  # Wrong status

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            handle_data = Mock(spec=AlertRecordHandle)
            handle_data.note = "test"

            with pytest.raises(HTTPException) as exc_info:
                service.resolve_alert(1, handle_data, current_user)

            assert exc_info.value.status_code == 400


class TestCloseAlert:
    """Test suite for close_alert method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def current_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user

    def test_close_alert_success(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "resolved"
        mock_alert.title = "Test"

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            with patch.object(service, '_send_alert_notification'):
                handle_data = Mock(spec=AlertRecordHandle)
                handle_data.note = "关闭原因"

                result = service.close_alert(1, handle_data, current_user)

                assert result.status == "closed"
                assert result.closed_by == current_user.id
                assert result.closure_reason == "关闭原因"

    def test_close_alert_already_closed(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "closed"

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            handle_data = Mock(spec=AlertRecordHandle)
            handle_data.note = "test"

            with pytest.raises(HTTPException) as exc_info:
                service.close_alert(1, handle_data, current_user)

            assert exc_info.value.status_code == 400
            assert "已经关闭" in exc_info.value.detail


class TestIgnoreAlert:
    """Test suite for ignore_alert method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def current_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user

    def test_ignore_alert_success(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "pending"

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            handle_data = Mock(spec=AlertRecordHandle)
            handle_data.note = "误报"

            result = service.ignore_alert(1, handle_data, current_user)

            assert result.status == "ignored"
            assert result.ignored_by == current_user.id
            assert result.ignore_reason == "误报"

    def test_ignore_alert_wrong_status(self, db_session, current_user):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.status = "acknowledged"  # Wrong status

        with patch.object(service, 'get_alert_record', return_value=mock_alert):
            handle_data = Mock(spec=AlertRecordHandle)
            handle_data.note = "test"

            with pytest.raises(HTTPException) as exc_info:
                service.ignore_alert(1, handle_data, current_user)

            assert exc_info.value.status_code == 400
            assert "待处理状态" in exc_info.value.detail


class TestCreateAlertFromRule:
    """Test suite for create_alert_from_rule method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_create_alert_from_rule_basic(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_rule = Mock(spec=AlertRule)
        mock_rule.id = 1
        mock_rule.rule_name = "测试规则"
        mock_rule.severity = "high"
        mock_rule.description = "规则描述"
        mock_rule.notification_config = None

        with patch.object(service, '_send_alert_notification'):
            result = service.create_alert_from_rule(
                rule=mock_rule,
                project_id=100,
                target_id=200,
                extra_data={"key": "value"}
            )

            db_session.add.assert_called_once()
            db_session.commit.assert_called()

    def test_create_alert_from_rule_with_assignee(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_rule = Mock(spec=AlertRule)
        mock_rule.id = 1
        mock_rule.rule_name = "测试规则"
        mock_rule.severity = "high"
        mock_rule.description = None
        mock_rule.notification_config = {"assignee_id": 5}

        with patch.object(service, '_send_alert_notification'):
            service.create_alert_from_rule(rule=mock_rule)

            # The alert should have assigned_to set
            call_args = db_session.add.call_args[0][0]
            assert call_args.assigned_to == 5


class TestSendAlertNotification:
    """Test suite for _send_alert_notification method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_send_alert_notification(self, db_session):
        from app.services.alert.alert_records_service import AlertRecordsService

        service = AlertRecordsService(db_session)

        mock_alert = Mock(spec=AlertRecord)
        mock_alert.id = 1
        mock_alert.title = "Test Alert"

        service._send_alert_notification(mock_alert, "created")

        # Verify notification was added
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

        # Check the notification object
        notification = db_session.add.call_args[0][0]
        assert notification.alert_id == 1
        assert notification.notification_type == "system"
        assert "created" in notification.content
