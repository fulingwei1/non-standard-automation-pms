# -*- coding: utf-8 -*-
"""
第三十五批 - cost_trend.py / cost_trend_analyzer.py 单元测试
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


def _make_order(order_date, amount_with_tax):
    o = MagicMock()
    o.order_date = order_date
    o.amount_with_tax = amount_with_tax
    o.project_id = None
    return o


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestCostTrendAnalyzer:

    def _make_db(self, orders):
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = orders
        db.query.return_value = mock_query
        return db

    def test_monthly_grouping_basic(self):
        """按月分组返回正确的月份键"""
        orders = [
            _make_order(date(2024, 1, 15), 1000),
            _make_order(date(2024, 2, 10), 2000),
        ]
        db = self._make_db(orders)
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 2, 28), group_by="month"
        )
        periods = [d["period"] for d in result["trend_data"]]
        assert "2024-01" in periods
        assert "2024-02" in periods

    def test_summary_total_amount(self):
        """汇总金额等于所有订单金额之和"""
        orders = [
            _make_order(date(2024, 3, 1), 500),
            _make_order(date(2024, 3, 20), 500),
        ]
        db = self._make_db(orders)
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 3, 1), date(2024, 3, 31)
        )
        assert result["summary"]["total_amount"] == 1000.0

    def test_empty_orders_returns_zero_amounts(self):
        """没有订单时各统计项为0"""
        db = self._make_db([])
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["summary"]["total_amount"] == 0.0
        assert result["summary"]["total_orders"] == 0

    def test_mom_rate_calculation(self):
        """环比增长率正确计算"""
        orders = [
            _make_order(date(2024, 1, 10), 1000),
            _make_order(date(2024, 2, 10), 1500),
        ]
        db = self._make_db(orders)
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 2, 29)
        )
        trend = result["trend_data"]
        assert trend[0]["mom_rate"] == 0  # 第一期无环比
        assert trend[1]["mom_rate"] == 50.0  # (1500-1000)/1000*100

    def test_quarterly_grouping(self):
        """按季度分组"""
        orders = [_make_order(date(2024, 1, 15), 3000)]
        db = self._make_db(orders)
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 3, 31), group_by="quarter"
        )
        periods = [d["period"] for d in result["trend_data"]]
        assert any("Q1" in p for p in periods)

    def test_yearly_grouping(self):
        """按年分组"""
        orders = [_make_order(date(2024, 6, 15), 9999)]
        db = self._make_db(orders)
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 12, 31), group_by="year"
        )
        periods = [d["period"] for d in result["trend_data"]]
        assert "2024" in periods

    def test_avg_amount_per_order(self):
        """平均订单金额计算正确"""
        orders = [
            _make_order(date(2024, 1, 5), 100),
            _make_order(date(2024, 1, 20), 300),
        ]
        db = self._make_db(orders)
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 1, 31)
        )
        jan = next(d for d in result["trend_data"] if d["period"] == "2024-01")
        assert jan["avg_amount"] == 200.0

    def test_summary_has_required_keys(self):
        """汇总数据包含所有必要键"""
        db = self._make_db([])
        result = CostTrendAnalyzer.get_cost_trend_data(
            db, date(2024, 1, 1), date(2024, 1, 31)
        )
        for key in ["total_amount", "total_orders", "avg_monthly_amount",
                    "max_month_amount", "min_month_amount"]:
            assert key in result["summary"]
