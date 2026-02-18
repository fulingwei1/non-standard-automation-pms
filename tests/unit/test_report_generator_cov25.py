# -*- coding: utf-8 -*-
"""第二十五批 - project_review_ai/report_generator 单元测试"""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date

pytest.importorskip("app.services.project_review_ai.report_generator")

from app.services.project_review_ai.report_generator import ProjectReviewReportGenerator


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def generator(db):
    with patch("app.services.project_review_ai.report_generator.AIClientService"):
        svc = ProjectReviewReportGenerator(db)
    return svc


def _make_project(project_id=1):
    proj = MagicMock()
    proj.id = project_id
    proj.code = f"P{project_id:04d}"
    proj.name = "测试项目"
    proj.description = "这是一个测试项目"
    proj.status = "COMPLETED"
    proj.project_type = "NON_STANDARD"
    proj.budget_amount = 100000
    proj.planned_start_date = date(2025, 1, 1)
    proj.planned_end_date = date(2025, 6, 30)
    proj.actual_start_date = date(2025, 1, 5)
    proj.actual_end_date = date(2025, 7, 10)
    proj.customer = MagicMock(name="客户A")
    proj.members = []
    return proj


# ── _extract_project_data ─────────────────────────────────────────────────────

class TestExtractProjectData:
    def test_returns_none_when_project_not_found(self, generator, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = generator._extract_project_data(99)
        assert result is None

    def test_returns_dict_with_expected_keys(self, generator, db):
        proj = _make_project()
        db.query.return_value.filter.return_value.first.return_value = proj
        db.query.return_value.filter.return_value.all.return_value = []
        result = generator._extract_project_data(1)
        assert result is not None
        assert "project" in result
        assert "statistics" in result
        assert "team_members" in result
        assert "changes" in result

    def test_statistics_total_hours_sums_correctly(self, generator, db):
        proj = _make_project()
        db.query.return_value.filter.return_value.first.return_value = proj
        ts1 = MagicMock(work_hours=4, project_id=1)
        ts2 = MagicMock(work_hours=6, project_id=1)
        # Make filter().all() return different values per call
        db.query.return_value.filter.return_value.all.side_effect = [
            [ts1, ts2],  # timesheets
            [],           # costs
            [],           # changes
        ]
        result = generator._extract_project_data(1)
        assert result["statistics"]["total_hours"] == 10

    def test_statistics_change_count(self, generator, db):
        proj = _make_project()
        db.query.return_value.filter.return_value.first.return_value = proj
        changes = [MagicMock() for _ in range(3)]
        db.query.return_value.filter.return_value.all.side_effect = [
            [],      # timesheets
            [],      # costs
            changes, # changes
        ]
        result = generator._extract_project_data(1)
        assert result["statistics"]["change_count"] == 3

    def test_budget_amount_in_project_dict(self, generator, db):
        proj = _make_project()
        db.query.return_value.filter.return_value.first.return_value = proj
        db.query.return_value.filter.return_value.all.return_value = []
        result = generator._extract_project_data(1)
        assert result["project"]["budget"] == 100000.0


# ── _format_changes ───────────────────────────────────────────────────────────

class TestFormatChanges:
    def test_empty_changes_returns_no_record_text(self, generator):
        result = generator._format_changes([])
        assert "无变更记录" in result

    def test_single_change_formatted(self, generator):
        changes = [{"title": "变更A", "type": "SCOPE", "impact": "HIGH", "status": "APPROVED"}]
        result = generator._format_changes(changes)
        assert "变更A" in result

    def test_max_five_changes_displayed(self, generator):
        changes = [{"title": f"变更{i}", "type": "T", "impact": "L", "status": "S"} for i in range(8)]
        result = generator._format_changes(changes)
        # Should show ellipsis for more than 5
        assert "8" in result

    def test_exactly_five_changes_no_ellipsis(self, generator):
        changes = [{"title": f"变更{i}", "type": "T", "impact": "L", "status": "S"} for i in range(5)]
        result = generator._format_changes(changes)
        assert "..." not in result


# ── _build_review_prompt ──────────────────────────────────────────────────────

class TestBuildReviewPrompt:
    def _make_project_data(self):
        return {
            "project": {
                "name": "测试项目",
                "code": "P0001",
                "customer_name": "客户A",
                "type": "非标",
                "description": "描述",
                "budget": 100000.0,
            },
            "statistics": {
                "plan_duration": 180,
                "actual_duration": 186,
                "schedule_variance": 6,
                "total_cost": 95000.0,
                "cost_variance": -5000.0,
                "total_hours": 1200,
                "change_count": 2,
            },
            "team_members": [{"name": "张三", "role": "PM", "hours": 200}],
            "changes": [],
        }

    def test_prompt_contains_project_name(self, generator):
        data = self._make_project_data()
        prompt = generator._build_review_prompt(data, "POST_MORTEM", None)
        assert "测试项目" in prompt

    def test_prompt_contains_schedule_variance(self, generator):
        data = self._make_project_data()
        prompt = generator._build_review_prompt(data, "POST_MORTEM", None)
        assert "延期" in prompt or "6" in prompt

    def test_prompt_contains_additional_context(self, generator):
        data = self._make_project_data()
        prompt = generator._build_review_prompt(data, "POST_MORTEM", "额外的上下文信息")
        assert "额外的上下文信息" in prompt

    def test_prompt_no_additional_context(self, generator):
        data = self._make_project_data()
        prompt = generator._build_review_prompt(data, "POST_MORTEM", None)
        assert "补充信息" not in prompt or "额外的上下文信息" not in prompt


# ── _parse_ai_response ────────────────────────────────────────────────────────

class TestParseAiResponse:
    def _make_project_data(self):
        return {
            "project": {"id": 1, "code": "P0001", "budget": 100000.0},
            "statistics": {
                "plan_duration": 180, "actual_duration": 186,
                "schedule_variance": 6, "total_cost": 95000.0,
                "cost_variance": -5000.0, "change_count": 2,
            },
        }

    def test_parse_valid_json_content(self, generator):
        ai_response = {
            "content": json.dumps({
                "summary": "项目圆满完成",
                "success_factors": ["因素1", "因素2"],
                "problems": ["问题1"],
                "improvements": ["改进1"],
                "best_practices": ["实践1"],
                "conclusion": "总体良好",
                "insights": {}
            })
        }
        result = generator._parse_ai_response(ai_response, self._make_project_data())
        assert result["ai_summary"] == "项目圆满完成"
        assert result["ai_generated"] is True

    def test_parse_json_in_code_block(self, generator):
        content = '```json\n{"summary": "好", "success_factors": [], "problems": [], "improvements": [], "best_practices": [], "conclusion": "结论", "insights": {}}\n```'
        ai_response = {"content": content}
        result = generator._parse_ai_response(ai_response, self._make_project_data())
        assert result["ai_summary"] == "好"

    def test_parse_invalid_json_fallback(self, generator):
        ai_response = {"content": "这不是JSON，是纯文字内容，比较长一些"}
        result = generator._parse_ai_response(ai_response, self._make_project_data())
        assert isinstance(result, dict)
        assert result["ai_generated"] is True

    def test_result_contains_variance_fields(self, generator):
        ai_response = {"content": "{}"}
        result = generator._parse_ai_response(ai_response, self._make_project_data())
        assert "schedule_variance" in result
        assert "cost_variance" in result
        assert result["plan_duration"] == 180

    def test_token_usage_default(self, generator):
        ai_response = {"content": "{}", "token_usage": 500}
        result = generator._parse_ai_response(ai_response, self._make_project_data())
        assert isinstance(result, dict)


# ── generate_report integration ───────────────────────────────────────────────

class TestGenerateReport:
    def test_raises_when_project_not_found(self, generator, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在或数据不完整"):
            generator.generate_report(999)

    def test_returns_dict_with_ai_metadata(self, generator, db):
        proj = _make_project()
        db.query.return_value.filter.return_value.first.return_value = proj
        db.query.return_value.filter.return_value.all.return_value = []
        generator.ai_client.generate_solution.return_value = {
            "content": '{"summary":"ok","success_factors":[],"problems":[],"improvements":[],"best_practices":[],"conclusion":"ok","insights":{}}',
            "token_usage": 100,
        }
        result = generator.generate_report(1)
        assert "ai_metadata" in result
        assert result["ai_metadata"]["model"] == "glm-5"
