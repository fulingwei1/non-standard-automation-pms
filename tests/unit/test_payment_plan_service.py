# -*- coding: utf-8 -*-
"""Tests for sales/payment_plan_service.py"""

from unittest.mock import MagicMock, PropertyMock

import pytest


class TestPaymentPlanService:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.sales.payment_plan_service import PaymentPlanService
        self.service = PaymentPlanService(self.db)

    def test_get_payment_configurations(self):
        configs = self.service._get_payment_configurations()
        assert isinstance(configs, list)
        assert len(configs) == 4
        ratios = sum(c["payment_ratio"] for c in configs)
        assert ratios == 100.0

    def test_validate_contract_no_project_id(self):
        contract = MagicMock()
        contract.project_id = None
        assert self.service._validate_contract(contract) is False

    def test_validate_contract_no_project(self):
        contract = MagicMock()
        contract.project_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.service._validate_contract(contract) is False

    def test_validate_contract_zero_amount(self):
        contract = MagicMock()
        contract.project_id = 1
        contract.contract_amount = 0
        project = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = project
        assert self.service._validate_contract(contract) is False

    def test_validate_contract_valid(self):
        contract = MagicMock()
        contract.project_id = 1
        contract.id = 10
        contract.contract_amount = 100000
        project = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.count.return_value = 0
        assert self.service._validate_contract(contract) is True

    def test_generate_plans_invalid_contract(self):
        contract = MagicMock()
        contract.project_id = None
        result = self.service.generate_payment_plans_from_contract(contract)
        assert result == []
