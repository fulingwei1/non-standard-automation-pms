# -*- coding: utf-8 -*-
"""
SmartAlertEngine N2 深度覆盖测试
覆盖: _calculate_risk_score 所有分支, _score_* 全部路径,
      generate_solutions, _generate_partial_delivery_plan,
      _generate_reschedule_plan, _score_cost ratios
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.shortage.smart_alert_engine import SmartAlertEngine


@pytest.fixture
def engine():
    db = MagicMock()
    return SmartAlertEngine(db)


def make_alert(alert_id=1, shortage_qty=None, available_qty=None, required_date=None,
               estimated_delay_days=5, estimated_cost_impact=None, alert_level="WARNING"):
    a = MagicMock()
    a.id = alert_id
    a.alert_no = "ALT-001"
    a.shortage_qty = shortage_qty or Decimal("50")
    a.available_qty = available_qty or Decimal("20")
    a.required_date = required_date or date.today() + timedelta(days=10)
    a.estimated_delay_days = estimated_delay_days
    a.estimated_cost_impact = estimated_cost_impact or Decimal("10000")
    a.alert_level = alert_level
    a.risks = []
    return a


# ======================= _calculate_risk_score =======================

class TestCalculateRiskScore:
    """所有权重分支的完整覆盖"""

    def test_maximum_score_all_high(self, engine):
        score = engine._calculate_risk_score(
            delay_days=35,
            cost_impact=Decimal("200000"),
            project_count=6,
            shortage_qty=Decimal("2000")
        )
        assert score == Decimal("100")

    def test_delay_30_plus_gives_40(self, engine):
        score = engine._calculate_risk_score(
            delay_days=31, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("40")

    def test_delay_15_to_30_gives_30(self, engine):
        score = engine._calculate_risk_score(
            delay_days=20, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("30")

    def test_delay_7_to_15_gives_20(self, engine):
        score = engine._calculate_risk_score(
            delay_days=10, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("20")

    def test_delay_1_to_7_gives_10(self, engine):
        score = engine._calculate_risk_score(
            delay_days=3, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("10")

    def test_delay_zero_gives_no_delay_score(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("0")

    def test_cost_100k_plus_gives_30(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("150000"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("30")

    def test_cost_50k_to_100k_gives_20(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("60000"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("20")

    def test_cost_10k_to_50k_gives_10(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("20000"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("10")

    def test_project_count_5_plus_gives_20(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=6, shortage_qty=Decimal("0")
        )
        assert score == Decimal("20")

    def test_project_count_3_to_5_gives_15(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=4, shortage_qty=Decimal("0")
        )
        assert score == Decimal("15")

    def test_project_count_1_to_3_gives_10(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=2, shortage_qty=Decimal("0")
        )
        assert score == Decimal("10")

    def test_shortage_1000_plus_gives_10(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("1500")
        )
        assert score == Decimal("10")

    def test_shortage_100_to_1000_gives_7(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("500")
        )
        assert score == Decimal("7")

    def test_shortage_10_to_100_gives_5(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("50")
        )
        assert score == Decimal("5")

    def test_zero_everything_gives_zero(self, engine):
        score = engine._calculate_risk_score(
            delay_days=0, cost_impact=Decimal("0"), project_count=0, shortage_qty=Decimal("0")
        )
        assert score == Decimal("0")


# ======================= _score_feasibility =======================

class TestScoreFeasibility:
    """所有 solution_type 评分"""

    @pytest.mark.parametrize("solution_type,expected", [
        ("URGENT_PURCHASE", 80),
        ("SUBSTITUTE", 60),
        ("TRANSFER", 70),
        ("PARTIAL_DELIVERY", 85),
        ("RESCHEDULE", 90),
        ("UNKNOWN_TYPE", 50),
    ])
    def test_feasibility_scores(self, engine, solution_type, expected):
        sol = MagicMock()
        sol.solution_type = solution_type
        result = engine._score_feasibility(sol)
        assert result == Decimal(str(expected))


# ======================= _score_cost =======================

class TestScoreCost:
    """成本评分所有比率分支"""

    def test_no_estimated_cost_returns_100(self, engine):
        sol = MagicMock()
        sol.estimated_cost = None
        alert = MagicMock()
        alert.estimated_cost_impact = Decimal("10000")
        result = engine._score_cost(sol, alert)
        assert result == Decimal("100")

    def test_cost_ratio_less_than_half_returns_100(self, engine):
        sol = MagicMock()
        sol.estimated_cost = Decimal("3000")  # 3000/10000 = 0.3 < 0.5
        alert = MagicMock()
        alert.estimated_cost_impact = Decimal("10000")
        result = engine._score_cost(sol, alert)
        assert result == Decimal("100")

    def test_cost_ratio_0_5_to_1_returns_80(self, engine):
        sol = MagicMock()
        sol.estimated_cost = Decimal("7000")  # 0.7
        alert = MagicMock()
        alert.estimated_cost_impact = Decimal("10000")
        result = engine._score_cost(sol, alert)
        assert result == Decimal("80")

    def test_cost_ratio_1_to_1_5_returns_60(self, engine):
        sol = MagicMock()
        sol.estimated_cost = Decimal("12000")  # 1.2
        alert = MagicMock()
        alert.estimated_cost_impact = Decimal("10000")
        result = engine._score_cost(sol, alert)
        assert result == Decimal("60")

    def test_cost_ratio_over_1_5_returns_40(self, engine):
        sol = MagicMock()
        sol.estimated_cost = Decimal("20000")  # 2.0
        alert = MagicMock()
        alert.estimated_cost_impact = Decimal("10000")
        result = engine._score_cost(sol, alert)
        assert result == Decimal("40")

    def test_zero_cost_impact_returns_40(self, engine):
        """cost_impact=0 时 ratio=1，返回 40"""
        sol = MagicMock()
        sol.estimated_cost = Decimal("5000")
        alert = MagicMock()
        alert.estimated_cost_impact = Decimal("0")
        result = engine._score_cost(sol, alert)
        assert result == Decimal("40")


# ======================= _score_time =======================

class TestScoreTime:
    @pytest.mark.parametrize("lead_time,expected", [
        (0, 100),
        (2, 90),
        (5, 70),
        (10, 50),
        (20, 30),
    ])
    def test_all_lead_times(self, engine, lead_time, expected):
        sol = MagicMock()
        sol.estimated_lead_time = lead_time
        alert = MagicMock()
        result = engine._score_time(sol, alert)
        assert result == Decimal(str(expected))

    def test_none_lead_time_treated_as_zero(self, engine):
        sol = MagicMock()
        sol.estimated_lead_time = None
        alert = MagicMock()
        result = engine._score_time(sol, alert)
        assert result == Decimal("100")


# ======================= _score_risk =======================

class TestScoreRisk:
    @pytest.mark.parametrize("risk_count,expected", [
        (0, 100),
        (1, 80),
        (2, 80),
        (3, 60),
        (4, 60),
        (5, 40),
    ])
    def test_all_risk_counts(self, engine, risk_count, expected):
        sol = MagicMock()
        sol.risks = ["risk"] * risk_count
        result = engine._score_risk(sol)
        assert result == Decimal(str(expected))

    def test_none_risks_returns_100(self, engine):
        sol = MagicMock()
        sol.risks = None
        result = engine._score_risk(sol)
        assert result == Decimal("100")


# ======================= _generate_partial_delivery_plan =======================

class TestGeneratePartialDeliveryPlan:
    def test_returns_plan_when_available_qty_positive(self, engine):
        alert = make_alert(available_qty=Decimal("30"))
        engine._generate_plan_no = MagicMock(return_value="SP-001")
        result = engine._generate_partial_delivery_plan(alert)
        assert result is not None
        assert result.solution_type == "PARTIAL_DELIVERY"

    def test_returns_none_when_available_qty_zero(self, engine):
        alert = make_alert(available_qty=Decimal("0"))
        result = engine._generate_partial_delivery_plan(alert)
        assert result is None


# ======================= _generate_reschedule_plan =======================

class TestGenerateReschedulePlan:
    def test_returns_reschedule_plan(self, engine):
        alert = make_alert(estimated_delay_days=7)
        engine._generate_plan_no = MagicMock(return_value="SP-002")
        result = engine._generate_reschedule_plan(alert)
        assert result is not None
        assert result.solution_type == "RESCHEDULE"


# ======================= generate_solutions =======================

class TestGenerateSolutions:
    def test_returns_sorted_by_score(self, engine):
        """解决方案按 ai_score 降序排列"""
        alert = make_alert()

        sol1 = MagicMock()
        sol1.ai_score = Decimal("70")
        sol1.is_recommended = False

        sol2 = MagicMock()
        sol2.ai_score = Decimal("90")
        sol2.is_recommended = False

        engine._generate_urgent_purchase_plan = MagicMock(return_value=sol1)
        engine._generate_substitute_plans = MagicMock(return_value=[])
        engine._generate_transfer_plans = MagicMock(return_value=[])
        engine._generate_partial_delivery_plan = MagicMock(return_value=sol2)
        engine._generate_reschedule_plan = MagicMock(return_value=None)
        engine._score_solution = MagicMock()

        result = engine.generate_solutions(alert)
        # First should be highest ai_score
        assert result[0].ai_score >= result[-1].ai_score

    def test_first_solution_marked_as_recommended(self, engine):
        alert = make_alert()
        sol = MagicMock()
        sol.ai_score = Decimal("80")
        sol.is_recommended = False

        engine._generate_urgent_purchase_plan = MagicMock(return_value=sol)
        engine._generate_substitute_plans = MagicMock(return_value=[])
        engine._generate_transfer_plans = MagicMock(return_value=[])
        engine._generate_partial_delivery_plan = MagicMock(return_value=None)
        engine._generate_reschedule_plan = MagicMock(return_value=None)
        engine._score_solution = MagicMock()

        result = engine.generate_solutions(alert)
        if result:
            assert result[0].is_recommended is True

    def test_empty_solutions_when_all_return_none(self, engine):
        alert = make_alert()
        engine._generate_urgent_purchase_plan = MagicMock(return_value=None)
        engine._generate_substitute_plans = MagicMock(return_value=[])
        engine._generate_transfer_plans = MagicMock(return_value=[])
        engine._generate_partial_delivery_plan = MagicMock(return_value=None)
        engine._generate_reschedule_plan = MagicMock(return_value=None)
        engine._score_solution = MagicMock()

        result = engine.generate_solutions(alert)
        assert result == []


# ======================= _generate_alert_no =======================

class TestGenerateAlertNo:
    def test_generates_formatted_alert_no(self, engine):
        engine.db.query.return_value.filter.return_value.scalar.return_value = 0
        alert_no = engine._generate_alert_no()
        assert alert_no.startswith("SA")
        assert len(alert_no) > 8

    def test_increments_with_existing_count(self, engine):
        engine.db.query.return_value.filter.return_value.scalar.return_value = 5
        alert_no = engine._generate_alert_no()
        # Should end in 0006
        assert alert_no.endswith("0006")
