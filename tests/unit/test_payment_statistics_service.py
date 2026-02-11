# -*- coding: utf-8 -*-
"""Tests for payment_statistics_service"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


class TestPaymentStatisticsService:

    def _make_invoice(self, issue_date=None, total_amount=None, amount=None,
                      paid_amount=None, payment_status="PENDING", due_date=None,
                      contract=None):
        inv = MagicMock()
        inv.issue_date = issue_date
        inv.total_amount = total_amount
        inv.amount = amount
        inv.paid_amount = paid_amount
        inv.payment_status = payment_status
        inv.due_date = due_date
        inv.contract = contract
        inv.created_at = datetime(2024, 1, 15)
        inv.status = "ISSUED"
        return inv

    def test_calculate_monthly_statistics_happy(self):
        from app.services.payment_statistics_service import calculate_monthly_statistics
        inv = self._make_invoice(
            issue_date=date(2024, 3, 15),
            total_amount=Decimal("10000"),
            paid_amount=Decimal("5000")
        )
        result = calculate_monthly_statistics([inv])
        assert "2024-03" in result
        assert result["2024-03"]["invoiced"] == Decimal("10000")
        assert result["2024-03"]["paid"] == Decimal("5000")

    def test_calculate_monthly_statistics_empty(self):
        from app.services.payment_statistics_service import calculate_monthly_statistics
        result = calculate_monthly_statistics([])
        assert result == {}

    def test_calculate_monthly_statistics_no_issue_date(self):
        from app.services.payment_statistics_service import calculate_monthly_statistics
        inv = self._make_invoice(issue_date=None, total_amount=Decimal("1000"))
        result = calculate_monthly_statistics([inv])
        assert result == {}

    def test_calculate_customer_statistics(self):
        from app.services.payment_statistics_service import calculate_customer_statistics
        contract = MagicMock()
        contract.customer_id = 1
        contract.customer.customer_name = "客户A"
        inv = self._make_invoice(
            total_amount=Decimal("8000"),
            paid_amount=Decimal("3000"),
            contract=contract
        )
        result = calculate_customer_statistics([inv])
        assert 1 in result
        assert result[1]["unpaid"] == Decimal("5000")

    def test_calculate_status_statistics(self):
        from app.services.payment_statistics_service import calculate_status_statistics
        inv1 = self._make_invoice(payment_status="PAID", total_amount=Decimal("5000"))
        inv2 = self._make_invoice(payment_status="PENDING", total_amount=Decimal("3000"))
        result = calculate_status_statistics([inv1, inv2])
        assert result["PAID"]["count"] == 1
        assert result["PENDING"]["count"] == 1

    def test_calculate_overdue_amount(self):
        from app.services.payment_statistics_service import calculate_overdue_amount
        inv = self._make_invoice(
            due_date=date(2024, 1, 1),
            payment_status="PENDING",
            total_amount=Decimal("10000"),
            paid_amount=Decimal("2000")
        )
        result = calculate_overdue_amount([inv], date(2024, 2, 1))
        assert result == Decimal("8000")

    def test_calculate_overdue_amount_not_overdue(self):
        from app.services.payment_statistics_service import calculate_overdue_amount
        inv = self._make_invoice(
            due_date=date(2024, 12, 31),
            payment_status="PENDING",
            total_amount=Decimal("10000"),
            paid_amount=Decimal("0")
        )
        result = calculate_overdue_amount([inv], date(2024, 2, 1))
        assert result == Decimal("0")

    def test_build_monthly_list(self):
        from app.services.payment_statistics_service import build_monthly_list
        stats = {
            "2024-01": {"invoiced": Decimal("10000"), "paid": Decimal("8000"), "count": 2},
            "2024-02": {"invoiced": Decimal("5000"), "paid": Decimal("0"), "count": 1},
        }
        result = build_monthly_list(stats)
        assert len(result) == 2
        assert result[0]["month"] == "2024-01"
        assert result[0]["collection_rate"] == 80.0

    def test_build_customer_list(self):
        from app.services.payment_statistics_service import build_customer_list
        stats = {
            1: {"customer_id": 1, "customer_name": "A", "invoiced": Decimal("10000"),
                "paid": Decimal("5000"), "unpaid": Decimal("5000"), "count": 1}
        }
        result = build_customer_list(stats)
        assert len(result) == 1
        assert result[0]["customer_name"] == "A"

    def test_build_customer_list_limit(self):
        from app.services.payment_statistics_service import build_customer_list
        stats = {i: {"customer_id": i, "customer_name": f"C{i}", "invoiced": Decimal("1000"),
                      "paid": Decimal("0"), "unpaid": Decimal(str(i * 100)), "count": 1}
                 for i in range(15)}
        result = build_customer_list(stats, limit=5)
        assert len(result) == 5
