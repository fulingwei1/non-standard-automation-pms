from datetime import date, datetime
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from pydantic import ValidationError

_MODULE_PATH = Path(__file__).resolve().parents[2] / "app/schemas/project_review.py"
_SPEC = spec_from_file_location("app.schemas._project_review_flat", _MODULE_PATH)
project_review_flat = module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(project_review_flat)

BestPracticeRecommendationRequest = project_review_flat.BestPracticeRecommendationRequest
BestPracticeRecommendationResponse = project_review_flat.BestPracticeRecommendationResponse
LessonStatisticsResponse = project_review_flat.LessonStatisticsResponse
ProjectBestPracticeCreate = project_review_flat.ProjectBestPracticeCreate
ProjectBestPracticeResponse = project_review_flat.ProjectBestPracticeResponse
ProjectBestPracticeUpdate = project_review_flat.ProjectBestPracticeUpdate
ProjectLessonCreate = project_review_flat.ProjectLessonCreate
ProjectLessonResponse = project_review_flat.ProjectLessonResponse
ProjectLessonUpdate = project_review_flat.ProjectLessonUpdate
ProjectReviewCreate = project_review_flat.ProjectReviewCreate
ProjectReviewResponse = project_review_flat.ProjectReviewResponse
ProjectReviewUpdate = project_review_flat.ProjectReviewUpdate


def test_project_review_create_defaults_and_validation():
    model = ProjectReviewCreate(
        project_id=1,
        review_date=date.today(),
        reviewer_id=2,
        reviewer_name="张三",
    )

    assert model.review_type == "POST_MORTEM"
    assert model.quality_issues == 0
    assert model.change_count == 0
    assert model.status == "DRAFT"

    with pytest.raises(ValidationError):
        ProjectReviewCreate(
            project_id=1,
            review_date=date.today(),
            reviewer_id=2,
            reviewer_name="张三",
            customer_satisfaction=6,
        )


def test_project_review_update_and_response_models():
    update = ProjectReviewUpdate(
        review_type="MID_TERM",
        customer_satisfaction=5,
        reviewer_name="李四",
        participant_names="张三,李四",
    )
    response = ProjectReviewResponse(
        id=1,
        review_no="PR-001",
        project_id=1,
        project_code="PJ-001",
        review_date=date.today(),
        review_type="POST_MORTEM",
        budget_amount=Decimal("1000.50"),
        actual_cost=Decimal("900.25"),
        reviewer_id=2,
        reviewer_name="张三",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert update.customer_satisfaction == 5
    assert response.status == "DRAFT"
    assert response.quality_issues == 0
    assert response.change_count == 0

    with pytest.raises(ValidationError):
        ProjectReviewUpdate(customer_satisfaction=0)


def test_project_lesson_models():
    create = ProjectLessonCreate(
        review_id=1,
        project_id=1,
        lesson_type="SUCCESS",
        title="经验总结",
        description="描述内容",
    )
    update = ProjectLessonUpdate(
        title="更新标题",
        responsible_person="王五",
        priority="HIGH",
        status="RESOLVED",
        resolved_date=date.today(),
    )
    response = ProjectLessonResponse(
        id=1,
        review_id=1,
        project_id=1,
        lesson_type="FAILURE",
        title="教训",
        description="问题描述",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert create.priority == "MEDIUM"
    assert create.status == "OPEN"
    assert update.priority == "HIGH"
    assert response.priority == "MEDIUM"
    assert response.status == "OPEN"


def test_project_best_practice_models():
    create = ProjectBestPracticeCreate(
        review_id=1,
        project_id=1,
        title="最佳实践",
        description="实践描述",
    )
    update = ProjectBestPracticeUpdate(
        title="更新实践",
        category="技术",
        is_reusable=False,
        validation_status="VALIDATED",
        validation_date=date.today(),
        validated_by=9,
    )
    response = ProjectBestPracticeResponse(
        id=1,
        review_id=1,
        project_id=1,
        title="最佳实践",
        description="实践描述",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert create.is_reusable is True
    assert create.validation_status == "PENDING"
    assert update.validation_status == "VALIDATED"
    assert response.validation_status == "PENDING"
    assert response.reuse_count == 0
    assert response.status == "ACTIVE"


def test_statistics_and_recommendation_models():
    stats = LessonStatisticsResponse(
        total=10,
        success_count=6,
        failure_count=4,
        resolved_count=7,
        unresolved_count=3,
        overdue_count=1,
    )
    request = BestPracticeRecommendationRequest()
    practice = ProjectBestPracticeResponse(
        id=1,
        review_id=1,
        project_id=1,
        title="最佳实践",
        description="实践描述",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    response = BestPracticeRecommendationResponse(
        practice=practice,
        match_score=0.92,
    )

    assert stats.by_category == {}
    assert stats.by_status == {}
    assert stats.by_priority == {}
    assert request.limit == 10
    assert response.match_reasons == []

    with pytest.raises(ValidationError):
        BestPracticeRecommendationRequest(limit=0)

    with pytest.raises(ValidationError):
        BestPracticeRecommendationRequest(limit=51)
