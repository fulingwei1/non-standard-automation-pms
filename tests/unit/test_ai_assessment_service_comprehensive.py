# -*- coding: utf-8 -*-
"""
AIAssessmentService 综合单元测试

测试覆盖:
- is_available: 检查AI服务是否可用
- analyze_requirement: 分析需求并生成报告
- _build_analysis_prompt: 构建分析提示词
- analyze_case_similarity: 分析案例相似度
- _build_similarity_prompt: 构建相似度分析提示词
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestAIAssessmentServiceInit:
    """测试 AIAssessmentService 初始化"""

    def test_initializes_with_api_key(self):
        """测试使用API密钥初始化"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'), \
             patch('app.services.ai_assessment_service.ALIBABA_MODEL', 'qwen-plus'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()

            assert service.api_key == 'test-key'
            assert service.model == 'qwen-plus'
            assert service.enabled is True

    def test_initializes_without_api_key(self):
        """测试无API密钥初始化"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', ''), \
             patch('app.services.ai_assessment_service.ALIBABA_MODEL', 'qwen-plus'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()

            assert service.api_key == ''
            assert service.enabled is False


class TestIsAvailable:
    """测试 is_available 方法"""

    def test_returns_true_when_enabled(self):
        """测试服务可用时返回True"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()

            assert service.is_available() is True

    def test_returns_false_when_disabled(self):
        """测试服务不可用时返回False"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', ''):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()

            assert service.is_available() is False


class TestBuildAnalysisPrompt:
    """测试 _build_analysis_prompt 方法"""

    def test_builds_prompt_with_full_data(self):
        """测试使用完整数据构建提示词"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            requirement_data = {
                'project_name': '自动化测试设备',
                'industry': '新能源',
                'customer_name': '测试客户',
                'budget_value': 100,
                'budget_status': '已落实',
                'tech_requirements': '需要自动化测试功能',
                'delivery_months': 6,
                'requirement_maturity': 4
            }

            prompt = service._build_analysis_prompt(requirement_data)

            assert '自动化测试设备' in prompt
            assert '新能源' in prompt
            assert '测试客户' in prompt
            assert '100 万元' in prompt
            assert '6 个月' in prompt
            assert '4 级' in prompt

    def test_builds_prompt_with_camel_case_keys(self):
        """测试使用驼峰命名的键构建提示词"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            requirement_data = {
                'projectName': '测试项目',
                'customerName': '客户A',
                'budgetValue': 50,
                'budgetStatus': '待确认',
                'techRequirements': '技术需求',
                'deliveryMonths': 3,
                'requirementMaturity': 3
            }

            prompt = service._build_analysis_prompt(requirement_data)

            assert '测试项目' in prompt
            assert '客户A' in prompt
            assert '50 万元' in prompt

    def test_builds_prompt_with_missing_data(self):
        """测试使用缺失数据构建提示词"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            requirement_data = {}

            prompt = service._build_analysis_prompt(requirement_data)

            assert '未填写' in prompt
            assert '项目可行性评估' in prompt

    def test_prompt_contains_analysis_dimensions(self):
        """测试提示词包含分析维度"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            prompt = service._build_analysis_prompt({})

            assert '项目可行性评估' in prompt
            assert '需求成熟度评估' in prompt
            assert '风险点识别' in prompt
            assert '技术方案方向' in prompt
            assert '立项建议' in prompt


class TestAnalyzeRequirement:
    """测试 analyze_requirement 方法"""

    @pytest.mark.asyncio
    async def test_returns_none_when_not_available(self):
        """测试服务不可用时返回None"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', ''):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()

            result = await service.analyze_requirement({'project_name': '测试'})

            assert result is None

    @pytest.mark.asyncio
    async def test_calls_qwen_and_returns_analysis(self):
        """测试调用千问API并返回分析"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            service._call_qwen = AsyncMock(return_value="AI分析结果")

            result = await service.analyze_requirement({'project_name': '测试项目'})

            assert result == "AI分析结果"
            service._call_qwen.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        """测试异常时返回None"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            service._call_qwen = AsyncMock(side_effect=Exception("API error"))

            result = await service.analyze_requirement({'project_name': '测试'})

            assert result is None


class TestCallQwen:
    """测试 _call_qwen 方法"""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_api_key(self):
        """测试无API密钥时抛出错误"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', ''):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            service.api_key = ''

            with pytest.raises(ValueError, match="未配置 ALIBABA_API_KEY"):
                await service._call_qwen("test prompt")

    @pytest.mark.asyncio
    async def test_makes_correct_api_call(self):
        """测试发起正确的API调用"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'), \
             patch('httpx.AsyncClient') as mock_client:

            from app.services.ai_assessment_service import AIAssessmentService

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "分析结果"}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            service = AIAssessmentService()
            result = await service._call_qwen("测试提示词")

            assert result == "分析结果"

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_response(self):
        """测试响应格式无效时抛出错误"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'), \
             patch('httpx.AsyncClient') as mock_client:

            from app.services.ai_assessment_service import AIAssessmentService

            mock_response = MagicMock()
            mock_response.json.return_value = {"error": "bad request"}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            service = AIAssessmentService()

            with pytest.raises(ValueError, match="API返回格式异常"):
                await service._call_qwen("测试提示词")


class TestBuildSimilarityPrompt:
    """测试 _build_similarity_prompt 方法"""

    def test_builds_prompt_with_cases(self):
        """测试使用案例构建提示词"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            current_project = {
                'project_name': '新项目',
                'industry': '汽车',
                'product_type': '测试设备',
                'budget_value': 200
            }
            historical_cases = [
                {'project_name': '案例1', 'core_failure_reason': '技术问题'},
                {'project_name': '案例2', 'core_failure_reason': '预算不足'},
            ]

            prompt = service._build_similarity_prompt(current_project, historical_cases)

            assert '新项目' in prompt
            assert '汽车' in prompt
            assert '案例1' in prompt
            assert '案例2' in prompt
            assert '技术问题' in prompt

    def test_builds_prompt_with_empty_cases(self):
        """测试使用空案例列表构建提示词"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            current_project = {'project_name': '项目A'}
            historical_cases = []

            prompt = service._build_similarity_prompt(current_project, historical_cases)

            assert '项目A' in prompt

    def test_limits_cases_to_five(self):
        """测试限制案例数量为5"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            current_project = {'project_name': '项目'}
            historical_cases = [
                {'project_name': f'案例{i}', 'core_failure_reason': f'原因{i}'}
                for i in range(10)
            ]

            prompt = service._build_similarity_prompt(current_project, historical_cases)

            # 检查只有前5个案例
            assert '案例4' in prompt
            assert '案例5' not in prompt


class TestAnalyzeCaseSimilarity:
    """测试 analyze_case_similarity 方法"""

    @pytest.mark.asyncio
    async def test_returns_none_when_not_available(self):
        """测试服务不可用时返回None"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', ''):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()

            result = await service.analyze_case_similarity({}, [])

            assert result is None

    @pytest.mark.asyncio
    async def test_calls_qwen_and_returns_analysis(self):
        """测试调用千问API并返回分析"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            service._call_qwen = AsyncMock(return_value="相似度分析结果")

            result = await service.analyze_case_similarity(
                {'project_name': '项目'},
                [{'project_name': '案例1'}]
            )

            assert result == "相似度分析结果"

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        """测试异常时返回None"""
        with patch('app.services.ai_assessment_service.ALIBABA_API_KEY', 'test-key'):
            from app.services.ai_assessment_service import AIAssessmentService

            service = AIAssessmentService()
            service._call_qwen = AsyncMock(side_effect=Exception("API error"))

            result = await service.analyze_case_similarity({}, [])

            assert result is None
