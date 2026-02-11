# -*- coding: utf-8 -*-
"""Tests for invoice_auto_service/creation.py"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestCreateInvoiceRequest:

    def _setup(self):
        from app.services.invoice_auto_service.creation import create_invoice_request
        service = MagicMock()
        plan = MagicMock()
        plan.id = 1
        plan.contract_id = 10
        plan.project_id = 100
        plan.planned_amount = Decimal("10000")
        plan.planned_date = date(2024, 6, 1)
        plan.project.project_name = "测试项目"
        order = MagicMock()
        order.order_no = "AO001"
        order.created_by = 1
        milestone = MagicMock()
        milestone.milestone_name = "FAT验收"
        contract = MagicMock()
        contract.id = 10
        contract.customer_id = 5
        contract.customer.customer_name = "客户A"
        return create_invoice_request, service, plan, order, milestone, contract

    def test_existing_request(self):
        fn, service, plan, order, milestone, contract = self._setup()
        existing = MagicMock()
        existing.id = 99
        service.db.query.return_value.filter.return_value.first.return_value = existing
        result = fn(service, plan, order, milestone)
        assert result["success"] is False
        assert result["request_id"] == 99

    def test_no_contract(self):
        fn, service, plan, order, milestone, contract = self._setup()
        service.db.query.return_value.filter.return_value.first.side_effect = [None, None]
        result = fn(service, plan, order, milestone)
        assert result["success"] is False

    def test_happy_path(self):
        fn, service, plan, order, milestone, contract = self._setup()
        # No existing request
        service.db.query.return_value.filter.return_value.first.side_effect = [None, contract, None]
        service.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        service.db.flush = MagicMock()
        # Mock the added invoice_request
        def capture_add(obj):
            obj.id = 42
        service.db.add.side_effect = capture_add

        result = fn(service, plan, order, milestone)
        assert result["success"] is True
        assert "request_no" in result


class TestCreateInvoiceDirectly:

    def test_already_invoiced(self):
        from app.services.invoice_auto_service.creation import create_invoice_directly
        service = MagicMock()
        plan = MagicMock()
        plan.invoice_id = 1
        result = create_invoice_directly(service, plan, MagicMock(), MagicMock())
        assert result["success"] is False
        assert "已开票" in result["message"]

    def test_no_contract(self):
        from app.services.invoice_auto_service.creation import create_invoice_directly
        service = MagicMock()
        plan = MagicMock()
        plan.invoice_id = None
        plan.contract_id = 10
        service.db.query.return_value.filter.return_value.first.return_value = None
        result = create_invoice_directly(service, plan, MagicMock(), MagicMock())
        assert result["success"] is False

    @patch("app.services.invoice_auto_service.creation.desc")
    @patch("app.services.invoice_auto_service.creation.apply_like_filter", side_effect=lambda q, *a, **kw: q)
    @patch("app.services.invoice_auto_service.creation.Invoice")
    def test_happy_path(self, mock_invoice_cls, mock_like, mock_desc):
        from app.services.invoice_auto_service.creation import create_invoice_directly
        service = MagicMock()
        plan = MagicMock()
        plan.invoice_id = None
        plan.contract_id = 10
        plan.project_id = 100
        plan.planned_amount = Decimal("5000")
        plan.planned_date = date(2024, 7, 1)
        contract = MagicMock()
        contract.id = 10
        contract.customer.customer_name = "客户B"
        contract.customer.tax_no = "123456"
        contract.owner_id = 2
        service.db.query.return_value.filter.return_value.first.return_value = contract
        service.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_inv = MagicMock()
        mock_inv.id = 55
        mock_invoice_cls.return_value = mock_inv
        service.db.flush = MagicMock()

        result = create_invoice_directly(service, plan, MagicMock(), MagicMock())
        assert result["success"] is True
