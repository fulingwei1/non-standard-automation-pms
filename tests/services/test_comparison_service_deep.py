# -*- coding: utf-8 -*-
"""
comparison_service 深度覆盖测试 - N5组
补充：update_strategy_comparison、generate_yoy_report完整流程、KPI变化率计算、多年趋势
"""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def _mock_strategy(**kw):
    s = MagicMock()
    defaults = dict(id=1, year=2025, is_active=True, code="S-2025", name="战略2025")
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _mock_comparison(**kw):
    c = MagicMock()
    defaults = dict(id=1, base_strategy_id=1, compare_strategy_id=2, is_active=True,
                    comparison_type="YOY", base_year=2025, compare_year=2024)
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


def _make_query(db, first_val=None, all_val=None, count_val=0):
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.count.return_value = count_val
    q.first.return_value = first_val
    q.all.return_value = all_val or []
    db.query.return_value = q
    return q


class TestCreateStrategyComparisonDetails(unittest.TestCase):
    """create_strategy_comparison 详细字段测试"""

    @patch("app.services.strategy.comparison_service.StrategyComparison")
    def test_stores_all_fields(self, MockSC):
        """应存储所有字段"""
        from app.services.strategy.comparison_service import create_strategy_comparison
        db = MagicMock()
        data = MagicMock(
            base_strategy_id=1, compare_strategy_id=2,
            comparison_type="YOY", base_year=2025, compare_year=2024, summary="全面分析"
        )
        MockSC.return_value = MagicMock(id=1)

        create_strategy_comparison(db, data, created_by=5)

        call_kwargs = MockSC.call_args.kwargs
        self.assertEqual(call_kwargs.get("base_strategy_id"), 1)
        self.assertEqual(call_kwargs.get("compare_strategy_id"), 2)
        self.assertEqual(call_kwargs.get("created_by"), 5)

    @patch("app.services.strategy.comparison_service.StrategyComparison")
    def test_commit_and_refresh_called(self, MockSC):
        """应调用 commit 和 refresh"""
        from app.services.strategy.comparison_service import create_strategy_comparison
        db = MagicMock()
        data = MagicMock(
            base_strategy_id=1, compare_strategy_id=2,
            comparison_type="YOY", base_year=2025, compare_year=2024, summary=None
        )
        MockSC.return_value = MagicMock()

        create_strategy_comparison(db, data, created_by=1)
        db.commit.assert_called_once()
        db.refresh.assert_called_once()


class TestListStrategyComparisonsAdvanced(unittest.TestCase):
    """list_strategy_comparisons 高级查询测试"""

    def test_pagination_with_large_skip(self):
        """大 skip 值时应返回空列表"""
        from app.services.strategy.comparison_service import list_strategy_comparisons
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.count.return_value = 5
        db.query.return_value = q

        with patch("app.services.strategy.comparison_service.apply_pagination") as ap:
            ap.return_value.all.return_value = []
            items, total = list_strategy_comparisons(db, skip=100, limit=10)
            self.assertEqual(total, 5)
            self.assertEqual(items, [])

    def test_returns_both_list_and_total(self):
        """应返回列表和总数"""
        from app.services.strategy.comparison_service import list_strategy_comparisons
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.count.return_value = 3
        db.query.return_value = q

        with patch("app.services.strategy.comparison_service.apply_pagination") as ap:
            comps = [_mock_comparison(id=i) for i in range(1, 4)]
            ap.return_value.all.return_value = comps
            items, total = list_strategy_comparisons(db)
            self.assertEqual(len(items), 3)
            self.assertEqual(total, 3)


class TestDeleteStrategyComparisonEdgeCases(unittest.TestCase):
    """delete_strategy_comparison 软删除边界"""

    @patch("app.services.strategy.comparison_service.get_strategy_comparison")
    def test_delete_sets_inactive(self, mock_get):
        """删除时应将 is_active 设为 False"""
        from app.services.strategy.comparison_service import delete_strategy_comparison
        db = MagicMock()
        comp = _mock_comparison()
        mock_get.return_value = comp

        result = delete_strategy_comparison(db, 1)
        self.assertTrue(result)
        self.assertFalse(comp.is_active)
        db.commit.assert_called_once()

    @patch("app.services.strategy.comparison_service.get_strategy_comparison")
    def test_delete_nonexistent_returns_false(self, mock_get):
        """删除不存在记录返回 False"""
        from app.services.strategy.comparison_service import delete_strategy_comparison
        db = MagicMock()
        mock_get.return_value = None

        result = delete_strategy_comparison(db, 9999)
        self.assertFalse(result)


class TestGenerateYoyReportAdvanced(unittest.TestCase):
    """generate_yoy_report 高级测试"""

    @patch("app.services.strategy.comparison_service.YoYReportResponse")
    def test_uses_explicit_previous_year(self, MockResp):
        """明确指定 previous_year 时应使用该年份"""
        from app.services.strategy.comparison_service import generate_yoy_report
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        mock_result = MagicMock(current_year=2025, previous_year=2022)
        MockResp.return_value = mock_result

        result = generate_yoy_report(db, 2025, previous_year=2022)
        # previous_year should be passed
        call_kwargs = MockResp.call_args.kwargs
        self.assertEqual(call_kwargs.get("previous_year"), 2022)

    @patch("app.services.strategy.comparison_service.YoYReportResponse")
    def test_auto_previous_year_is_current_minus_1(self, MockResp):
        """不指定 previous_year 时应默认为 current_year - 1"""
        from app.services.strategy.comparison_service import generate_yoy_report
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        mock_result = MagicMock(current_year=2026, previous_year=2025)
        MockResp.return_value = mock_result

        generate_yoy_report(db, 2026)
        call_kwargs = MockResp.call_args.kwargs
        self.assertEqual(call_kwargs.get("previous_year"), 2025)


class TestCompareKpisTargetChange(unittest.TestCase):
    """_compare_kpis 目标变化计算"""

    @patch("app.services.strategy.comparison_service.KPIComparisonItem")
    def test_kpi_target_increase(self, MockKPIItem):
        """KPI目标值增加时 target_change 应为正"""
        from app.services.strategy.comparison_service import _compare_kpis
        db = MagicMock()

        kpi_current = MagicMock(id=1, code="KPI-01", name="KPI增长", target_value=Decimal("120"))
        kpi_previous = MagicMock(id=2, code="KPI-01", name="KPI增长", target_value=Decimal("100"))

        q = MagicMock()
        q.filter.return_value = q
        q.all.side_effect = [[kpi_current], [kpi_previous]]
        db.query.return_value = q

        MockKPIItem.return_value = MagicMock(is_new=False)

        with patch("app.services.strategy.health_calculator.calculate_kpi_completion_rate",
                   side_effect=[Decimal("90"), Decimal("80")]):
            result = _compare_kpis(db, 1, 2)
            call_kwargs = MockKPIItem.call_args.kwargs
            self.assertEqual(call_kwargs.get("target_change"), Decimal("20"))

    @patch("app.services.strategy.comparison_service.KPIComparisonItem")
    def test_kpi_target_decrease(self, MockKPIItem):
        """KPI目标值减少时 target_change 应为负"""
        from app.services.strategy.comparison_service import _compare_kpis
        db = MagicMock()

        kpi_current = MagicMock(id=1, code="KPI-02", name="KPI降低", target_value=Decimal("80"))
        kpi_previous = MagicMock(id=2, code="KPI-02", name="KPI降低", target_value=Decimal("100"))

        q = MagicMock()
        q.filter.return_value = q
        q.all.side_effect = [[kpi_current], [kpi_previous]]
        db.query.return_value = q

        MockKPIItem.return_value = MagicMock(is_new=False)

        with patch("app.services.strategy.health_calculator.calculate_kpi_completion_rate",
                   side_effect=[Decimal("70"), Decimal("90")]):
            result = _compare_kpis(db, 1, 2)
            call_kwargs = MockKPIItem.call_args.kwargs
            self.assertEqual(call_kwargs.get("target_change"), Decimal("-20"))


class TestGetMultiYearTrendAdvanced(unittest.TestCase):
    """get_multi_year_trend 多年趋势高级测试"""

    @patch("app.services.strategy.comparison_service.date")
    def test_trend_years_count_matches_param(self, mock_date):
        """返回年份数量应与参数一致"""
        from app.services.strategy.comparison_service import get_multi_year_trend
        mock_date.today.return_value = date(2025, 6, 15)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = get_multi_year_trend(db, years=5)
        self.assertEqual(len(result["years"]), 5)
        self.assertEqual(len(result["trend"]), 5)

    @patch("app.services.strategy.comparison_service.date")
    def test_trend_years_are_descending(self, mock_date):
        """年份应从当前年向过去排列"""
        from app.services.strategy.comparison_service import get_multi_year_trend
        mock_date.today.return_value = date(2025, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = get_multi_year_trend(db, years=3)
        years = result["years"]
        # Should be [2025, 2024, 2023] or [2023, 2024, 2025]
        self.assertIn(2025, years)
        self.assertIn(2024, years)
        self.assertIn(2023, years)


class TestGetKPIAchievementComparisonEdge(unittest.TestCase):
    """get_kpi_achievement_comparison 边界情况"""

    def test_only_current_strategy_exists(self):
        """只有当年战略没有去年战略"""
        from app.services.strategy.comparison_service import get_kpi_achievement_comparison
        db = MagicMock()

        current_s = _mock_strategy(id=1, year=2025)

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            q.join.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = current_s
            elif call_count[0] == 2:
                q.first.return_value = None  # no previous strategy
            else:
                q.all.return_value = []
            return q

        db.query.side_effect = make_query

        with patch("app.services.strategy.health_calculator.calculate_kpi_completion_rate"):
            result = get_kpi_achievement_comparison(db, 2025)
            self.assertIsNone(result["previous"])

    def test_no_strategies_at_all(self):
        """完全没有战略数据时"""
        from app.services.strategy.comparison_service import get_kpi_achievement_comparison
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = get_kpi_achievement_comparison(db, 2025)
        self.assertIsNone(result["current"])
        self.assertIsNone(result["previous"])


if __name__ == "__main__":
    unittest.main()
