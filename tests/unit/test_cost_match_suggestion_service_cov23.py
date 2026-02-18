# -*- coding: utf-8 -*-
"""第二十三批：cost_match_suggestion_service 单元测试"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.cost_match_suggestion_service")

from app.services.cost_match_suggestion_service import (
    check_cost_anomalies,
    find_matching_cost,
    build_cost_suggestion,
    check_overall_anomalies,
    calculate_summary,
    process_cost_match_suggestions,
)


def _mock_item(item_id=1, item_name="螺丝", cost=0.0, qty=10):
    item = MagicMock()
    item.id = item_id
    item.item_name = item_name
    item.cost = cost
    item.qty = qty
    return item


def _mock_cost_record(unit_cost=100.0, material_name="螺丝", material_type="标准件",
                      specification="M8", unit="个", lead_time_days=7,
                      match_priority=1, purchase_date=None, usage_count=1):
    r = MagicMock()
    r.unit_cost = unit_cost
    r.material_name = material_name
    r.material_type = material_type
    r.specification = specification
    r.unit = unit
    r.lead_time_days = lead_time_days
    r.match_priority = match_priority
    r.purchase_date = purchase_date
    r.usage_count = usage_count
    r.submitter = None
    # __table__.columns
    col = MagicMock()
    col.name = "unit_cost"
    r.__table__ = MagicMock()
    r.__table__.columns = [col]
    return r


class TestCheckCostAnomalies:
    def test_no_item_name_returns_empty(self):
        db = MagicMock()
        item = _mock_item(item_name=None)
        result = check_cost_anomalies(db, item, MagicMock(), 100.0)
        assert result == []

    def test_no_historical_costs_returns_empty(self):
        db = MagicMock()
        item = _mock_item(item_name="钢管")
        cost_query = MagicMock()
        with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.all.return_value = []
            result = check_cost_anomalies(db, item, cost_query, 50.0)
        assert result == []

    def test_abnormally_high_cost_warns(self):
        db = MagicMock()
        item = _mock_item(item_name="钢管")
        hist = [_mock_cost_record(unit_cost=100.0)]
        with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.all.return_value = hist
            result = check_cost_anomalies(db, item, MagicMock(), 200.0)  # > 100*1.5
        assert len(result) == 1
        assert "异常偏高" in result[0]

    def test_abnormally_low_cost_warns(self):
        db = MagicMock()
        item = _mock_item(item_name="钢管")
        hist = [_mock_cost_record(unit_cost=100.0)]
        with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.all.return_value = hist
            result = check_cost_anomalies(db, item, MagicMock(), 30.0)  # < 100*0.5
        assert len(result) == 1
        assert "异常偏低" in result[0]

    def test_deviation_over_30_percent_warns(self):
        db = MagicMock()
        item = _mock_item(item_name="钢管")
        hist = [_mock_cost_record(unit_cost=100.0)]
        with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.all.return_value = hist
            result = check_cost_anomalies(db, item, MagicMock(), 140.0)  # 40% deviation
        assert len(result) == 1
        assert "偏差" in result[0]


class TestFindMatchingCost:
    def test_no_item_name_returns_none(self):
        db = MagicMock()
        item = _mock_item(item_name=None)
        r, score, reason = find_matching_cost(db, item, MagicMock())
        assert r is None and score is None and reason is None

    def test_exact_match_returns_score_100(self):
        db = MagicMock()
        item = _mock_item(item_name="螺丝")
        matched = _mock_cost_record()
        cost_query = MagicMock()
        cost_query.filter.return_value.order_by.return_value.first.return_value = matched
        r, score, reason = find_matching_cost(db, item, cost_query)
        assert score == 100
        assert "精确" in reason

    def test_fuzzy_match_returns_score_80(self):
        db = MagicMock()
        item = _mock_item(item_name="特殊螺丝")
        matched = _mock_cost_record()
        cost_query = MagicMock()
        cost_query.filter.return_value.order_by.return_value.first.return_value = None
        with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
            q = MagicMock()
            q.order_by.return_value.limit.return_value.all.return_value = [matched]
            mock_filter.return_value = q
            r, score, reason = find_matching_cost(db, item, cost_query)
        assert score == 80

    def test_no_match_returns_none(self):
        db = MagicMock()
        item = _mock_item(item_name="ab")  # keywords too short
        cost_query = MagicMock()
        cost_query.filter.return_value.order_by.return_value.first.return_value = None
        with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
            q = MagicMock()
            q.order_by.return_value.limit.return_value.all.return_value = []
            mock_filter.return_value = q
            r, score, reason = find_matching_cost(db, item, cost_query)
        assert r is None


class TestCheckOverallAnomalies:
    def test_low_margin_warns(self):
        result = check_overall_anomalies(1000, 900, 950, [], [])
        assert any("毛利率" in w for w in result)

    def test_zero_price_returns_empty(self):
        result = check_overall_anomalies(0, 0, 500, [], [])
        assert result == []


class TestCalculateSummary:
    def test_summary_calculates_margin(self):
        items = [_mock_item(cost=100.0, qty=10)]
        suggestion = MagicMock()
        suggestion.suggested_cost = Decimal("100")
        suggestion.current_cost = Decimal("100")
        suggestion.item_id = 1
        result = calculate_summary(1000.0, 2000.0, items, [suggestion])
        assert result["current_total_cost"] == 1000.0
        assert result["current_margin"] == pytest.approx(50.0)


class TestProcessCostMatchSuggestions:
    def test_items_with_cost_skip_matching(self):
        db = MagicMock()
        item = _mock_item(cost=100.0, qty=5)
        cost_query = MagicMock()
        with patch("app.services.cost_match_suggestion_service.check_cost_anomalies", return_value=[]):
            with patch("app.services.cost_match_suggestion_service.build_cost_suggestion") as mock_build:
                mock_build.return_value = MagicMock()
                suggestions, matched, unmatched, warnings, total = process_cost_match_suggestions(db, [item], cost_query)
        assert matched == 0

    def test_items_without_cost_try_matching(self):
        db = MagicMock()
        item = _mock_item(cost=0.0, qty=5)
        cost_query = MagicMock()
        with patch("app.services.cost_match_suggestion_service.find_matching_cost", return_value=(None, None, None)):
            with patch("app.services.cost_match_suggestion_service.build_cost_suggestion") as mock_build:
                mock_build.return_value = MagicMock()
                suggestions, matched, unmatched, warnings, total = process_cost_match_suggestions(db, [item], cost_query)
        assert unmatched == 1
