"""
第四批覆盖测试 - cost_prediction_service
"""
import pytest
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.cost_prediction_service import GLM5CostPredictor, CostPredictionService
    HAS_SERVICE = True
except Exception:
    HAS_SERVICE = False

pytestmark = pytest.mark.skipif(not HAS_SERVICE, reason="服务导入失败")


class TestGLM5CostPredictor:
    def setup_method(self):
        self.predictor = GLM5CostPredictor(api_key="test-key")

    def test_init(self):
        assert self.predictor.api_key == "test-key"

    def test_init_without_key_raises(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GLM API密钥未配置"):
                GLM5CostPredictor(api_key=None)

    def test_parse_eac_prediction_valid_json(self):
        project_data = {'bac': 1000000, 'current_cpi': 0.95, 'current_ac': 500000, 'current_ev': 450000}
        ai_response = json.dumps({
            "predicted_eac": 1100000,
            "confidence": 75,
            "prediction_method": "AI",
            "eac_lower_bound": 1050000,
            "eac_upper_bound": 1150000,
            "eac_most_likely": 1100000,
            "reasoning": "基于历史数据"
        })
        result = self.predictor._parse_eac_prediction(ai_response, project_data)
        assert result['predicted_eac'] == 1100000
        assert result['confidence'] == 75

    def test_parse_eac_prediction_fallback_on_invalid_json(self):
        project_data = {'bac': 1000000, 'current_cpi': 0.9, 'current_ac': 500000, 'current_ev': 450000}
        result = self.predictor._parse_eac_prediction("invalid json {{", project_data)
        assert 'predicted_eac' in result
        assert result['prediction_method'] == 'CPI_BASED_FALLBACK'

    def test_parse_risk_analysis_valid(self):
        ai_response = json.dumps({
            "overrun_probability": 30,
            "risk_level": "MEDIUM",
            "risk_score": 45,
            "risk_factors": [],
            "trend_analysis": "稳定",
            "cost_trend": "STABLE",
            "key_concerns": [],
            "early_warning_signals": []
        })
        result = self.predictor._parse_risk_analysis(ai_response)
        assert result['risk_level'] == "MEDIUM"

    def test_parse_risk_analysis_fallback(self):
        result = self.predictor._parse_risk_analysis("not json at all")
        assert isinstance(result, dict)

    def test_build_eac_prediction_prompt(self):
        project_data = {'name': '测试项目', 'bac': 1000000}
        evm_history = []
        prompt = self.predictor._build_eac_prediction_prompt(project_data, evm_history, additional_context=None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_summarize_evm_history_empty(self):
        result = self.predictor._summarize_evm_history([])
        assert isinstance(result, str)

    def test_summarize_evm_history_with_data(self):
        evm_item = {'date': '2024-01', 'cpi': 0.95, 'spi': 1.0}
        result = self.predictor._summarize_evm_history([evm_item])
        assert isinstance(result, str)


class TestCostPredictionService:
    def setup_method(self):
        self.db = MagicMock()
        with patch('app.services.cost_prediction_service.GLM5CostPredictor') as mock_pred:
            mock_pred.side_effect = ValueError("no key")
            self.service = CostPredictionService(self.db, glm_api_key=None)

    def test_calculate_data_quality_empty(self):
        result = self.service._calculate_data_quality([])
        assert result >= Decimal('0')

    def test_calculate_data_quality_few_records(self):
        evm_records = [MagicMock(is_verified=False) for _ in range(2)]
        result = self.service._calculate_data_quality(evm_records)
        assert 0 <= float(result) <= 100

    def test_traditional_eac_prediction(self):
        evm = MagicMock()
        evm.cost_performance_index = Decimal('0.95')
        evm.budget_at_completion = Decimal('1000000')
        evm.actual_cost = Decimal('500000')
        evm.earned_value = Decimal('450000')
        result = self.service._traditional_eac_prediction(evm)
        assert 'predicted_eac' in result
        assert result['predicted_eac'] > 0

    def test_traditional_risk_analysis_low_risk(self):
        latest_evm = MagicMock()
        latest_evm.cost_performance_index = Decimal('1.0')
        result = self.service._traditional_risk_analysis(latest_evm, [])
        assert result['risk_level'] == 'LOW'

    def test_traditional_risk_analysis_critical(self):
        latest_evm = MagicMock()
        latest_evm.cost_performance_index = Decimal('0.7')
        result = self.service._traditional_risk_analysis(latest_evm, [])
        assert result['risk_level'] == 'CRITICAL'

    def test_get_latest_prediction(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = self.service.get_latest_prediction(1)
        assert result is None
