# -*- coding: utf-8 -*-
"""
N1组深度覆盖: AIRequirementAnalyzer / PresaleAIRequirementService
补充 _extract_json_from_response, _calculate_confidence_score,
fallback 方法, get_clarification_questions, update_structured_requirement,
get_requirement_confidence 等核心分支
"""
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.presale_ai_requirement_service import (
    AIRequirementAnalyzer,
    PresaleAIRequirementService,
)
from app.schemas.presale_ai_requirement import (
    RequirementUpdateRequest,
    ClarificationQuestion,
    FeasibilityAnalysis,
    StructuredRequirement,
    EquipmentItem,
    ProcessStep,
    TechnicalParameter,
)


def _make_analyzer():
    return AIRequirementAnalyzer(api_key="test-key")


def _make_service():
    db = MagicMock()
    svc = PresaleAIRequirementService(db)
    return svc, db


def _make_mock_analysis(**kwargs):
    a = MagicMock()
    a.id = kwargs.get("id", 1)
    a.presale_ticket_id = kwargs.get("ticket_id", 100)
    a.raw_requirement = kwargs.get("raw_requirement", "机器人装配线")
    a.structured_requirement = kwargs.get("structured_requirement", {})
    a.clarification_questions = kwargs.get("clarification_questions", [])
    a.confidence_score = kwargs.get("confidence_score", 0.75)
    a.equipment_list = kwargs.get("equipment_list", [])
    a.process_flow = kwargs.get("process_flow", [])
    a.technical_parameters = kwargs.get("technical_parameters", [])
    a.acceptance_criteria = kwargs.get("acceptance_criteria", [])
    a.is_refined = False
    a.refinement_count = 0
    return a


# ============================================================
# 1. _extract_json_from_response - 三条分支
# ============================================================

class TestExtractJsonFromResponse:
    def test_direct_json_parse(self):
        """直接 JSON 解析成功"""
        analyzer = _make_analyzer()
        data = {"key": "value", "num": 42}
        result = analyzer._extract_json_from_response(json.dumps(data))
        assert result == data

    def test_json_in_code_block(self):
        """从 Markdown 代码块提取 JSON"""
        analyzer = _make_analyzer()
        response = '```json\n{"project_type": "非标"}\n```'
        result = analyzer._extract_json_from_response(response)
        assert result["project_type"] == "非标"

    def test_json_embedded_in_text(self):
        """从纯文本中提取 JSON 对象"""
        analyzer = _make_analyzer()
        response = 'here is the result: {"answer": true} end'
        result = analyzer._extract_json_from_response(response)
        assert result["answer"] is True

    def test_invalid_raises_value_error(self):
        """无法解析时抛出 ValueError"""
        analyzer = _make_analyzer()
        with pytest.raises(ValueError):
            analyzer._extract_json_from_response("no json here at all !!!")


# ============================================================
# 2. _calculate_confidence_score - 各维度评分
# ============================================================

class TestCalculateConfidenceScore:
    def test_empty_input_low_score(self):
        analyzer = _make_analyzer()
        parsed = {}
        score = analyzer._calculate_confidence_score("short", parsed)
        assert 0.0 <= score <= 1.0
        assert score < 0.3

    def test_long_requirement_increases_length_score(self):
        analyzer = _make_analyzer()
        long_req = "x" * 600
        parsed = {}
        score = analyzer._calculate_confidence_score(long_req, parsed)
        # 长度维度满分 0.1
        score2 = analyzer._calculate_confidence_score("short", parsed)
        assert score > score2

    def test_structured_requirement_increases_score(self):
        analyzer = _make_analyzer()
        parsed = {
            "structured_requirement": {
                "core_objectives": ["obj"],
                "functional_requirements": ["req"],
                "non_functional_requirements": ["perf"],
                "project_type": "非标",
            }
        }
        score = analyzer._calculate_confidence_score("test req", parsed)
        assert score >= 0.25

    def test_equipment_list_increases_score(self):
        analyzer = _make_analyzer()
        parsed = {
            "equipment_list": [{"name": f"设备{i}"} for i in range(5)]
        }
        score = analyzer._calculate_confidence_score("test", parsed)
        assert score >= 0.2

    def test_full_info_high_score(self):
        analyzer = _make_analyzer()
        long_req = "这是一个很长的需求描述" * 50
        parsed = {
            "structured_requirement": {
                "core_objectives": ["obj1", "obj2"],
                "functional_requirements": ["req1"],
                "non_functional_requirements": ["perf"],
                "project_type": "非标",
            },
            "equipment_list": [{"name": f"设备{i}"} for i in range(5)],
            "technical_parameters": [{"name": f"param{i}"} for i in range(8)],
            "process_flow": [{"name": f"step{i}"} for i in range(5)],
        }
        score = analyzer._calculate_confidence_score(long_req, parsed)
        assert score > 0.8


# ============================================================
# 3. _build_system_prompt - depth 分支
# ============================================================

class TestBuildSystemPrompt:
    def test_deep_includes_deep_keyword(self):
        analyzer = _make_analyzer()
        prompt = analyzer._build_system_prompt("deep")
        assert "深度" in prompt

    def test_quick_includes_quick_keyword(self):
        analyzer = _make_analyzer()
        prompt = analyzer._build_system_prompt("quick")
        assert "快速" in prompt

    def test_standard_no_extra(self):
        analyzer = _make_analyzer()
        prompt = analyzer._build_system_prompt("standard")
        assert "深度" not in prompt and "快速" not in prompt


# ============================================================
# 4. _fallback_rule_based_analysis
# ============================================================

class TestFallbackRuleBasedAnalysis:
    def test_detects_keywords(self):
        analyzer = _make_analyzer()
        req = "需要一个机器人传送带视觉系统进行装配焊接"
        result = analyzer._fallback_rule_based_analysis(req)
        assert "structured_requirement" in result
        assert len(result["equipment_list"]) > 0
        assert result["confidence_score"] == 0.35

    def test_empty_req_returns_defaults(self):
        analyzer = _make_analyzer()
        result = analyzer._fallback_rule_based_analysis("")
        assert "confidence_score" in result
        assert result["confidence_score"] == 0.35

    def test_no_keywords_empty_equipment(self):
        analyzer = _make_analyzer()
        result = analyzer._fallback_rule_based_analysis("未知需求")
        assert result["equipment_list"] == []


# ============================================================
# 5. _fallback_generate_questions
# ============================================================

class TestFallbackGenerateQuestions:
    def test_returns_five_questions(self):
        analyzer = _make_analyzer()
        questions = analyzer._fallback_generate_questions("任意需求")
        assert len(questions) == 5

    def test_questions_have_required_fields(self):
        analyzer = _make_analyzer()
        questions = analyzer._fallback_generate_questions("test")
        for q in questions:
            assert hasattr(q, "question_id")
            assert hasattr(q, "category")
            assert hasattr(q, "question")
            assert hasattr(q, "importance")

    def test_first_question_is_critical(self):
        analyzer = _make_analyzer()
        questions = analyzer._fallback_generate_questions("test")
        assert questions[0].importance == "critical"


# ============================================================
# 6. _fallback_feasibility_analysis
# ============================================================

class TestFallbackFeasibilityAnalysis:
    def test_returns_medium_feasibility(self):
        analyzer = _make_analyzer()
        result = analyzer._fallback_feasibility_analysis({})
        assert result.overall_feasibility == "medium"
        assert len(result.recommendations) > 0


# ============================================================
# 7. PresaleAIRequirementService.get_analysis
# ============================================================

class TestGetAnalysis:
    def test_get_analysis_found(self):
        svc, db = _make_service()
        mock_a = _make_mock_analysis()
        db.query.return_value.filter.return_value.first.return_value = mock_a

        result = svc.get_analysis(1)
        assert result is mock_a

    def test_get_analysis_not_found(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_analysis(999)
        assert result is None


# ============================================================
# 8. PresaleAIRequirementService.get_clarification_questions
# ============================================================

class TestGetClarificationQuestions:
    def test_no_analysis_returns_empty(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        questions, analysis_id = svc.get_clarification_questions(ticket_id=100)
        assert questions == []
        assert analysis_id is None

    def test_analysis_no_questions_returns_empty(self):
        svc, db = _make_service()
        a = _make_mock_analysis(clarification_questions=None)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        questions, analysis_id = svc.get_clarification_questions(ticket_id=100)
        assert questions == []
        assert analysis_id is None

    def test_returns_question_objects(self):
        svc, db = _make_service()
        q_data = [{
            "question_id": 1,
            "category": "技术参数",
            "question": "速度要求是多少？",
            "importance": "critical",
            "suggested_answer": None
        }]
        a = _make_mock_analysis(id=5, clarification_questions=q_data)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        questions, analysis_id = svc.get_clarification_questions(ticket_id=100)
        assert len(questions) == 1
        assert analysis_id == 5
        assert questions[0].question == "速度要求是多少？"


# ============================================================
# 9. PresaleAIRequirementService.update_structured_requirement
# ============================================================

class TestUpdateStructuredRequirement:
    def test_not_found_raises(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        req = MagicMock(spec=RequirementUpdateRequest)
        req.analysis_id = 999
        req.structured_requirement = None
        req.equipment_list = None
        req.process_flow = None
        req.technical_parameters = None
        req.acceptance_criteria = None

        with pytest.raises(ValueError, match="not found"):
            svc.update_structured_requirement(req, user_id=1)

    def test_updates_status_to_reviewed(self):
        svc, db = _make_service()
        a = _make_mock_analysis()
        db.query.return_value.filter.return_value.first.return_value = a

        req = MagicMock(spec=RequirementUpdateRequest)
        req.analysis_id = 1
        req.structured_requirement = None
        req.equipment_list = None
        req.process_flow = None
        req.technical_parameters = None
        req.acceptance_criteria = None

        result = svc.update_structured_requirement(req, user_id=1)
        assert a.status == "reviewed"
        db.commit.assert_called()

    def test_updates_acceptance_criteria(self):
        svc, db = _make_service()
        a = _make_mock_analysis()
        db.query.return_value.filter.return_value.first.return_value = a

        req = MagicMock(spec=RequirementUpdateRequest)
        req.analysis_id = 1
        req.structured_requirement = None
        req.equipment_list = None
        req.process_flow = None
        req.technical_parameters = None
        req.acceptance_criteria = ["验收标准1", "验收标准2"]

        result = svc.update_structured_requirement(req, user_id=1)
        assert a.acceptance_criteria == ["验收标准1", "验收标准2"]


# ============================================================
# 10. PresaleAIRequirementService.get_requirement_confidence
# ============================================================

class TestGetRequirementConfidence:
    def test_no_analysis_returns_zero(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = svc.get_requirement_confidence(ticket_id=100)
        assert result["confidence_score"] == 0.0
        assert result["assessment"] == "no_analysis"

    def test_high_confidence_assessment(self):
        svc, db = _make_service()
        a = _make_mock_analysis(confidence_score=0.9)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        result = svc.get_requirement_confidence(ticket_id=100)
        assert result["assessment"] == "high_confidence"
        assert result["confidence_score"] == 0.9

    def test_medium_confidence_assessment(self):
        svc, db = _make_service()
        a = _make_mock_analysis(confidence_score=0.7)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        result = svc.get_requirement_confidence(ticket_id=100)
        assert result["assessment"] == "medium_confidence"

    def test_low_confidence_assessment(self):
        svc, db = _make_service()
        a = _make_mock_analysis(confidence_score=0.4)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        result = svc.get_requirement_confidence(ticket_id=100)
        assert result["assessment"] == "low_confidence"

    def test_score_breakdown_sums_to_score(self):
        svc, db = _make_service()
        a = _make_mock_analysis(confidence_score=0.8)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        result = svc.get_requirement_confidence(ticket_id=100)
        breakdown = result["score_breakdown"]
        total = sum(breakdown.values())
        assert abs(total - 0.8) < 0.01

    def test_none_confidence_score_defaults_to_zero(self):
        svc, db = _make_service()
        a = _make_mock_analysis(confidence_score=None)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = a

        result = svc.get_requirement_confidence(ticket_id=100)
        assert result["confidence_score"] == 0.0
        assert result["assessment"] == "low_confidence"
