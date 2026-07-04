# -*- coding: utf-8 -*-
"""
HR-10: 工程师五维绩效计算结果必须写入 performance_result。
"""

from datetime import date
from decimal import Decimal


def _seed_mechanical_engineer_period_and_config(db_session):
    from app.models.engineer_performance import EngineerDimensionConfig, EngineerProfile
    from app.models.performance import PerformancePeriod
    from app.models.user import User

    user = User(
        username="hr10-mechanical",
        password_hash="not-used",
        real_name="HR10机械工程师",
        department_id=10,
        department="机械研发部",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    profile = EngineerProfile(
        user_id=user.id,
        job_type="mechanical",
        job_level="junior",
        job_start_date=date(2025, 1, 1),
        level_start_date=date(2025, 1, 1),
    )
    db_session.add(profile)

    period = PerformancePeriod(
        period_code="HR10-2026-06",
        period_name="HR10 2026年6月",
        period_type="MONTHLY",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(period)

    config = EngineerDimensionConfig(
        job_type="mechanical",
        job_level="junior",
        is_global=True,
        technical_weight=30,
        execution_weight=25,
        cost_quality_weight=20,
        knowledge_weight=15,
        collaboration_weight=10,
        effective_date=date(2026, 1, 1),
        config_name="HR10机械初级权重",
        approval_status="APPROVED",
    )
    db_session.add(config)
    db_session.commit()
    return user, period


def test_calculate_and_save_result_persists_complete_performance_result(db_session):
    from app.models.performance import PerformanceResult
    from app.services.engineer_performance.engineer_performance_service import (
        EngineerPerformanceService,
    )

    user, period = _seed_mechanical_engineer_period_and_config(db_session)

    service = EngineerPerformanceService(db_session)
    result = service.calculate_and_save_result(user.id, period.id)

    persisted = (
        db_session.query(PerformanceResult)
        .filter(
            PerformanceResult.period_id == period.id,
            PerformanceResult.user_id == user.id,
        )
        .one()
    )

    assert persisted.id == result.id
    assert persisted.total_score == Decimal("80.00")
    assert persisted.level == "A"
    assert persisted.workload_score == Decimal("100.00")
    assert persisted.task_score == Decimal("80.00")
    assert persisted.quality_score == Decimal("75.00")
    assert persisted.growth_score == Decimal("50.00")
    assert persisted.collaboration_score == Decimal("75.00")
    assert persisted.job_type == "mechanical"
    assert persisted.job_level == "junior"
    assert persisted.user_name == "HR10机械工程师"
    assert persisted.department_id == 10
    assert persisted.department_name == "机械研发部"
    assert persisted.status == "CALCULATED"
    assert persisted.calculated_at is not None
    assert persisted.company_rank == 1
    assert persisted.dept_rank == 1
    assert set(persisted.indicator_scores) == {
        "technical",
        "execution",
        "cost_quality",
        "knowledge",
        "collaboration",
    }

    updated = service.calculate_and_save_result(user.id, period.id)

    assert updated.id == persisted.id
    assert (
        db_session.query(PerformanceResult)
        .filter(
            PerformanceResult.period_id == period.id,
            PerformanceResult.user_id == user.id,
        )
        .count()
        == 1
    )
