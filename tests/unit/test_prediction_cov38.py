# -*- coding: utf-8 -*-
"""
Unit tests for win_rate_prediction_service/prediction.py (第三十八批)
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip(
    "app.services.win_rate_prediction_service.prediction",
    reason="导入失败，跳过"
)

try:
    from app.services.win_rate_prediction_service.prediction import predict
except ImportError:
    pytestmark = pytest.mark.skip(reason="prediction 不可用")
    predict = None


def make_dimension_scores():
    scores = MagicMock()
    scores.requirement_maturity = 75.0
    scores.technical_feasibility = 80.0
    scores.business_feasibility = 70.0
    scores.delivery_risk = 65.0
    scores.customer_relationship = 72.0
    scores.total_score = 72.4
    return scores


@pytest.fixture
def mock_service():
    svc = MagicMock()
    svc.db = MagicMock()
    return svc


class TestPredict:
    """测试 predict 函数"""

    def _patch_all(self):
        return [
            patch("app.services.win_rate_prediction_service.prediction.calculate_base_score",
                  return_value=0.7),
            patch("app.services.win_rate_prediction_service.prediction.get_salesperson_historical_win_rate",
                  return_value=(0.65, 20)),
            patch("app.services.win_rate_prediction_service.prediction.calculate_salesperson_factor",
                  return_value=1.0),
            patch("app.services.win_rate_prediction_service.prediction.get_customer_cooperation_history",
                  return_value=(3, 2)),
            patch("app.services.win_rate_prediction_service.prediction.calculate_customer_factor",
                  return_value=1.1),
            patch("app.services.win_rate_prediction_service.prediction.calculate_competitor_factor",
                  return_value=0.9),
            patch("app.services.win_rate_prediction_service.prediction.calculate_amount_factor",
                  return_value=1.0),
            patch("app.services.win_rate_prediction_service.prediction.calculate_product_factor",
                  return_value=1.0),
            patch("app.services.win_rate_prediction_service.prediction.get_similar_leads_statistics",
                  return_value=(5, 0.65)),
        ]

    def test_predict_returns_dict(self, mock_service):
        """predict 返回字典"""
        scores = make_dimension_scores()
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            result = predict(
                service=mock_service,
                dimension_scores=scores,
                salesperson_id=1
            )
            assert isinstance(result, dict)
        finally:
            for p in patches:
                p.stop()

    def test_predict_has_predicted_rate(self, mock_service):
        """结果包含 predicted_rate"""
        scores = make_dimension_scores()
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            result = predict(
                service=mock_service,
                dimension_scores=scores,
                salesperson_id=1
            )
            assert "predicted_rate" in result
        finally:
            for p in patches:
                p.stop()

    def test_predict_has_probability_level(self, mock_service):
        """结果包含 probability_level"""
        scores = make_dimension_scores()
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            result = predict(
                service=mock_service,
                dimension_scores=scores,
                salesperson_id=1
            )
            assert "probability_level" in result
        finally:
            for p in patches:
                p.stop()

    def test_predict_has_recommendations(self, mock_service):
        """结果包含 recommendations"""
        scores = make_dimension_scores()
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            result = predict(
                service=mock_service,
                dimension_scores=scores,
                salesperson_id=1
            )
            assert "recommendations" in result
        finally:
            for p in patches:
                p.stop()

    def test_predict_rate_in_valid_range(self, mock_service):
        """predicted_rate 在 0-1 之间"""
        scores = make_dimension_scores()
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            result = predict(
                service=mock_service,
                dimension_scores=scores,
                salesperson_id=1
            )
            rate = result.get("predicted_rate", 0)
            assert 0 <= float(rate) <= 1
        finally:
            for p in patches:
                p.stop()

    def test_predict_with_customer_info(self, mock_service):
        """带客户信息时正常预测"""
        scores = make_dimension_scores()
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            result = predict(
                service=mock_service,
                dimension_scores=scores,
                salesperson_id=1,
                customer_id=5,
                customer_name="测试客户",
                estimated_amount=Decimal("500000"),
                is_repeat_customer=True
            )
            assert isinstance(result, dict)
        finally:
            for p in patches:
                p.stop()
