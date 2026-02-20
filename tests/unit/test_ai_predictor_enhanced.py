# -*- coding: utf-8 -*-
"""
GLM5CostPredictor 完整测试套件
测试覆盖：AI模型调用、特征工程、预测结果处理、置信度计算、异常处理
"""

import json
import os
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from app.services.project_cost_prediction.ai_predictor import GLM5CostPredictor


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_api_key():
    """Mock API密钥"""
    return "test_glm_api_key_12345"


@pytest.fixture
def predictor(mock_api_key):
    """创建预测器实例"""
    return GLM5CostPredictor(api_key=mock_api_key)


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "project_code": "PRJ-2024-001",
        "project_name": "测试项目",
        "bac": 1000000,
        "planned_start": "2024-01-01",
        "planned_end": "2024-12-31",
        "current_pv": 500000,
        "current_ev": 450000,
        "current_ac": 480000,
        "current_cpi": 0.9375,
        "current_spi": 0.9,
        "percent_complete": 45
    }


@pytest.fixture
def sample_evm_history():
    """示例EVM历史数据"""
    return [
        {"period": "2024-01", "pv": 100000, "ev": 95000, "ac": 98000, "cpi": 0.969, "spi": 0.95},
        {"period": "2024-02", "pv": 200000, "ev": 190000, "ac": 195000, "cpi": 0.974, "spi": 0.95},
        {"period": "2024-03", "pv": 300000, "ev": 285000, "ac": 295000, "cpi": 0.966, "spi": 0.95},
        {"period": "2024-04", "pv": 400000, "ev": 370000, "ac": 390000, "cpi": 0.949, "spi": 0.925},
        {"period": "2024-05", "pv": 500000, "ev": 450000, "ac": 480000, "cpi": 0.9375, "spi": 0.9},
    ]


@pytest.fixture
def sample_current_evm():
    """当前EVM状态"""
    return {
        "cpi": 0.9375,
        "spi": 0.9,
        "ac": 480000,
        "ev": 450000,
        "pv": 500000,
        "percent_complete": 45
    }


@pytest.fixture
def mock_ai_eac_response():
    """Mock AI的EAC预测响应"""
    return json.dumps({
        "predicted_eac": 1066667,
        "confidence": 85,
        "prediction_method": "CPI_BASED_WITH_TREND_ADJUSTMENT",
        "eac_lower_bound": 1050000,
        "eac_upper_bound": 1100000,
        "eac_most_likely": 1066667,
        "reasoning": "基于当前CPI 0.9375和历史趋势分析",
        "key_assumptions": ["CPI保持当前水平", "无重大变更"],
        "uncertainty_factors": ["市场波动", "资源可用性"]
    })


@pytest.fixture
def mock_ai_risk_response():
    """Mock AI的风险分析响应"""
    return json.dumps({
        "overrun_probability": 75,
        "risk_level": "HIGH",
        "risk_score": 72,
        "risk_factors": [
            {
                "factor": "CPI持续下降",
                "impact": "HIGH",
                "weight": 0.4,
                "description": "成本效率持续恶化",
                "evidence": "最近3期CPI从0.969降至0.9375"
            }
        ],
        "trend_analysis": "成本控制趋势恶化",
        "cost_trend": "DECLINING",
        "key_concerns": ["成本超支风险高", "资源效率低"],
        "early_warning_signals": ["CPI<0.95", "SPI持续<1.0"]
    })


@pytest.fixture
def mock_ai_optimization_response():
    """Mock AI的优化建议响应"""
    return json.dumps([
        {
            "title": "优化资源配置",
            "type": "RESOURCE_OPTIMIZATION",
            "priority": "CRITICAL",
            "description": "调整团队结构以提升效率",
            "current_situation": "当前资源利用率偏低",
            "proposed_action": "重新分配资源",
            "implementation_steps": [
                {
                    "step": 1,
                    "action": "评估当前资源",
                    "duration_days": 5,
                    "responsible": "项目经理"
                }
            ],
            "estimated_cost_saving": 50000,
            "implementation_cost": 10000,
            "roi_percentage": 400,
            "impact_on_schedule": "NEUTRAL",
            "impact_on_quality": "POSITIVE",
            "implementation_risk": "LOW",
            "ai_confidence_score": 88,
            "ai_reasoning": "基于历史数据和行业最佳实践"
        }
    ])


# =============================================================================
# 初始化测试 (5个测试)
# =============================================================================

class TestInitialization:
    """测试初始化功能"""

    def test_init_with_api_key(self, mock_api_key):
        """测试使用API密钥初始化"""
        predictor = GLM5CostPredictor(api_key=mock_api_key)
        assert predictor.api_key == mock_api_key
        assert predictor.calculator is not None

    def test_init_with_env_var(self, mock_api_key):
        """测试从环境变量获取API密钥"""
        with patch.dict(os.environ, {"GLM_API_KEY": mock_api_key}):
            predictor = GLM5CostPredictor()
            assert predictor.api_key == mock_api_key

    def test_init_without_api_key(self):
        """测试缺少API密钥时抛出异常"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GLM API密钥未配置"):
                GLM5CostPredictor()

    def test_init_api_base_url(self, predictor):
        """测试API基础URL设置正确"""
        assert predictor.API_BASE_URL == "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def test_init_calculator_instance(self, predictor):
        """测试EVM计算器实例创建"""
        from app.services.evm_service import EVMCalculator
        assert isinstance(predictor.calculator, EVMCalculator)


# =============================================================================
# EAC预测测试 (8个测试)
# =============================================================================

class TestPredictEAC:
    """测试EAC预测功能"""

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_success(self, mock_api, predictor, sample_project_data, 
                                  sample_evm_history, mock_ai_eac_response):
        """测试成功预测EAC"""
        mock_api.return_value = mock_ai_eac_response
        
        result = predictor.predict_eac(sample_project_data, sample_evm_history)
        
        assert result["predicted_eac"] == 1066667
        assert result["confidence"] == 85
        assert result["prediction_method"] == "CPI_BASED_WITH_TREND_ADJUSTMENT"
        mock_api.assert_called_once()

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_with_additional_context(self, mock_api, predictor, 
                                                   sample_project_data, sample_evm_history,
                                                   mock_ai_eac_response):
        """测试带额外上下文的EAC预测"""
        mock_api.return_value = mock_ai_eac_response
        additional_context = {"team_size": 10, "complexity": "high"}
        
        result = predictor.predict_eac(sample_project_data, sample_evm_history, additional_context)
        
        assert result is not None
        assert "predicted_eac" in result

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_temperature_setting(self, mock_api, predictor, 
                                              sample_project_data, sample_evm_history):
        """测试EAC预测使用正确的temperature参数"""
        mock_api.return_value = "{}"
        
        predictor.predict_eac(sample_project_data, sample_evm_history)
        
        call_args = mock_api.call_args
        assert call_args[1]["temperature"] == 0.3

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_bounds_validation(self, mock_api, predictor, 
                                            sample_project_data, sample_evm_history,
                                            mock_ai_eac_response):
        """测试EAC预测边界值验证"""
        mock_api.return_value = mock_ai_eac_response
        
        result = predictor.predict_eac(sample_project_data, sample_evm_history)
        
        assert result["eac_lower_bound"] <= result["eac_most_likely"] <= result["eac_upper_bound"]

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_empty_history(self, mock_api, predictor, sample_project_data):
        """测试空历史数据的EAC预测"""
        mock_api.return_value = "{}"
        
        result = predictor.predict_eac(sample_project_data, [])
        
        assert result is not None
        assert "predicted_eac" in result

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_api_failure_fallback(self, mock_api, predictor, 
                                                sample_project_data, sample_evm_history):
        """测试API失败时的回退机制"""
        mock_api.return_value = "invalid json response"
        
        result = predictor.predict_eac(sample_project_data, sample_evm_history)
        
        assert result["prediction_method"] == "CPI_BASED_FALLBACK"
        assert result["confidence"] == 50.0

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_includes_reasoning(self, mock_api, predictor, 
                                             sample_project_data, sample_evm_history,
                                             mock_ai_eac_response):
        """测试预测结果包含推理过程"""
        mock_api.return_value = mock_ai_eac_response
        
        result = predictor.predict_eac(sample_project_data, sample_evm_history)
        
        assert "reasoning" in result
        assert isinstance(result["reasoning"], str)

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_predict_eac_key_assumptions(self, mock_api, predictor, 
                                          sample_project_data, sample_evm_history,
                                          mock_ai_eac_response):
        """测试预测结果包含关键假设"""
        mock_api.return_value = mock_ai_eac_response
        
        result = predictor.predict_eac(sample_project_data, sample_evm_history)
        
        assert "key_assumptions" in result
        assert isinstance(result["key_assumptions"], list)


# =============================================================================
# 风险分析测试 (7个测试)
# =============================================================================

class TestAnalyzeCostRisks:
    """测试成本风险分析功能"""

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_success(self, mock_api, predictor, sample_project_data,
                                    sample_evm_history, sample_current_evm,
                                    mock_ai_risk_response):
        """测试成功分析风险"""
        mock_api.return_value = mock_ai_risk_response
        
        result = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                               sample_current_evm)
        
        assert result["risk_level"] == "HIGH"
        assert result["overrun_probability"] == 75

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_temperature(self, mock_api, predictor, sample_project_data,
                                        sample_evm_history, sample_current_evm):
        """测试风险分析使用正确的temperature"""
        mock_api.return_value = "{}"
        
        predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                      sample_current_evm)
        
        call_args = mock_api.call_args
        assert call_args[1]["temperature"] == 0.4

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_factors_structure(self, mock_api, predictor, sample_project_data,
                                              sample_evm_history, sample_current_evm,
                                              mock_ai_risk_response):
        """测试风险因素结构完整性"""
        mock_api.return_value = mock_ai_risk_response
        
        result = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                               sample_current_evm)
        
        assert "risk_factors" in result
        assert len(result["risk_factors"]) > 0
        factor = result["risk_factors"][0]
        assert "factor" in factor
        assert "impact" in factor
        assert "weight" in factor

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_trend_analysis(self, mock_api, predictor, sample_project_data,
                                           sample_evm_history, sample_current_evm,
                                           mock_ai_risk_response):
        """测试趋势分析包含在结果中"""
        mock_api.return_value = mock_ai_risk_response
        
        result = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                               sample_current_evm)
        
        assert "trend_analysis" in result
        assert "cost_trend" in result
        assert result["cost_trend"] in ["IMPROVING", "STABLE", "DECLINING", "VOLATILE"]

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_early_warnings(self, mock_api, predictor, sample_project_data,
                                           sample_evm_history, sample_current_evm,
                                           mock_ai_risk_response):
        """测试预警信号识别"""
        mock_api.return_value = mock_ai_risk_response
        
        result = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                               sample_current_evm)
        
        assert "early_warning_signals" in result
        assert isinstance(result["early_warning_signals"], list)

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_failure_fallback(self, mock_api, predictor, sample_project_data,
                                             sample_evm_history, sample_current_evm):
        """测试解析失败时的默认值"""
        mock_api.return_value = "invalid json"
        
        result = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                               sample_current_evm)
        
        assert result["risk_level"] == "MEDIUM"
        assert result["overrun_probability"] == 50.0

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_analyze_risks_score_range(self, mock_api, predictor, sample_project_data,
                                        sample_evm_history, sample_current_evm,
                                        mock_ai_risk_response):
        """测试风险评分在有效范围内"""
        mock_api.return_value = mock_ai_risk_response
        
        result = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                               sample_current_evm)
        
        assert 0 <= result["risk_score"] <= 100
        assert 0 <= result["overrun_probability"] <= 100


# =============================================================================
# 优化建议测试 (6个测试)
# =============================================================================

class TestGenerateOptimizationSuggestions:
    """测试优化建议生成功能"""

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_generate_suggestions_success(self, mock_api, predictor, sample_project_data,
                                           mock_ai_optimization_response):
        """测试成功生成优化建议"""
        mock_api.return_value = mock_ai_optimization_response
        prediction_result = {"predicted_eac": 1066667}
        risk_analysis = {"risk_level": "HIGH"}
        
        result = predictor.generate_optimization_suggestions(
            sample_project_data, prediction_result, risk_analysis
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["type"] == "RESOURCE_OPTIMIZATION"

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_generate_suggestions_temperature(self, mock_api, predictor, sample_project_data):
        """测试优化建议使用正确的temperature"""
        mock_api.return_value = "[]"
        
        predictor.generate_optimization_suggestions(
            sample_project_data, {}, {}
        )
        
        call_args = mock_api.call_args
        assert call_args[1]["temperature"] == 0.6

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_generate_suggestions_structure(self, mock_api, predictor, sample_project_data,
                                             mock_ai_optimization_response):
        """测试建议结构完整性"""
        mock_api.return_value = mock_ai_optimization_response
        
        result = predictor.generate_optimization_suggestions(
            sample_project_data, {}, {}
        )
        
        suggestion = result[0]
        assert "title" in suggestion
        assert "priority" in suggestion
        assert "estimated_cost_saving" in suggestion
        assert "implementation_steps" in suggestion

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_generate_suggestions_roi_calculation(self, mock_api, predictor, sample_project_data,
                                                   mock_ai_optimization_response):
        """测试ROI计算包含在建议中"""
        mock_api.return_value = mock_ai_optimization_response
        
        result = predictor.generate_optimization_suggestions(
            sample_project_data, {}, {}
        )
        
        assert "roi_percentage" in result[0]
        assert result[0]["roi_percentage"] > 0

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_generate_suggestions_failure_fallback(self, mock_api, predictor, sample_project_data):
        """测试解析失败时返回默认建议"""
        mock_api.return_value = "invalid json"
        
        result = predictor.generate_optimization_suggestions(
            sample_project_data, {}, {}
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["ai_confidence_score"] == 0

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_generate_suggestions_dict_to_list_conversion(self, mock_api, predictor, 
                                                           sample_project_data):
        """测试单个字典转换为列表"""
        single_suggestion = {
            "title": "测试建议",
            "type": "PROCESS_IMPROVEMENT",
            "priority": "HIGH"
        }
        mock_api.return_value = json.dumps(single_suggestion)
        
        result = predictor.generate_optimization_suggestions(
            sample_project_data, {}, {}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1


# =============================================================================
# API调用测试 (6个测试)
# =============================================================================

class TestCallGLM5API:
    """测试GLM-5 API调用功能"""

    @patch('requests.post')
    def test_api_call_success(self, mock_post, predictor):
        """测试成功的API调用"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试响应"}}]
        }
        mock_post.return_value = mock_response
        
        result = predictor._call_glm5_api("测试提示词")
        
        assert result == "测试响应"
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_api_call_headers(self, mock_post, predictor, mock_api_key):
        """测试API调用包含正确的headers"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        predictor._call_glm5_api("提示词")
        
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {mock_api_key}"
        assert headers["Content-Type"] == "application/json"

    @patch('requests.post')
    def test_api_call_payload_structure(self, mock_post, predictor):
        """测试API请求payload结构"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        predictor._call_glm5_api("提示词", temperature=0.7, max_tokens=2000)
        
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "glm-4-plus"
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 2000
        assert len(payload["messages"]) == 2

    @patch('requests.post')
    def test_api_call_timeout(self, mock_post, predictor):
        """测试API调用设置超时"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        predictor._call_glm5_api("提示词")
        
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30

    @patch('requests.post')
    def test_api_call_network_error(self, mock_post, predictor):
        """测试网络错误处理"""
        mock_post.side_effect = requests.exceptions.ConnectionError("网络错误")
        
        with pytest.raises(Exception, match="GLM-5 API调用失败"):
            predictor._call_glm5_api("提示词")

    @patch('requests.post')
    def test_api_call_http_error(self, mock_post, predictor):
        """测试HTTP错误处理"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401")
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="GLM-5 API调用失败"):
            predictor._call_glm5_api("提示词")


# =============================================================================
# 响应解析测试 (5个测试)
# =============================================================================

class TestResponseParsing:
    """测试响应解析功能"""

    def test_parse_eac_valid_json(self, predictor, sample_project_data):
        """测试解析有效的EAC JSON响应"""
        response = json.dumps({
            "predicted_eac": 1100000,
            "confidence": 90,
            "prediction_method": "AI_ANALYSIS",
            "reasoning": "基于综合分析"
        })
        
        result = predictor._parse_eac_prediction(response, sample_project_data)
        
        assert result["predicted_eac"] == 1100000
        assert result["confidence"] == 90

    def test_parse_eac_json_with_wrapper_text(self, predictor, sample_project_data):
        """测试解析包含额外文本的JSON"""
        response = "这是分析结果：\n" + json.dumps({"predicted_eac": 1050000}) + "\n以上是结果"
        
        result = predictor._parse_eac_prediction(response, sample_project_data)
        
        assert result["predicted_eac"] == 1050000

    def test_parse_risk_valid_json(self, predictor):
        """测试解析有效的风险分析JSON"""
        response = json.dumps({
            "risk_level": "CRITICAL",
            "overrun_probability": 85,
            "risk_score": 88
        })
        
        result = predictor._parse_risk_analysis(response)
        
        assert result["risk_level"] == "CRITICAL"
        assert result["overrun_probability"] == 85

    def test_parse_optimization_array(self, predictor):
        """测试解析优化建议数组"""
        response = json.dumps([
            {"title": "建议1", "priority": "HIGH"},
            {"title": "建议2", "priority": "MEDIUM"}
        ])
        
        result = predictor._parse_optimization_suggestions(response)
        
        assert len(result) == 2
        assert result[0]["title"] == "建议1"

    def test_parse_optimization_with_wrapper(self, predictor):
        """测试解析带包装文本的优化建议"""
        response = "建议如下：\n[" + json.dumps({"title": "建议"}) + "]\n结束"
        
        result = predictor._parse_optimization_suggestions(response)
        
        assert isinstance(result, list)


# =============================================================================
# 提示词构建测试 (4个测试)
# =============================================================================

class TestPromptBuilding:
    """测试提示词构建功能"""

    def test_build_eac_prompt_includes_project_info(self, predictor, sample_project_data,
                                                      sample_evm_history):
        """测试EAC提示词包含项目信息"""
        prompt = predictor._build_eac_prediction_prompt(
            sample_project_data, sample_evm_history, None
        )
        
        assert sample_project_data["project_code"] in prompt
        assert str(sample_project_data["bac"]) in prompt

    def test_build_risk_prompt_includes_cpi(self, predictor, sample_project_data,
                                             sample_evm_history, sample_current_evm):
        """测试风险提示词包含CPI信息"""
        prompt = predictor._build_risk_analysis_prompt(
            sample_project_data, sample_evm_history, sample_current_evm
        )
        
        assert str(sample_current_evm["cpi"]) in prompt

    def test_build_optimization_prompt_includes_eac(self, predictor, sample_project_data):
        """测试优化提示词包含EAC预测"""
        prediction = {"predicted_eac": 1100000}
        risk = {"risk_level": "HIGH"}
        
        prompt = predictor._build_optimization_prompt(
            sample_project_data, prediction, risk
        )
        
        assert "1100000" in prompt
        assert "HIGH" in prompt

    def test_build_eac_prompt_with_context(self, predictor, sample_project_data,
                                            sample_evm_history):
        """测试包含额外上下文的提示词"""
        context = {"team_changes": "新增3人"}
        
        prompt = predictor._build_eac_prediction_prompt(
            sample_project_data, sample_evm_history, context
        )
        
        assert "team_changes" in prompt


# =============================================================================
# EVM历史总结测试 (4个测试)
# =============================================================================

class TestSummarizeEVMHistory:
    """测试EVM历史数据总结功能"""

    def test_summarize_empty_history(self, predictor):
        """测试空历史数据总结"""
        summary = predictor._summarize_evm_history([])
        
        assert summary == "无历史数据"

    def test_summarize_recent_data(self, predictor, sample_evm_history):
        """测试总结最近6期数据"""
        summary = predictor._summarize_evm_history(sample_evm_history)
        
        assert "2024-05" in summary  # 最新期
        assert "CPI" in summary

    def test_summarize_declining_trend(self, predictor):
        """测试识别CPI下降趋势"""
        history = [
            {"period": "P1", "cpi": 1.0, "spi": 1.0},
            {"period": "P2", "cpi": 0.95, "spi": 1.0},
            {"period": "P3", "cpi": 0.90, "spi": 1.0}
        ]
        
        summary = predictor._summarize_evm_history(history)
        
        assert "下降" in summary or "恶化" in summary

    def test_summarize_improving_trend(self, predictor):
        """测试识别CPI上升趋势"""
        history = [
            {"period": "P1", "cpi": 0.90, "spi": 1.0},
            {"period": "P2", "cpi": 0.95, "spi": 1.0},
            {"period": "P3", "cpi": 1.0, "spi": 1.0}
        ]
        
        summary = predictor._summarize_evm_history(history)
        
        assert "上升" in summary or "改善" in summary


# =============================================================================
# 边界情况和异常处理测试 (5个测试)
# =============================================================================

class TestEdgeCasesAndExceptions:
    """测试边界情况和异常处理"""

    def test_zero_cpi_handling(self, predictor, sample_project_data):
        """测试CPI为0的情况"""
        project_data = sample_project_data.copy()
        project_data["current_cpi"] = 0
        
        response = "invalid"
        result = predictor._parse_eac_prediction(response, project_data)
        
        assert result["predicted_eac"] > 0  # 应使用回退值

    def test_negative_values_handling(self, predictor, sample_project_data):
        """测试负值处理"""
        response = json.dumps({"predicted_eac": -1000})
        
        result = predictor._parse_eac_prediction(response, sample_project_data)
        
        # 应该能处理或转换为合理值
        assert "predicted_eac" in result

    def test_very_large_eac_value(self, predictor, sample_project_data):
        """测试超大EAC值"""
        response = json.dumps({"predicted_eac": 999999999999})
        
        result = predictor._parse_eac_prediction(response, sample_project_data)
        
        assert result["predicted_eac"] == 999999999999

    @patch('requests.post')
    def test_api_timeout_handling(self, mock_post, predictor):
        """测试API超时处理"""
        mock_post.side_effect = requests.exceptions.Timeout("超时")
        
        with pytest.raises(Exception, match="GLM-5 API调用失败"):
            predictor._call_glm5_api("提示词")

    def test_malformed_json_in_response(self, predictor, sample_project_data):
        """测试响应中的格式错误JSON"""
        response = '{"predicted_eac": 1000000, "confidence": 85,}'  # 多余逗号
        
        # 应该使用回退机制
        result = predictor._parse_eac_prediction(response, sample_project_data)
        
        assert "predicted_eac" in result
        assert result["prediction_method"] == "CPI_BASED_FALLBACK"


# =============================================================================
# 集成测试 (2个测试)
# =============================================================================

class TestIntegration:
    """集成测试"""

    @patch('requests.post')
    def test_full_prediction_workflow(self, mock_post, predictor, sample_project_data,
                                       sample_evm_history, sample_current_evm,
                                       mock_ai_eac_response, mock_ai_risk_response,
                                       mock_ai_optimization_response):
        """测试完整的预测工作流"""
        # Mock API响应序列
        mock_response = Mock()
        mock_response.json.side_effect = [
            {"choices": [{"message": {"content": mock_ai_eac_response}}]},
            {"choices": [{"message": {"content": mock_ai_risk_response}}]},
            {"choices": [{"message": {"content": mock_ai_optimization_response}}]}
        ]
        mock_post.return_value = mock_response
        
        # 执行完整流程
        eac_result = predictor.predict_eac(sample_project_data, sample_evm_history)
        risk_result = predictor.analyze_cost_risks(
            sample_project_data, sample_evm_history, sample_current_evm
        )
        opt_result = predictor.generate_optimization_suggestions(
            sample_project_data, eac_result, risk_result
        )
        
        # 验证结果
        assert eac_result["predicted_eac"] > 0
        assert risk_result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert len(opt_result) > 0

    @patch.object(GLM5CostPredictor, '_call_glm5_api')
    def test_consistent_results_across_methods(self, mock_api, predictor, sample_project_data,
                                                 sample_evm_history, sample_current_evm):
        """测试各方法结果的一致性"""
        mock_api.side_effect = [
            json.dumps({"predicted_eac": 1100000, "confidence": 80}),
            json.dumps({"risk_level": "HIGH", "overrun_probability": 75}),
            json.dumps([{"title": "优化建议", "estimated_cost_saving": 50000}])
        ]
        
        eac = predictor.predict_eac(sample_project_data, sample_evm_history)
        risk = predictor.analyze_cost_risks(sample_project_data, sample_evm_history, 
                                             sample_current_evm)
        
        # 高超支预测应对应高风险
        if eac["predicted_eac"] > sample_project_data["bac"] * 1.1:
            assert risk["risk_level"] in ["HIGH", "CRITICAL"]
