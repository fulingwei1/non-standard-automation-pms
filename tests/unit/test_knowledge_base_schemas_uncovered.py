from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.knowledge_base import (
    BestPracticeInductionResult,
    ExtractionRequest,
    ExtractionResult,
    KnowledgeAlertFeedback,
    KnowledgeAlertResponse,
    KnowledgeEntryCreate,
    KnowledgeEntryListResponse,
    KnowledgeEntryResponse,
    KnowledgeEntryUpdate,
    KnowledgeSearchRequest,
    PitfallAlertResult,
)


def make_entry_response() -> KnowledgeEntryResponse:
    return KnowledgeEntryResponse(
        id=1,
        entry_code="KB-001",
        knowledge_type="BEST_PRACTICE",
        source_type="REVIEW",
        title="最佳实践",
        summary="摘要",
        status="PUBLISHED",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_knowledge_entry_models_defaults_and_validation():
    create = KnowledgeEntryCreate(
        knowledge_type="RISK_RESPONSE",
        source_type="RISK",
        title="标题",
        summary="摘要",
    )
    update = KnowledgeEntryUpdate(title="更新标题", status="ARCHIVED")
    response = make_entry_response()
    list_response = KnowledgeEntryListResponse(items=[response], total=1, page=1, page_size=20)

    assert create.detail is None
    assert update.status == "ARCHIVED"
    assert response.view_count == 0
    assert response.cite_count == 0
    assert response.usefulness_score == 0.0
    assert response.vote_count == 0
    assert response.ai_generated is False
    assert list_response.items[0].entry_code == "KB-001"

    with pytest.raises(ValidationError):
        KnowledgeEntryCreate(
            knowledge_type="RISK_RESPONSE",
            source_type="RISK",
            title="x" * 301,
            summary="摘要",
        )


def test_alert_and_extraction_models():
    entry = make_entry_response()
    alert = KnowledgeAlertResponse(
        id=1,
        target_project_id=10,
        knowledge_entry_id=1,
        created_at=datetime.now(),
    )
    feedback = KnowledgeAlertFeedback(is_adopted=True, feedback="有帮助")
    request = ExtractionRequest(project_id=100)
    result = ExtractionResult(project_id=100, total_extracted=1, entries=[entry])
    induction = BestPracticeInductionResult(best_practices_generated=1, entries=[entry])
    pitfall = PitfallAlertResult(target_project_id=10, alerts_generated=1, alerts=[alert])

    assert alert.match_score == 0.0
    assert alert.is_read is False
    assert feedback.is_adopted is True
    assert request.extract_risks is True
    assert request.extract_issues is True
    assert request.extract_ecns is True
    assert request.extract_logs is True
    assert request.auto_publish is False
    assert result.risk_entries == 0
    assert result.issue_entries == 0
    assert result.change_entries == 0
    assert result.delay_entries == 0
    assert induction.total_projects_analyzed == 0
    assert induction.entries[0].status == "PUBLISHED"
    assert pitfall.alerts[0].knowledge_entry_id == 1


def test_search_request_validation():
    request = KnowledgeSearchRequest(keyword="知识")
    assert request.page == 1
    assert request.page_size == 20

    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(page=0)

    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(page_size=101)
