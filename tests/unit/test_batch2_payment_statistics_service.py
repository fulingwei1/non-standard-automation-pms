# -*- coding: utf-8 -*-
"""Payment Statistics Service 测试 - Batch 2"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock
import pytest

from app.services.payment_statistics_service import (
    build_invoice_query, calculate_monthly_statistics,
    calculate_customer_statistics, calculate_status_statistics,
    calculate_overdue_amount, build_monthly_list, build_customer_list
)


def make_invoice(issue_date=None, total_amount=None, amount=None, paid_amount=None,
                 payment_status="PENDING", due_date=None, contract=None, status="ISSUED"):
    inv = MagicMock()
    inv.issue_date = issue_date
    inv.total_amount = total_amount
    inv.amount = amount
    inv.paid_amount = paid_amount
    inv.payment_status = payment_status
    inv.due_date = due_date
    inv.contract = contract
    inv.status = status
    return inv


class TestCalculateMonthlyStatistics:
    def test_empty_invoices(self):
        result = calculate_monthly_statistics([])
        assert result == {}

    def test_single_invoice(self):
        inv = make_invoice(issue_date=date(2024, 1, 15), total_amount=Decimal("10000"), paid_amount=Decimal("5000"))
        result = calculate_monthly_statistics([inv])
        assert "2024-01" in result
        assert result["2024-01"]["invoiced"] == Decimal("10000")
        assert result["2024-01"]["paid"] == Decimal("5000")
        assert result["2024-01"]["count"] == 1

    def test_multiple_months(self):
        inv1 = make_invoice(issue_date=date(2024, 1, 1), total_amount=Decimal("1000"), paid_amount=Decimal("500"))
        inv2 = make_invoice(issue_date=date(2024, 2, 1), total_amount=Decimal("2000"), paid_amount=Decimal("1000"))
        result = calculate_monthly_statistics([inv1, inv2])
        assert len(result) == 2

    def test_no_issue_date_skipped(self):
        inv = make_invoice(issue_date=None, total_amount=Decimal("1000"))
        result = calculate_monthly_statistics([inv])
        assert result == {}

    def test_fallback_to_amount(self):
        inv = make_invoice(issue_date=date(2024, 3, 1), total_amount=None, amount=Decimal("800"), paid_amount=Decimal("0"))
        result = calculate_monthly_statistics([inv])
        assert result["2024-03"]["invoiced"] == Decimal("800")

    def test_none_paid_amount(self):
        inv = make_invoice(issue_date=date(2024, 1, 1), total_amount=Decimal("5000"), paid_amount=None)
        result = calculate_monthly_statistics([inv])
        assert result["2024-01"]["paid"] == Decimal("0")


class TestCalculateCustomerStatistics:
    def test_empty(self):
        assert calculate_customer_statistics([]) == {}

    def test_with_contract(self):
        customer = MagicMock()
        customer.customer_name = "客户A"
        contract = MagicMock()
        contract.customer_id = 1
        contract.customer = customer
        inv = make_invoice(total_amount=Decimal("10000"), paid_amount=Decimal("3000"), contract=contract)
        result = calculate_customer_statistics([inv])
        assert 1 in result
        assert result[1]["customer_name"] == "客户A"
        assert result[1]["unpaid"] == Decimal("7000")

    def test_no_contract(self):
        inv = make_invoice(total_amount=Decimal("5000"), contract=None)
        result = calculate_customer_statistics([inv])
        assert result == {}

    def test_multiple_invoices_same_customer(self):
        customer = MagicMock()
        customer.customer_name = "客户B"
        contract = MagicMock()
        contract.customer_id = 2
        contract.customer = customer
        inv1 = make_invoice(total_amount=Decimal("1000"), paid_amount=Decimal("500"), contract=contract)
        inv2 = make_invoice(total_amount=Decimal("2000"), paid_amount=Decimal("1000"), contract=contract)
        result = calculate_customer_statistics([inv1, inv2])
        assert result[2]["count"] == 2
        assert result[2]["invoiced"] == Decimal("3000")


class TestCalculateStatusStatistics:
    def test_empty(self):
        result = calculate_status_statistics([])
        assert result["PAID"]["count"] == 0
        assert result["PARTIAL"]["count"] == 0
        assert result["PENDING"]["count"] == 0

    def test_paid_status(self):
        inv = make_invoice(total_amount=Decimal("5000"), payment_status="PAID")
        result = calculate_status_statistics([inv])
        assert result["PAID"]["count"] == 1
        assert result["PAID"]["amount"] == Decimal("5000")

    def test_partial_status(self):
        inv = make_invoice(total_amount=Decimal("3000"), payment_status="PARTIAL")
        result = calculate_status_statistics([inv])
        assert result["PARTIAL"]["count"] == 1

    def test_default_pending(self):
        inv = make_invoice(total_amount=Decimal("2000"), payment_status=None)
        result = calculate_status_statistics([inv])
        assert result["PENDING"]["count"] == 1

    def test_unknown_status_ignored(self):
        inv = make_invoice(total_amount=Decimal("1000"), payment_status="CANCELLED")
        result = calculate_status_statistics([inv])
        assert all(v["count"] == 0 for v in result.values())


class TestCalculateOverdueAmount:
    def test_no_invoices(self):
        assert calculate_overdue_amount([], date(2024, 6, 1)) == Decimal("0")

    def test_overdue_invoice(self):
        inv = make_invoice(total_amount=Decimal("10000"), paid_amount=Decimal("3000"),
                          due_date=date(2024, 1, 1), payment_status="PENDING")
        result = calculate_overdue_amount([inv], date(2024, 6, 1))
        assert result == Decimal("7000")

    def test_not_overdue(self):
        inv = make_invoice(total_amount=Decimal("10000"), paid_amount=Decimal("0"),
                          due_date=date(2025, 1, 1), payment_status="PENDING")
        result = calculate_overdue_amount([inv], date(2024, 6, 1))
        assert result == Decimal("0")

    def test_paid_not_overdue(self):
        inv = make_invoice(total_amount=Decimal("5000"), paid_amount=Decimal("5000"),
                          due_date=date(2024, 1, 1), payment_status="PAID")
        result = calculate_overdue_amount([inv], date(2024, 6, 1))
        assert result == Decimal("0")

    def test_no_due_date(self):
        inv = make_invoice(total_amount=Decimal("5000"), due_date=None, payment_status="PENDING")
        assert calculate_overdue_amount([inv], date(2024, 6, 1)) == Decimal("0")


class TestBuildMonthlyList:
    def test_empty(self):
        assert build_monthly_list({}) == []

    def test_sorted_by_month(self):
        stats = {
            "2024-03": {"invoiced": Decimal("1000"), "paid": Decimal("500"), "count": 1},
            "2024-01": {"invoiced": Decimal("2000"), "paid": Decimal("1000"), "count": 2},
        }
        result = build_monthly_list(stats)
        assert result[0]["month"] == "2024-01"
        assert result[1]["month"] == "2024-03"

    def test_collection_rate(self):
        stats = {"2024-01": {"invoiced": Decimal("10000"), "paid": Decimal("5000"), "count": 1}}
        result = build_monthly_list(stats)
        assert result[0]["collection_rate"] == 50.0

    def test_zero_invoiced(self):
        stats = {"2024-01": {"invoiced": Decimal("0"), "paid": Decimal("0"), "count": 0}}
        result = build_monthly_list(stats)
        assert result[0]["collection_rate"] == 0


class TestBuildCustomerList:
    def test_empty(self):
        assert build_customer_list({}) == []

    def test_sorted_by_unpaid_desc(self):
        stats = {
            1: {"customer_id": 1, "customer_name": "A", "invoiced": Decimal("100"), "paid": Decimal("50"), "unpaid": Decimal("50"), "count": 1},
            2: {"customer_id": 2, "customer_name": "B", "invoiced": Decimal("200"), "paid": Decimal("10"), "unpaid": Decimal("190"), "count": 1},
        }
        result = build_customer_list(stats)
        assert result[0]["customer_name"] == "B"

    def test_limit(self):
        stats = {i: {"customer_id": i, "customer_name": f"C{i}", "invoiced": Decimal("100"),
                      "paid": Decimal("50"), "unpaid": Decimal("50"), "count": 1} for i in range(20)}
        result = build_customer_list(stats, limit=5)
        assert len(result) == 5
