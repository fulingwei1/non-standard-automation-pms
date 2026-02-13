# -*- coding: utf-8 -*-
"""Tests for procurement_analysis/cost_trend.py"""
import pytest
from unittest.mock import MagicMock
from datetime import date


class TestCostTrendAnalyzer:
    def test_empty_orders(self):
        from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = CostTrendAnalyzer.get_cost_trend_data(db, date(2025, 1, 1), date(2025, 3, 31))
        assert result['summary']['total_amount'] == 0
        assert len(result['trend_data']) == 3  # 3 months

    def test_with_orders(self):
        from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer
        db = MagicMock()
        order = MagicMock(order_date=date(2025, 1, 15), amount_with_tax=1000)
        db.query.return_value.filter.return_value.all.return_value = [order]
        result = CostTrendAnalyzer.get_cost_trend_data(db, date(2025, 1, 1), date(2025, 1, 31))
        assert result['summary']['total_amount'] == 1000.0
        assert result['trend_data'][0]['order_count'] == 1

    def test_quarterly_grouping(self):
        from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2025, 1, 1), date(2025, 6, 30), group_by="quarter"
        )
        assert any('Q' in d['period'] for d in result['trend_data'])

    def test_yearly_grouping(self):
        from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2025, 1, 1), date(2025, 12, 31), group_by="year"
        )
        assert result['trend_data'][0]['period'] == '2025'
