from app.schemas.health_trend import (
    AlertEvent,
    DimensionDetail,
    HealthTrendPeriod,
    HealthTrendResponse,
    ImprovementResponse,
    RiskBreakdownResponse,
    Simulation,
    SuccessCase,
    Suggestion,
)


def test_health_trend_response_models():
    period = HealthTrendPeriod(start="2026-04-01", end="2026-04-14", days=14)
    event = AlertEvent(date="2026-04-10", level="HIGH", title="交期预警", status="OPEN")
    response = HealthTrendResponse(
        project_id=1,
        project_name="项目A",
        period=period,
        dates=["2026-04-01", "2026-04-02"],
        scores=[80, 78],
        dimensions={"schedule": [75, 70], "cost": [85, 84]},
        events=[event],
    )

    assert response.period.days == 14
    assert response.events[0].title == "交期预警"
    assert response.dimensions["schedule"] == [75, 70]


def test_breakdown_and_improvement_models():
    detail = DimensionDetail(
        key="schedule",
        label="进度",
        weight=0.4,
        score=70,
        weighted_score=28.0,
    )
    simulation = Simulation(
        dimension="schedule",
        label="进度",
        current_score=70,
        target_score=85,
        current_overall=76.5,
        simulated_overall=82.0,
        improvement=5.5,
    )
    breakdown = RiskBreakdownResponse(
        project_id=1,
        overall_score=76.5,
        current_health="MEDIUM",
        dimensions=[detail],
        weak_factors=[detail],
        simulations=[simulation],
    )
    suggestion = Suggestion(
        priority=1,
        dimension="schedule",
        dimension_label="进度",
        title="加快关键路径",
        description="优先处理阻塞任务",
        impact="high",
        effort="medium",
        category="execution",
    )
    success_case = SuccessCase(
        project_id=2,
        project_name="项目B",
        from_health="LOW",
        to_health="HIGH",
        recovered_at="2026-04-12",
        note="补充资源后恢复",
    )
    improvement = ImprovementResponse(
        project_id=1,
        overall_score=76.5,
        suggestions=[suggestion],
        success_cases=[success_case],
    )

    assert breakdown.dimensions[0].weighted_score == 28.0
    assert breakdown.simulations[0].improvement == 5.5
    assert improvement.suggestions[0].current_score == 0
    assert improvement.success_cases[0].to_health == "HIGH"
