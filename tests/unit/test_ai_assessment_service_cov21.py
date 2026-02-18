# -*- coding: utf-8 -*-
"""第二十一批：AI评估服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

pytest.importorskip("app.services.ai_assessment_service")


@pytest.fixture
def service_no_key():
    """无 API key 的服务实例"""
    with patch.dict("os.environ", {"ALIBABA_API_KEY": "", "ALIBABA_MODEL": ""}):
        from app.services.ai_assessment_service import AIAssessmentService
        return AIAssessmentService()


@pytest.fixture
def service_with_key():
    """有 API key 的服务实例"""
    with patch.dict("os.environ", {"ALIBABA_API_KEY": "test-key-123", "ALIBABA_MODEL": "qwen-plus"}):
        from app.services.ai_assessment_service import AIAssessmentService
        return AIAssessmentService()


class TestIsAvailable:
    def test_not_available_without_key(self):
        with patch.dict("os.environ", {"ALIBABA_API_KEY": ""}):
            from app.services.ai_assessment_service import AIAssessmentService
            svc = AIAssessmentService()
            assert svc.is_available() is False

    def test_available_with_key(self):
        with patch.dict("os.environ", {"ALIBABA_API_KEY": "sk-test"}):
            from app.services.ai_assessment_service import AIAssessmentService
            svc = AIAssessmentService()
            assert svc.is_available() is True


class TestAnalyzeRequirement:
    @pytest.mark.asyncio
    async def test_returns_none_when_unavailable(self, service_no_key):
        result = await service_no_key.analyze_requirement({"project_name": "测试项目"})
        assert result is None

    @pytest.mark.asyncio
    async def test_calls_qwen_when_available(self, service_with_key):
        with patch.object(service_with_key, "_call_qwen", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "AI分析结果"
            result = await service_with_key.analyze_requirement({
                "project_name": "测试项目",
                "industry": "汽车",
                "tech_requirements": "AGV输送系统"
            })
        assert result == "AI分析结果"
        mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, service_with_key):
        with patch.object(service_with_key, "_call_qwen", new_callable=AsyncMock,
                          side_effect=Exception("API Error")):
            result = await service_with_key.analyze_requirement({"project_name": "X"})
        assert result is None


class TestBuildAnalysisPrompt:
    def test_prompt_contains_project_info(self):
        with patch.dict("os.environ", {"ALIBABA_API_KEY": "key"}):
            from app.services.ai_assessment_service import AIAssessmentService
            svc = AIAssessmentService()
        prompt = svc._build_analysis_prompt({
            "project_name": "智能仓储项目",
            "industry": "电商",
            "customer_name": "阿里巴巴",
            "budget_value": 500,
            "tech_requirements": "自动分拣系统"
        })
        assert "智能仓储项目" in prompt
        assert "电商" in prompt
        assert "阿里巴巴" in prompt
        assert "500" in prompt

    def test_prompt_handles_camel_case_keys(self):
        with patch.dict("os.environ", {"ALIBABA_API_KEY": "key"}):
            from app.services.ai_assessment_service import AIAssessmentService
            svc = AIAssessmentService()
        prompt = svc._build_analysis_prompt({
            "projectName": "项目A",
            "customerName": "客户B",
        })
        assert "项目A" in prompt
        assert "客户B" in prompt


class TestAnalyzeCaseSimilarity:
    @pytest.mark.asyncio
    async def test_returns_none_when_unavailable(self, service_no_key):
        result = await service_no_key.analyze_case_similarity({}, [])
        assert result is None

    @pytest.mark.asyncio
    async def test_calls_qwen_with_cases(self, service_with_key):
        cases = [{"project_name": "历史项目", "core_failure_reason": "交期延误"}]
        with patch.object(service_with_key, "_call_qwen", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "相似度分析"
            result = await service_with_key.analyze_case_similarity({"project_name": "新项目"}, cases)
        assert result == "相似度分析"
