# -*- coding: utf-8 -*-
"""
SalesPredictionService 单元测试 - N5组
覆盖：预测算法(MA/ES)、赢单概率、历史数据分析、置信度
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.sales_prediction_service import SalesPredictionService


def _make_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.join.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = []
    q.first.return_value = None
    return db


def _make_svc(db=None, **config):
    if db is None:
        db = _make_db()
    return SalesPredictionService(db, **config)


def _make_contract(signed_date, amount):
    c = MagicMock()
    c.signed_date = signed_date
    c.contract_amount = Decimal(str(amount))
    return c


def _make_opportunity(stage="PROPOSAL", est_amount=None):
    opp = MagicMock()
    opp.stage = stage
    opp.est_amount = Decimal(str(est_amount)) if est_amount else None
    return opp


class TestMovingAverageForecast(unittest.TestCase):
    """移动平均法预测"""

    def setUp(self):
        self.svc = _make_svc()

    def test_empty_data_returns_zero(self):
        """无历史数据时预测值为0"""
        result = self.svc._moving_average_forecast([], 30)
        self.assertEqual(result, Decimal("0"))

    def test_single_month_data(self):
        """单月数据：预测等于该月收入 × 天数比例"""
        data = [{"month": "2025-01", "revenue": 100000.0, "count": 3}]
        result = self.svc._moving_average_forecast(data, 30)
        self.assertEqual(result, Decimal(str(100000.0 * 1.0)))

    def test_three_months_average(self):
        """三个月数据取平均"""
        data = [
            {"month": "2025-01", "revenue": 100000.0, "count": 3},
            {"month": "2025-02", "revenue": 200000.0, "count": 4},
            {"month": "2025-03", "revenue": 300000.0, "count": 5},
        ]
        result = self.svc._moving_average_forecast(data, 30)
        # recent_months = 最后3个月, avg = (100000+200000+300000)/3 = 200000, ×1月
        self.assertAlmostEqual(float(result), 200000.0, places=2)

    def test_more_than_three_months_uses_last_three(self):
        """超过3个月时只取最近3个月"""
        data = [
            {"month": "2024-10", "revenue": 50000.0, "count": 1},
            {"month": "2024-11", "revenue": 50000.0, "count": 1},
            {"month": "2025-01", "revenue": 100000.0, "count": 3},
            {"month": "2025-02", "revenue": 200000.0, "count": 4},
            {"month": "2025-03", "revenue": 300000.0, "count": 5},
        ]
        result = self.svc._moving_average_forecast(data, 30)
        # 只取最后3个月: 100000, 200000, 300000, avg=200000
        self.assertAlmostEqual(float(result), 200000.0, places=2)

    def test_60_days_forecast(self):
        """60天预测 = 平均月收入 × 2"""
        data = [{"month": "2025-01", "revenue": 120000.0, "count": 3}]
        result = self.svc._moving_average_forecast(data, 60)
        self.assertAlmostEqual(float(result), 240000.0, places=2)


class TestExponentialSmoothingForecast(unittest.TestCase):
    """指数平滑法预测"""

    def setUp(self):
        self.svc = _make_svc()

    def test_empty_data_returns_zero(self):
        """无数据时返回0"""
        result = self.svc._exponential_smoothing_forecast([], 30)
        self.assertEqual(result, Decimal("0"))

    def test_single_data_point(self):
        """单数据点时预测等于该值×天数比例"""
        data = [{"month": "2025-01", "revenue": 100000.0, "count": 3}]
        result = self.svc._exponential_smoothing_forecast(data, 30)
        self.assertAlmostEqual(float(result), 100000.0, places=2)

    def test_multiple_points_alpha_smoothing(self):
        """多数据点时通过指数平滑计算"""
        data = [
            {"month": "2025-01", "revenue": 100000.0, "count": 3},
            {"month": "2025-02", "revenue": 200000.0, "count": 4},
        ]
        alpha = 0.3
        # forecast = 0.3*200000 + 0.7*100000 = 60000+70000 = 130000
        result = self.svc._exponential_smoothing_forecast(data, 30, alpha=alpha)
        self.assertAlmostEqual(float(result), 130000.0, places=2)

    def test_uses_default_alpha(self):
        """使用默认 alpha 时不传参数也能正常计算"""
        data = [
            {"month": "2025-01", "revenue": 100000.0, "count": 2},
            {"month": "2025-02", "revenue": 150000.0, "count": 3},
        ]
        # Should not raise
        result = self.svc._exponential_smoothing_forecast(data, 30)
        self.assertIsNotNone(result)
        self.assertGreater(float(result), 0)


class TestForecastFromOpportunities(unittest.TestCase):
    """基于商机的收入预测"""

    def setUp(self):
        self.svc = _make_svc()

    def test_empty_opportunities_returns_zero(self):
        """无商机时返回0"""
        result = self.svc._forecast_from_opportunities([], 90)
        self.assertEqual(result, Decimal("0"))

    def test_proposal_stage_weight(self):
        """PROPOSAL阶段商机使用0.6权重"""
        opp = _make_opportunity(stage="PROPOSAL", est_amount=1000000)
        result = self.svc._forecast_from_opportunities([opp], 90)
        # weight=0.6, months=90/30=3, min(3/3, 1)=1.0
        # total = 1000000 * 0.6 = 600000, * 1.0 = 600000
        self.assertAlmostEqual(float(result), 600000.0, places=2)

    def test_negotiation_stage_weight(self):
        """NEGOTIATION阶段商机使用0.8权重"""
        opp = _make_opportunity(stage="NEGOTIATION", est_amount=500000)
        result = self.svc._forecast_from_opportunities([opp], 90)
        # weight=0.8, months=3, min(1, 1.0)=1.0
        # total = 500000 * 0.8 = 400000
        self.assertAlmostEqual(float(result), 400000.0, places=2)

    def test_30_days_uses_fraction(self):
        """30天预测只取 1/3 比例"""
        opp = _make_opportunity(stage="PROPOSAL", est_amount=900000)
        result = self.svc._forecast_from_opportunities([opp], 30)
        # weight=0.6, months=30/30=1.0, min(1/3, 1)=0.333...
        # total = 900000 * 0.6 = 540000, * (1/3) ≈ 180000
        self.assertAlmostEqual(float(result), 180000.0, places=0)

    def test_none_est_amount_treated_as_zero(self):
        """est_amount 为 None 时视为0"""
        opp = _make_opportunity(stage="PROPOSAL", est_amount=None)
        result = self.svc._forecast_from_opportunities([opp], 90)
        self.assertEqual(result, Decimal("0"))


class TestPredictWinProbability(unittest.TestCase):
    """商机赢单概率预测"""

    def setUp(self):
        self.db = _make_db()
        self.svc = SalesPredictionService(self.db)

    def test_no_stage_returns_50_percent(self):
        """无阶段时返回50%默认概率"""
        result = self.svc.predict_win_probability()
        self.assertEqual(result["win_probability"], 0.5)
        self.assertEqual(result["confidence"], "LOW")

    def test_known_stage_returns_probability(self):
        """已知阶段时返回基于历史的概率"""
        # 模拟空历史（所有商机数量为0）
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        result = self.svc.predict_win_probability(stage="PROPOSAL")
        self.assertIn("win_probability", result)
        self.assertGreater(result["win_probability"], 0)
        self.assertLessEqual(result["win_probability"], 1.0)

    def test_large_amount_reduces_probability(self):
        """金额超过100万时应用折减因子"""
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        result_normal = self.svc.predict_win_probability(
            stage="PROPOSAL", amount=Decimal("100000")
        )
        result_large = self.svc.predict_win_probability(
            stage="PROPOSAL", amount=Decimal("2000000")
        )
        # 大金额应低于或等于普通金额
        self.assertLessEqual(
            result_large["win_probability"],
            result_normal["win_probability"]
        )

    def test_probability_within_bounds(self):
        """最终概率应在 [0.1, 0.95] 范围内"""
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        for stage in ["DISCOVERY", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON"]:
            result = self.svc.predict_win_probability(stage=stage)
            prob = result["win_probability"]
            self.assertGreaterEqual(prob, 0.1, f"Stage {stage} probability below lower bound")
            self.assertLessEqual(prob, 0.95, f"Stage {stage} probability above upper bound")

    def test_with_opportunity_id_loads_opp(self):
        """提供商机ID时从数据库获取商机信息"""
        opp = MagicMock(stage="NEGOTIATION", est_amount=Decimal("300000"), customer_id=None)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = opp
        q.all.return_value = []
        self.db.query.return_value = q

        result = self.svc.predict_win_probability(opportunity_id=1)
        self.assertIn("win_probability", result)

    def test_with_customer_history(self):
        """有客户历史赢单率时影响最终概率"""
        # Won 1 out of 2 → 50% customer win rate
        opp_won = MagicMock(stage="WON")
        opp_lost = MagicMock(stage="LOST")

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] <= 1:
                q.all.return_value = []  # historical win rates
            else:
                q.all.return_value = [opp_won, opp_lost]  # customer history
            return q

        self.db.query.side_effect = make_query

        result = self.svc.predict_win_probability(
            stage="PROPOSAL",
            customer_id=1,
        )
        self.assertIn("customer_factor", result)


class TestCalculateConfidence(unittest.TestCase):
    """置信度计算"""

    def setUp(self):
        self.svc = _make_svc()

    def test_high_confidence(self):
        """6+个月数据且5+个商机 → HIGH"""
        data = [{"month": f"2024-{i:02d}", "revenue": 100000.0, "count": 1} for i in range(1, 8)]
        result = self.svc._calculate_confidence(data, 6)
        self.assertEqual(result, "HIGH")

    def test_medium_confidence(self):
        """3-5个月数据且2+个商机 → MEDIUM"""
        data = [{"month": f"2025-0{i}", "revenue": 100000.0, "count": 1} for i in range(1, 4)]
        result = self.svc._calculate_confidence(data, 3)
        self.assertEqual(result, "MEDIUM")

    def test_low_confidence_few_data(self):
        """数据不足 → LOW"""
        result = self.svc._calculate_confidence([], 0)
        self.assertEqual(result, "LOW")

    def test_low_confidence_few_opportunities(self):
        """足够月份数据但商机数量不足 → MEDIUM"""
        data = [{"month": f"2025-0{i}", "revenue": 100000.0, "count": 1} for i in range(1, 4)]
        result = self.svc._calculate_confidence(data, 1)
        # 3个月数据但只有1个商机 (< 2), 应为 LOW
        self.assertEqual(result, "LOW")


class TestGetMonthlyRevenue(unittest.TestCase):
    """历史月度收入统计"""

    def setUp(self):
        self.svc = _make_svc()

    def test_empty_contracts(self):
        """无合同时返回空列表"""
        result = self.svc._get_monthly_revenue([])
        self.assertEqual(result, [])

    def test_groups_by_month(self):
        """同月合同应合并统计"""
        c1 = _make_contract(date(2025, 1, 10), 100000)
        c2 = _make_contract(date(2025, 1, 20), 200000)
        c3 = _make_contract(date(2025, 2, 5), 150000)

        result = self.svc._get_monthly_revenue([c1, c2, c3])
        self.assertEqual(len(result), 2)
        # 按月份排序
        self.assertEqual(result[0]["month"], "2025-01")
        self.assertAlmostEqual(result[0]["revenue"], 300000.0)
        self.assertEqual(result[1]["month"], "2025-02")

    def test_contract_without_signed_date_skipped(self):
        """无签约日期的合同跳过"""
        c = MagicMock()
        c.signed_date = None
        c.contract_amount = Decimal("100000")

        result = self.svc._get_monthly_revenue([c])
        self.assertEqual(result, [])


class TestEvaluatePredictionAccuracy(unittest.TestCase):
    """预测准确度评估"""

    def setUp(self):
        self.db = _make_db()
        self.svc = SalesPredictionService(self.db)

    def test_no_actual_revenue_returns_zero_accuracy(self):
        """实际收入为0时准确度为0"""
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        result = self.svc.evaluate_prediction_accuracy(days_back=30)
        self.assertEqual(result["actual_revenue"], 0)
        self.assertEqual(result["accuracy"], 0.0)
        self.assertEqual(result["error_rate"], 1.0)

    def test_with_actual_contracts(self):
        """有实际合同时计算准确度"""
        c = _make_contract(date.today() - timedelta(days=10), 500000)

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.all.return_value = [c]  # actual contracts
            else:
                q.all.return_value = []   # historical opps
            return q

        self.db.query.side_effect = make_query

        result = self.svc.evaluate_prediction_accuracy(days_back=30)
        self.assertEqual(result["actual_revenue"], 500000.0)
        self.assertIn("accuracy", result)
        self.assertIn("mape", result)


if __name__ == "__main__":
    unittest.main()
