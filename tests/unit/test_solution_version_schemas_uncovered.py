from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.sales.solution_version import (
    ApprovalRequest,
    BindingIssueResponse,
    BindingValidationResponse,
    CostSyncResponse,
    ImpactCheckResponse,
    SolutionVersionCreate,
    SolutionVersionListResponse,
    SolutionVersionResponse,
    SolutionVersionUpdate,
    VersionCompareResponse,
)


def test_solution_version_create_update_and_approval_models():
    create = SolutionVersionCreate(
        generated_solution={"summary": "方案A"},
        change_reason="客户新增要求",
        confidence_score=Decimal("0.85"),
        quality_score=Decimal("4.5"),
    )
    update = SolutionVersionUpdate(change_summary="补充接口定义")
    approval = ApprovalRequest(action="approve", comments="可以发布")

    assert create.generated_solution["summary"] == "方案A"
    assert create.change_reason == "客户新增要求"
    assert update.change_summary == "补充接口定义"
    assert approval.action == "approve"

    with pytest.raises(ValidationError):
        SolutionVersionCreate(confidence_score=Decimal("1.1"))

    with pytest.raises(ValidationError):
        SolutionVersionCreate(quality_score=Decimal("5.1"))


def test_solution_version_response_models():
    now = datetime.now()
    response = SolutionVersionResponse(
        id=1,
        solution_id=10,
        version_no="V1.0",
        generated_solution={"summary": "方案A"},
        architecture_diagram="graph TD",
        bom_list={"items": 3},
        solution_description="完整方案",
        status="draft",
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    list_item = SolutionVersionListResponse(
        id=1,
        solution_id=10,
        version_no="V1.0",
        status="approved",
        change_summary="成本优化",
        created_at=now,
        created_by=7,
    )
    compare = VersionCompareResponse(
        version_1={"version": "V1.0"},
        version_2={"version": "V2.0"},
        differences={"bom": "changed"},
        has_differences=True,
    )

    assert response.version_no == "V1.0"
    assert response.status == "draft"
    assert list_item.change_summary == "成本优化"
    assert compare.has_differences is True


def test_binding_impact_and_cost_sync_models():
    now = datetime.now()
    issue = BindingIssueResponse(
        level="warning",
        code="OUTDATED",
        message="版本已过期",
        details={"latest": "V2.0"},
    )
    binding = BindingValidationResponse(
        quote_version_id=88,
        status="outdated",
        issues=[issue],
        validated_at=now,
        is_valid=False,
    )
    impact = ImpactCheckResponse(
        affected_items=[{"type": "quote", "id": 1}],
        total_count=1,
    )
    sync = CostSyncResponse(
        quote_version_id=88,
        cost_total=Decimal("1000.50"),
        gross_margin=Decimal("0.25"),
        binding_status="valid",
        synced_at=now,
    )

    assert binding.issues[0].code == "OUTDATED"
    assert binding.is_valid is False
    assert impact.total_count == 1
    assert sync.cost_total == Decimal("1000.50")
    assert sync.binding_status == "valid"
