# -*- coding: utf-8 -*-
"""第十五批: lesson_extractor 单元测试"""
import pytest

pytest.importorskip("app.services.project_review_ai.lesson_extractor")

from unittest.mock import MagicMock, patch
import json
from app.services.project_review_ai.lesson_extractor import ProjectLessonExtractor


def make_db():
    return MagicMock()


def test_extract_lessons_review_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    with patch("app.services.project_review_ai.lesson_extractor.AIClientService"):
        svc = ProjectLessonExtractor(db)
        with pytest.raises(ValueError, match="不存在"):
            svc.extract_lessons(99)


def _make_ai_response(lessons_data):
    """Build the expected dict format: {'content': '[...]'}"""
    import json
    return {"content": json.dumps(lessons_data)}


def test_extract_lessons_filters_low_confidence():
    db = make_db()
    review = MagicMock()
    review.project_code = "PJ001"
    review.review_type = "阶段复盘"
    review.schedule_variance = 5
    review.cost_variance = 1000
    review.change_count = 2
    review.customer_satisfaction = 4
    review.success_factors = "good team"
    review.failure_factors = "bad planning"
    review.improvement_suggestions = "improve"
    db.query.return_value.filter.return_value.first.return_value = review

    # Note: parser reads 'confidence' key from raw data, outputs 'ai_confidence'
    lessons_data = [
        {"confidence": 0.8, "lesson_type": "success", "title": "Good"},
        {"confidence": 0.3, "lesson_type": "failure", "title": "Bad"},
    ]

    with patch("app.services.project_review_ai.lesson_extractor.AIClientService") as MockAI:
        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_solution.return_value = _make_ai_response(lessons_data)
        MockAI.return_value = mock_ai_instance
        svc = ProjectLessonExtractor(db)
        result = svc.extract_lessons(1, min_confidence=0.6)
        assert len(result) == 1
        assert result[0]["ai_confidence"] == 0.8


def test_extract_lessons_empty_response():
    db = make_db()
    review = MagicMock()
    review.project_code = "PJ002"
    review.review_type = "项目复盘"
    review.schedule_variance = 0
    review.cost_variance = 0
    review.change_count = 0
    review.customer_satisfaction = 5
    review.success_factors = ""
    review.failure_factors = ""
    review.improvement_suggestions = ""
    db.query.return_value.filter.return_value.first.return_value = review

    with patch("app.services.project_review_ai.lesson_extractor.AIClientService") as MockAI:
        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_solution.return_value = _make_ai_response([])
        MockAI.return_value = mock_ai_instance
        svc = ProjectLessonExtractor(db)
        result = svc.extract_lessons(1)
        assert result == []


def test_extract_lessons_all_pass():
    db = make_db()
    review = MagicMock()
    review.project_code = "PJ003"
    review.review_type = "里程碑复盘"
    review.schedule_variance = -2
    review.cost_variance = -500
    review.change_count = 1
    review.customer_satisfaction = 5
    review.success_factors = "great"
    review.failure_factors = "none"
    review.improvement_suggestions = "keep up"
    db.query.return_value.filter.return_value.first.return_value = review

    lessons_data = [
        {"confidence": 0.9, "lesson_type": "success", "title": "Excellent"},
        {"confidence": 0.7, "lesson_type": "process", "title": "Good Process"},
    ]

    with patch("app.services.project_review_ai.lesson_extractor.AIClientService") as MockAI:
        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_solution.return_value = _make_ai_response(lessons_data)
        MockAI.return_value = mock_ai_instance
        svc = ProjectLessonExtractor(db)
        result = svc.extract_lessons(1, min_confidence=0.5)
        assert len(result) == 2


def test_build_extraction_prompt_contains_project_code():
    db = make_db()
    review = MagicMock()
    review.project_code = "TEST-123"
    review.review_type = "阶段"
    review.schedule_variance = 10
    review.cost_variance = 2000
    review.change_count = 3
    review.customer_satisfaction = 3
    review.success_factors = "ok"
    review.failure_factors = "bad"
    review.improvement_suggestions = "fix"

    with patch("app.services.project_review_ai.lesson_extractor.AIClientService"):
        svc = ProjectLessonExtractor(db)
        prompt = svc._build_extraction_prompt(review)
        assert "TEST-123" in prompt
