from datetime import datetime

from app.schemas.production_schedule import (
    AdjustmentLogResponse,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleScoreMetrics,
)


NOW = datetime(2026, 4, 14, 8, 0, 0)
LATER = datetime(2026, 4, 14, 12, 0, 0)


def test_schedule_create_normalizes_none_fields():
    schema = ScheduleCreate(
        work_order_id=1,
        scheduled_start_time=NOW,
        scheduled_end_time=LATER,
        duration_hours=4,
        priority_score=None,
        is_urgent=None,
    )

    assert schema.priority_score == 0.0
    assert schema.is_urgent is False


def test_schedule_response_normalizes_none_fields():
    schema = ScheduleResponse(
        id=1,
        work_order_id=1,
        scheduled_start_time=NOW,
        scheduled_end_time=LATER,
        duration_hours=4,
        schedule_plan_id=None,
        status=None,
        actual_start_time=None,
        actual_end_time=None,
        actual_duration_hours=None,
        algorithm_version=None,
        score=None,
        constraints_met=None,
        is_manually_adjusted=None,
        adjustment_reason=None,
        sequence_no=None,
        created_at=NOW,
        updated_at=LATER,
        confirmed_at=None,
    )

    assert schema.status == "PENDING"
    assert schema.is_manually_adjusted is False


def test_adjustment_log_response_normalizes_none_fields():
    schema = AdjustmentLogResponse(
        id=1,
        schedule_id=1,
        adjustment_type="MANUAL",
        trigger_source="USER",
        before_data=None,
        after_data=None,
        changes_summary=None,
        reason="调整顺序",
        impact_analysis=None,
        affected_schedules_count=None,
        adjusted_at=NOW,
    )

    assert schema.affected_schedules_count == 0


def test_schedule_score_metrics_calculate_overall_score():
    metrics = ScheduleScoreMetrics(
        completion_rate=0.9,
        equipment_utilization=0.8,
        worker_utilization=0.7,
        total_duration_hours=100,
        average_waiting_time=2,
        skill_match_rate=0.95,
        priority_satisfaction=0.85,
        conflict_count=3,
        overtime_hours=20,
    )

    assert metrics.calculate_overall_score() == 64.75
