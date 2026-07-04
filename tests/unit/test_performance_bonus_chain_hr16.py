# -*- coding: utf-8 -*-
"""
HR-16: 绩效结果必须能串联生成绩效奖金计算记录。
"""

from datetime import date
from decimal import Decimal
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def _seed_user_period_and_result(
    db_session,
    *,
    total_score=Decimal("82.00"),
    level="A",
):
    from app.models.performance import PerformancePeriod, PerformanceResult
    from app.models.user import User

    user = User(
        username=_code("hr16").lower(),
        password_hash="not-used",
        real_name="HR16绩效奖金工程师",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    period = PerformancePeriod(
        period_code=_code("HR16P"),
        period_name="HR16奖金周期",
        period_type="MONTHLY",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(period)
    db_session.flush()

    result = PerformanceResult(
        period_id=period.id,
        user_id=user.id,
        user_name=user.display_name,
        total_score=total_score,
        level=level,
        workload_score=Decimal("90.00") if total_score is not None else None,
        task_score=Decimal("80.00") if total_score is not None else None,
        quality_score=Decimal("80.00") if total_score is not None else None,
        growth_score=Decimal("75.00") if total_score is not None else None,
        collaboration_score=Decimal("80.00") if total_score is not None else None,
        job_type="mechanical" if total_score is not None else None,
        job_level="junior" if total_score is not None else None,
        status="CALCULATED",
    )
    db_session.add(result)
    db_session.flush()
    return user, period, result


def _seed_performance_bonus_rule(db_session, *, bonus_type="PERFORMANCE"):
    from app.models.bonus import BonusRule

    rule = BonusRule(
        rule_code=_code("BR-HR16"),
        rule_name="HR16绩效奖金规则",
        bonus_type=bonus_type,
        base_amount=Decimal("1000.00"),
        trigger_condition={"min_score": 80},
        is_active=True,
    )
    db_session.add(rule)
    db_session.commit()
    return rule


def test_performance_bonus_uses_rule_alias_and_persists_calculation(db_session):
    from app.api.v1.endpoints.bonus.calculation import calculate_performance_bonus
    from app.models.bonus import BonusCalculation
    from app.schemas.bonus import CalculatePerformanceBonusRequest

    user, period, result = _seed_user_period_and_result(db_session)
    rule = _seed_performance_bonus_rule(db_session, bonus_type="PERFORMANCE")

    response = calculate_performance_bonus(
        db=db_session,
        request=CalculatePerformanceBonusRequest(period_id=period.id),
        current_user=user,
    )

    assert response.code == 200
    assert len(response.data) == 1
    calculation = db_session.query(BonusCalculation).one()
    assert calculation.rule_id == rule.id
    assert calculation.performance_result_id == result.id
    assert calculation.user_id == user.id
    assert calculation.calculated_amount == Decimal("1200.00")
    assert calculation.calculation_detail["coefficient"] == 1.2
    assert calculation.calculation_detail["performance_level"] == "A"


def test_performance_bonus_calculation_is_idempotent(db_session):
    from app.api.v1.endpoints.bonus.calculation import calculate_performance_bonus
    from app.models.bonus import BonusCalculation
    from app.schemas.bonus import CalculatePerformanceBonusRequest

    user, period, result = _seed_user_period_and_result(db_session)
    _seed_performance_bonus_rule(db_session, bonus_type="PERFORMANCE_BASED")
    request = CalculatePerformanceBonusRequest(period_id=period.id, user_id=user.id)

    first = calculate_performance_bonus(db=db_session, request=request, current_user=user)
    second = calculate_performance_bonus(db=db_session, request=request, current_user=user)

    assert len(first.data) == 1
    assert len(second.data) == 1
    assert db_session.query(BonusCalculation).count() == 1
    assert db_session.query(BonusCalculation).one().performance_result_id == result.id


def test_incomplete_performance_result_is_not_paid(db_session):
    from app.api.v1.endpoints.bonus.calculation import calculate_performance_bonus
    from app.models.bonus import BonusCalculation
    from app.schemas.bonus import CalculatePerformanceBonusRequest

    user, period, _ = _seed_user_period_and_result(
        db_session,
        total_score=None,
        level=None,
    )
    _seed_performance_bonus_rule(db_session, bonus_type="PERFORMANCE_BASED")

    response = calculate_performance_bonus(
        db=db_session,
        request=CalculatePerformanceBonusRequest(period_id=period.id),
        current_user=user,
    )

    assert response.code == 200
    assert response.data == []
    assert db_session.query(BonusCalculation).count() == 0
