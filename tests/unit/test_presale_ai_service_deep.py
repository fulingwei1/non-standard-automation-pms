# -*- coding: utf-8 -*-
"""
N1组深度覆盖: PresaleAIService
补充 _parse_solution_response, _calculate_confidence, _extract_mermaid_code,
generate_bom, _generate_bom_item, get_solution, update_solution,
review_solution, get_template_library 等核心分支
"""
import json
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.presale_ai_service import PresaleAIService
from app.schemas.presale_ai_solution import (
    TemplateMatchRequest,
    SolutionGenerationRequest,
)


def _make_service():
    db = MagicMock()
    mock_ai = MagicMock()
    with patch("app.services.presale_ai_service.AIClientService", return_value=mock_ai):
        svc = PresaleAIService()
        svc.ai_client = mock_ai
    return svc, db, mock_ai


def _make_template(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", 1)
    t.name = kwargs.get("name", "标准模板")
    t.industry = kwargs.get("industry", "汽车")
    t.equipment_type = kwargs.get("equipment_type", "机器人")
    t.keywords = kwargs.get("keywords", "机器人 装配 汽车")
    t.usage_count = kwargs.get("usage_count", 10)
    t.avg_quality_score = kwargs.get("avg_quality_score", Decimal("0.85"))
    t.is_active = kwargs.get("is_active", 1)
    t.solution_content = kwargs.get("solution_content", {"description": "模板内容"})
    return t


def _make_solution(**kwargs):
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.status = kwargs.get("status", "draft")
    s.architecture_diagram = kwargs.get("architecture_diagram", None)
    s.topology_diagram = kwargs.get("topology_diagram", None)
    s.signal_flow_diagram = kwargs.get("signal_flow_diagram", None)
    s.bom_list = kwargs.get("bom_list", None)
    s.estimated_cost = kwargs.get("estimated_cost", None)
    return s


# ============================================================
# 1. _parse_solution_response - 三条分支
# ============================================================

class TestParseSolutionResponse:
    def test_parse_json_code_block(self):
        svc, db, _ = _make_service()
        content = '```json\n{"description": "自动化方案", "equipment_list": []}\n```'
        result = svc._parse_solution_response({"content": content})
        assert result["description"] == "自动化方案"

    def test_parse_plain_code_block(self):
        svc, db, _ = _make_service()
        content = '```\n{"key": "val"}\n```'
        result = svc._parse_solution_response({"content": content})
        assert result["key"] == "val"

    def test_parse_direct_json(self):
        svc, db, _ = _make_service()
        content = '{"description": "直接JSON", "key_features": ["fast"]}'
        result = svc._parse_solution_response({"content": content})
        assert result["description"] == "直接JSON"

    def test_parse_failure_returns_fallback(self):
        svc, db, _ = _make_service()
        content = "this is not JSON at all"
        result = svc._parse_solution_response({"content": content})
        assert "description" in result
        assert result["description"] == content

    def test_empty_content_returns_fallback(self):
        svc, db, _ = _make_service()
        result = svc._parse_solution_response({"content": ""})
        assert "description" in result


# ============================================================
# 2. _calculate_confidence - 各字段影响
# ============================================================

class TestCalculateConfidence:
    def test_base_score_no_extras(self):
        svc, db, _ = _make_service()
        score = svc._calculate_confidence({}, None)
        assert score == pytest.approx(0.5)

    def test_with_template(self):
        svc, db, _ = _make_service()
        template = _make_template()
        score = svc._calculate_confidence({}, template)
        assert score >= 0.7  # 0.5 + 0.2

    def test_with_equipment_list(self):
        svc, db, _ = _make_service()
        solution = {"equipment_list": [{"name": "机器人"}]}
        score = svc._calculate_confidence(solution, None)
        assert score >= 0.65  # 0.5 + 0.15

    def test_with_technical_parameters(self):
        svc, db, _ = _make_service()
        solution = {"technical_parameters": {"speed": "1m/s"}}
        score = svc._calculate_confidence(solution, None)
        assert score >= 0.6  # 0.5 + 0.1

    def test_with_process_flow(self):
        svc, db, _ = _make_service()
        solution = {"process_flow": "步骤1: 上料"}
        score = svc._calculate_confidence(solution, None)
        assert score >= 0.55  # 0.5 + 0.05

    def test_max_score_capped_at_one(self):
        svc, db, _ = _make_service()
        solution = {
            "equipment_list": [{"name": "x"}],
            "technical_parameters": {"k": "v"},
            "process_flow": "step1",
        }
        template = _make_template()
        score = svc._calculate_confidence(solution, template)
        assert score <= 1.0


# ============================================================
# 3. _extract_mermaid_code - 三条分支
# ============================================================

class TestExtractMermaidCode:
    def test_extract_from_mermaid_block(self):
        svc, db, _ = _make_service()
        content = "```mermaid\ngraph TD\n  A-->B\n```"
        result = svc._extract_mermaid_code(content)
        assert "graph TD" in result
        assert "```" not in result

    def test_extract_from_generic_block(self):
        svc, db, _ = _make_service()
        content = "```\ngraph LR\n  X-->Y\n```"
        result = svc._extract_mermaid_code(content)
        assert "graph LR" in result

    def test_plain_content_returned_as_is(self):
        svc, db, _ = _make_service()
        content = "  graph TD\n  A-->B  "
        result = svc._extract_mermaid_code(content)
        assert result.strip() == content.strip()


# ============================================================
# 4. generate_bom - 基本流程
# ============================================================

class TestGenerateBOM:
    def test_empty_equipment_list(self):
        svc, db, _ = _make_service()
        result = svc.generate_bom(equipment_list=[], include_cost=True)
        assert result["item_count"] == 0
        assert result["total_cost"] == Decimal("0")

    def test_generates_bom_items(self):
        svc, db, _ = _make_service()
        equipment = [{"name": "机器人", "quantity": 2}]
        result = svc.generate_bom(equipment_list=equipment, include_cost=True)
        assert result["item_count"] == 1
        assert result["bom_items"][0]["item_name"] == "机器人"

    def test_with_solution_id_updates_db(self):
        svc, db, _ = _make_service()
        solution = _make_solution(id=5)
        db.query.return_value.filter_by.return_value.first.return_value = solution

        equipment = [{"name": "传感器", "quantity": 1}]
        result = svc.generate_bom(equipment_list=equipment, solution_id=5)
        db.commit.assert_called()


# ============================================================
# 5. _generate_bom_item - include_cost / include_suppliers
# ============================================================

class TestGenerateBOMItem:
    def test_with_cost(self):
        svc, db, _ = _make_service()
        item = svc._generate_bom_item(
            {"name": "PLC", "quantity": 1},
            include_cost=True,
            include_suppliers=False
        )
        assert "unit_price" in item
        assert "total_price" in item

    def test_without_cost(self):
        svc, db, _ = _make_service()
        item = svc._generate_bom_item(
            {"name": "PLC", "quantity": 1},
            include_cost=False,
            include_suppliers=False
        )
        assert "unit_price" not in item

    def test_with_suppliers(self):
        svc, db, _ = _make_service()
        item = svc._generate_bom_item(
            {"name": "传感器", "quantity": 2},
            include_cost=False,
            include_suppliers=True
        )
        assert "supplier" in item
        assert "lead_time_days" in item

    def test_quantity_used_in_total(self):
        svc, db, _ = _make_service()
        item = svc._generate_bom_item(
            {"name": "机器人", "quantity": 3},
            include_cost=True,
            include_suppliers=False
        )
        assert item["total_price"] == item["unit_price"] * 3


# ============================================================
# 6. get_solution
# ============================================================

class TestGetSolution:
    def test_found(self):
        svc, db, _ = _make_service()
        solution = _make_solution(id=1)
        db.query.return_value.filter_by.return_value.first.return_value = solution
        result = svc.get_solution(1)
        assert result.id == 1

    def test_not_found(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter_by.return_value.first.return_value = None
        result = svc.get_solution(999)
        assert result is None


# ============================================================
# 7. update_solution
# ============================================================

class TestUpdateSolution:
    def test_update_success(self):
        svc, db, _ = _make_service()
        solution = _make_solution(id=1)
        db.query.return_value.filter_by.return_value.first.return_value = solution

        result = svc.update_solution(1, {"status": "reviewed"})
        assert result is not None
        db.commit.assert_called()

    def test_update_not_found_raises(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            svc.update_solution(999, {"status": "reviewed"})


# ============================================================
# 8. review_solution
# ============================================================

class TestReviewSolution:
    def test_review_approved(self):
        svc, db, _ = _make_service()
        solution = _make_solution(id=1)
        db.query.return_value.filter_by.return_value.first.return_value = solution

        result = svc.review_solution(1, reviewer_id=5, status="approved", comments="LGTM")
        assert result.status == "approved"
        assert result.reviewed_by == 5
        db.commit.assert_called()

    def test_review_not_found_raises(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            svc.review_solution(999, reviewer_id=1, status="rejected")


# ============================================================
# 9. get_template_library
# ============================================================

class TestGetTemplateLibrary:
    def test_returns_active_templates(self):
        svc, db, _ = _make_service()
        templates = [_make_template(id=i) for i in range(3)]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = templates

        result = svc.get_template_library()
        assert len(result) == 3

    def test_filter_by_industry(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = svc.get_template_library(industry="汽车")
        assert result == []

    def test_include_inactive_when_is_active_false(self):
        svc, db, _ = _make_service()
        db.query.return_value.order_by.return_value.all.return_value = []

        result = svc.get_template_library(is_active=False)
        assert result == []


# ============================================================
# 10. match_templates - 无关键词分支
# ============================================================

class TestMatchTemplatesDeep:
    def test_no_keywords_sorted_by_usage_count(self):
        svc, db, _ = _make_service()
        t1 = _make_template(id=1, usage_count=5)
        t2 = _make_template(id=2, usage_count=20)
        db.query.return_value.filter.return_value.all.return_value = [t1, t2]

        req = TemplateMatchRequest(
            query="机器人",
            keywords=None,
            top_k=2
        )
        result, _ = svc.match_templates(req, user_id=1)
        # usage_count 更高的排前面
        assert result[0].template_id == 2

    def test_empty_templates_returns_empty(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        req = TemplateMatchRequest(query="机器人", top_k=5)
        result, _ = svc.match_templates(req, user_id=1)
        assert result == []

    def test_returns_search_time_ms(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        req = TemplateMatchRequest(query="test", top_k=5)
        result, time_ms = svc.match_templates(req, user_id=1)
        assert isinstance(time_ms, int)
        assert time_ms >= 0


# ============================================================
# 11. _build_solution_prompt
# ============================================================

class TestBuildSolutionPrompt:
    def test_without_template(self):
        svc, db, _ = _make_service()
        prompt = svc._build_solution_prompt({"industry": "汽车"}, None)
        assert "需求信息" in prompt
        assert "参考模板" not in prompt

    def test_with_template(self):
        svc, db, _ = _make_service()
        template = _make_template()
        prompt = svc._build_solution_prompt({"industry": "汽车"}, template)
        assert "参考模板" in prompt
        assert "标准模板" in prompt
