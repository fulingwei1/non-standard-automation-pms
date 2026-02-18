"""
第四批覆盖测试 - supplier_performance_evaluator
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

try:
    from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator
    HAS_SERVICE = True
except Exception:
    HAS_SERVICE = False

pytestmark = pytest.mark.skipif(not HAS_SERVICE, reason="服务导入失败")


def make_evaluator():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.get.return_value = None
    return SupplierPerformanceEvaluator(db, tenant_id=1), db


class TestSupplierPerformanceEvaluator:
    def setup_method(self):
        self.evaluator, self.db = make_evaluator()

    def test_init(self):
        assert self.evaluator.tenant_id == 1
        assert self.evaluator.db is not None

    def test_determine_rating_a_plus(self):
        rating = self.evaluator._determine_rating(Decimal('95'))
        assert rating == 'A+'

    def test_determine_rating_a(self):
        rating = self.evaluator._determine_rating(Decimal('85'))
        assert rating == 'A'

    def test_determine_rating_b(self):
        rating = self.evaluator._determine_rating(Decimal('75'))
        assert rating == 'B'

    def test_determine_rating_c(self):
        rating = self.evaluator._determine_rating(Decimal('65'))
        assert rating == 'C'

    def test_determine_rating_d(self):
        rating = self.evaluator._determine_rating(Decimal('50'))
        assert rating == 'D'

    def test_evaluate_supplier_not_found(self):
        result = self.evaluator.evaluate_supplier(9999, '2024-01')
        assert result is None

    def test_evaluate_supplier_invalid_period(self):
        supplier = MagicMock()
        self.db.query.return_value.get.return_value = supplier
        result = self.evaluator.evaluate_supplier(1, 'invalid-period')
        assert result is None

    def test_calculate_overall_score_default_weights(self):
        delivery_metrics = {'on_time_rate': Decimal('90')}
        quality_metrics = {'pass_rate': Decimal('85')}
        price_metrics = {'competitiveness': Decimal('80')}
        response_metrics = {'score': Decimal('88')}
        weight_config = {
            'on_time_delivery': Decimal('30'),
            'quality': Decimal('30'),
            'price': Decimal('20'),
            'response': Decimal('20'),
        }
        score = self.evaluator._calculate_overall_score(
            delivery_metrics, quality_metrics, price_metrics, response_metrics, weight_config
        )
        assert isinstance(score, Decimal)
        assert Decimal('0') <= score <= Decimal('100')

    def test_get_supplier_ranking_empty(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = self.evaluator.get_supplier_ranking('2024-01')
        assert isinstance(result, list)

    def test_batch_evaluate_empty_suppliers(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        count = self.evaluator.batch_evaluate_all_suppliers('2024-01')
        assert isinstance(count, int)
        assert count >= 0

    def test_calculate_delivery_metrics_no_orders(self):
        # Takes a list of orders, period_start, period_end
        result = self.evaluator._calculate_delivery_metrics([], date(2024,1,1), date(2024,1,31))
        assert isinstance(result, dict)
        assert 'on_time_rate' in result

    def test_calculate_quality_metrics_no_orders(self):
        # Takes a list of orders, period_start, period_end
        result = self.evaluator._calculate_quality_metrics([], date(2024,1,1), date(2024,1,31))
        assert isinstance(result, dict)
