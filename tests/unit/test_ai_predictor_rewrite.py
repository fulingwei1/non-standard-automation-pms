# -*- coding: utf-8 -*-
"""
GLM-5 AI成本预测器单元测试 - 重写版本

目标：
1. 只mock外部依赖（requests.post, os.getenv）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import json
import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.project_cost_prediction.ai_predictor import GLM5CostPredictor


class TestGLM5CostPredictorInit(unittest.TestCase):
    """测试初始化"""

    @patch("os.getenv")
    def test_init_with_api_key_param(self, mock_getenv):
        """测试通过参数传入API key"""
        predictor = GLM5CostPredictor(api_key="test_key_123")
        self.assertEqual(predictor.api_key, "test_key_123")
        # 不应该调用getenv
        mock_getenv.assert_not_called()

    @patch("os.getenv", return_value="env_key_456")
    def test_init_with_env_api_key(self, mock_getenv):
        """测试从环境变量获取API key"""
        predictor = GLM5CostPredictor()
        self.assertEqual(predictor.api_key, "env_key_456")
        mock_getenv.assert_called_once_with("GLM_API_KEY")

    @patch("os.getenv", return_value=None)
    def test_init_without_api_key_raises_error(self, mock_getenv):
        """测试无API key时抛出异常"""
        with self.assertRaises(ValueError) as cm:
            GLM5CostPredictor()
        self.assertIn("GLM API密钥未配置", str(cm.exception))

    @patch("os.getenv", return_value="test_key")
    def test_init_creates_evm_calculator(self, mock_getenv):
        """测试初始化时创建EVM计算器"""
        predictor = GLM5CostPredictor()
        self.assertIsNotNone(predictor.calculator)


class TestPredictEAC(unittest.TestCase):
    """测试EAC预测主方法"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")
        self.project_data = {
            "project_code": "PRJ001",
            "project_name": "测试项目",
            "bac": 100000,
            "planned_start": "2024-01-01",
            "planned_end": "2024-12-31",
            "current_pv": 50000,
            "current_ev": 45000,
            "current_ac": 48000,
            "current_cpi": 0.9375,
            "current_spi": 0.9,
            "percent_complete": 45,
        }
        self.evm_history = [
            {"period": "2024-01", "cpi": 1.0, "spi": 1.0, "ac": 10000, "ev": 10000},
            {"period": "2024-02", "cpi": 0.95, "spi": 0.95, "ac": 20000, "ev": 19000},
        ]

    @patch("requests.post")
    def test_predict_eac_success(self, mock_post):
        """测试成功预测EAC"""
        # Mock API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "predicted_eac": 110000,
                            "confidence": 85,
                            "prediction_method": "AI_ANALYSIS",
                            "eac_lower_bound": 105000,
                            "eac_upper_bound": 115000,
                            "eac_most_likely": 110000,
                            "reasoning": "基于CPI趋势分析",
                            "key_assumptions": ["CPI保持当前水平"],
                            "uncertainty_factors": ["市场变化"],
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = self.predictor.predict_eac(
            self.project_data, self.evm_history, {"market": "stable"}
        )

        # 验证结果
        self.assertEqual(result["predicted_eac"], 110000)
        self.assertEqual(result["confidence"], 85)
        self.assertEqual(result["prediction_method"], "AI_ANALYSIS")
        self.assertEqual(result["eac_lower_bound"], 105000)
        self.assertEqual(result["eac_upper_bound"], 115000)

        # 验证API调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("headers", call_args.kwargs)
        self.assertIn("Authorization", call_args.kwargs["headers"])

    @patch("requests.post")
    def test_predict_eac_with_additional_context(self, mock_post):
        """测试带额外上下文的EAC预测"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "predicted_eac": 105000,
                            "confidence": 90,
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        additional_context = {"risk_level": "low", "team_experience": "high"}
        result = self.predictor.predict_eac(
            self.project_data, self.evm_history, additional_context
        )

        self.assertIsNotNone(result)
        self.assertIn("predicted_eac", result)


class TestAnalyzeCostRisks(unittest.TestCase):
    """测试成本风险分析"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")
        self.project_data = {
            "project_code": "PRJ001",
            "bac": 100000,
        }
        self.evm_history = [
            {"period": "2024-01", "cpi": 1.0, "spi": 1.0},
            {"period": "2024-02", "cpi": 0.95, "spi": 0.95},
        ]
        self.current_evm = {
            "cpi": 0.9,
            "spi": 0.88,
            "ac": 50000,
            "percent_complete": 40,
        }

    @patch("requests.post")
    def test_analyze_cost_risks_success(self, mock_post):
        """测试成功分析风险"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "overrun_probability": 75,
                            "risk_level": "HIGH",
                            "risk_score": 78,
                            "risk_factors": [
                                {
                                    "factor": "CPI持续下降",
                                    "impact": "HIGH",
                                    "weight": 0.8,
                                    "description": "成本效率持续恶化",
                                    "evidence": "CPI从1.0降至0.9",
                                }
                            ],
                            "trend_analysis": "成本绩效恶化趋势明显",
                            "cost_trend": "DECLINING",
                            "key_concerns": ["成本超支风险高"],
                            "early_warning_signals": ["CPI低于0.95"],
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = self.predictor.analyze_cost_risks(
            self.project_data, self.evm_history, self.current_evm
        )

        # 验证结果
        self.assertEqual(result["overrun_probability"], 75)
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertEqual(result["risk_score"], 78)
        self.assertEqual(len(result["risk_factors"]), 1)
        self.assertEqual(result["cost_trend"], "DECLINING")


class TestGenerateOptimizationSuggestions(unittest.TestCase):
    """测试优化建议生成"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")
        self.project_data = {"project_code": "PRJ001", "bac": 100000}
        self.prediction_result = {"predicted_eac": 110000}
        self.risk_analysis = {
            "risk_level": "HIGH",
            "overrun_probability": 75,
            "risk_factors": [],
        }

    @patch("requests.post")
    def test_generate_optimization_suggestions_success(self, mock_post):
        """测试成功生成优化建议"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps([
                            {
                                "title": "优化资源配置",
                                "type": "RESOURCE_OPTIMIZATION",
                                "priority": "HIGH",
                                "description": "调整资源分配",
                                "current_situation": "资源利用率低",
                                "proposed_action": "重新分配人力",
                                "implementation_steps": [
                                    {
                                        "step": 1,
                                        "action": "评估当前资源",
                                        "duration_days": 3,
                                        "responsible": "项目经理",
                                    }
                                ],
                                "estimated_cost_saving": 5000,
                                "implementation_cost": 1000,
                                "roi_percentage": 400,
                                "impact_on_schedule": "NEUTRAL",
                                "impact_on_quality": "POSITIVE",
                                "implementation_risk": "LOW",
                                "ai_confidence_score": 85,
                                "ai_reasoning": "基于历史数据分析",
                            }
                        ])
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = self.predictor.generate_optimization_suggestions(
            self.project_data, self.prediction_result, self.risk_analysis
        )

        # 验证结果
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "优化资源配置")
        self.assertEqual(result[0]["type"], "RESOURCE_OPTIMIZATION")
        self.assertEqual(result[0]["estimated_cost_saving"], 5000)

    @patch("requests.post")
    def test_generate_optimization_suggestions_dict_response(self, mock_post):
        """测试API返回单个对象时自动转换为列表"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "title": "单个建议",
                            "type": "PROCESS_IMPROVEMENT",
                            "priority": "MEDIUM",
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = self.predictor.generate_optimization_suggestions(
            self.project_data, self.prediction_result, self.risk_analysis
        )

        # 应该转换为列表
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)


class TestCallGLM5API(unittest.TestCase):
    """测试GLM-5 API调用"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key_123")

    @patch("requests.post")
    def test_call_glm5_api_success(self, mock_post):
        """测试成功调用API"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response content"}}]
        }
        mock_post.return_value = mock_response

        result = self.predictor._call_glm5_api("test prompt")

        # 验证返回内容
        self.assertEqual(result, "AI response content")

        # 验证API调用参数
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["json"]["model"], "glm-4-plus")
        self.assertEqual(call_kwargs["json"]["temperature"], 0.5)
        self.assertEqual(call_kwargs["json"]["max_tokens"], 4000)
        self.assertEqual(len(call_kwargs["json"]["messages"]), 2)

    @patch("requests.post")
    def test_call_glm5_api_with_custom_params(self, mock_post):
        """测试自定义参数"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }
        mock_post.return_value = mock_response

        self.predictor._call_glm5_api(
            "test prompt", temperature=0.8, max_tokens=2000
        )

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["json"]["temperature"], 0.8)
        self.assertEqual(call_kwargs["json"]["max_tokens"], 2000)

    @patch("requests.post")
    def test_call_glm5_api_with_authorization_header(self, mock_post):
        """测试Authorization header"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }
        mock_post.return_value = mock_response

        self.predictor._call_glm5_api("test prompt")

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(
            call_kwargs["headers"]["Authorization"], "Bearer test_key_123"
        )
        self.assertEqual(call_kwargs["headers"]["Content-Type"], "application/json")

    @patch("requests.post")
    def test_call_glm5_api_request_exception(self, mock_post):
        """测试请求异常"""
        import requests
        
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with self.assertRaises(Exception) as cm:
            self.predictor._call_glm5_api("test prompt")

        self.assertIn("GLM-5 API调用失败", str(cm.exception))

    @patch("requests.post")
    def test_call_glm5_api_http_error(self, mock_post):
        """测试HTTP错误"""
        import requests
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP 500")
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.predictor._call_glm5_api("test prompt")

        self.assertIn("GLM-5 API调用失败", str(cm.exception))


class TestParseEACPrediction(unittest.TestCase):
    """测试EAC预测响应解析"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")
        self.project_data = {
            "bac": 100000,
            "current_cpi": 0.95,
            "current_ac": 50000,
            "current_ev": 47500,
        }

    def test_parse_eac_prediction_valid_json(self):
        """测试解析有效JSON"""
        ai_response = json.dumps({
            "predicted_eac": 105000,
            "confidence": 88,
            "prediction_method": "AI_ANALYSIS",
            "eac_lower_bound": 100000,
            "eac_upper_bound": 110000,
            "eac_most_likely": 105000,
            "reasoning": "详细分析",
            "key_assumptions": ["假设1", "假设2"],
            "uncertainty_factors": ["因素1"],
        })

        result = self.predictor._parse_eac_prediction(ai_response, self.project_data)

        self.assertEqual(result["predicted_eac"], 105000)
        self.assertEqual(result["confidence"], 88)
        self.assertEqual(result["prediction_method"], "AI_ANALYSIS")
        self.assertEqual(len(result["key_assumptions"]), 2)

    def test_parse_eac_prediction_json_with_prefix(self):
        """测试带前缀文本的JSON"""
        ai_response = """
        根据分析，预测结果如下：
        {
            "predicted_eac": 108000,
            "confidence": 82,
            "prediction_method": "HYBRID"
        }
        """

        result = self.predictor._parse_eac_prediction(ai_response, self.project_data)

        self.assertEqual(result["predicted_eac"], 108000)
        self.assertEqual(result["confidence"], 82)

    def test_parse_eac_prediction_fallback_on_invalid_json(self):
        """测试JSON解析失败时的回退逻辑"""
        ai_response = "这不是有效的JSON"

        result = self.predictor._parse_eac_prediction(ai_response, self.project_data)

        # 应该使用CPI方法回退
        self.assertIn("predicted_eac", result)
        self.assertEqual(result["prediction_method"], "CPI_BASED_FALLBACK")
        self.assertEqual(result["confidence"], 50.0)
        self.assertIn("AI解析失败", result["reasoning"])

    def test_parse_eac_prediction_fallback_calculation(self):
        """测试回退计算逻辑"""
        ai_response = "invalid"

        result = self.predictor._parse_eac_prediction(ai_response, self.project_data)

        # EAC = AC + (BAC - EV) / CPI
        # = 50000 + (100000 - 47500) / 0.95
        # = 50000 + 55263.16 ≈ 105263
        expected_eac = 50000 + (100000 - 47500) / 0.95
        self.assertAlmostEqual(result["predicted_eac"], expected_eac, places=0)

    def test_parse_eac_prediction_with_zero_cpi_fallback(self):
        """测试CPI为0时的回退"""
        project_data = {
            "bac": 100000,
            "current_cpi": 0,  # CPI为0
            "current_ac": 50000,
            "current_ev": 0,
        }
        ai_response = "invalid"

        result = self.predictor._parse_eac_prediction(ai_response, project_data)

        # CPI为0时，使用BAC * 1.2
        expected_eac = 100000 * 1.2
        self.assertEqual(result["predicted_eac"], expected_eac)

    def test_parse_eac_prediction_fills_missing_fields(self):
        """测试填充缺失字段"""
        ai_response = json.dumps({"predicted_eac": 105000})  # 只有部分字段

        result = self.predictor._parse_eac_prediction(ai_response, self.project_data)

        # 应该填充默认值
        self.assertIn("confidence", result)
        self.assertIn("eac_lower_bound", result)
        self.assertIn("eac_upper_bound", result)
        self.assertEqual(result["prediction_method"], "AI_GLM5")


class TestParseRiskAnalysis(unittest.TestCase):
    """测试风险分析响应解析"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")

    def test_parse_risk_analysis_valid_json(self):
        """测试解析有效JSON"""
        ai_response = json.dumps({
            "overrun_probability": 65,
            "risk_level": "MEDIUM",
            "risk_score": 70,
            "risk_factors": [{"factor": "风险1", "impact": "HIGH"}],
            "trend_analysis": "趋势分析",
            "cost_trend": "DECLINING",
            "key_concerns": ["关注点1"],
            "early_warning_signals": ["信号1"],
        })

        result = self.predictor._parse_risk_analysis(ai_response)

        self.assertEqual(result["overrun_probability"], 65)
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertEqual(result["risk_score"], 70)
        self.assertEqual(len(result["risk_factors"]), 1)

    def test_parse_risk_analysis_json_with_wrapper_text(self):
        """测试带包装文本的JSON"""
        ai_response = """
        风险分析结果：
        {"overrun_probability": 80, "risk_level": "HIGH", "risk_score": 85}
        以上是分析结果
        """

        result = self.predictor._parse_risk_analysis(ai_response)

        self.assertEqual(result["overrun_probability"], 80)
        self.assertEqual(result["risk_level"], "HIGH")

    def test_parse_risk_analysis_fallback_on_error(self):
        """测试解析失败时的回退"""
        ai_response = "not json"

        result = self.predictor._parse_risk_analysis(ai_response)

        # 应该返回默认值
        self.assertEqual(result["overrun_probability"], 50.0)
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertEqual(result["risk_score"], 50.0)
        self.assertIn("AI分析失败", result["trend_analysis"])

    def test_parse_risk_analysis_partial_data(self):
        """测试部分数据"""
        ai_response = json.dumps({"overrun_probability": 90})

        result = self.predictor._parse_risk_analysis(ai_response)

        self.assertEqual(result["overrun_probability"], 90)
        # 其他字段应该有默认值
        self.assertIn("risk_level", result)
        self.assertIn("risk_score", result)


class TestParseOptimizationSuggestions(unittest.TestCase):
    """测试优化建议响应解析"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")

    def test_parse_optimization_suggestions_valid_array(self):
        """测试解析有效数组"""
        ai_response = json.dumps([
            {"title": "建议1", "type": "RESOURCE_OPTIMIZATION"},
            {"title": "建议2", "type": "PROCESS_IMPROVEMENT"},
        ])

        result = self.predictor._parse_optimization_suggestions(ai_response)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "建议1")

    def test_parse_optimization_suggestions_single_object(self):
        """测试单个对象转换为数组"""
        ai_response = json.dumps({"title": "单个建议", "type": "SCOPE_ADJUSTMENT"})

        result = self.predictor._parse_optimization_suggestions(ai_response)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "单个建议")

    def test_parse_optimization_suggestions_with_wrapper_text(self):
        """测试带包装文本"""
        ai_response = """
        优化建议如下：
        [{"title": "建议A", "priority": "HIGH"}]
        """

        result = self.predictor._parse_optimization_suggestions(ai_response)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_parse_optimization_suggestions_fallback_on_error(self):
        """测试解析失败回退"""
        ai_response = "invalid json"

        result = self.predictor._parse_optimization_suggestions(ai_response)

        # 应该返回默认建议
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn("AI建议生成失败", result[0]["description"])
        self.assertEqual(result[0]["ai_confidence_score"], 0)


class TestSummarizeEVMHistory(unittest.TestCase):
    """测试EVM历史数据总结"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")

    def test_summarize_evm_history_empty(self):
        """测试空历史数据"""
        result = self.predictor._summarize_evm_history([])
        self.assertEqual(result, "无历史数据")

    def test_summarize_evm_history_single_period(self):
        """测试单期数据"""
        history = [{"period": "2024-01", "cpi": 1.0, "spi": 1.0, "ac": 10000, "ev": 10000}]

        result = self.predictor._summarize_evm_history(history)

        self.assertIn("最近的EVM数据", result)
        self.assertIn("2024-01", result)
        self.assertIn("CPI=1.0", result)

    def test_summarize_evm_history_multiple_periods(self):
        """测试多期数据（显示最近6期）"""
        history = [
            {"period": f"2024-{i:02d}", "cpi": 1.0 - i * 0.01, "spi": 1.0, "ac": i * 10000, "ev": i * 10000}
            for i in range(1, 10)
        ]

        result = self.predictor._summarize_evm_history(history)

        # 应该只包含最近6期
        self.assertIn("2024-04", result)  # 第4期
        self.assertIn("2024-09", result)  # 第9期（最后一期）
        self.assertNotIn("2024-01", result)  # 第1期不应出现

    def test_summarize_evm_history_declining_cpi_trend(self):
        """测试CPI持续下降趋势"""
        history = [
            {"period": "2024-01", "cpi": 1.0, "spi": 1.0, "ac": 10000, "ev": 10000},
            {"period": "2024-02", "cpi": 0.95, "spi": 1.0, "ac": 20000, "ev": 19000},
            {"period": "2024-03", "cpi": 0.90, "spi": 1.0, "ac": 30000, "ev": 27000},
        ]

        result = self.predictor._summarize_evm_history(history)

        self.assertIn("CPI持续下降", result)
        self.assertIn("成本效率恶化", result)

    def test_summarize_evm_history_improving_cpi_trend(self):
        """测试CPI持续上升趋势"""
        history = [
            {"period": "2024-01", "cpi": 0.90, "spi": 1.0, "ac": 10000, "ev": 9000},
            {"period": "2024-02", "cpi": 0.95, "spi": 1.0, "ac": 20000, "ev": 19000},
            {"period": "2024-03", "cpi": 1.00, "spi": 1.0, "ac": 30000, "ev": 30000},
        ]

        result = self.predictor._summarize_evm_history(history)

        self.assertIn("CPI持续上升", result)
        self.assertIn("成本效率改善", result)

    def test_summarize_evm_history_volatile_cpi(self):
        """测试CPI波动"""
        history = [
            {"period": "2024-01", "cpi": 1.0, "spi": 1.0, "ac": 10000, "ev": 10000},
            {"period": "2024-02", "cpi": 0.90, "spi": 1.0, "ac": 20000, "ev": 18000},
            {"period": "2024-03", "cpi": 0.95, "spi": 1.0, "ac": 30000, "ev": 28500},
        ]

        result = self.predictor._summarize_evm_history(history)

        self.assertIn("CPI波动", result)
        self.assertIn("成本控制不稳定", result)

    def test_summarize_evm_history_less_than_3_periods(self):
        """测试少于3期数据（不做趋势分析）"""
        history = [
            {"period": "2024-01", "cpi": 1.0, "spi": 1.0, "ac": 10000, "ev": 10000},
            {"period": "2024-02", "cpi": 0.95, "spi": 1.0, "ac": 20000, "ev": 19000},
        ]

        result = self.predictor._summarize_evm_history(history)

        # 应该不包含趋势分析
        self.assertNotIn("趋势分析", result)


class TestBuildPrompts(unittest.TestCase):
    """测试提示词构建方法"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")
        self.project_data = {
            "project_code": "PRJ001",
            "project_name": "测试项目",
            "bac": 100000,
            "planned_start": "2024-01-01",
            "planned_end": "2024-12-31",
            "current_pv": 50000,
            "current_ev": 45000,
            "current_ac": 48000,
            "current_cpi": 0.9375,
            "current_spi": 0.9,
            "percent_complete": 45,
        }

    def test_build_eac_prediction_prompt(self):
        """测试构建EAC预测提示词"""
        evm_history = [
            {"period": "2024-01", "cpi": 1.0, "spi": 1.0, "ac": 10000, "ev": 10000}
        ]
        additional_context = {"market": "stable"}

        prompt = self.predictor._build_eac_prediction_prompt(
            self.project_data, evm_history, additional_context
        )

        # 验证关键信息
        self.assertIn("PRJ001", prompt)
        self.assertIn("测试项目", prompt)
        self.assertIn("100000", prompt)
        self.assertIn("predicted_eac", prompt)
        self.assertIn("confidence", prompt)
        self.assertIn(str(date.today()), prompt)

    def test_build_risk_analysis_prompt(self):
        """测试构建风险分析提示词"""
        evm_history = [{"period": "2024-01", "cpi": 1.0}]
        current_evm = {"cpi": 0.9, "spi": 0.88, "ac": 50000, "percent_complete": 40}

        prompt = self.predictor._build_risk_analysis_prompt(
            self.project_data, evm_history, current_evm
        )

        # 验证关键信息
        self.assertIn("PRJ001", prompt)
        self.assertIn("overrun_probability", prompt)
        self.assertIn("risk_level", prompt)
        self.assertIn("0.9", prompt)  # CPI

    def test_build_optimization_prompt(self):
        """测试构建优化建议提示词"""
        prediction_result = {"predicted_eac": 110000}
        risk_analysis = {"risk_level": "HIGH", "overrun_probability": 75, "risk_factors": []}

        prompt = self.predictor._build_optimization_prompt(
            self.project_data, prediction_result, risk_analysis
        )

        # 验证关键信息
        self.assertIn("PRJ001", prompt)
        self.assertIn("110000", prompt)
        self.assertIn("HIGH", prompt)
        self.assertIn("estimated_cost_saving", prompt)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.predictor = GLM5CostPredictor(api_key="test_key")

    def test_parse_eac_with_missing_project_data_fields(self):
        """测试项目数据字段缺失"""
        project_data = {}  # 空数据
        ai_response = "invalid"

        result = self.predictor._parse_eac_prediction(ai_response, project_data)

        # 应该能处理，使用默认值
        self.assertIn("predicted_eac", result)

    def test_summarize_history_with_missing_fields(self):
        """测试历史数据字段缺失"""
        history = [
            {"period": "2024-01"},  # 缺少cpi等字段
        ]

        result = self.predictor._summarize_evm_history(history)

        # 应该能处理
        self.assertIn("2024-01", result)

    @patch("requests.post")
    def test_api_timeout(self, mock_post):
        """测试API超时"""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with self.assertRaises(Exception) as cm:
            self.predictor._call_glm5_api("test")

        self.assertIn("GLM-5 API调用失败", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
