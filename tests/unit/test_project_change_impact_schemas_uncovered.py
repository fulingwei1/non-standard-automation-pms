from datetime import datetime
from decimal import Decimal

from app.schemas.project_change_impact import (
    AssessImpactRequest,
    CostBreakdown,
    ExecuteLinkageRequest,
    ImpactAssessmentReport,
    MilestoneImpactItem,
    ProjectChangeImpactListResponse,
    ProjectChangeImpactResponse,
    ProjectChangeSummary,
)


def test_assess_request_and_nested_models():
    milestone = MilestoneImpactItem(
        milestone_id=1,
        name="设计完成",
        original_date="2026-04-10",
        new_date="2026-04-15",
        delay_days=5,
    )
    breakdown = CostBreakdown(
        rework_hours=8,
        hourly_rate=100,
        scrap_materials=[{"name": "旧料", "cost": 80}],
        new_materials=[{"name": "新料", "cost": 120}],
        description="返工和替换",
    )
    request = AssessImpactRequest(
        ecn_id=10,
        project_id=20,
        machine_id=30,
        schedule_impact_days=5,
        affected_milestones=[milestone],
        rework_cost=Decimal("100.50"),
        scrap_cost=Decimal("20.00"),
        additional_cost=Decimal("50.00"),
        cost_breakdown=breakdown,
        risk_level="HIGH",
        risk_description="影响交期",
        impact_summary="有中等以上影响",
        remark="优先处理",
    )

    assert request.affected_milestones[0].delay_days == 5
    assert request.cost_breakdown.description == "返工和替换"
    assert request.risk_level == "HIGH"


def test_execute_and_response_models():
    execute = ExecuteLinkageRequest(impact_id=1)
    response = ProjectChangeImpactResponse(
        id=1,
        ecn_id=10,
        ecn_no="ECN-001",
        project_id=20,
        rework_cost=Decimal("100.00"),
        scrap_cost=Decimal("20.00"),
        additional_cost=Decimal("30.00"),
        total_cost_impact=Decimal("150.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert execute.update_milestones is True
    assert execute.record_costs is True
    assert execute.create_risk is True
    assert response.schedule_impact_days == 0
    assert response.risk_level == "LOW"
    assert response.milestones_updated is False
    assert response.costs_recorded is False
    assert response.risk_created is False
    assert response.status == "ASSESSED"


def test_list_summary_and_report_models():
    item = ProjectChangeImpactListResponse(
        id=1,
        ecn_id=10,
        ecn_no="ECN-001",
        project_id=20,
        created_at=datetime.now(),
    )
    summary = ProjectChangeSummary(project_id=20, impacts=[item])
    report = ImpactAssessmentReport(
        ecn_id=10,
        ecn_no="ECN-001",
        project_id=20,
        impact_summary="建议审批",
    )

    assert item.schedule_impact_days == 0
    assert item.total_cost_impact == 0
    assert item.risk_level == "LOW"
    assert item.status == "ASSESSED"
    assert summary.total_ecn_count == 0
    assert summary.assessed_count == 0
    assert summary.executing_count == 0
    assert summary.completed_count == 0
    assert summary.total_delay_days == 0
    assert summary.total_cost_impact == 0
    assert summary.high_risk_count == 0
    assert summary.impacts[0].ecn_no == "ECN-001"
    assert report.schedule_impact_days == 0
    assert report.affected_milestone_count == 0
    assert report.total_cost_impact == 0
    assert report.risk_level == "LOW"
    assert report.recommendation is None
    assert report.impact_record_id is None
