from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.presale_technical_parameter import (
    BatchCostEstimateRequest,
    CostBreakdownItem,
    CostEstimateRequest,
    CostEstimateResponse,
    IndustryStatistics,
    LaborHoursDetail,
    TechnicalParameterTemplateCreate,
    TechnicalParameterTemplateListItem,
    TechnicalParameterTemplateResponse,
    TechnicalParameterTemplateUpdate,
    TemplateListQuery,
    TemplateMatchQuery,
    TestTypeStatistics as PresaleTestTypeStatistics,
)


def test_template_create_update_and_response_models():
    create = TechnicalParameterTemplateCreate(
        name="ICT 标准模板",
        code="TPL-001",
        industry="电子",
        test_type="ICT",
    )
    update = TechnicalParameterTemplateUpdate(name="新模板", is_active=False)
    response = TechnicalParameterTemplateResponse(
        id=1,
        name="ICT 标准模板",
        code="TPL-001",
        industry="电子",
        test_type="ICT",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    item = TechnicalParameterTemplateListItem(
        id=1,
        name="ICT 标准模板",
        code="TPL-001",
        industry="电子",
        test_type="ICT",
        created_at=datetime.now(),
    )

    assert create.parameters == {}
    assert create.cost_factors == {}
    assert create.typical_labor_hours == {}
    assert create.reference_docs == []
    assert create.sample_images == []
    assert update.is_active is False
    assert response.use_count == 0
    assert response.is_active is True
    assert item.use_count == 0

    with pytest.raises(ValidationError):
        TechnicalParameterTemplateCreate(
            name="",
            code="TPL-001",
            industry="电子",
            test_type="ICT",
        )


def test_cost_estimate_and_statistics_models():
    request = CostEstimateRequest(template_id=1, parameters={"stations": 4})
    breakdown = {
        "ME": CostBreakdownItem(ratio=0.4, amount=4000.0),
        "EE": CostBreakdownItem(ratio=0.6, amount=6000.0),
    }
    labor = LaborHoursDetail(detail={"design": 10, "debug": 8}, total=18)
    response = CostEstimateResponse(
        template_id=1,
        template_name="ICT 标准模板",
        template_code="TPL-001",
        base_cost=8000.0,
        adjustment=2000.0,
        total_cost=10000.0,
        cost_breakdown=breakdown,
        labor_hours=labor,
        parameters_used={"stations": 4},
        estimated_at="2026-04-14T03:40:00",
    )
    batch = BatchCostEstimateRequest(industry="电子", test_type="ICT", parameters={"stations": 6})
    industry_stats = IndustryStatistics(industry="电子", template_count=3, total_usage=20)
    type_stats = PresaleTestTypeStatistics(test_type="ICT", template_count=2, total_usage=15)

    assert request.parameters["stations"] == 4
    assert response.cost_breakdown["ME"].amount == 4000.0
    assert response.labor_hours.total == 18
    assert batch.test_type == "ICT"
    assert industry_stats.total_usage == 20
    assert type_stats.template_count == 2


def test_query_models_validation():
    query = TemplateListQuery(keyword="ICT")
    match = TemplateMatchQuery(industry="电子", test_type="ICT")

    assert query.is_active is True
    assert query.page == 1
    assert query.page_size == 20
    assert match.top_k == 5

    with pytest.raises(ValidationError):
        TemplateListQuery(page=0)

    with pytest.raises(ValidationError):
        TemplateListQuery(page_size=101)

    with pytest.raises(ValidationError):
        TemplateMatchQuery(industry="电子", test_type="ICT", top_k=21)
