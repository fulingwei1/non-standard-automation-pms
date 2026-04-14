from decimal import Decimal

import pytest

from app.models.project.labor_cost_detail import (
    LaborCostStatusEnum,
    ProjectLaborCostDetail,
    ProjectLaborCostSummary,
    WorkTypeEnum,
)


@pytest.mark.unit
def test_project_labor_cost_detail_metadata_and_enums():
    assert WorkTypeEnum.DESIGN.value == "DESIGN"
    assert WorkTypeEnum.SUPPORT.value == "SUPPORT"
    assert LaborCostStatusEnum.ESTIMATED.value == "ESTIMATED"
    assert LaborCostStatusEnum.CANCELLED.value == "CANCELLED"

    assert ProjectLaborCostDetail.__tablename__ == "project_labor_cost_details"
    assert ProjectLaborCostDetail.__table__.comment == "项目劳动力成本明细表"

    index_names = {index.name for index in ProjectLaborCostDetail.__table__.indexes}
    assert index_names == {
        "idx_labor_cost_project",
        "idx_labor_cost_machine",
        "idx_labor_cost_work_type",
        "idx_labor_cost_engineer",
        "idx_labor_cost_status",
    }


@pytest.mark.unit
def test_project_labor_cost_detail_calculate_costs_handles_full_formula():
    detail = ProjectLaborCostDetail(project_id=7, work_type=WorkTypeEnum.INSTALLATION.value)
    detail.estimated_hours = Decimal("10.00")
    detail.actual_hours = Decimal("12.50")
    detail.hourly_rate = Decimal("100.00")
    detail.overtime_hours = Decimal("3.00")
    detail.overtime_rate = Decimal("2.00")
    detail.travel_cost = Decimal("88.00")

    detail.calculate_costs()

    assert detail.estimated_cost == Decimal("1000.0000")
    assert detail.overtime_cost == Decimal("300.000000")
    assert detail.actual_cost == Decimal("1638.000000")
    assert detail.variance_hours == Decimal("2.50")
    assert detail.variance_cost == Decimal("638.000000")
    assert repr(detail) == "<ProjectLaborCostDetail 7: INSTALLATION>"


@pytest.mark.unit
def test_project_labor_cost_detail_calculate_costs_defaults_missing_values_to_zero():
    detail = ProjectLaborCostDetail(project_id=3, work_type=WorkTypeEnum.OTHER.value)
    detail.estimated_hours = None
    detail.actual_hours = None
    detail.hourly_rate = None
    detail.overtime_hours = None
    detail.overtime_rate = None
    detail.travel_cost = None

    detail.calculate_costs()

    assert detail.estimated_cost == 0
    assert detail.overtime_cost == 0.0
    assert detail.actual_cost == 0.0
    assert detail.variance_hours == 0
    assert detail.variance_cost == 0.0


@pytest.mark.unit
def test_project_labor_cost_summary_metadata_and_repr():
    summary = ProjectLaborCostSummary(project_id=11, work_type=WorkTypeEnum.DEBUG.value)

    assert ProjectLaborCostSummary.__tablename__ == "project_labor_cost_summaries"
    assert ProjectLaborCostSummary.__table__.comment == "项目劳动力成本汇总表"
    assert repr(summary) == "<ProjectLaborCostSummary 11: DEBUG>"

    indexes = {index.name: index for index in ProjectLaborCostSummary.__table__.indexes}
    assert set(indexes) == {
        "idx_labor_summary_project",
        "idx_labor_summary_work_type",
        "idx_labor_summary_unique",
    }
    assert indexes["idx_labor_summary_unique"].unique is True
