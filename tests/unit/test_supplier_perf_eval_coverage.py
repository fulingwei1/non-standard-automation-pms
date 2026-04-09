# -*- coding: utf-8 -*-
"""供应商绩效评估服务 - 补充覆盖测试"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator


def _make_vendor(**kw):
    v = MagicMock()
    v.id = kw.get("id", 1)
    v.supplier_code = kw.get("supplier_code", "SUP001")
    v.supplier_name = kw.get("supplier_name", "测试供应商")
    v.status = kw.get("status", "ACTIVE")
    v.vendor_type = kw.get("vendor_type", "MATERIAL")
    return v


def _make_order(**kw):
    o = MagicMock()
    o.id = kw.get("id", 1)
    o.supplier_id = kw.get("supplier_id", 1)
    o.order_date = kw.get("order_date", date(2026, 1, 15))
    o.total_amount = kw.get("total_amount", Decimal("10000"))
    o.promised_date = kw.get("promised_date", date(2026, 2, 1))
    o.required_date = kw.get("required_date", date(2026, 2, 5))
    o.submitted_at = kw.get("submitted_at", None)
    o.approved_at = kw.get("approved_at", None)
    return o


class TestDetermineRating:
    def test_a_plus(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        assert e._determine_rating(Decimal("95")) == "A+"

    def test_a(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        assert e._determine_rating(Decimal("85")) == "A"

    def test_b(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        assert e._determine_rating(Decimal("75")) == "B"

    def test_c(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        assert e._determine_rating(Decimal("65")) == "C"

    def test_d(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        assert e._determine_rating(Decimal("50")) == "D"

    def test_boundary_90(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        assert e._determine_rating(Decimal("90")) == "A+"


class TestCalculateOverallScore:
    def test_perfect_scores(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        d = {"on_time_rate": Decimal("100")}
        q = {"pass_rate": Decimal("100")}
        p = {"competitiveness": Decimal("100")}
        r = {"score": Decimal("100")}
        w = {"on_time_delivery": Decimal("30"), "quality": Decimal("30"),
             "price": Decimal("20"), "response": Decimal("20")}
        assert e._calculate_overall_score(d, q, p, r, w) == Decimal("100")

    def test_mixed_scores(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        d = {"on_time_rate": Decimal("80")}
        q = {"pass_rate": Decimal("90")}
        p = {"competitiveness": Decimal("70")}
        r = {"score": Decimal("60")}
        w = {"on_time_delivery": Decimal("30"), "quality": Decimal("30"),
             "price": Decimal("20"), "response": Decimal("20")}
        assert e._calculate_overall_score(d, q, p, r, w) == Decimal("77")


class TestDeliveryMetrics:
    def test_empty_orders(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        r = e._calculate_delivery_metrics([], date(2026, 1, 1), date(2026, 1, 31))
        assert r["on_time_rate"] == Decimal("0")

    def test_on_time(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        order = _make_order(promised_date=date(2026, 2, 1))
        receipt = MagicMock()
        receipt.receipt_date = date(2026, 1, 28)
        db.query.return_value.filter.return_value.all.return_value = [receipt]
        r = e._calculate_delivery_metrics([order], date(2026, 1, 1), date(2026, 2, 28))
        assert r["on_time_orders"] == 1
        assert r["on_time_rate"] == Decimal("100")

    def test_late(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        order = _make_order(promised_date=date(2026, 2, 1))
        receipt = MagicMock()
        receipt.receipt_date = date(2026, 2, 5)
        db.query.return_value.filter.return_value.all.return_value = [receipt]
        r = e._calculate_delivery_metrics([order], date(2026, 1, 1), date(2026, 2, 28))
        assert r["late_orders"] == 1
        assert r["avg_delay_days"] == Decimal("4")


class TestQualityMetrics:
    def test_empty(self):
        e = SupplierPerformanceEvaluator(MagicMock())
        r = e._calculate_quality_metrics([], date(2026, 1, 1), date(2026, 1, 31))
        assert r["pass_rate"] == Decimal("0")

    def test_full_quality(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        order = _make_order()
        item = MagicMock()
        item.received_qty = Decimal("100")
        item.qualified_qty = Decimal("100")
        item.rejected_qty = Decimal("0")
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [item]
        r = e._calculate_quality_metrics([order], date(2026, 1, 1), date(2026, 2, 28))
        assert r["pass_rate"] == Decimal("100")


class TestPriceCompetitiveness:
    def test_no_data(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = None
        r = e._calculate_price_competitiveness(1, date(2026, 1, 1), date(2026, 1, 31))
        assert r["competitiveness"] == Decimal("50")

    def test_much_cheaper(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        db.query.return_value.join.return_value.filter.return_value.scalar.side_effect = [80, 100]
        r = e._calculate_price_competitiveness(1, date(2026, 1, 1), date(2026, 1, 31))
        assert r["competitiveness"] == Decimal("100")

    def test_much_expensive(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        db.query.return_value.join.return_value.filter.return_value.scalar.side_effect = [125, 100]
        r = e._calculate_price_competitiveness(1, date(2026, 1, 1), date(2026, 1, 31))
        assert r["competitiveness"] == Decimal("20")


class TestResponseSpeed:
    def test_no_orders(self):
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        db.query.return_value.filter.return_value.all.return_value = []
        r = e._calculate_response_speed(1, date(2026, 1, 1), date(2026, 1, 31))
        assert r["score"] == Decimal("50")

    def test_fast(self):
        from datetime import datetime as dt
        db = MagicMock()
        e = SupplierPerformanceEvaluator(db)
        order = MagicMock()
        order.submitted_at = dt(2026, 1, 1, 10, 0)
        order.approved_at = dt(2026, 1, 1, 12, 0)
        db.query.return_value.filter.return_value.all.return_value = [order]
        r = e._calculate_response_speed(1, date(2026, 1, 1), date(2026, 1, 31))
        assert r["score"] == Decimal("100")


class TestEvaluateSupplier:
    def test_not_found(self):
        db = MagicMock()
        db.query.return_value.get.return_value = None
        e = SupplierPerformanceEvaluator(db)
        assert e.evaluate_supplier(999, "2026-01") is None

    def test_invalid_period(self):
        db = MagicMock()
        db.query.return_value.get.return_value = _make_vendor()
        e = SupplierPerformanceEvaluator(db)
        assert e.evaluate_supplier(1, "bad") is None


class TestBatchEvaluate:
    def test_counts_successes(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            _make_vendor(id=1), _make_vendor(id=2)
        ]
        e = SupplierPerformanceEvaluator(db)
        with patch.object(e, "evaluate_supplier", return_value=MagicMock()):
            assert e.batch_evaluate_all_suppliers("2026-01") == 2

    def test_skips_errors(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            _make_vendor(id=1), _make_vendor(id=2)
        ]
        e = SupplierPerformanceEvaluator(db)
        with patch.object(e, "evaluate_supplier", side_effect=[Exception(), MagicMock()]):
            assert e.batch_evaluate_all_suppliers("2026-01") == 1
