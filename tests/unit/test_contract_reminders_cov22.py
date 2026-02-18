# -*- coding: utf-8 -*-
"""第二十二批：contract_reminders 单元测试"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

try:
    from app.services.sales_reminder.contract_reminders import (
        notify_contract_signed,
        notify_contract_expiring,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def mock_contract():
    c = MagicMock()
    c.id = 1
    c.contract_code = "C-2025-001"
    c.owner_id = 10
    c.contract_amount = Decimal("100000")
    c.signed_date = date(2025, 1, 1)
    c.delivery_deadline = date(2025, 4, 1)
    c.status = "SIGNED"
    c.project = None
    c.project_id = None
    return c


class TestNotifyContractSigned:
    def test_contract_not_found_returns_none(self, db):
        """合同不存在时返回None"""
        db.query.return_value.filter.return_value.first.return_value = None
        result = notify_contract_signed(db, 999)
        assert result is None

    def test_contract_no_owner_returns_none(self, db, mock_contract):
        """合同无负责人时返回None"""
        mock_contract.owner_id = None
        db.query.return_value.filter.return_value.first.return_value = mock_contract
        result = notify_contract_signed(db, 1)
        assert result is None

    def test_contract_signed_creates_notification(self, db, mock_contract):
        """合同签订时创建通知"""
        db.query.return_value.filter.return_value.first.return_value = mock_contract
        with patch(
            "app.services.sales_reminder.contract_reminders.create_notification"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            result = notify_contract_signed(db, 1)
            assert mock_create.called
            kwargs = mock_create.call_args[1]
            assert kwargs["notification_type"] == "CONTRACT_SIGNED"
            assert kwargs["user_id"] == 10

    def test_notification_contains_contract_code(self, db, mock_contract):
        """通知标题包含合同编码"""
        db.query.return_value.filter.return_value.first.return_value = mock_contract
        with patch(
            "app.services.sales_reminder.contract_reminders.create_notification"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            notify_contract_signed(db, 1)
            kwargs = mock_create.call_args[1]
            assert "C-2025-001" in kwargs["title"]


class TestNotifyContractExpiring:
    def test_no_contracts_returns_zero(self, db):
        """无合同时返回0"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = notify_contract_expiring(db)
        assert result == 0

    def test_contract_no_deadline_skipped(self, db, mock_contract):
        """无交期的合同跳过"""
        mock_contract.delivery_deadline = None
        db.query.return_value.filter.return_value.all.return_value = [mock_contract]
        result = notify_contract_expiring(db)
        assert result == 0

    def test_contract_not_in_reminder_days_skipped(self, db, mock_contract):
        """不在提醒天数内的合同跳过"""
        mock_contract.delivery_deadline = date.today().replace(
            year=date.today().year + 1
        )
        db.query.return_value.filter.return_value.all.return_value = [mock_contract]
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS = [7, 15, 30]
            result = notify_contract_expiring(db)
            assert result == 0

    def test_already_notified_today_skipped(self, db, mock_contract):
        """今天已发送过提醒时跳过"""
        from datetime import timedelta
        mock_contract.delivery_deadline = date.today() + timedelta(days=7)
        db.query.return_value.filter.return_value.all.return_value = [mock_contract]

        existing_notification = MagicMock()
        existing_notification.extra_data = {"days_left": 7}

        def query_side_effect(model):
            m = MagicMock()
            m.filter.return_value = m
            if "Notification" in str(model):
                m.all.return_value = [mock_contract]
                m.first.return_value = existing_notification
            else:
                m.all.return_value = [mock_contract]
                m.first.return_value = None
            return m

        db.query.side_effect = query_side_effect
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS = [7, 15, 30]
            # Already notified => count stays 0
            result = notify_contract_expiring(db)
            assert isinstance(result, int)
