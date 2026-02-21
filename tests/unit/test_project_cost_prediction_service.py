# -*- coding: utf-8 -*-
"""
项目成本预测服务单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.project_cost_prediction.service import ProjectCostPredictionService
from app.models import (
    CostOptimizationSuggestion,
    CostPrediction,
    EarnedValueData,
    Project,
)


class TestProjectCostPredictionService(unittest.TestCase):
    """测试ProjectCostPredictionService核心方法"""

    def setUp(self):
        """每个测试前执行"""
        # Mock数据库Session
        self.mock_db = MagicMock()
        
        # 初始化服务（不配置GLM API Key）
        self.service = ProjectCostPredictionService(db=self.mock_db, glm_api_key=None)
        
        # 准备测试数据
        self.project_id = 1
        self.project = self._create_mock_project()
        self.latest_evm = self._create_mock_evm_data()
        self.evm_history = [self._create_mock_evm_data(i) for i in range(1, 4)]

    def _create_mock_project(self):
        """创建mock项目对象"""
        project = MagicMock(spec=Project)
        project.id = self.project_id
        project.project_code = "PRJ-2024-001"
        project.project_name = "测试项目"
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 12, 31)
        return project

    def _create_mock_evm_data(self, period_index=0):
        """创建mock EVM数据对象"""
        evm = MagicMock(spec=EarnedValueData)
        evm.id = period_index or 1
        evm.project_id = self.project_id
        evm.period_date = date(2024, period_index or 3, 1)
        evm.budget_at_completion = Decimal('1000000')
        evm.planned_value = Decimal('300000')
        evm.earned_value = Decimal('250000')
        evm.actual_cost = Decimal('280000')
        evm.cost_performance_index = Decimal('0.8929')  # EV/AC
        evm.schedule_performance_index = Decimal('0.8333')  # EV/PV
        evm.actual_percent_complete = Decimal('25.00')
        return evm

    # ==================== 初始化测试 ====================
    
    def test_init_without_api_key(self):
        """测试无API密钥初始化"""
        service = ProjectCostPredictionService(db=self.mock_db, glm_api_key=None)
        self.assertIsNone(service.ai_predictor)
        self.assertIsNotNone(service.calculator)

    def test_init_with_api_key(self):
        """测试有API密钥初始化"""
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor') as MockPredictor:
            mock_predictor_instance = MagicMock()
            MockPredictor.return_value = mock_predictor_instance
            
            service = ProjectCostPredictionService(db=self.mock_db, glm_api_key="test-key")
            
            MockPredictor.assert_called_once_with(api_key="test-key")
            self.assertEqual(service.ai_predictor, mock_predictor_instance)

    # ==================== create_prediction() 测试 ====================
    
    def test_create_prediction_project_not_found(self):
        """测试项目不存在的情况"""
        # Mock query返回None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.create_prediction(project_id=999)
        
        self.assertIn("项目不存在", str(context.exception))

    def test_create_prediction_no_evm_data(self):
        """测试无EVM数据的情况"""
        # 第一次query返回项目，第二次返回None（无EVM数据）
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        
        # 使用side_effect模拟多次调用
        first_mock = MagicMock()
        first_mock.first.side_effect = [self.project, None]  # 第一次项目，第二次EVM为None
        
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = None
        
        filter_mock.first.side_effect = [self.project, None]
        
        with self.assertRaises(ValueError) as context:
            self.service.create_prediction(project_id=self.project_id)
        
        self.assertIn("项目无EVM数据", str(context.exception))

    def test_create_prediction_traditional_method(self):
        """测试传统预测方法（无AI）"""
        # Setup mock返回值
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        
        # Project查询
        filter_mock.first.side_effect = [self.project]
        
        # Latest EVM查询
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = self.latest_evm
        
        # History EVM查询
        order_by_mock.limit.return_value.all.return_value = self.evm_history
        
        # 执行预测
        result = self.service.create_prediction(
            project_id=self.project_id,
            use_ai=False,
            created_by=1,
            notes="测试预测"
        )
        
        # 验证保存被调用
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
        
        # 验证返回的是CostPrediction类型
        self.assertIsInstance(result, CostPrediction)
        self.assertEqual(result.project_id, self.project_id)
        self.assertEqual(result.prediction_method, "CPI_BASED")

    def test_create_prediction_with_ai(self):
        """测试AI预测方法"""
        # 添加mock AI predictor
        self.service.ai_predictor = MagicMock()
        self.service.ai_predictor.predict_eac.return_value = {
            'predicted_eac': 1200000,
            'confidence': 85.0,
            'eac_lower_bound': 1150000,
            'eac_upper_bound': 1250000,
            'eac_most_likely': 1200000,
            'reasoning': 'AI推理结果',
            'key_assumptions': ['假设1', '假设2'],
            'uncertainty_factors': ['不确定因素1']
        }
        self.service.ai_predictor.analyze_cost_risks.return_value = {
            'overrun_probability': 75.0,
            'risk_level': 'HIGH',
            'risk_score': 80.0,
            'risk_factors': ['因素1'],
            'trend_analysis': '趋势分析',
            'cost_trend': 'INCREASING',
            'key_concerns': ['关注点1'],
            'early_warning_signals': ['预警1']
        }
        
        # Setup mock返回值
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [self.project]
        
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = self.latest_evm
        order_by_mock.limit.return_value.all.return_value = self.evm_history
        
        # 执行预测
        result = self.service.create_prediction(
            project_id=self.project_id,
            use_ai=True,
            prediction_version="V2.0"
        )
        
        # 验证AI predictor被调用
        self.service.ai_predictor.predict_eac.assert_called_once()
        self.service.ai_predictor.analyze_cost_risks.assert_called_once()
        
        # 验证结果
        self.assertEqual(result.prediction_method, "AI_GLM5")
        self.assertEqual(float(result.predicted_eac), 1200000)

    def test_create_prediction_with_high_risk_generates_suggestions(self):
        """测试高风险时生成优化建议"""
        # 添加mock AI predictor
        self.service.ai_predictor = MagicMock()
        self.service.ai_predictor.predict_eac.return_value = {
            'predicted_eac': 1200000,
            'confidence': 85.0,
            'eac_lower_bound': 1150000,
            'eac_upper_bound': 1250000,
            'eac_most_likely': 1200000,
            'reasoning': 'AI推理结果'
        }
        self.service.ai_predictor.analyze_cost_risks.return_value = {
            'overrun_probability': 90.0,
            'risk_level': 'CRITICAL',
            'risk_score': 95.0,
            'risk_factors': [],
            'trend_analysis': '',
            'cost_trend': 'INCREASING'
        }
        self.service.ai_predictor.generate_optimization_suggestions.return_value = [
            {
                'title': '优化建议1',
                'type': 'RESOURCE',
                'priority': 'HIGH',
                'description': '建议描述',
                'current_situation': '当前情况',
                'proposed_action': '建议措施',
                'implementation_steps': ['步骤1', '步骤2'],
                'estimated_cost_saving': 50000,
                'implementation_cost': 10000,
                'impact_on_schedule': '无影响',
                'impact_on_quality': '正面',
                'implementation_risk': 'LOW',
                'ai_confidence_score': 80,
                'ai_reasoning': 'AI推理'
            }
        ]
        
        # Setup mock返回值
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [self.project]
        
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = self.latest_evm
        order_by_mock.limit.return_value.all.return_value = self.evm_history
        
        # 执行预测
        result = self.service.create_prediction(
            project_id=self.project_id,
            use_ai=True
        )
        
        # 验证生成优化建议
        self.service.ai_predictor.generate_optimization_suggestions.assert_called_once()

    # ==================== get_latest_prediction() 测试 ====================
    
    def test_get_latest_prediction_exists(self):
        """测试获取最新预测（存在）"""
        mock_prediction = MagicMock(spec=CostPrediction)
        mock_prediction.id = 1
        mock_prediction.project_id = self.project_id
        
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = mock_prediction
        
        result = self.service.get_latest_prediction(self.project_id)
        
        self.assertEqual(result, mock_prediction)

    def test_get_latest_prediction_not_exists(self):
        """测试获取最新预测（不存在）"""
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = None
        
        result = self.service.get_latest_prediction(self.project_id)
        
        self.assertIsNone(result)

    # ==================== get_prediction_history() 测试 ====================
    
    def test_get_prediction_history_with_limit(self):
        """测试获取预测历史（带限制）"""
        mock_predictions = [MagicMock(spec=CostPrediction) for _ in range(3)]
        
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_by_mock = filter_mock.order_by.return_value
        limit_mock = order_by_mock.limit.return_value
        limit_mock.all.return_value = mock_predictions
        
        result = self.service.get_prediction_history(self.project_id, limit=3)
        
        self.assertEqual(len(result), 3)
        order_by_mock.limit.assert_called_once_with(3)

    def test_get_prediction_history_without_limit(self):
        """测试获取预测历史（无限制）"""
        mock_predictions = [MagicMock(spec=CostPrediction) for _ in range(10)]
        
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.all.return_value = mock_predictions
        
        result = self.service.get_prediction_history(self.project_id, limit=None)
        
        self.assertEqual(len(result), 10)

    # ==================== get_cost_health_analysis() 测试 ====================
    
    def test_get_cost_health_analysis_no_prediction(self):
        """测试无预测数据的健康分析"""
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_cost_health_analysis(self.project_id)
        
        self.assertIn("项目暂无预测数据", str(context.exception))

    def test_get_cost_health_analysis_success(self):
        """测试成功获取健康分析"""
        # Mock prediction
        mock_prediction = MagicMock(spec=CostPrediction)
        mock_prediction.project_id = self.project_id
        mock_prediction.risk_level = "MEDIUM"
        mock_prediction.overrun_probability = Decimal('50.00')
        mock_prediction.expected_overrun_amount = Decimal('100000')
        mock_prediction.cost_trend = "STABLE"
        mock_prediction.current_cpi = Decimal('0.90')
        mock_prediction.prediction_date = date.today()
        
        # Mock query for prediction
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        
        # 模拟多次filter调用的返回
        filter_returns = [
            mock_prediction,  # get_latest_prediction
            Mock(count=Mock(return_value=2)),  # pending suggestions
            Mock(count=Mock(return_value=1)),  # approved suggestions
            Mock(count=Mock(return_value=0)),  # in_progress suggestions
        ]
        
        order_by_mock = filter_mock.order_by.return_value
        order_by_mock.first.return_value = mock_prediction
        
        # Mock count queries
        count_mock = filter_mock.count
        count_mock.side_effect = [2, 1, 0]
        
        result = self.service.get_cost_health_analysis(self.project_id)
        
        # 验证返回结构
        self.assertEqual(result['project_id'], self.project_id)
        self.assertEqual(result['risk_level'], "MEDIUM")
        self.assertIn('health_score', result)
        self.assertIn('suggestions_summary', result)
        self.assertIn('recommendation', result)

    # ==================== 私有方法测试 ====================
    
    def test_prepare_project_data(self):
        """测试准备项目数据"""
        project_data = self.service._prepare_project_data(self.project, self.latest_evm)
        
        self.assertEqual(project_data['project_code'], "PRJ-2024-001")
        self.assertEqual(project_data['project_name'], "测试项目")
        self.assertEqual(project_data['bac'], self.latest_evm.budget_at_completion)
        self.assertEqual(project_data['current_cpi'], self.latest_evm.cost_performance_index)

    def test_prepare_evm_history_data(self):
        """测试准备EVM历史数据"""
        history_data = self.service._prepare_evm_history_data(self.evm_history)
        
        self.assertEqual(len(history_data), 3)
        # 验证数据被reversed（最早的在前）
        self.assertIn('period', history_data[0])
        self.assertIn('cpi', history_data[0])

    def test_traditional_eac_prediction(self):
        """测试传统EAC预测"""
        result = self.service._traditional_eac_prediction(self.latest_evm)
        
        self.assertIn('predicted_eac', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['confidence'], 70.0)
        
        # 验证EAC计算逻辑: EAC = AC + (BAC - EV) / CPI
        expected_eac = (
            self.latest_evm.actual_cost + 
            (self.latest_evm.budget_at_completion - self.latest_evm.earned_value) / 
            self.latest_evm.cost_performance_index
        )
        self.assertAlmostEqual(result['predicted_eac'], float(expected_eac), places=2)

    def test_traditional_eac_prediction_zero_cpi(self):
        """测试CPI为0时的传统预测"""
        evm_zero_cpi = self._create_mock_evm_data()
        evm_zero_cpi.cost_performance_index = Decimal('0')
        
        result = self.service._traditional_eac_prediction(evm_zero_cpi)
        
        # CPI为0时，使用BAC * 1.2作为EAC
        expected_eac = float(evm_zero_cpi.budget_at_completion * Decimal('1.2'))
        self.assertEqual(result['predicted_eac'], expected_eac)

    def test_traditional_risk_analysis_low_risk(self):
        """测试传统风险分析 - 低风险"""
        evm = self._create_mock_evm_data()
        evm.cost_performance_index = Decimal('0.95')
        
        result = self.service._traditional_risk_analysis(evm, self.evm_history)
        
        self.assertEqual(result['risk_level'], 'LOW')
        self.assertEqual(result['overrun_probability'], 20.0)

    def test_traditional_risk_analysis_medium_risk(self):
        """测试传统风险分析 - 中风险"""
        evm = self._create_mock_evm_data()
        evm.cost_performance_index = Decimal('0.87')
        
        result = self.service._traditional_risk_analysis(evm, self.evm_history)
        
        self.assertEqual(result['risk_level'], 'MEDIUM')
        self.assertEqual(result['overrun_probability'], 50.0)

    def test_traditional_risk_analysis_high_risk(self):
        """测试传统风险分析 - 高风险"""
        evm = self._create_mock_evm_data()
        evm.cost_performance_index = Decimal('0.77')
        
        result = self.service._traditional_risk_analysis(evm, self.evm_history)
        
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertEqual(result['overrun_probability'], 75.0)

    def test_traditional_risk_analysis_critical_risk(self):
        """测试传统风险分析 - 严重风险"""
        evm = self._create_mock_evm_data()
        evm.cost_performance_index = Decimal('0.70')
        
        result = self.service._traditional_risk_analysis(evm, self.evm_history)
        
        self.assertEqual(result['risk_level'], 'CRITICAL')
        self.assertEqual(result['overrun_probability'], 90.0)

    def test_calculate_data_quality_sufficient_data(self):
        """测试数据质量计算 - 充足数据"""
        history_data = [{'period': f'2024-0{i}-01'} for i in range(1, 10)]
        
        score = self.service._calculate_data_quality(history_data)
        
        self.assertEqual(score, Decimal('100'))

    def test_calculate_data_quality_moderate_data(self):
        """测试数据质量计算 - 中等数据"""
        history_data = [{'period': f'2024-0{i}-01'} for i in range(1, 5)]
        
        score = self.service._calculate_data_quality(history_data)
        
        self.assertEqual(score, Decimal('85'))  # 100 - 15

    def test_calculate_data_quality_insufficient_data(self):
        """测试数据质量计算 - 不足数据"""
        history_data = [{'period': '2024-01-01'}, {'period': '2024-02-01'}]
        
        score = self.service._calculate_data_quality(history_data)
        
        self.assertEqual(score, Decimal('70'))  # 100 - 30

    def test_get_suggestions_summary(self):
        """测试获取优化建议摘要"""
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        count_mock = filter_mock.count
        count_mock.side_effect = [2, 1, 0]
        
        result = self.service._get_suggestions_summary(self.project_id)
        
        self.assertEqual(result['pending'], 2)
        self.assertEqual(result['approved'], 1)
        self.assertEqual(result['in_progress'], 0)

    def test_calculate_health_score_critical(self):
        """测试健康评分 - 严重风险"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "CRITICAL"
        mock_prediction.current_cpi = Decimal('0.70')
        
        suggestions = {"pending": 5, "approved": 0, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 40(CRITICAL) - 20(CPI<0.8) - 5(pending) = 35
        self.assertEqual(score, 35)

    def test_calculate_health_score_high(self):
        """测试健康评分 - 高风险"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "HIGH"
        mock_prediction.current_cpi = Decimal('0.85')
        
        suggestions = {"pending": 0, "approved": 0, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 25(HIGH) - 10(CPI<0.9) = 65
        self.assertEqual(score, 65)

    def test_calculate_health_score_good(self):
        """测试健康评分 - 良好"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "LOW"
        mock_prediction.current_cpi = Decimal('0.95')
        
        suggestions = {"pending": 0, "approved": 0, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 0 = 100
        self.assertEqual(score, 100)

    def test_get_health_recommendation_excellent(self):
        """测试健康建议 - 优秀"""
        result = self.service._get_health_recommendation(85, "LOW")
        self.assertIn("良好", result)

    def test_get_health_recommendation_good(self):
        """测试健康建议 - 良好"""
        result = self.service._get_health_recommendation(65, "MEDIUM")
        self.assertIn("一定风险", result)

    def test_get_health_recommendation_poor(self):
        """测试健康建议 - 较差"""
        result = self.service._get_health_recommendation(45, "HIGH")
        self.assertIn("风险较高", result)

    def test_get_health_recommendation_critical(self):
        """测试健康建议 - 严重"""
        result = self.service._get_health_recommendation(20, "CRITICAL")
        self.assertIn("紧急干预", result)

    # ==================== 边界情况测试 ====================
    
    def test_create_prediction_record_calculation(self):
        """测试预测记录创建时的计算"""
        prediction_result = {
            'predicted_eac': 1200000,
            'confidence': 85.0,
            'eac_lower_bound': 1150000,
            'eac_upper_bound': 1250000,
            'eac_most_likely': 1200000,
            'reasoning': 'Test reasoning',
            'key_assumptions': ['假设1'],
            'uncertainty_factors': ['不确定1']
        }
        
        risk_analysis = {
            'overrun_probability': 75.0,
            'risk_level': 'HIGH',
            'risk_score': 80.0,
            'risk_factors': ['因素1'],
            'trend_analysis': '趋势',
            'cost_trend': 'INCREASING',
            'key_concerns': ['关注1'],
            'early_warning_signals': ['预警1']
        }
        
        evm_history_data = [
            {'period': '2024-01-01', 'cpi': 0.9, 'spi': 0.85, 'ac': 100000, 'ev': 90000, 'pv': 100000}
        ]
        
        record = self.service._create_prediction_record(
            self.project,
            self.latest_evm,
            prediction_result,
            risk_analysis,
            "V1.0",
            "AI_GLM5",
            evm_history_data,
            created_by=1,
            notes="测试"
        )
        
        # 验证计算
        self.assertEqual(record.project_id, self.project.id)
        self.assertEqual(record.prediction_method, "AI_GLM5")
        
        # 验证超支金额计算
        expected_overrun = Decimal('1200000') - self.latest_evm.budget_at_completion
        self.assertEqual(record.expected_overrun_amount, expected_overrun)
        
        # 验证超支百分比计算
        expected_percentage = (expected_overrun / self.latest_evm.budget_at_completion) * Decimal('100')
        self.assertEqual(record.overrun_percentage, expected_percentage)

    def test_generate_optimization_suggestions_no_ai(self):
        """测试无AI时不生成建议"""
        self.service.ai_predictor = None
        mock_prediction = MagicMock()
        
        # 不应抛出异常
        self.service._generate_optimization_suggestions(
            mock_prediction, {}, {}, {}
        )
        
        # 无db操作
        self.mock_db.add.assert_not_called()

    def test_generate_optimization_suggestions_with_exception(self):
        """测试生成建议时的异常处理"""
        self.service.ai_predictor = MagicMock()
        self.service.ai_predictor.generate_optimization_suggestions.side_effect = Exception("API Error")
        
        mock_prediction = MagicMock()
        mock_prediction.id = 1
        mock_prediction.project_id = self.project_id
        mock_prediction.project_code = "PRJ-001"
        mock_prediction.prediction_date = date.today()
        
        # 不应抛出异常（异常被捕获）
        self.service._generate_optimization_suggestions(
            mock_prediction, {}, {}, {'risk_level': 'HIGH'}
        )


class TestCostPredictionEdgeCases(unittest.TestCase):
    """测试边界情况和特殊场景"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectCostPredictionService(db=self.mock_db, glm_api_key=None)

    def test_evm_with_none_cpi(self):
        """测试CPI为None的情况"""
        evm = MagicMock(spec=EarnedValueData)
        evm.cost_performance_index = None
        evm.budget_at_completion = Decimal('1000000')
        evm.actual_cost = Decimal('500000')
        evm.earned_value = Decimal('400000')
        
        result = self.service._traditional_eac_prediction(evm)
        
        # 应该使用默认值1
        self.assertIsNotNone(result['predicted_eac'])

    def test_empty_evm_history(self):
        """测试空历史数据"""
        history_data = self.service._prepare_evm_history_data([])
        
        self.assertEqual(len(history_data), 0)

    def test_prediction_with_zero_bac(self):
        """测试BAC为0的情况"""
        evm = MagicMock(spec=EarnedValueData)
        evm.budget_at_completion = Decimal('0')
        evm.actual_cost = Decimal('100000')
        evm.earned_value = Decimal('80000')
        evm.cost_performance_index = Decimal('0.8')
        
        # 不应崩溃
        result = self.service._traditional_eac_prediction(evm)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
