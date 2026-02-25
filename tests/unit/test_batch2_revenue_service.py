# -*- coding: utf-8 -*-
"""Revenue Service 测试 - Batch 2"""
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.services.revenue_service import RevenueService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_project():
    p = MagicMock()
    p.id = 1
    p.contract_amount = 100000
    p.project_code = "P001"
    p.project_name = "Test Project"
    return p


class TestGetProjectRevenue:
    def test_project_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        assert RevenueService.get_project_revenue(mock_db, 999) == Decimal("0")

    def test_contract_type(self, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        assert RevenueService.get_project_revenue(mock_db, 1, "CONTRACT") == Decimal("100000")

    def test_contract_none(self, mock_db):
        p = MagicMock(); p.contract_amount = None
        mock_db.query.return_value.filter.return_value.first.return_value = p
        assert RevenueService.get_project_revenue(mock_db, 1, "CONTRACT") == Decimal("0")

    @patch.object(RevenueService, '_get_received_amount', return_value=Decimal("8000"))
    def test_received_type(self, m, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        assert RevenueService.get_project_revenue(mock_db, 1, "RECEIVED") == Decimal("8000")

    @patch.object(RevenueService, '_get_invoiced_amount', return_value=Decimal("12000"))
    def test_invoiced_type(self, m, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        assert RevenueService.get_project_revenue(mock_db, 1, "INVOICED") == Decimal("12000")

    @patch.object(RevenueService, '_get_paid_invoice_amount', return_value=Decimal("6000"))
    def test_paid_invoice_type(self, m, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        assert RevenueService.get_project_revenue(mock_db, 1, "PAID_INVOICE") == Decimal("6000")

    def test_unknown_type(self, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        assert RevenueService.get_project_revenue(mock_db, 1, "UNKNOWN") == Decimal("100000")


class TestInvoiceAmounts:
    def test_invoiced_amount(self, mock_db):
        inv = MagicMock(); inv.total_amount = 5000; inv.amount = 5000
        mock_db.query.return_value.filter.return_value.all.return_value = [inv]
        assert RevenueService._get_invoiced_amount(mock_db, 1) == Decimal("5000")

    def test_invoiced_empty(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        assert RevenueService._get_invoiced_amount(mock_db, 1) == Decimal("0")

    def test_invoiced_fallback(self, mock_db):
        inv = MagicMock(); inv.total_amount = None; inv.amount = 2000
        mock_db.query.return_value.filter.return_value.all.return_value = [inv]
        assert RevenueService._get_invoiced_amount(mock_db, 1) == Decimal("2000")

    def test_paid_invoice(self, mock_db):
        inv = MagicMock(); inv.paid_amount = 3000; inv.total_amount = 5000; inv.amount = 5000
        mock_db.query.return_value.filter.return_value.all.return_value = [inv]
        assert RevenueService._get_paid_invoice_amount(mock_db, 1) == Decimal("3000")

    def test_paid_invoice_fallback(self, mock_db):
        inv = MagicMock(); inv.paid_amount = None; inv.total_amount = None; inv.amount = 1500
        mock_db.query.return_value.filter.return_value.all.return_value = [inv]
        assert RevenueService._get_paid_invoice_amount(mock_db, 1) == Decimal("1500")


class TestRevenueDetail:
    def test_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        r = RevenueService.get_project_revenue_detail(mock_db, 999)
        assert r["contract_amount"] == Decimal("0")

    @patch.object(RevenueService, '_get_received_amount', return_value=Decimal("5000"))
    @patch.object(RevenueService, '_get_invoiced_amount', return_value=Decimal("8000"))
    @patch.object(RevenueService, '_get_paid_invoice_amount', return_value=Decimal("3000"))
    def test_found(self, m1, m2, m3, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        r = RevenueService.get_project_revenue_detail(mock_db, 1)
        assert r["pending_amount"] == Decimal("95000")

    @patch.object(RevenueService, '_get_received_amount', return_value=Decimal("0"))
    @patch.object(RevenueService, '_get_invoiced_amount', return_value=Decimal("0"))
    @patch.object(RevenueService, '_get_paid_invoice_amount', return_value=Decimal("0"))
    def test_zero_contract(self, m1, m2, m3, mock_db):
        p = MagicMock(); p.id = 1; p.contract_amount = 0; p.project_code = "X"; p.project_name = "X"
        mock_db.query.return_value.filter.return_value.first.return_value = p
        r = RevenueService.get_project_revenue_detail(mock_db, 1)
        assert r["receive_rate"] == Decimal("0")


class TestBatchRevenue:
    @patch.object(RevenueService, 'get_project_revenue', side_effect=[Decimal("100"), Decimal("200")])
    def test_batch(self, m, mock_db):
        assert RevenueService.get_projects_revenue(mock_db, [1, 2]) == {1: Decimal("100"), 2: Decimal("200")}

    def test_empty(self, mock_db):
        assert RevenueService.get_projects_revenue(mock_db, []) == {}

    @patch.object(RevenueService, 'get_projects_revenue', return_value={1: Decimal("100"), 2: Decimal("200")})
    def test_total(self, m, mock_db):
        assert RevenueService.get_total_revenue(mock_db, [1, 2]) == Decimal("300")
