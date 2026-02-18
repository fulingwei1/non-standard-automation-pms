# -*- coding: utf-8 -*-
"""第二十八批 - knowledge_syncer 单元测试（项目知识库同步服务）"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.project_review_ai.knowledge_syncer")

from app.services.project_review_ai.knowledge_syncer import ProjectKnowledgeSyncer


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_review(
    review_id=1,
    project_code="P-001",
    budget_amount=Decimal("1000000"),
    customer_satisfaction=4,
    schedule_variance=0,
    cost_variance=Decimal("50000"),
    change_count=2,
    success_factors="成功因素" * 20,
    problems="问题教训" * 20,
    best_practices="最佳实践" * 20,
    conclusion="结论" * 20,
    ai_summary=None,
):
    r = MagicMock()
    r.id = review_id
    r.project_code = project_code
    r.budget_amount = budget_amount
    r.customer_satisfaction = customer_satisfaction
    r.schedule_variance = schedule_variance
    r.cost_variance = cost_variance
    r.change_count = change_count
    r.success_factors = success_factors
    r.problems = problems
    r.best_practices = best_practices
    r.conclusion = conclusion
    r.ai_summary = ai_summary

    project = MagicMock()
    project.code = project_code
    project.name = "测试项目"
    customer = MagicMock()
    customer.name = "测试客户"
    project.customer = customer
    r.project = project

    return r


# ─── _calculate_quality_score ────────────────────────────────

class TestCalculateQualityScore:

    def setup_method(self):
        db = MagicMock()
        with patch(
            "app.services.project_review_ai.knowledge_syncer.AIClientService"
        ):
            self.syncer = ProjectKnowledgeSyncer(db)

    def test_base_score_without_any_data(self):
        review = MagicMock()
        review.customer_satisfaction = None
        review.schedule_variance = None
        review.cost_variance = None
        review.budget_amount = None
        review.change_count = None
        review.success_factors = None
        review.problems = None
        review.best_practices = None
        review.conclusion = None

        score = self.syncer._calculate_quality_score(review)
        assert score == pytest.approx(0.5, abs=0.01)

    def test_max_score_with_perfect_data(self):
        review = _make_review(
            customer_satisfaction=5,
            schedule_variance=0,
            cost_variance=Decimal("10000"),
            budget_amount=Decimal("1000000"),
            change_count=1,
        )
        score = self.syncer._calculate_quality_score(review)
        assert score > 0.9

    def test_score_clipped_to_one(self):
        """分数不超过 1.0"""
        review = _make_review(
            customer_satisfaction=5,
            schedule_variance=-5,
            cost_variance=Decimal("0"),
            budget_amount=Decimal("1000000"),
            change_count=0,
        )
        score = self.syncer._calculate_quality_score(review)
        assert score <= 1.0

    def test_score_clipped_to_zero(self):
        """分数不低于 0.0"""
        review = MagicMock()
        review.customer_satisfaction = 0
        review.schedule_variance = 100
        review.cost_variance = Decimal("999999")
        review.budget_amount = Decimal("1")
        review.change_count = 100
        review.success_factors = ""
        review.problems = ""
        review.best_practices = ""
        review.conclusion = ""

        score = self.syncer._calculate_quality_score(review)
        assert score >= 0.0

    def test_on_time_delivery_adds_score(self):
        review_on_time = _make_review(schedule_variance=0, customer_satisfaction=None)
        review_on_time.customer_satisfaction = None
        review_on_time.cost_variance = None
        review_on_time.change_count = None
        review_on_time.success_factors = None
        review_on_time.problems = None
        review_on_time.best_practices = None
        review_on_time.conclusion = None

        review_late = MagicMock()
        review_late.customer_satisfaction = None
        review_late.schedule_variance = 30
        review_late.cost_variance = None
        review_late.budget_amount = None
        review_late.change_count = None
        review_late.success_factors = None
        review_late.problems = None
        review_late.best_practices = None
        review_late.conclusion = None

        score_on_time = self.syncer._calculate_quality_score(review_on_time)
        score_late = self.syncer._calculate_quality_score(review_late)
        assert score_on_time > score_late


# ─── _extract_tags ───────────────────────────────────────────

class TestExtractTags:

    def setup_method(self):
        db = MagicMock()
        with patch(
            "app.services.project_review_ai.knowledge_syncer.AIClientService"
        ):
            self.syncer = ProjectKnowledgeSyncer(db)

    def _make_project(self, industry=None, project_type=None):
        p = MagicMock()
        p.industry = industry
        p.project_type = project_type
        return p

    def test_includes_industry_tag(self):
        review = _make_review()
        review.customer_satisfaction = 4
        review.schedule_variance = 0
        review.cost_variance = None
        project = self._make_project(industry="制造业")
        tags = self.syncer._extract_tags(review, project)
        assert "制造业" in tags

    def test_large_project_tag(self):
        review = _make_review(budget_amount=Decimal("3000000"))
        review.customer_satisfaction = None
        review.schedule_variance = None
        review.cost_variance = None
        project = self._make_project()
        tags = self.syncer._extract_tags(review, project)
        assert "大型项目" in tags

    def test_small_project_tag(self):
        review = _make_review(budget_amount=Decimal("200000"))
        review.customer_satisfaction = None
        review.schedule_variance = None
        review.cost_variance = None
        project = self._make_project()
        tags = self.syncer._extract_tags(review, project)
        assert "小型项目" in tags

    def test_on_time_delivery_tag(self):
        review = _make_review(schedule_variance=0)
        review.customer_satisfaction = None
        review.cost_variance = None
        project = self._make_project()
        tags = self.syncer._extract_tags(review, project)
        assert "按期交付" in tags

    def test_high_satisfaction_tag(self):
        review = _make_review(customer_satisfaction=5)
        review.schedule_variance = None
        review.cost_variance = None
        project = self._make_project()
        tags = self.syncer._extract_tags(review, project)
        assert "高满意度" in tags

    def test_tags_are_unique(self):
        review = _make_review(budget_amount=Decimal("1000000"), customer_satisfaction=4)
        review.schedule_variance = None
        review.cost_variance = None
        project = self._make_project(industry="制造业", project_type="自动化")
        tags = self.syncer._extract_tags(review, project)
        assert len(tags) == len(set(tags))


# ─── _parse_summary_response ─────────────────────────────────

class TestParseSummaryResponse:

    def setup_method(self):
        db = MagicMock()
        with patch(
            "app.services.project_review_ai.knowledge_syncer.AIClientService"
        ):
            self.syncer = ProjectKnowledgeSyncer(db)

    def test_parses_valid_json(self):
        import json
        payload = {"summary": "摘要内容", "technical_highlights": "技术亮点"}
        ai_response = {"content": json.dumps(payload)}
        result = self.syncer._parse_summary_response(ai_response)
        assert result["summary"] == "摘要内容"

    def test_parses_json_wrapped_in_markdown(self):
        import json
        payload = {"summary": "摘要", "technical_highlights": "亮点"}
        content = f"```json\n{json.dumps(payload)}\n```"
        ai_response = {"content": content}
        result = self.syncer._parse_summary_response(ai_response)
        assert result["summary"] == "摘要"

    def test_fallback_on_invalid_json(self):
        ai_response = {"content": "非JSON内容，长度超过预期的文本描述"}
        result = self.syncer._parse_summary_response(ai_response)
        assert "summary" in result
        assert len(result["summary"]) > 0

    def test_empty_content_returns_empty_summary(self):
        ai_response = {"content": "{}"}
        result = self.syncer._parse_summary_response(ai_response)
        assert isinstance(result, dict)


# ─── get_sync_status ─────────────────────────────────────────

class TestGetSyncStatus:

    def setup_method(self):
        db = MagicMock()
        with patch(
            "app.services.project_review_ai.knowledge_syncer.AIClientService"
        ):
            self.syncer = ProjectKnowledgeSyncer(db)
            self.syncer.db = MagicMock()

    def test_returns_not_synced_when_review_not_found(self):
        self.syncer.db.query.return_value.filter.return_value.first.return_value = None
        result = self.syncer.get_sync_status(review_id=99)
        assert result["synced"] is False
        assert "error" in result

    def test_returns_synced_false_when_case_not_found(self):
        review = _make_review()
        # First query: review found; second: case not found
        self.syncer.db.query.return_value.filter.return_value.first.side_effect = [review, None]
        result = self.syncer.get_sync_status(review_id=1)
        assert result["synced"] is False
        assert "message" in result

    def test_returns_synced_true_when_case_found(self):
        review = _make_review()
        case = MagicMock()
        case.id = 5
        case.case_name = "P-001 - 测试项目"
        case.quality_score = Decimal("0.85")
        case.updated_at = datetime(2024, 6, 1)
        case.tags = ["大型项目", "制造业"]

        self.syncer.db.query.return_value.filter.return_value.first.side_effect = [review, case]
        result = self.syncer.get_sync_status(review_id=1)
        assert result["synced"] is True
        assert result["case_id"] == 5
        assert result["quality_score"] == pytest.approx(0.85, abs=0.001)
