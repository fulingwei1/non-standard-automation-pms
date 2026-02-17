# -*- coding: utf-8 -*-
"""
I1组: AI需求理解服务 单元测试
直接实例化类，AI调用用 @patch mock
"""
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.presale_ai_requirement_service import (
    AIRequirementAnalyzer,
    PresaleAIRequirementService,
)
from app.schemas.presale_ai_requirement import (
    RequirementAnalysisRequest,
    RequirementRefinementRequest,
    RequirementUpdateRequest,
    ClarificationQuestion,
    FeasibilityAnalysis,
)


# ============================================================
# Helper factory
# ============================================================

def _make_analyzer():
    return AIRequirementAnalyzer(api_key="test-key", model="gpt-4")


def _make_service():
    db = MagicMock()
    svc = PresaleAIRequirementService(db)
    return svc, db


def _make_mock_analysis(**kwargs):
    a = MagicMock()
    a.id = kwargs.get("id", 1)
    a.presale_ticket_id = kwargs.get("presale_ticket_id", 100)
    a.raw_requirement = kwargs.get("raw_requirement", "需要一个机器人装配系统")
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
# TestAIRequirementAnalyzer - 静态/纯方法
# ============================================================

class TestAIRequirementAnalyzerHelpers:
    def test_build_system_prompt_standard(self):
        """standard 深度生成提示词"""
        analyzer = _make_analyzer()
        prompt = analyzer._build_system_prompt("standard")
        assert "JSON" in prompt
        assert "structured_requirement" in prompt

    def test_build_system_prompt_deep(self):
        """deep 深度包含额外指令"""
        analyzer = _make_analyzer()
        prompt = analyzer._build_system_prompt("deep")
        assert "深度分析" in prompt

    def test_build_system_prompt_quick(self):
        """quick 深度包含快速指令"""
        analyzer = _make_analyzer()
        prompt = analyzer._build_system_prompt("quick")
        assert "快速" in prompt

    def test_build_user_prompt(self):
        """用户提示词包含需求文本"""
        analyzer = _make_analyzer()
        req = "需要一套自动装配系统"
        prompt = analyzer._build_user_prompt(req)
        assert req in prompt

    def test_extract_json_from_response_direct(self):
        """直接 JSON 字符串解析"""
        analyzer = _make_analyzer()
        data = {"key": "value"}
        result = analyzer._extract_json_from_response(json.dumps(data))
        assert result == data

    def test_extract_json_from_response_code_block(self):
        """从 markdown 代码块中提取"""
        analyzer = _make_analyzer()
        response = '```json\n{"answer": 42}\n```'
        result = analyzer._extract_json_from_response(response)
        assert result["answer"] == 42

    def test_extract_json_from_response_inline(self):
        """从内联JSON提取"""
        analyzer = _make_analyzer()
        response = 'some text {"result": "ok"} more text'
        result = analyzer._extract_json_from_response(response)
        assert result["result"] == "ok"

    def test_extract_json_raises_on_invalid(self):
        """无效响应抛出 ValueError"""
        analyzer = _make_analyzer()
        with pytest.raises(ValueError):
            analyzer._extract_json_from_response("不是JSON内容，纯文字")

    def test_calculate_confidence_score_short_req(self):
        """短需求描述置信度低"""
        analyzer = _make_analyzer()
        raw = "需要机器人"
        parsed = {}
        score = analyzer._calculate_confidence_score(raw, parsed)
        assert score < 0.5

    def test_calculate_confidence_score_complete(self):
        """完整数据置信度高"""
        analyzer = _make_analyzer()
        raw = "x" * 600
        parsed = {
            "structured_requirement": {
                "project_type": "非标",
                "core_objectives": ["目标1"],
                "functional_requirements": ["需求1"],
                "non_functional_requirements": ["性能要求"],
            },
            "equipment_list": [{"name": f"设备{i}"} for i in range(6)],
            "technical_parameters": [{"name": f"参数{i}"} for i in range(8)],
            "process_flow": [{"step_number": i} for i in range(5)],
        }
        score = analyzer._calculate_confidence_score(raw, parsed)
        assert score > 0.5

    def test_fallback_rule_based_analysis(self):
        """降级分析包含关键字识别的设备"""
        analyzer = _make_analyzer()
        raw = "需要机器人和传送带进行焊接"
        result = analyzer._fallback_rule_based_analysis(raw)
        assert "confidence_score" in result
        assert result["confidence_score"] == 0.35
        # 发现了至少一个设备关键词
        names = [e["name"] for e in result.get("equipment_list", [])]
        assert "机器人" in names or "传送带" in names

    def test_fallback_generate_questions(self):
        """降级生成5个澄清问题"""
        analyzer = _make_analyzer()
        questions = analyzer._fallback_generate_questions("测试需求")
        assert len(questions) == 5
        for q in questions:
            assert isinstance(q, ClarificationQuestion)

    def test_fallback_feasibility_analysis(self):
        """降级可行性分析返回 FeasibilityAnalysis"""
        analyzer = _make_analyzer()
        result = analyzer._fallback_feasibility_analysis({})
        assert isinstance(result, FeasibilityAnalysis)
        assert result.overall_feasibility == "medium"


# ============================================================
# TestAIRequirementAnalyzer - async 方法（patch AI调用）
# ============================================================

class TestAIRequirementAnalyzerAsync:
    @pytest.mark.asyncio
    async def test_analyze_requirement_success(self):
        """AI分析成功时返回解析结果"""
        analyzer = _make_analyzer()
        mock_result = json.dumps({
            "structured_requirement": {"project_type": "非标"},
            "equipment_list": [],
            "process_flow": [],
            "technical_parameters": [],
            "acceptance_criteria": [],
        })

        with patch.object(analyzer, "_call_openai_api", new=AsyncMock(return_value=mock_result)):
            result = await analyzer.analyze_requirement("需要一套装配系统")

        assert "structured_requirement" in result
        assert "confidence_score" in result

    @pytest.mark.asyncio
    async def test_analyze_requirement_fallback_on_error(self):
        """AI调用失败时使用规则降级"""
        analyzer = _make_analyzer()

        with patch.object(analyzer, "_call_openai_api", new=AsyncMock(side_effect=Exception("API Error"))):
            result = await analyzer.analyze_requirement("需要机器人传送带")

        assert result["confidence_score"] == 0.35

    @pytest.mark.asyncio
    async def test_generate_clarification_questions_success(self):
        """成功生成澄清问题"""
        analyzer = _make_analyzer()
        mock_response = json.dumps([
            {
                "question_id": 1,
                "category": "技术参数",
                "question": "精度要求是多少?",
                "importance": "critical",
            }
        ])

        with patch.object(analyzer, "_call_openai_api", new=AsyncMock(return_value=mock_response)):
            questions = await analyzer.generate_clarification_questions("需要一套系统")

        assert len(questions) >= 1
        assert questions[0].question == "精度要求是多少?"

    @pytest.mark.asyncio
    async def test_generate_clarification_questions_fallback(self):
        """AI失败时降级生成问题"""
        analyzer = _make_analyzer()

        with patch.object(analyzer, "_call_openai_api", new=AsyncMock(side_effect=Exception("timeout"))):
            questions = await analyzer.generate_clarification_questions("需要一套系统")

        assert len(questions) == 5

    @pytest.mark.asyncio
    async def test_perform_feasibility_analysis_success(self):
        """可行性分析成功"""
        analyzer = _make_analyzer()
        mock_response = json.dumps({
            "overall_feasibility": "high",
            "technical_risks": [],
            "resource_requirements": {},
            "estimated_complexity": "low",
            "development_challenges": [],
            "recommendations": [],
        })

        with patch.object(analyzer, "_call_openai_api", new=AsyncMock(return_value=mock_response)):
            result = await analyzer.perform_feasibility_analysis("需求", {})

        assert isinstance(result, FeasibilityAnalysis)
        assert result.overall_feasibility == "high"

    @pytest.mark.asyncio
    async def test_perform_feasibility_analysis_fallback(self):
        """可行性分析失败时降级"""
        analyzer = _make_analyzer()

        with patch.object(analyzer, "_call_openai_api", new=AsyncMock(side_effect=Exception("err"))):
            result = await analyzer.perform_feasibility_analysis("需求", {})

        assert isinstance(result, FeasibilityAnalysis)


# ============================================================
# TestPresaleAIRequirementService
# ============================================================

class TestPresaleAIRequirementService:
    @pytest.mark.asyncio
    async def test_analyze_requirement(self):
        """analyze_requirement 保存到数据库"""
        service, db = _make_service()

        mock_analysis_result = {
            "structured_requirement": {"project_type": "非标"},
            "equipment_list": [],
            "process_flow": [],
            "technical_parameters": [],
            "acceptance_criteria": [],
            "confidence_score": 0.7,
        }
        mock_questions = [ClarificationQuestion(
            question_id=1, category="技术", question="精度?", importance="high"
        )]
        mock_feasibility = FeasibilityAnalysis(
            overall_feasibility="medium",
            technical_risks=[],
            resource_requirements={},
            estimated_complexity="medium",
            development_challenges=[],
            recommendations=[],
        )

        with patch.object(service.analyzer, "analyze_requirement", new=AsyncMock(return_value=mock_analysis_result)), \
             patch.object(service.analyzer, "generate_clarification_questions", new=AsyncMock(return_value=mock_questions)), \
             patch.object(service.analyzer, "perform_feasibility_analysis", new=AsyncMock(return_value=mock_feasibility)), \
             patch("app.services.presale_ai_requirement_service.save_obj") as mock_save:

            req = RequirementAnalysisRequest(
                presale_ticket_id=1,
                raw_requirement="需要一套机器人系统",
            )
            result = await service.analyze_requirement(req, user_id=1)

        mock_save.assert_called_once()

    def test_get_analysis_found(self):
        """获取存在的分析记录"""
        service, db = _make_service()
        mock_a = _make_mock_analysis()
        db.query.return_value.filter.return_value.first.return_value = mock_a

        result = service.get_analysis(1)
        assert result is mock_a

    def test_get_analysis_not_found(self):
        """获取不存在的分析记录"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_analysis(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_refine_requirement_not_found(self):
        """精炼不存在的分析抛出异常"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        req = RequirementRefinementRequest(analysis_id=999)
        with pytest.raises(ValueError, match="not found"):
            await service.refine_requirement(req, user_id=1)

    @pytest.mark.asyncio
    async def test_refine_requirement_success(self):
        """精炼成功更新数据库"""
        service, db = _make_service()
        mock_a = _make_mock_analysis()
        db.query.return_value.filter.return_value.first.return_value = mock_a

        refined_result = {
            "structured_requirement": {"project_type": "精炼后"},
            "equipment_list": [],
            "process_flow": [],
            "technical_parameters": [],
            "acceptance_criteria": [],
            "confidence_score": 0.85,
        }

        with patch.object(service.analyzer, "analyze_requirement", new=AsyncMock(return_value=refined_result)):
            req = RequirementRefinementRequest(analysis_id=1, additional_context="补充信息")
            result = await service.refine_requirement(req, user_id=1)

        db.commit.assert_called()
        assert mock_a.is_refined is True
        assert mock_a.refinement_count == 1

    def test_get_clarification_questions_not_found(self):
        """工单无分析记录时返回空"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        questions, analysis_id = service.get_clarification_questions(ticket_id=1)
        assert questions == []
        assert analysis_id is None

    def test_get_clarification_questions_with_data(self):
        """获取澄清问题列表"""
        service, db = _make_service()
        mock_a = _make_mock_analysis(clarification_questions=[
            {"question_id": 1, "category": "技术", "question": "精度?", "importance": "high"}
        ])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_a

        questions, analysis_id = service.get_clarification_questions(ticket_id=1)
        assert len(questions) == 1
        assert questions[0].question == "精度?"

    def test_update_structured_requirement_not_found(self):
        """更新不存在的分析抛出异常"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        req = RequirementUpdateRequest(analysis_id=999, acceptance_criteria=["标准1"])
        with pytest.raises(ValueError, match="not found"):
            service.update_structured_requirement(req, user_id=1)

    def test_update_structured_requirement_success(self):
        """成功更新结构化需求"""
        service, db = _make_service()
        mock_a = _make_mock_analysis()
        db.query.return_value.filter.return_value.first.return_value = mock_a

        req = RequirementUpdateRequest(analysis_id=1, acceptance_criteria=["验收标准1"])
        result = service.update_structured_requirement(req, user_id=1)

        assert mock_a.acceptance_criteria == ["验收标准1"]
        assert mock_a.status == "reviewed"
        db.commit.assert_called()

    def test_get_requirement_confidence_no_analysis(self):
        """无分析记录时置信度为0"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = service.get_requirement_confidence(ticket_id=1)
        assert result["confidence_score"] == 0.0
        assert result["assessment"] == "no_analysis"

    def test_get_requirement_confidence_high(self):
        """高置信度评估"""
        service, db = _make_service()
        mock_a = _make_mock_analysis(confidence_score=0.9)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_a

        result = service.get_requirement_confidence(ticket_id=1)
        assert result["assessment"] == "high_confidence"
        assert result["confidence_score"] == 0.9

    def test_get_requirement_confidence_medium(self):
        """中等置信度评估"""
        service, db = _make_service()
        mock_a = _make_mock_analysis(confidence_score=0.65)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_a

        result = service.get_requirement_confidence(ticket_id=1)
        assert result["assessment"] == "medium_confidence"

    def test_get_requirement_confidence_low(self):
        """低置信度评估"""
        service, db = _make_service()
        mock_a = _make_mock_analysis(confidence_score=0.4)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_a

        result = service.get_requirement_confidence(ticket_id=1)
        assert result["assessment"] == "low_confidence"
