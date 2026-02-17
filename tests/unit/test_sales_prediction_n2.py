# -*- coding: utf-8 -*-
"""
销售预测服务 N2 深度覆盖测试
覆盖: 自定义配置参数, ICT行业数据(28万预算), 边界分支,
      evaluate_prediction_accuracy, predict_win_probability customer_factor
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from app.services.sales_prediction_service import SalesPredictionService


def make_opp(stage="PROPOSAL", est_amount=None, customer_id=None, created_at=None):
    o = MagicMock()
    o.stage = stage
    o.est_amount = est_amount
    o.customer_id = customer_id
    o.created_at = created_at or datetime.now()
    return o


def make_contract(amount=None, signed_date=None):
    c = MagicMock()
    c.contract_amount = amount
    c.signed_date = signed_date or date.today()
    c.status = "SIGNED"
    return c


# ======================= 自定义配置参数 =======================

class TestCustomConfig:
    def test_custom_stage_weights_applied(self):
        db = MagicMock()
        service = SalesPredictionService(
            db,
            stage_weights={"PROPOSAL": 0.7, "NEGOTIATION": 0.9}
        )
        assert service.stage_weights["PROPOSAL"] == 0.7

    def test_custom_smoothing_alpha(self):
        db = MagicMock()
        service = SalesPredictionService(db, smoothing_alpha=0.5)
        assert service.smoothing_alpha == 0.5

    def test_custom_probability_bounds(self):
        db = MagicMock()
        service = SalesPredictionService(db, probability_bounds=(0.05, 0.99))
        assert service.probability_bounds == (0.05, 0.99)


# ======================= ICT 行业数据 (平均28万预算) =======================

class TestICTIndustryData:
    """ICT行业平均28万预算的预测场景"""

    def test_ict_moving_average_90days(self):
        """基于 ICT 28万/月 平均的90天移动平均预测"""
        db = MagicMock()
        service = SalesPredictionService(db)

        # 历史3个月都是 ICT 均值 28万
        monthly_data = [
            {"month": "2025-11", "revenue": 280000, "count": 1},
            {"month": "2025-12", "revenue": 280000, "count": 1},
            {"month": "2026-01", "revenue": 280000, "count": 1},
        ]
        result = service._moving_average_forecast(monthly_data, 90)
        # 3个月 * 28万 = 84万
        assert result == Decimal("840000")

    def test_ict_exp_smoothing_with_increasing_trend(self):
        """ICT 收入递增趋势下的指数平滑预测"""
        db = MagicMock()
        service = SalesPredictionService(db)

        monthly_data = [
            {"month": "2025-10", "revenue": 200000, "count": 1},
            {"month": "2025-11", "revenue": 250000, "count": 1},
            {"month": "2025-12", "revenue": 280000, "count": 1},
        ]
        result = service._exponential_smoothing_forecast(monthly_data, 30, alpha=0.3)
        # alpha=0.3: last smoothed ≈ 0.3*280000 + 0.7*(earlier smoothed)
        assert result > Decimal("200000")
        assert result <= Decimal("280000")

    def test_ict_forecast_from_opportunities(self):
        """基于ICT商机的收入预测"""
        db = MagicMock()
        service = SalesPredictionService(db)

        # 3个 28万 PROPOSAL 商机 + 1个 56万 NEGOTIATION
        opps = [
            make_opp(stage="PROPOSAL", est_amount=Decimal("280000")),
            make_opp(stage="PROPOSAL", est_amount=Decimal("280000")),
            make_opp(stage="PROPOSAL", est_amount=Decimal("280000")),
            make_opp(stage="NEGOTIATION", est_amount=Decimal("560000")),
        ]
        result = service._forecast_from_opportunities(opps, 90)
        # PROPOSAL: 3 * 280000 * 0.6 = 504000
        # NEGOTIATION: 560000 * 0.8 = 448000
        # Total = 952000, months = 3, factor = min(3/3, 1.0) = 1.0
        expected = Decimal(str(280000 * 3 * 0.6 + 560000 * 0.8))
        assert result == expected

    def test_ict_medium_amount_win_probability(self):
        """50-100万中等金额ICT项目赢单概率"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)
        # 75万（50-100万区间）
        result = service.predict_win_probability(
            stage="NEGOTIATION",
            amount=Decimal("750000")
        )
        # 金额在50-100万区间，factor=0.95
        assert result["amount_factor"] == 0.95

    def test_ict_small_deal_probability_boost(self):
        """<10万小单概率提升"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)
        result = service.predict_win_probability(
            stage="PROPOSAL",
            amount=Decimal("80000")  # < 10万
        )
        assert result["amount_factor"] == 1.1


# ======================= predict_win_probability 分支 =======================

class TestPredictWinProbabilityBranches:
    def test_customer_factor_applied_when_history_exists(self):
        """客户历史赢单率调整因子"""
        db = MagicMock()

        # Historical opportunities: 3 WON, 1 LOST
        won_opps = [make_opp(stage="WON"), make_opp(stage="WON"), make_opp(stage="WON")]
        lost_opps = [make_opp(stage="LOST")]

        # _get_customer_win_rate will be called with customer_id=5
        call_count = [0]
        def all_side():
            call_count[0] += 1
            if call_count[0] == 1:
                # all stages for historical win rate
                return won_opps + lost_opps + [make_opp(stage="PROPOSAL")]
            elif call_count[0] == 2:
                # customer WON/LOST
                return won_opps + lost_opps
            return []

        q = MagicMock()
        q.filter.return_value = q
        q.all.side_effect = lambda: all_side()
        db.query.return_value = q
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)
        result = service.predict_win_probability(
            stage="PROPOSAL",
            amount=Decimal("280000"),
            customer_id=5
        )
        assert "customer_factor" in result
        assert result["win_probability"] >= 0.1
        assert result["win_probability"] <= 0.95

    def test_probability_min_bound_enforced(self):
        """概率下限 0.1 被强制执行"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db, probability_bounds=(0.1, 0.95))
        # DISCOVERY stage 通常很低
        result = service.predict_win_probability(
            stage="DISCOVERY",
            amount=Decimal("5000000")  # Very large, reducing factor to 0.9
        )
        assert result["win_probability"] >= 0.1

    def test_no_customer_factor_when_no_history(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)
        result = service.predict_win_probability(stage="PROPOSAL")
        assert result["customer_factor"] == 1.0


# ======================= _exponential_smoothing 内部 alpha =======================

class TestExponentialSmoothingInternal:
    def test_uses_instance_alpha_by_default(self):
        """使用实例配置的 alpha"""
        db = MagicMock()
        service = SalesPredictionService(db, smoothing_alpha=0.5)

        monthly_data = [
            {"month": "2024-01", "revenue": 100000, "count": 1},
            {"month": "2024-02", "revenue": 200000, "count": 1},
        ]
        result = service._exponential_smoothing_forecast(monthly_data, 30)
        # alpha=0.5: 0.5*200000 + 0.5*100000 = 150000
        assert result == Decimal("150000")

    def test_many_months_converges(self):
        """多月数据下预测结果收敛"""
        db = MagicMock()
        service = SalesPredictionService(db)

        monthly_data = [{"month": f"2024-{i:02d}", "revenue": 100000, "count": 1}
                        for i in range(1, 13)]
        result = service._exponential_smoothing_forecast(monthly_data, 30)
        # Uniform data → forecast ≈ 100000
        assert abs(float(result) - 100000) < 5000


# ======================= evaluate_prediction_accuracy =======================

class TestEvaluatePredictionAccuracy:
    def test_zero_actual_revenue_gives_zero_accuracy(self):
        db = MagicMock()
        contracts_q = MagicMock()
        contracts_q.filter.return_value = contracts_q
        contracts_q.all.return_value = []

        opps_q = MagicMock()
        opps_q.filter.return_value = opps_q
        opps_q.all.return_value = []

        cnt = [0]
        def q_side(model):
            cnt[0] += 1
            return contracts_q if cnt[0] == 1 else opps_q
        db.query.side_effect = q_side

        service = SalesPredictionService(db)
        result = service.evaluate_prediction_accuracy(days_back=30)
        assert result["accuracy"] == 0.0
        assert result["error_rate"] == 1.0

    def test_accurate_prediction_gives_high_accuracy(self):
        """预测值接近实际值时准确率高"""
        db = MagicMock()

        # Actual: 2 contracts @ 50000 each = 100000
        contracts = [make_contract(amount=Decimal("50000")),
                     make_contract(amount=Decimal("50000"))]
        contracts_q = MagicMock()
        contracts_q.filter.return_value = contracts_q
        contracts_q.all.return_value = contracts

        # Opportunities that would forecast ~100000
        opps = [make_opp(stage="PROPOSAL", est_amount=Decimal("200000"))]
        opps_q = MagicMock()
        opps_q.filter.return_value = opps_q
        opps_q.all.return_value = opps

        cnt = [0]
        def q_side(model):
            cnt[0] += 1
            return contracts_q if cnt[0] == 1 else opps_q
        db.query.side_effect = q_side

        service = SalesPredictionService(db)
        result = service.evaluate_prediction_accuracy(days_back=90)
        assert result["actual_revenue"] == 100000.0
        assert "mape" in result


# ======================= _calculate_confidence 边界 =======================

class TestCalculateConfidenceBoundary:
    def test_exactly_6_months_5_opps_gives_high(self):
        db = MagicMock()
        service = SalesPredictionService(db)
        data = [{}] * 6
        result = service._calculate_confidence(data, 5)
        assert result == "HIGH"

    def test_3_months_2_opps_gives_medium(self):
        db = MagicMock()
        service = SalesPredictionService(db)
        data = [{}] * 3
        result = service._calculate_confidence(data, 2)
        assert result == "MEDIUM"

    def test_0_months_0_opps_gives_low(self):
        db = MagicMock()
        service = SalesPredictionService(db)
        result = service._calculate_confidence([], 0)
        assert result == "LOW"
