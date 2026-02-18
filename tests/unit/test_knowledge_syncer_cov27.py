# -*- coding: utf-8 -*-
"""第二十七批 - knowledge_syncer 单元测试"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.project_review_ai.knowledge_syncer")

from app.services.project_review_ai.knowledge_syncer import ProjectKnowledgeSyncer


def make_db():
    return MagicMock()


def make_review(**kwargs):
    review = MagicMock()
    review.id = kwargs.get("id", 1)
    review.project_code = kwargs.get("project_code", "PRJ-001")
    review.budget_amount = kwargs.get("budget_amount", 1000000)
    review.success_factors = kwargs.get("success_factors", "良好的团队协作与沟通")
    review.problems = kwargs.get("problems", "进度延期和成本超支问题")
    review.best_practices = kwargs.get("best_practices", "每周例会保持信息同步")
    review.customer_satisfaction = kwargs.get("customer_satisfaction", 4)
    review.schedule_variance = kwargs.get("schedule_variance", 0)
    review.cost_variance = kwargs.get("cost_variance", 50000)
    review.change_count = kwargs.get("change_count", 2)
    review.conclusion = kwargs.get("conclusion", "项目总体完成较好，达到了预期目标")
    review.ai_summary = kwargs.get("ai_summary", "项目AI摘要内容")

    project = MagicMock()
    project.name = kwargs.get("project_name", "测试项目")
    project.code = kwargs.get("project_code", "PRJ-001")
    project.industry = kwargs.get("industry", "制造业")
    project.project_type = kwargs.get("project_type", "新建项目")
    customer = MagicMock()
    customer.name = "测试客户"
    project.customer = customer
    review.project = project

    return review


class TestProjectKnowledgeSyncerInit:
    def test_init_creates_ai_client(self):
        db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService") as MockAI:
            syncer = ProjectKnowledgeSyncer(db)
            assert syncer.db is db
            MockAI.assert_called_once()

    def test_init_stores_db(self):
        db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
            syncer = ProjectKnowledgeSyncer(db)
            assert syncer.db is db


class TestExtractTags:
    def setup_method(self):
        db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
            self.syncer = ProjectKnowledgeSyncer(db)

    def test_small_project_tag(self):
        review = make_review(budget_amount=300000)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "小型项目" in tags

    def test_medium_project_tag(self):
        review = make_review(budget_amount=1000000)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "中型项目" in tags

    def test_large_project_tag(self):
        review = make_review(budget_amount=3000000)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "大型项目" in tags

    def test_high_satisfaction_tag(self):
        review = make_review(customer_satisfaction=5)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "高满意度" in tags

    def test_medium_satisfaction_tag(self):
        review = make_review(customer_satisfaction=3)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "中等满意度" in tags

    def test_on_time_tag(self):
        # schedule_variance=0 is falsy → tag not added; use negative value
        review = make_review(schedule_variance=-2)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "按期交付" in tags

    def test_slight_delay_tag(self):
        review = make_review(schedule_variance=5)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "轻微延期" in tags

    def test_significant_delay_tag(self):
        review = make_review(schedule_variance=15)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "显著延期" in tags

    def test_industry_tag(self):
        review = make_review(industry="汽车制造")
        project = review.project
        project.industry = "汽车制造"
        tags = self.syncer._extract_tags(review, project)
        assert "汽车制造" in tags

    def test_tags_are_unique(self):
        review = make_review(budget_amount=1000000, customer_satisfaction=4)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert len(tags) == len(set(tags))

    def test_cost_controllable_tag(self):
        review = make_review(budget_amount=1000000, cost_variance=30000)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "成本可控" in tags

    def test_cost_overrun_tag(self):
        review = make_review(budget_amount=1000000, cost_variance=120000)
        project = review.project
        tags = self.syncer._extract_tags(review, project)
        assert "成本超支" in tags


class TestCalculateQualityScore:
    def setup_method(self):
        db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
            self.syncer = ProjectKnowledgeSyncer(db)

    def test_score_between_0_and_1(self):
        review = make_review()
        score = self.syncer._calculate_quality_score(review)
        assert 0.0 <= score <= 1.0

    def test_perfect_score_high_satisfaction(self):
        review = make_review(
            customer_satisfaction=5,
            schedule_variance=0,
            cost_variance=30000,
            budget_amount=1000000,
            change_count=2,
            success_factors="良好团队协作且沟通顺畅高效",
            problems="仅有少量问题需要解决",
            best_practices="最佳实践用于指导团队成员",
            conclusion="总体项目完成优秀达标"
        )
        score = self.syncer._calculate_quality_score(review)
        assert score > 0.8

    def test_base_score_applied(self):
        # Even with no bonus fields, base score is 0.5
        review = MagicMock()
        review.customer_satisfaction = None
        review.schedule_variance = None
        review.cost_variance = None
        review.change_count = None
        review.success_factors = None
        review.problems = None
        review.best_practices = None
        review.conclusion = None
        review.budget_amount = None
        score = self.syncer._calculate_quality_score(review)
        assert score == 0.5

    def test_delayed_project_lower_score(self):
        # Compare reviews with same parameters but different schedule_variance
        # Use MagicMock directly to control all fields
        on_time = MagicMock()
        on_time.customer_satisfaction = 3
        on_time.schedule_variance = -1  # on time
        on_time.cost_variance = None
        on_time.change_count = None
        on_time.success_factors = None
        on_time.problems = None
        on_time.best_practices = None
        on_time.conclusion = None
        on_time.budget_amount = None

        delayed = MagicMock()
        delayed.customer_satisfaction = 3
        delayed.schedule_variance = 20  # delayed
        delayed.cost_variance = None
        delayed.change_count = None
        delayed.success_factors = None
        delayed.problems = None
        delayed.best_practices = None
        delayed.conclusion = None
        delayed.budget_amount = None

        score_on_time = self.syncer._calculate_quality_score(on_time)
        score_delayed = self.syncer._calculate_quality_score(delayed)
        assert score_on_time > score_delayed

    def test_few_changes_bonus(self):
        few = MagicMock()
        few.customer_satisfaction = None
        few.schedule_variance = None
        few.cost_variance = None
        few.change_count = 2  # few
        few.success_factors = None
        few.problems = None
        few.best_practices = None
        few.conclusion = None
        few.budget_amount = None

        many = MagicMock()
        many.customer_satisfaction = None
        many.schedule_variance = None
        many.cost_variance = None
        many.change_count = 10  # many
        many.success_factors = None
        many.problems = None
        many.best_practices = None
        many.conclusion = None
        many.budget_amount = None

        score_few = self.syncer._calculate_quality_score(few)
        score_many = self.syncer._calculate_quality_score(many)
        assert score_few > score_many


class TestParseSummaryResponse:
    def setup_method(self):
        db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
            self.syncer = ProjectKnowledgeSyncer(db)

    def test_parse_valid_json(self):
        import json
        data = {"summary": "项目摘要", "technical_highlights": "亮点"}
        response = {"content": json.dumps(data)}
        result = self.syncer._parse_summary_response(response)
        assert result["summary"] == "项目摘要"

    def test_parse_json_in_code_block(self):
        import json
        data = {"summary": "代码块摘要"}
        content = f"```json\n{json.dumps(data)}\n```"
        response = {"content": content}
        result = self.syncer._parse_summary_response(response)
        assert result["summary"] == "代码块摘要"

    def test_parse_invalid_json_fallback(self):
        response = {"content": "这不是JSON格式的内容"}
        result = self.syncer._parse_summary_response(response)
        assert "summary" in result
        assert result["summary"] == "这不是JSON格式的内容"[:300]

    def test_empty_content_fallback(self):
        response = {"content": "{}"}
        result = self.syncer._parse_summary_response(response)
        assert isinstance(result, dict)


class TestExtractTechnicalHighlights:
    def setup_method(self):
        db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
            self.syncer = ProjectKnowledgeSyncer(db)

    def test_empty_best_practices(self):
        review = MagicMock()
        review.best_practices = None
        result = self.syncer._extract_technical_highlights(review)
        assert result == ""

    def test_short_practices_returned_as_is(self):
        review = MagicMock()
        review.best_practices = "短内容"
        result = self.syncer._extract_technical_highlights(review)
        assert result == "短内容"

    def test_long_practices_truncated(self):
        review = MagicMock()
        review.best_practices = "A" * 400
        result = self.syncer._extract_technical_highlights(review)
        assert len(result) <= 303  # 300 chars + "..."
        assert result.endswith("...")


class TestGetSyncStatus:
    def setup_method(self):
        self.db = make_db()
        with patch("app.services.project_review_ai.knowledge_syncer.AIClientService"):
            self.syncer = ProjectKnowledgeSyncer(self.db)

    def test_review_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.syncer.get_sync_status(999)
        assert result["synced"] is False

    def test_not_synced_yet(self):
        review = make_review()
        # First query returns review, second returns None (no case found)
        self.db.query.return_value.filter.return_value.first.side_effect = [review, None]
        result = self.syncer.get_sync_status(1)
        assert result["synced"] is False

    def test_already_synced(self):
        review = make_review()
        case = MagicMock()
        case.id = 10
        case.case_name = "PRJ-001 - 测试项目"
        case.quality_score = 0.85
        case.updated_at = datetime(2024, 1, 1)
        case.tags = ["制造业", "中型项目"]
        self.db.query.return_value.filter.return_value.first.side_effect = [review, case]
        result = self.syncer.get_sync_status(1)
        assert result["synced"] is True
        assert result["case_id"] == 10
