# -*- coding: utf-8 -*-
"""HR-19: bonus coefficients should be rule-driven, not hardcoded."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def test_performance_bonus_uses_rule_level_coefficients(db_session):
    """绩效等级系数应从规则 JSON 读取。"""
    from app.models.bonus import BonusRule
    from app.models.performance import PerformancePeriod, PerformanceResult
    from app.models.user import User
    from app.services.bonus.performance import PerformanceBonusCalculator

    user = User(
        username=_code("hr19").lower(),
        password_hash="not-used",
        real_name="HR19绩效奖金工程师",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    period = PerformancePeriod(
        period_code=_code("HR19P"),
        period_name="HR19奖金周期",
        period_type="MONTHLY",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(period)
    db_session.flush()

    result = PerformanceResult(
        period_id=period.id,
        user_id=user.id,
        user_name=user.display_name,
        total_score=Decimal("88.00"),
        level="A",
        status="CALCULATED",
    )
    rule = BonusRule(
        rule_code=_code("BR-HR19"),
        rule_name="HR19绩效系数规则",
        bonus_type="PERFORMANCE",
        base_amount=Decimal("1000.00"),
        trigger_condition={
            "min_score": 80,
            "performance_coefficients": {"A": "2.5"},
        },
        is_active=True,
    )
    db_session.add_all([result, rule])
    db_session.commit()

    calculation = PerformanceBonusCalculator(db_session).calculate(result, rule)

    assert calculation.calculated_amount == Decimal("2500.00")
    assert calculation.calculation_detail["coefficient"] == 2.5


def test_presale_completion_bonus_uses_rule_coefficients(db_session):
    """售前紧急程度和满意度系数应从规则 JSON 读取。"""
    from app.models.bonus import BonusRule
    from app.services.bonus.presale import PresaleBonusCalculator

    rule = BonusRule(
        id=1,
        rule_code="BR-HR19-PRE",
        rule_name="HR19售前系数规则",
        bonus_type="PRESALE",
        base_amount=Decimal("100.00"),
        trigger_condition={
            "urgency_coefficients": {"VERY_URGENT": "2.0"},
            "satisfaction_coefficients": {
                "score_gte_5": "1.5",
                "score_gte_4": "1.1",
                "default": "0.7",
            },
        },
        is_active=True,
    )
    ticket = SimpleNamespace(
        id=1,
        ticket_no="PRE-HR19-001",
        ticket_type="TECH",
        assignee_id=9,
        urgency="VERY_URGENT",
        satisfaction_score=5,
        opportunity_id=None,
        project_id=None,
    )

    calculation = PresaleBonusCalculator(db_session).calculate(ticket, rule, based_on="COMPLETION")

    assert calculation.calculated_amount == Decimal("300.000")
    assert calculation.calculation_detail["urgency_coefficient"] == 2.0
    assert calculation.calculation_detail["satisfaction_coefficient"] == 1.5
