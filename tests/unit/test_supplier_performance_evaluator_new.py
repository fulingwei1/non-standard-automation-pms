# -*- coding: utf-8 -*-
"""
供应商绩效评估服务单元测试 (F组)

测试 SupplierPerformanceEvaluator 的核心方法：
- evaluate_supplier
- _calculate_delivery_metrics
- _calculate_quality_metrics
- _calculate_price_competitiveness
- _calculate_response_speed
- _calculate_overall_score
- _determine_rating
- get_supplier_ranking
- batch_evaluate_all_suppliers
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def evaluator(db):
    return SupplierPerformanceEvaluator(db, tenant_id=1)


# ============================================================
# 初始化测试
# ============================================================

class TestInit:
    def test_init_defaults(self, db):
        ev = SupplierPerformanceEvaluator(db)
        assert ev.db is db
        assert ev.tenant_id == 1

    def test_init_custom_tenant(self, db):
        ev = SupplierPerformanceEvaluator(db, tenant_id=5)
        assert ev.tenant_id == 5


# ============================================================
# evaluate_supplier 测试
# ============================================================

class TestEvaluateSupplier:
    def test_supplier_not_found(self, evaluator, db):
        db.query.return_value.get.return_value = None
        result = evaluator.evaluate_supplier(999, "2025-01")
        assert result is None

    def test_invalid_period_format(self, evaluator, db):
        supplier = MagicMock()
        db.query.return_value.get.return_value = supplier
        result = evaluator.evaluate_supplier(1, "invalid-period")
        assert result is None

    def test_no_orders_existing_record(self, evaluator, db):
        supplier = MagicMock(supplier_code="SUP001", supplier_name="供应商A")
        existing = MagicMock()
        db.query.return_value.get.return_value = supplier
        # filter chain for existing + orders
        db.query.return_value.filter.return_value.first.return_value = existing
        db.query.return_value.filter.return_value.all.return_value = []
        result = evaluator.evaluate_supplier(1, "2025-01")
        assert result == existing

    def test_evaluate_creates_new_record(self, evaluator, db):
        """测试有订单时创建新评估记录"""
        supplier = MagicMock(supplier_code="SUP001", supplier_name="供应商A")
        db.query.return_value.get.return_value = supplier
        db.query.return_value.filter.return_value.first.return_value = None

        order = MagicMock(id=1, total_amount=Decimal("10000"), order_date=date(2025, 1, 15))
        db.query.return_value.filter.return_value.all.return_value = [order]

        # Delivery: receipts per order
        receipt = MagicMock(receipt_date=date(2025, 1, 14))
        # Quality: receipt items
        item = MagicMock(received_qty=Decimal("100"), qualified_qty=Decimal("95"), rejected_qty=Decimal("5"))
        # Price query (scalar)
        db.query.return_value.filter.return_value.scalar.return_value = 100.0
        # Response: orders with timestamps
        db.query.return_value.filter.return_value.all.side_effect = [
            [order],   # main orders
            [receipt], # delivery receipts
            [item],    # quality items (joined)
            [],        # response orders
        ]
        performance = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        # Patch SupplierPerformance constructor call
        with patch('app.services.supplier_performance_evaluator.SupplierPerformance') as MockPerf:
            MockPerf.return_value = performance
            db.refresh.return_value = None
            result = evaluator.evaluate_supplier(1, "2025-01")
        # verify db.add was called (new record)
        assert db.add.called


# ============================================================
# _calculate_delivery_metrics 测试
# ============================================================

class TestCalculateDeliveryMetrics:
    def test_empty_orders(self, evaluator, db):
        result = evaluator._calculate_delivery_metrics([], date(2025, 1, 1), date(2025, 1, 31))
        assert result["on_time_rate"] == Decimal("0")
        assert result["on_time_orders"] == 0
        assert result["late_orders"] == 0
        assert result["avg_delay_days"] == Decimal("0")

    def test_on_time_delivery(self, evaluator, db):
        order = MagicMock(id=1, promised_date=date(2025, 1, 20), required_date=None)
        receipt = MagicMock(receipt_date=date(2025, 1, 18))
        db.query.return_value.filter.return_value.all.return_value = [receipt]

        result = evaluator._calculate_delivery_metrics(
            [order], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["on_time_orders"] == 1
        assert result["late_orders"] == 0
        assert result["on_time_rate"] == Decimal("100")

    def test_late_delivery(self, evaluator, db):
        order = MagicMock(id=1, promised_date=date(2025, 1, 10), required_date=None)
        receipt = MagicMock(receipt_date=date(2025, 1, 15))
        db.query.return_value.filter.return_value.all.return_value = [receipt]

        result = evaluator._calculate_delivery_metrics(
            [order], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["late_orders"] == 1
        assert result["avg_delay_days"] == Decimal("5")

    def test_no_receipts(self, evaluator, db):
        order = MagicMock(id=1, promised_date=date(2025, 1, 10))
        db.query.return_value.filter.return_value.all.return_value = []

        result = evaluator._calculate_delivery_metrics(
            [order], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["on_time_orders"] == 0


# ============================================================
# _calculate_quality_metrics 测试
# ============================================================

class TestCalculateQualityMetrics:
    def test_empty_orders(self, evaluator, db):
        result = evaluator._calculate_quality_metrics([], date(2025, 1, 1), date(2025, 1, 31))
        assert result["pass_rate"] == Decimal("0")
        assert result["total_qty"] == Decimal("0")

    def test_full_quality(self, evaluator, db):
        order = MagicMock(id=1)
        item = MagicMock(
            received_qty=Decimal("100"),
            qualified_qty=Decimal("100"),
            rejected_qty=Decimal("0")
        )
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [item]

        result = evaluator._calculate_quality_metrics(
            [order], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["pass_rate"] == Decimal("100")

    def test_partial_quality(self, evaluator, db):
        order = MagicMock(id=1)
        item = MagicMock(
            received_qty=Decimal("100"),
            qualified_qty=Decimal("80"),
            rejected_qty=Decimal("20")
        )
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [item]

        result = evaluator._calculate_quality_metrics(
            [order], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["pass_rate"] == Decimal("80")
        assert result["rejected_qty"] == Decimal("20")


# ============================================================
# _calculate_price_competitiveness 测试
# ============================================================

class TestCalculatePriceCompetitiveness:
    def test_no_price_data(self, evaluator, db):
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = None
        result = evaluator._calculate_price_competitiveness(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["competitiveness"] == Decimal("50")

    def test_below_market_price(self, evaluator, db):
        # Supplier avg 80, market avg 100 -> vs_market = -20%
        db.query.return_value.join.return_value.filter.return_value.scalar.side_effect = [80.0, 100.0]
        result = evaluator._calculate_price_competitiveness(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["competitiveness"] == Decimal("100")

    def test_above_market_price(self, evaluator, db):
        # Supplier avg 120, market avg 100 -> vs_market = +20%
        db.query.return_value.join.return_value.filter.return_value.scalar.side_effect = [120.0, 100.0]
        result = evaluator._calculate_price_competitiveness(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["competitiveness"] == Decimal("40")

    def test_at_market_price(self, evaluator, db):
        # Supplier avg 100, market avg 100 -> vs_market = 0%
        db.query.return_value.join.return_value.filter.return_value.scalar.side_effect = [100.0, 100.0]
        result = evaluator._calculate_price_competitiveness(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["competitiveness"] == Decimal("80")


# ============================================================
# _calculate_response_speed 测试
# ============================================================

class TestCalculateResponseSpeed:
    def test_no_orders(self, evaluator, db):
        db.query.return_value.filter.return_value.all.return_value = []
        result = evaluator._calculate_response_speed(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["score"] == Decimal("50")
        assert result["avg_hours"] == Decimal("0")

    def test_fast_response(self, evaluator, db):
        from datetime import datetime
        order = MagicMock(
            submitted_at=datetime(2025, 1, 10, 8, 0),
            approved_at=datetime(2025, 1, 10, 10, 0)  # 2 hours
        )
        db.query.return_value.filter.return_value.all.return_value = [order]
        result = evaluator._calculate_response_speed(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["score"] == Decimal("100")

    def test_slow_response(self, evaluator, db):
        from datetime import datetime
        order = MagicMock(
            submitted_at=datetime(2025, 1, 10, 8, 0),
            approved_at=datetime(2025, 1, 13, 8, 0)  # 72 hours
        )
        db.query.return_value.filter.return_value.all.return_value = [order]
        result = evaluator._calculate_response_speed(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["score"] < Decimal("80")


# ============================================================
# _calculate_overall_score 测试
# ============================================================

class TestCalculateOverallScore:
    def test_perfect_score(self, evaluator):
        delivery = {"on_time_rate": Decimal("100")}
        quality = {"pass_rate": Decimal("100")}
        price = {"competitiveness": Decimal("100")}
        response = {"score": Decimal("100")}
        weights = {
            "on_time_delivery": Decimal("30"),
            "quality": Decimal("30"),
            "price": Decimal("20"),
            "response": Decimal("20"),
        }
        result = evaluator._calculate_overall_score(delivery, quality, price, response, weights)
        assert result == Decimal("100")

    def test_zero_score(self, evaluator):
        delivery = {"on_time_rate": Decimal("0")}
        quality = {"pass_rate": Decimal("0")}
        price = {"competitiveness": Decimal("0")}
        response = {"score": Decimal("0")}
        weights = {
            "on_time_delivery": Decimal("30"),
            "quality": Decimal("30"),
            "price": Decimal("20"),
            "response": Decimal("20"),
        }
        result = evaluator._calculate_overall_score(delivery, quality, price, response, weights)
        assert result == Decimal("0")

    def test_mixed_score(self, evaluator):
        delivery = {"on_time_rate": Decimal("90")}
        quality = {"pass_rate": Decimal("80")}
        price = {"competitiveness": Decimal("70")}
        response = {"score": Decimal("60")}
        weights = {
            "on_time_delivery": Decimal("25"),
            "quality": Decimal("25"),
            "price": Decimal("25"),
            "response": Decimal("25"),
        }
        result = evaluator._calculate_overall_score(delivery, quality, price, response, weights)
        assert result == Decimal("75")


# ============================================================
# _determine_rating 测试
# ============================================================

class TestDetermineRating:
    def test_rating_a_plus(self, evaluator):
        assert evaluator._determine_rating(Decimal("95")) == "A+"

    def test_rating_a(self, evaluator):
        assert evaluator._determine_rating(Decimal("85")) == "A"

    def test_rating_b(self, evaluator):
        assert evaluator._determine_rating(Decimal("75")) == "B"

    def test_rating_c(self, evaluator):
        assert evaluator._determine_rating(Decimal("65")) == "C"

    def test_rating_d(self, evaluator):
        assert evaluator._determine_rating(Decimal("50")) == "D"

    def test_rating_boundary_90(self, evaluator):
        assert evaluator._determine_rating(Decimal("90")) == "A+"

    def test_rating_boundary_80(self, evaluator):
        assert evaluator._determine_rating(Decimal("80")) == "A"


# ============================================================
# get_supplier_ranking 测试
# ============================================================

class TestGetSupplierRanking:
    def test_get_ranking(self, evaluator, db):
        perf1 = MagicMock(overall_score=Decimal("90"))
        perf2 = MagicMock(overall_score=Decimal("80"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [perf1, perf2]
        result = evaluator.get_supplier_ranking("2025-01", limit=10)
        assert len(result) == 2

    def test_get_ranking_empty(self, evaluator, db):
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = evaluator.get_supplier_ranking("2025-01")
        assert result == []


# ============================================================
# batch_evaluate_all_suppliers 测试
# ============================================================

class TestBatchEvaluateAllSuppliers:
    def test_no_suppliers(self, evaluator, db):
        db.query.return_value.filter.return_value.all.return_value = []
        result = evaluator.batch_evaluate_all_suppliers("2025-01")
        assert result == 0

    def test_evaluates_all_suppliers(self, evaluator, db):
        sup1 = MagicMock(id=1, supplier_code="SUP001")
        sup2 = MagicMock(id=2, supplier_code="SUP002")
        db.query.return_value.filter.return_value.all.return_value = [sup1, sup2]

        with patch.object(evaluator, 'evaluate_supplier', side_effect=[MagicMock(), MagicMock()]):
            result = evaluator.batch_evaluate_all_suppliers("2025-01")
        assert result == 2

    def test_handles_error_gracefully(self, evaluator, db):
        sup1 = MagicMock(id=1, supplier_code="SUP001")
        db.query.return_value.filter.return_value.all.return_value = [sup1]

        with patch.object(evaluator, 'evaluate_supplier', side_effect=Exception("DB error")):
            result = evaluator.batch_evaluate_all_suppliers("2025-01")
        assert result == 0
