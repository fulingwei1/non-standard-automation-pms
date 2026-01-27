# -*- coding: utf-8 -*-
"""
ai_assessment_service 单元测试

测试 AI 分析服务的各个方法：
- 服务可用性检查
- 需求分析
- 案例相似度分析
- 提示词构建
- API 调用
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_assessment_service import AIAssessmentService


@pytest.mark.unit
class TestIsAvailable:
    """测试 is_available 方法"""

    def test_returns_true_when_api_key_configured(self):
        """测试配置 API key 时返回 True"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.api_key = "test-api-key"
            service.enabled = True

            assert service.is_available() is True

    def test_returns_false_when_no_api_key(self):
        """测试未配置 API key 时返回 False"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.api_key = ""
            service.enabled = False

            assert service.is_available() is False


@pytest.mark.unit
class TestBuildAnalysisPrompt:
    """测试 _build_analysis_prompt 方法"""

    def test_builds_prompt_with_all_fields(self):
        """测试包含所有字段的提示词构建"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()

            requirement_data = {
            "project_name": "测试自动化项目",
            "industry": "新能源",
            "customer_name": "测试客户",
            "budget_value": 100,
            "budget_status": "已确认",
            "tech_requirements": "需要开发一套自动化测试系统",
            "delivery_months": 6,
            "requirement_maturity": 4,
            }

            prompt = service._build_analysis_prompt(requirement_data)

            assert "测试自动化项目" in prompt
            assert "新能源" in prompt
            assert "测试客户" in prompt
            assert "100 万元" in prompt
            assert "6 个月" in prompt
            assert "4 级" in prompt
            assert "已确认" in prompt
            assert "自动化测试系统" in prompt

    def test_builds_prompt_with_camelcase_fields(self):
        """测试驼峰命名字段的提示词构建"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()

            requirement_data = {
            "projectName": "ICT测试设备",
            "customerName": "ABC公司",
            "budgetValue": 50,
            "budgetStatus": "待定",
            "techRequirements": "自动ICT测试需求",
            "deliveryMonths": 3,
            "requirementMaturity": 3,
            }

            prompt = service._build_analysis_prompt(requirement_data)

            assert "ICT测试设备" in prompt
            assert "ABC公司" in prompt
            assert "50 万元" in prompt
            assert "3 个月" in prompt

    def test_builds_prompt_with_missing_fields(self):
        """测试缺少字段时的提示词构建"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()

            requirement_data = {
            "project_name": "简单项目",
            }

            prompt = service._build_analysis_prompt(requirement_data)

            assert "简单项目" in prompt
            assert "未填写" in prompt  # 缺失字段应显示"未填写"

    def test_prompt_structure(self):
        """测试提示词包含必要的分析维度"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()

            prompt = service._build_analysis_prompt({})

            assert "项目可行性评估" in prompt
            assert "需求成熟度评估" in prompt
            assert "风险点识别" in prompt
            assert "建议的技术方案方向" in prompt
            assert "立项建议" in prompt


@pytest.mark.unit
class TestBuildSimilarityPrompt:
    """测试 _build_similarity_prompt 方法"""

    def test_builds_similarity_prompt(self):
        """测试相似度分析提示词构建"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()

            current_project = {
            "project_name": "当前项目",
            "industry": "储能",
            "product_type": "BMS系统",
            "budget_value": 200,
            }

            historical_cases = [
            {"project_name": "历史项目1", "core_failure_reason": "需求不清晰"},
            {"project_name": "历史项目2", "core_failure_reason": "交付延期"},
            ]

            prompt = service._build_similarity_prompt(current_project, historical_cases)

            assert "当前项目" in prompt
            assert "储能" in prompt
            assert "BMS系统" in prompt
            assert "历史项目1" in prompt
            assert "需求不清晰" in prompt
            assert "历史项目2" in prompt
            assert "交付延期" in prompt

    def test_limits_historical_cases(self):
        """测试历史案例数量限制"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()

            current_project = {"project_name": "测试项目"}
            # 创建 10 个历史案例，但应该只取前 5 个
        historical_cases = [
        {"project_name": f"案例{i}", "core_failure_reason": f"原因{i}"}
        for i in range(10)
        ]

        prompt = service._build_similarity_prompt(current_project, historical_cases)

            # 应该只包含前 5 个案例
        assert "案例0" in prompt
        assert "案例4" in prompt
        assert "案例5" not in prompt
        assert "案例9" not in prompt


@pytest.mark.unit
class TestAnalyzeRequirement:
    """测试 analyze_requirement 方法"""

    def test_returns_none_when_not_available(self):
        """测试服务不可用时返回 None"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.enabled = False
            service.api_key = ""

            result = asyncio.run(service.analyze_requirement({"project_name": "测试"}))

            assert result is None

    def test_calls_api_when_available(self):
        """测试服务可用时调用 API"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.enabled = True
            service.api_key = "test-key"
            service.model = "qwen-plus"

            # Mock _call_qwen 方法
        service._call_qwen = AsyncMock(return_value="AI 分析结果")

        result = asyncio.run(service.analyze_requirement({"project_name": "测试项目"}))

        assert result == "AI 分析结果"
        service._call_qwen.assert_called_once()

    def test_returns_none_on_api_error(self):
        """测试 API 调用失败时返回 None"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.enabled = True
            service.api_key = "test-key"
            service.model = "qwen-plus"

            # Mock _call_qwen 抛出异常
        service._call_qwen = AsyncMock(side_effect=Exception("API 错误"))

        result = asyncio.run(service.analyze_requirement({"project_name": "测试项目"}))

        assert result is None


@pytest.mark.unit
class TestAnalyzeCaseSimilarity:
    """测试 analyze_case_similarity 方法"""

    def test_returns_none_when_not_available(self):
        """测试服务不可用时返回 None"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.enabled = False
            service.api_key = ""

            result = asyncio.run(service.analyze_case_similarity(
            {"project_name": "测试"},
            [{"project_name": "历史案例"}]
            ))

            assert result is None

    def test_calls_api_when_available(self):
        """测试服务可用时调用 API"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.enabled = True
            service.api_key = "test-key"
            service.model = "qwen-plus"

            service._call_qwen = AsyncMock(return_value="相似度分析结果")

            result = asyncio.run(service.analyze_case_similarity(
            {"project_name": "当前项目"},
            [{"project_name": "历史案例"}]
            ))

            assert result == "相似度分析结果"
            service._call_qwen.assert_called_once()

    def test_returns_none_on_api_error(self):
        """测试 API 调用失败时返回 None"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.enabled = True
            service.api_key = "test-key"
            service.model = "qwen-plus"

            service._call_qwen = AsyncMock(side_effect=Exception("网络错误"))

            result = asyncio.run(service.analyze_case_similarity(
            {"project_name": "当前项目"},
            [{"project_name": "历史案例"}]
            ))

            assert result is None


@pytest.mark.unit
class TestCallQwen:
    """测试 _call_qwen 方法"""

    def test_raises_error_when_no_api_key(self):
        """测试无 API key 时抛出错误"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.api_key = ""

            with pytest.raises(ValueError, match="未配置 ALIBABA_API_KEY"):
                asyncio.run(service._call_qwen("测试提示词"))

    def test_makes_api_call_correctly(self):
        """测试正确发起 API 调用"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.api_key = "test-api-key"
            service.model = "qwen-plus"

            mock_response = MagicMock()
            mock_response.json.return_value = {
            "choices": [
            {"message": {"content": "这是 AI 的回复"}}
            ]
            }
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                MockClient.return_value.__aenter__.return_value = mock_client

                result = asyncio.run(service._call_qwen("测试提示词"))

                assert result == "这是 AI 的回复"
                mock_client.post.assert_called_once()

    def test_raises_error_on_invalid_response(self):
        """测试 API 返回格式异常时抛出错误"""
        with patch.object(AIAssessmentService, "__init__", lambda s: None):
            service = AIAssessmentService()
            service.api_key = "test-api-key"
            service.model = "qwen-plus"

            mock_response = MagicMock()
            mock_response.json.return_value = {"error": "invalid request"}
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                MockClient.return_value.__aenter__.return_value = mock_client

                with pytest.raises(ValueError, match="API返回格式异常"):
                    asyncio.run(service._call_qwen("测试提示词"))


@pytest.mark.unit
class TestServiceInitialization:
    """测试服务初始化"""

    def test_init_with_env_var(self):
        """测试使用环境变量初始化"""
        with patch("app.services.ai_assessment_service.ALIBABA_API_KEY", "test-key"):
            with patch("app.services.ai_assessment_service.ALIBABA_MODEL", "qwen-max"):
                service = AIAssessmentService()
                assert service.api_key == "test-key"
                assert service.model == "qwen-max"
                assert service.enabled is True

    def test_init_without_env_var(self):
        """测试未配置环境变量时初始化"""
        with patch("app.services.ai_assessment_service.ALIBABA_API_KEY", ""):
            with patch("app.services.ai_assessment_service.ALIBABA_MODEL", "qwen-plus"):
                service = AIAssessmentService()
                assert service.api_key == ""
                assert service.enabled is False
