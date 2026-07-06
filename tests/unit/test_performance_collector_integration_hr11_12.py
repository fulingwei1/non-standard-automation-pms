# -*- coding: utf-8 -*-
"""HR-11/12: engineer performance scoring must consume collected data."""

from datetime import date
from decimal import Decimal
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


class _CollectedMechanicalData:
    def __init__(self, _db):
        pass

    def collect_all_data(self, engineer_id, start_date, end_date):
        assert engineer_id > 0
        assert start_date == date(2026, 7, 1)
        assert end_date == date(2026, 7, 31)
        return {
            "data": {
                "design_review": {
                    "total_reviews": 10,
                    "first_pass_reviews": 7,
                    "first_pass_rate": 70.0,
                },
                "debug_issue": {
                    "mechanical_issues": 2,
                    "test_bugs": 0,
                    "resolved_bugs": 0,
                    "avg_fix_time": 0.0,
                },
                "task_completion": {
                    "total_tasks": 10,
                    "completed_tasks": 4,
                    "on_time_tasks": 2,
                    "completion_rate": 40.0,
                    "on_time_rate": 50.0,
                },
                "bom_data": {
                    "total_bom": 5,
                    "on_time_bom": 2,
                    "bom_timeliness_rate": 50.0,
                    "standard_part_rate": 60.0,
                    "reuse_rate": 0.0,
                },
                "ecn_responsibility": {
                    "total_ecn": 4,
                    "responsible_ecn": 1,
                    "ecn_responsibility_rate": 20.0,
                },
                "knowledge_contribution": {
                    "total_contributions": 2,
                    "document_count": 2,
                    "template_count": 0,
                    "module_count": 0,
                    "total_reuse_count": 0,
                },
            }
        }


def test_calculate_and_save_result_uses_collected_data_for_mechanical_scores(
    db_session, monkeypatch
):
    from app.models.engineer_performance import EngineerDimensionConfig, EngineerProfile
    from app.models.performance import PerformancePeriod
    from app.models.user import User
    from app.services.engineer_performance import performance_calculator as calculator_module
    from app.services.engineer_performance.engineer_performance_service import (
        EngineerPerformanceService,
    )

    monkeypatch.setattr(
        calculator_module,
        "PerformanceDataAggregator",
        _CollectedMechanicalData,
        raising=False,
    )

    user = User(
        username=_code("hr11-mechanical").lower(),
        password_hash="not-used",
        real_name="HR11机械工程师",
        department_id=11,
        department="机械研发部",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    db_session.add(
        EngineerProfile(
            user_id=user.id,
            job_type="mechanical",
            job_level="junior",
            job_start_date=date(2025, 1, 1),
            level_start_date=date(2025, 1, 1),
        )
    )
    period = PerformancePeriod(
        period_code=_code("HR11P"),
        period_name="HR11 2026年7月",
        period_type="MONTHLY",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
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
        config_name="HR11机械初级权重",
        approval_status="APPROVED",
    )
    db_session.add(config)
    db_session.commit()

    result = EngineerPerformanceService(db_session).calculate_and_save_result(
        user.id, period.id
    )

    assert result.workload_score == Decimal("72.35")
    assert result.task_score == Decimal("44.0")
    assert result.quality_score == Decimal("63.33")
    assert result.growth_score == Decimal("70")
    assert result.collaboration_score == Decimal("75")
    assert result.total_score == Decimal("63.37")
    assert result.level == "B"
    assert result.indicator_scores["technical"] == 72.35
    assert result.indicator_scores["execution"] == 44.0
    assert result.indicator_scores["cost_quality"] == 63.33
