# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from app.services.sales_reminder.contract_reminders import notify_contract_signed, notify_contract_expiring


class TestNotifyContractSigned:
    def test_contract_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        assert notify_contract_signed(db, 999) is None

    def test_contract_no_owner(self):
        db = MagicMock()
        contract = MagicMock()
        contract.owner_id = None
        db.query.return_value.filter.return_value.first.return_value = contract
        assert notify_contract_signed(db, 1) is None

    @patch("app.services.sales_reminder.contract_reminders.create_notification")
    def test_contract_signed_success(self, mock_notify):
        db = MagicMock()
        contract = MagicMock()
        contract.owner_id = 1
        contract.id = 10
        contract.contract_code = "C001"
        contract.contract_amount = 50000
        contract.signed_date = date(2024, 1, 1)
        db.query.return_value.filter.return_value.first.return_value = contract
        mock_notify.return_value = MagicMock()
        result = notify_contract_signed(db, 10)
        mock_notify.assert_called_once()


class TestNotifyContractExpiring:
    @patch("app.services.sales_reminder.contract_reminders.settings")
    def test_no_contracts(self, mock_settings):
        mock_settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS = [30, 15, 7]
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        assert notify_contract_expiring(db) == 0
