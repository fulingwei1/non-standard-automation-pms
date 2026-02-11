# -*- coding: utf-8 -*-
"""Tests for status_handlers/contract_handler.py"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestContractStatusHandler:

    def _make_handler(self):
        from app.services.status_handlers.contract_handler import ContractStatusHandler
        db = MagicMock()
        parent = MagicMock()
        return ContractStatusHandler(db, parent), db

    def test_contract_not_found(self):
        handler, db = self._make_handler()
        db.query.return_value.filter.return_value.first.return_value = None
        result = handler.handle_contract_signed(contract_id=999)
        assert result is None

    def test_existing_project_update(self):
        handler, db = self._make_handler()
        contract = MagicMock()
        contract.id = 1
        contract.project_id = 10
        contract.signed_date = datetime(2024, 1, 1)
        contract.contract_amount = 100000
        contract.customer_contract_no = "CC001"

        project = MagicMock()
        project.id = 10
        project.stage = "S2"
        project.status = "ST05"

        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        db.commit = MagicMock()

        result = handler.handle_contract_signed(contract_id=1)
        assert project.stage == "S3"
        assert project.status == "ST08"
        db.commit.assert_called()

    def test_no_auto_create(self):
        handler, db = self._make_handler()
        contract = MagicMock()
        contract.id = 1
        contract.project_id = None
        db.query.return_value.filter.return_value.first.return_value = contract

        result = handler.handle_contract_signed(contract_id=1, auto_create_project=False)
        assert result is None

    @patch("app.services.status_handlers.contract_handler.generate_project_code", return_value="P2024001")
    @patch("app.services.status_handlers.contract_handler.init_project_stages")
    def test_auto_create_project(self, mock_init, mock_gen):
        handler, db = self._make_handler()
        contract = MagicMock()
        contract.id = 1
        contract.project_id = None
        contract.customer_id = 5
        contract.contract_code = "C001"
        contract.contract_amount = 200000
        contract.signed_date = datetime(2024, 2, 1)
        contract.contract_name = "测试合同"
        contract.delivery_deadline = datetime(2024, 12, 31)
        contract.opportunity_id = None
        contract.customer_contract_no = "CC002"

        customer = MagicMock()
        customer.customer_name = "客户X"
        customer.contact_person = "张三"
        customer.contact_phone = "13800138000"

        db.query.return_value.filter.return_value.first.side_effect = [contract, customer]
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()

        result = handler.handle_contract_signed(contract_id=1)
        db.add.assert_called()
        db.commit.assert_called()
        mock_init.assert_called()

    def test_log_status_change_with_callback(self):
        handler, db = self._make_handler()
        callback = MagicMock()
        handler._log_status_change(
            project_id=1,
            old_stage="S2",
            new_stage="S3",
            change_type="TEST",
            log_status_change=callback
        )
        callback.assert_called_once()

    def test_log_status_change_direct(self):
        handler, db = self._make_handler()
        handler._log_status_change(
            project_id=1,
            old_stage="S2",
            new_stage="S3",
            change_type="TEST"
        )
        db.add.assert_called_once()
