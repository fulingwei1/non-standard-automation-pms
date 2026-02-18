# -*- coding: utf-8 -*-
"""第二十五批 - project_review_ai/knowledge_syncer 单元测试"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.project_review_ai.knowledge_syncer")

from app.services.project_review_ai.knowledge_syncer import ProjectKnowledgeSyncer


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def syncer(db):
    with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
        svc = ProjectKnowledgeSyncer(db)
    return svc


def _make_review(review_id=1):
    review = MagicMock()
    review.id = review_id
    review.budget_amount = 500000
    review.success_factors = "成功因素：团队协作良好，需求管理规范"
    review.problems = "问题：进度管理不足，导致轻微延期"
    review.best_practices = "最佳实践：每周回顾，持续改进"
    review.conclusion = "总体来看，项目达成了预定目标"
    review.ai_summary = "AI摘要内容"
    review.customer_satisfaction = 4
    review.schedule_variance = -2
    review.cost_variance = 10000
    review.change_count = 2

    project = MagicMock()
    project.code = "P0001"
    project.name = "测试项目"
    project.customer = MagicMock(name="客户公司")
    project.project_type = "NON_STANDARD"
    project.industry = "制造业"

    review.project = project
    return review


# ── _extract_tags ─────────────────────────────────────────────────────────────

class TestExtractTags:
    def test_adds_industry_tag(self, syncer):
        review = _make_review()
        review.project.industry = "汽车"
        tags = syncer._extract_tags(review, review.project)
        assert "汽车" in tags

    def test_adds_project_type_tag(self, syncer):
        review = _make_review()
        review.project.project_type = "非标"
        tags = syncer._extract_tags(review, review.project)
        assert "非标" in tags

    def test_small_project_tag(self, syncer):
        review = _make_review()
        review.budget_amount = 200000
        tags = syncer._extract_tags(review, review.project)
        assert "小型项目" in tags

    def test_medium_project_tag(self, syncer):
        review = _make_review()
        review.budget_amount = 800000
        tags = syncer._extract_tags(review, review.project)
        assert "中型项目" in tags

    def test_large_project_tag(self, syncer):
        review = _make_review()
        review.budget_amount = 5000000
        tags = syncer._extract_tags(review, review.project)
        assert "大型项目" in tags

    def test_high_satisfaction_tag(self, syncer):
        review = _make_review()
        review.customer_satisfaction = 5
        tags = syncer._extract_tags(review, review.project)
        assert "高满意度" in tags

    def test_medium_satisfaction_tag(self, syncer):
        review = _make_review()
        review.customer_satisfaction = 3
        tags = syncer._extract_tags(review, review.project)
        assert "中等满意度" in tags

    def test_on_time_delivery_tag(self, syncer):
        review = _make_review()
        review.schedule_variance = -1  # 提前完成 → 也是按期/提前
        tags = syncer._extract_tags(review, review.project)
        assert "按期交付" in tags

    def test_slight_delay_tag(self, syncer):
        review = _make_review()
        review.schedule_variance = 5
        tags = syncer._extract_tags(review, review.project)
        assert "轻微延期" in tags

    def test_significant_delay_tag(self, syncer):
        review = _make_review()
        review.schedule_variance = 15
        tags = syncer._extract_tags(review, review.project)
        assert "显著延期" in tags

    def test_tags_deduplicated(self, syncer):
        review = _make_review()
        tags = syncer._extract_tags(review, review.project)
        assert len(tags) == len(set(tags))


# ── _calculate_quality_score ──────────────────────────────────────────────────

class TestCalculateQualityScore:
    def test_base_score_at_least_half(self, syncer):
        review = MagicMock()
        review.customer_satisfaction = None
        review.schedule_variance = None
        review.cost_variance = None
        review.budget_amount = None
        review.change_count = None
        review.success_factors = ""
        review.problems = ""
        review.best_practices = ""
        review.conclusion = ""
        score = syncer._calculate_quality_score(review)
        assert score >= 0.5

    def test_perfect_project_high_score(self, syncer):
        review = MagicMock()
        review.customer_satisfaction = 5
        review.schedule_variance = -1  # ahead of schedule
        review.cost_variance = 1000
        review.budget_amount = 1000000  # <5% variance
        review.change_count = 1
        review.success_factors = "a" * 100
        review.problems = "b" * 100
        review.best_practices = "c" * 100
        review.conclusion = "d" * 100
        score = syncer._calculate_quality_score(review)
        assert score > 0.8

    def test_score_between_0_and_1(self, syncer):
        review = _make_review()
        score = syncer._calculate_quality_score(review)
        assert 0.0 <= score <= 1.0

    def test_no_customer_satisfaction_does_not_add_score(self, syncer):
        review = MagicMock()
        review.customer_satisfaction = None
        review.schedule_variance = None
        review.cost_variance = None
        review.budget_amount = None
        review.change_count = None
        review.success_factors = ""
        review.problems = ""
        review.best_practices = ""
        review.conclusion = ""
        score_no_sat = syncer._calculate_quality_score(review)

        review2 = MagicMock()
        review2.customer_satisfaction = 5
        review2.schedule_variance = None
        review2.cost_variance = None
        review2.budget_amount = None
        review2.change_count = None
        review2.success_factors = ""
        review2.problems = ""
        review2.best_practices = ""
        review2.conclusion = ""
        score_with_sat = syncer._calculate_quality_score(review2)
        assert score_with_sat > score_no_sat


# ── _extract_technical_highlights ────────────────────────────────────────────

class TestExtractTechnicalHighlights:
    def test_returns_empty_when_no_best_practices(self, syncer):
        review = MagicMock()
        review.best_practices = None
        result = syncer._extract_technical_highlights(review)
        assert result == ""

    def test_returns_short_text_as_is(self, syncer):
        review = MagicMock()
        review.best_practices = "短文本"
        result = syncer._extract_technical_highlights(review)
        assert result == "短文本"

    def test_truncates_long_text(self, syncer):
        review = MagicMock()
        review.best_practices = "x" * 500
        result = syncer._extract_technical_highlights(review)
        assert len(result) <= 303  # 300 chars + "..."
        assert result.endswith("...")

    def test_exactly_300_chars_not_truncated(self, syncer):
        review = MagicMock()
        review.best_practices = "y" * 300
        result = syncer._extract_technical_highlights(review)
        assert result == "y" * 300
        assert not result.endswith("...")


# ── _parse_summary_response ───────────────────────────────────────────────────

class TestParseSummaryResponse:
    def test_parses_valid_json(self, syncer):
        ai_response = {
            "content": json.dumps({
                "summary": "项目摘要",
                "technical_highlights": "技术亮点",
                "key_success_factors": "关键因素",
                "applicable_scenarios": "适用场景",
            })
        }
        result = syncer._parse_summary_response(ai_response)
        assert result["summary"] == "项目摘要"

    def test_parses_json_code_block(self, syncer):
        content = '```json\n{"summary": "摘要内容"}\n```'
        ai_response = {"content": content}
        result = syncer._parse_summary_response(ai_response)
        assert result["summary"] == "摘要内容"

    def test_fallback_on_invalid_json(self, syncer):
        ai_response = {"content": "这是无效的JSON内容，无法解析"}
        result = syncer._parse_summary_response(ai_response)
        assert "summary" in result
        assert isinstance(result["summary"], str)

    def test_empty_content_returns_dict(self, syncer):
        ai_response = {"content": "{}"}
        result = syncer._parse_summary_response(ai_response)
        assert isinstance(result, dict)


# ── sync_to_knowledge_base ────────────────────────────────────────────────────

class TestSyncToKnowledgeBase:
    def test_raises_when_review_not_found(self, syncer, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            syncer.sync_to_knowledge_base(999)

    def test_returns_success_dict_when_review_found(self, syncer, db):
        review = _make_review(1)
        db.query.return_value.filter.return_value.first.side_effect = [
            review,       # ProjectReview query
            None,         # PresaleKnowledgeCase query (no existing)
        ]

        syncer.ai_client.generate_solution.return_value = {
            "content": '{"summary": "OK", "technical_highlights": "亮点"}',
            "token_usage": 100,
        }
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()

        # Mock PresaleKnowledgeCase constructor
        with patch("app.services.project_review_ai.knowledge_syncer.PresaleKnowledgeCase") as MockCase:
            mock_case = MagicMock()
            mock_case.id = 10
            mock_case.case_name = "P0001 - 测试项目"
            mock_case.quality_score = 0.8
            MockCase.return_value = mock_case
            db.refresh.side_effect = lambda x: None

            result = syncer.sync_to_knowledge_base(1)

        assert result["success"] is True
