# -*- coding: utf-8 -*-
"""
项目知识库同步服务单元测试 (I3组)
测试 ProjectKnowledgeSyncer 各方法
"""
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.project_review_ai.knowledge_syncer import ProjectKnowledgeSyncer


def _make_syncer(db=None):
    if db is None:
        db = MagicMock()
    with patch("app.services.project_review_ai.knowledge_syncer.AIClientService") as mock_ai_cls:
        mock_ai = MagicMock()
        mock_ai_cls.return_value = mock_ai
        syncer = ProjectKnowledgeSyncer(db)
        syncer.ai_client = mock_ai  # store for assertions
    return syncer


def _make_review(budget=1_000_000, satisfaction=4, schedule_var=0, cost_var=0,
                 change_count=2, success_factors="success" * 15,
                 problems="problems" * 15, best_practices="bp" * 30,
                 conclusion="conclusion" * 15):
    review = MagicMock()
    review.budget_amount = Decimal(str(budget))
    review.customer_satisfaction = satisfaction
    review.schedule_variance = schedule_var
    review.cost_variance = Decimal(str(cost_var))
    review.change_count = change_count
    review.success_factors = success_factors
    review.problems = problems
    review.best_practices = best_practices
    review.conclusion = conclusion
    review.ai_summary = "AI summary"
    review.project_code = "PJ-001"
    return review


def _make_project(code="PJ-001", name="Test Project", industry="制造业", project_type="工程"):
    project = MagicMock()
    project.code = code
    project.name = name
    project.industry = industry
    project.project_type = project_type
    project.customer = MagicMock()
    project.customer.name = "Client Co"
    return project


# ─────────────────────────────────────────────────────────────────────────────
# _parse_summary_response
# ─────────────────────────────────────────────────────────────────────────────
class TestParseSummaryResponse:
    def test_valid_json(self):
        syncer = _make_syncer()
        data = {"summary": "test summary", "technical_highlights": "highlights"}
        response = {"content": json.dumps(data)}
        result = syncer._parse_summary_response(response)
        assert result["summary"] == "test summary"

    def test_json_in_code_block(self):
        syncer = _make_syncer()
        content = '```json\n{"summary": "from code block"}\n```'
        response = {"content": content}
        result = syncer._parse_summary_response(response)
        assert result["summary"] == "from code block"

    def test_invalid_json_falls_back(self):
        syncer = _make_syncer()
        response = {"content": "not valid json at all"}
        result = syncer._parse_summary_response(response)
        assert "summary" in result
        assert "not valid json at all" in result["summary"]

    def test_empty_content_key(self):
        syncer = _make_syncer()
        response = {"content": "{}"}
        result = syncer._parse_summary_response(response)
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# _extract_tags
# ─────────────────────────────────────────────────────────────────────────────
class TestExtractTags:
    def _make_review_for_tags(self, budget, satisfaction, schedule_var, cost_var):
        review = MagicMock()
        review.budget_amount = Decimal(str(budget))
        review.customer_satisfaction = satisfaction
        review.schedule_variance = schedule_var
        review.cost_variance = Decimal(str(cost_var)) if cost_var is not None else None
        return review

    def test_small_project_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(300000, 4, 0, 0)
        project = _make_project(industry="机械", project_type="维修")
        tags = syncer._extract_tags(review, project)
        assert "小型项目" in tags

    def test_medium_project_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 3, 5, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "中型项目" in tags

    def test_large_project_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(5_000_000, 5, -1, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "大型项目" in tags

    def test_high_satisfaction_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 5, 0, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "高满意度" in tags

    def test_medium_satisfaction_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 3, 0, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "中等满意度" in tags

    def test_on_time_delivery_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 4, -1, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "按期交付" in tags

    def test_slight_delay_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 4, 5, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "轻微延期" in tags

    def test_significant_delay_tag(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 4, 20, 0)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "显著延期" in tags

    def test_cost_control_tag(self):
        syncer = _make_syncer()
        # cost_var = 40000 (4% of 1M) → 成本可控
        review = self._make_review_for_tags(1_000_000, 4, 0, 40000)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "成本可控" in tags

    def test_cost_overrun_tag(self):
        syncer = _make_syncer()
        # cost_var = 120000 (12% of 1M) → 成本超支
        review = self._make_review_for_tags(1_000_000, 4, 0, 120000)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "成本超支" in tags

    def test_severe_overrun_tag(self):
        syncer = _make_syncer()
        # cost_var = 200000 (20% of 1M) → 严重超支
        review = self._make_review_for_tags(1_000_000, 4, 0, 200000)
        project = _make_project()
        tags = syncer._extract_tags(review, project)
        assert "严重超支" in tags

    def test_industry_tag_included(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 4, 0, 0)
        project = _make_project(industry="航空")
        tags = syncer._extract_tags(review, project)
        assert "航空" in tags

    def test_no_duplicates(self):
        syncer = _make_syncer()
        review = self._make_review_for_tags(1_000_000, 4, 0, 0)
        project = _make_project(industry="制造")
        tags = syncer._extract_tags(review, project)
        assert len(tags) == len(set(tags))


# ─────────────────────────────────────────────────────────────────────────────
# _calculate_quality_score
# ─────────────────────────────────────────────────────────────────────────────
class TestCalculateQualityScore:
    def test_perfect_review_scores_high(self):
        syncer = _make_syncer()
        review = _make_review(budget=1_000_000, satisfaction=5, schedule_var=0,
                              cost_var=0, change_count=1,
                              success_factors="A" * 60, problems="B" * 60,
                              best_practices="C" * 60, conclusion="D" * 60)
        score = syncer._calculate_quality_score(review)
        assert score > 0.9

    def test_score_between_0_and_1(self):
        syncer = _make_syncer()
        review = _make_review()
        score = syncer._calculate_quality_score(review)
        assert 0.0 <= score <= 1.0

    def test_no_satisfaction_uses_base(self):
        syncer = _make_syncer()
        review = _make_review(satisfaction=None)
        score = syncer._calculate_quality_score(review)
        assert score >= 0.5  # at least base score

    def test_delayed_schedule_no_bonus(self):
        syncer = _make_syncer()
        review = _make_review(schedule_var=15, satisfaction=None)
        score_delayed = syncer._calculate_quality_score(review)
        review2 = _make_review(schedule_var=0, satisfaction=None)
        score_on_time = syncer._calculate_quality_score(review2)
        assert score_on_time > score_delayed

    def test_high_change_count_reduced_bonus(self):
        syncer = _make_syncer()
        review_low = _make_review(change_count=1)
        review_high = _make_review(change_count=10)
        score_low = syncer._calculate_quality_score(review_low)
        score_high = syncer._calculate_quality_score(review_high)
        assert score_low > score_high


# ─────────────────────────────────────────────────────────────────────────────
# _extract_technical_highlights
# ─────────────────────────────────────────────────────────────────────────────
class TestExtractTechnicalHighlights:
    def test_no_best_practices_returns_empty(self):
        syncer = _make_syncer()
        review = MagicMock(); review.best_practices = None
        result = syncer._extract_technical_highlights(review)
        assert result == ""

    def test_short_best_practices_returned_as_is(self):
        syncer = _make_syncer()
        review = MagicMock(); review.best_practices = "short"
        result = syncer._extract_technical_highlights(review)
        assert result == "short"

    def test_long_best_practices_truncated(self):
        syncer = _make_syncer()
        review = MagicMock(); review.best_practices = "A" * 400
        result = syncer._extract_technical_highlights(review)
        assert len(result) <= 303  # 300 + "..."
        assert result.endswith("...")


# ─────────────────────────────────────────────────────────────────────────────
# _build_summary_prompt
# ─────────────────────────────────────────────────────────────────────────────
class TestBuildSummaryPrompt:
    def test_prompt_contains_project_info(self):
        syncer = _make_syncer()
        review = _make_review()
        project = _make_project(code="PJ-001", name="My Project")
        review.budget_amount = Decimal("500000")
        review.customer_satisfaction = 4
        review.success_factors = "Good"
        review.problems = "Few"
        review.best_practices = "Some"
        prompt = syncer._build_summary_prompt(review, project)
        assert "My Project" in prompt
        assert "PJ-001" in prompt
        assert "JSON" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# sync_to_knowledge_base
# ─────────────────────────────────────────────────────────────────────────────
class TestSyncToKnowledgeBase:
    def test_review_not_found_raises(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        syncer = _make_syncer(db)
        with pytest.raises(ValueError, match="不存在"):
            syncer.sync_to_knowledge_base(999)

    def test_creates_new_case_when_none_exists(self):
        db = MagicMock()
        review = _make_review()
        project = _make_project()
        review.project = project

        # First query returns review, second returns None (no existing case)
        q = MagicMock()
        q.filter.return_value = q
        q.first.side_effect = [review, None]
        db.query.return_value = q

        syncer = _make_syncer(db)
        # Mock AI response
        syncer.ai_client.generate_solution.return_value = {
            "content": '{"summary": "AI summary", "technical_highlights": "highlights"}'
        }

        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        case = MagicMock(); case.id = 1; case.case_name = "PJ-001 - Test Project"; case.quality_score = Decimal("0.8")
        db.refresh.side_effect = lambda x: None

        # Patch PresaleKnowledgeCase constructor
        with patch("app.services.project_review_ai.knowledge_syncer.PresaleKnowledgeCase") as MockCase:
            mock_case_instance = MagicMock()
            mock_case_instance.id = 1
            mock_case_instance.case_name = "PJ-001 - Test Project"
            mock_case_instance.quality_score = Decimal("0.8")
            MockCase.return_value = mock_case_instance

            result = syncer.sync_to_knowledge_base(1)

        assert result["success"] is True
        db.add.assert_called()
        db.commit.assert_called()

    def test_updates_existing_case(self):
        db = MagicMock()
        review = _make_review()
        project = _make_project()
        review.project = project

        existing_case = MagicMock()
        existing_case.id = 5
        existing_case.case_name = "PJ-001 - Test Project"
        existing_case.quality_score = Decimal("0.7")

        q = MagicMock()
        q.filter.return_value = q
        q.first.side_effect = [review, existing_case]
        db.query.return_value = q

        syncer = _make_syncer(db)
        syncer.ai_client.generate_solution.return_value = {
            "content": '{"summary": "updated", "technical_highlights": "new"}'
        }
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = syncer.sync_to_knowledge_base(1)
        assert result["success"] is True
        db.commit.assert_called()


# ─────────────────────────────────────────────────────────────────────────────
# get_sync_status
# ─────────────────────────────────────────────────────────────────────────────
class TestGetSyncStatus:
    def test_review_not_found(self):
        db = MagicMock()
        q = MagicMock(); q.filter.return_value = q; q.first.return_value = None
        db.query.return_value = q
        syncer = _make_syncer(db)
        result = syncer.get_sync_status(999)
        assert result["synced"] is False

    def test_not_synced_yet(self):
        db = MagicMock()
        review = MagicMock()
        review.project_code = "PJ-001"
        review.project = MagicMock(); review.project.name = "Test"

        q = MagicMock(); q.filter.return_value = q
        q.first.side_effect = [review, None]
        db.query.return_value = q

        syncer = _make_syncer(db)
        result = syncer.get_sync_status(1)
        assert result["synced"] is False
        assert "message" in result

    def test_already_synced(self):
        db = MagicMock()
        review = MagicMock()
        review.project_code = "PJ-001"
        review.project = MagicMock(); review.project.name = "Test"

        case = MagicMock()
        case.id = 3
        case.case_name = "PJ-001 - Test"
        case.quality_score = Decimal("0.85")
        case.updated_at = datetime(2024, 1, 1)
        case.tags = ["制造业", "大型项目"]

        q = MagicMock(); q.filter.return_value = q
        q.first.side_effect = [review, case]
        db.query.return_value = q

        syncer = _make_syncer(db)
        result = syncer.get_sync_status(1)
        assert result["synced"] is True
        assert result["case_id"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# update_case_from_lessons
# ─────────────────────────────────────────────────────────────────────────────
class TestUpdateCaseFromLessons:
    def test_case_not_found_raises(self):
        db = MagicMock()
        q = MagicMock(); q.filter.return_value = q
        q.all.return_value = []  # lessons
        q.first.return_value = None  # case not found
        db.query.return_value = q

        syncer = _make_syncer(db)
        with pytest.raises(ValueError, match="不存在"):
            syncer.update_case_from_lessons(1, 999)

    def test_updates_case_with_lessons(self):
        db = MagicMock()

        lesson1 = MagicMock(); lesson1.lesson_type = "SUCCESS"; lesson1.title = "T1"; lesson1.description = "D1"; lesson1.tags = ["tag1"]
        lesson2 = MagicMock(); lesson2.lesson_type = "FAILURE"; lesson2.title = "T2"; lesson2.description = "D2"; lesson2.tags = ["tag2"]

        case = MagicMock()
        case.tags = []
        case.success_factors = None
        case.lessons_learned = None

        q = MagicMock(); q.filter.return_value = q
        q.all.return_value = [lesson1, lesson2]
        q.first.return_value = case
        db.query.return_value = q

        syncer = _make_syncer(db)
        result = syncer.update_case_from_lessons(1, 5)
        assert result["success"] is True
        assert "updated_fields" in result
        db.commit.assert_called()
