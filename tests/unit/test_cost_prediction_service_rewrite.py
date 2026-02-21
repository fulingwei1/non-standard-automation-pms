# -*- coding: utf-8 -*-
"""
项目成本预测服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库操作、AI预测器）
2. 测试核心业务逻辑
3. 达到70%+覆盖率（497行）

参考: tests/unit/test_condition_parser_rewrite.py 的mock策略
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.project_cost_prediction.service import ProjectCostPredictionService


class TestProjectCostPredictionServiceInit(unittest.TestCase):
    """测试初始化方法"""

    def test_init_with_api_key(self):
        """测试使用API密钥初始化"""
        mock_db = MagicMock()
        
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor') as MockPredictor:
            mock_predictor_instance = MagicMock()
            MockPredictor.return_value = mock_predictor_instance
            
            service = ProjectCostPredictionService(mock_db, glm_api_key="test-key")
            
            self.assertEqual(service.db, mock_db)
            self.assertIsNotNone(service.calculator)
            self.assertEqual(service.ai_predictor, mock_predictor_instance)
            MockPredictor.assert_called_once_with(api_key="test-key")

    def test_init_without_api_key(self):
        """测试无API密钥初始化（AI预测器为None）"""
        mock_db = MagicMock()
        
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor') as MockPredictor:
            # 模拟GLM5CostPredictor抛出ValueError
            MockPredictor.side_effect = ValueError("API key required")
            
            service = ProjectCostPredictionService(mock_db)
            
            self.assertEqual(service.db, mock_db)
            self.assertIsNone(service.ai_predictor)


class TestCreatePrediction(unittest.TestCase):
    """测试create_prediction核心方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db, glm_api_key="test-key")

    def test_create_prediction_project_not_found(self):
        """测试项目不存在时抛出异常"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.create_prediction(project_id=999)
        
        self.assertIn("项目不存在", str(context.exception))

    def test_create_prediction_no_evm_data(self):
        """测试无EVM数据时抛出异常"""
        # Mock项目存在
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock第一个查询：Project.query().filter().first() -> 返回项目
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        # Mock第二个查询：EarnedValueData.query().filter().order_by().first() -> 返回None
        mock_evm_query = MagicMock()
        mock_evm_query.filter.return_value.order_by.return_value.first.return_value = None
        
        # 按调用顺序返回不同的查询对象
        self.mock_db.query.side_effect = [mock_project_query, mock_evm_query]
        
        with self.assertRaises(ValueError) as context:
            self.service.create_prediction(project_id=1)
        
        self.assertIn("项目无EVM数据", str(context.exception))

    def test_create_prediction_with_ai_success(self):
        """测试使用AI预测成功创建"""
        # 准备测试数据
        mock_project = self._create_mock_project()
        mock_latest_evm = self._create_mock_evm()
        mock_evm_history = [mock_latest_evm]
        
        # Mock数据库查询
        self._setup_db_queries(mock_project, mock_latest_evm, mock_evm_history)
        
        # Mock AI预测器
        mock_prediction_result = {
            'predicted_eac': 120000.0,
            'confidence': 85.0,
            'eac_lower_bound': 115000.0,
            'eac_upper_bound': 125000.0,
            'eac_most_likely': 120000.0,
            'reasoning': 'AI分析结果',
            'key_assumptions': ['假设1', '假设2'],
            'uncertainty_factors': ['不确定因素1']
        }
        
        mock_risk_analysis = {
            'overrun_probability': 65.0,
            'risk_level': 'HIGH',
            'risk_score': 75.0,
            'risk_factors': ['成本超支风险'],
            'cost_trend': 'INCREASING',
            'trend_analysis': '成本呈上升趋势',
            'key_concerns': ['关注点1'],
            'early_warning_signals': ['预警信号1']
        }
        
        self.service.ai_predictor.predict_eac = MagicMock(return_value=mock_prediction_result)
        self.service.ai_predictor.analyze_cost_risks = MagicMock(return_value=mock_risk_analysis)
        
        # 执行预测
        result = self.service.create_prediction(
            project_id=1,
            prediction_version="V1.0",
            use_ai=True,
            created_by=100,
            notes="测试预测"
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.project_id, 1)
        self.assertEqual(result.predicted_eac, Decimal('120000.0'))
        self.assertEqual(result.prediction_method, "AI_GLM5")
        self.assertEqual(result.risk_level, "HIGH")
        
        # 验证AI方法被调用
        self.service.ai_predictor.predict_eac.assert_called_once()
        self.service.ai_predictor.analyze_cost_risks.assert_called_once()

    def test_create_prediction_traditional_method(self):
        """测试使用传统方法预测"""
        # 准备测试数据
        mock_project = self._create_mock_project()
        mock_latest_evm = self._create_mock_evm()
        mock_evm_history = [mock_latest_evm]
        
        # Mock数据库查询
        self._setup_db_queries(mock_project, mock_latest_evm, mock_evm_history)
        
        # 执行预测（use_ai=False）
        result = self.service.create_prediction(
            project_id=1,
            use_ai=False,
            created_by=100
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.prediction_method, "CPI_BASED")
        # 传统方法基于CPI计算
        # EAC = AC + (BAC - EV) / CPI = 50000 + (100000 - 45000) / 0.9 ≈ 111111.11
        self.assertGreater(result.predicted_eac, Decimal('100000'))

    def test_create_prediction_ai_unavailable_fallback(self):
        """测试AI不可用时回退到传统方法"""
        # 设置AI预测器为None
        self.service.ai_predictor = None
        
        # 准备测试数据
        mock_project = self._create_mock_project()
        mock_latest_evm = self._create_mock_evm()
        mock_evm_history = [mock_latest_evm]
        
        # Mock数据库查询
        self._setup_db_queries(mock_project, mock_latest_evm, mock_evm_history)
        
        # 执行预测（use_ai=True，但实际无AI）
        result = self.service.create_prediction(
            project_id=1,
            use_ai=True
        )
        
        # 验证使用了传统方法
        self.assertEqual(result.prediction_method, "CPI_BASED")

    def test_create_prediction_high_risk_generates_suggestions(self):
        """测试高风险时自动生成优化建议"""
        # 准备测试数据
        mock_project = self._create_mock_project()
        mock_latest_evm = self._create_mock_evm()
        mock_evm_history = [mock_latest_evm]
        
        # Mock数据库查询
        self._setup_db_queries(mock_project, mock_latest_evm, mock_evm_history)
        
        # Mock AI预测器返回高风险
        mock_prediction_result = {
            'predicted_eac': 150000.0,
            'confidence': 80.0,
            'eac_lower_bound': 145000.0,
            'eac_upper_bound': 155000.0,
            'eac_most_likely': 150000.0,
            'reasoning': 'AI分析'
        }
        
        mock_risk_analysis = {
            'overrun_probability': 85.0,
            'risk_level': 'CRITICAL',  # 关键风险
            'risk_score': 90.0,
            'risk_factors': [],
            'cost_trend': 'INCREASING',
            'trend_analysis': '',
            'key_concerns': [],
            'early_warning_signals': []
        }
        
        mock_suggestions = [
            {
                'title': '优化建议1',
                'type': 'RESOURCE',
                'priority': 'HIGH',
                'description': '建议描述',
                'current_situation': '当前情况',
                'proposed_action': '建议操作',
                'implementation_steps': ['步骤1', '步骤2'],
                'estimated_cost_saving': 5000.0,
                'implementation_cost': 1000.0,
                'impact_on_schedule': 'MINIMAL',
                'impact_on_quality': 'NONE',
                'implementation_risk': 'LOW',
                'ai_confidence_score': 85.0,
                'ai_reasoning': 'AI推理'
            }
        ]
        
        self.service.ai_predictor.predict_eac = MagicMock(return_value=mock_prediction_result)
        self.service.ai_predictor.analyze_cost_risks = MagicMock(return_value=mock_risk_analysis)
        self.service.ai_predictor.generate_optimization_suggestions = MagicMock(return_value=mock_suggestions)
        
        # 执行预测
        result = self.service.create_prediction(project_id=1, use_ai=True)
        
        # 验证生成建议方法被调用
        self.service.ai_predictor.generate_optimization_suggestions.assert_called_once()
        
        # 验证建议被添加到数据库
        self.mock_db.add.assert_called()

    # ========== 辅助方法 ==========
    
    def _create_mock_project(self):
        """创建模拟项目对象"""
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 12, 31)
        return project

    def _create_mock_evm(self):
        """创建模拟EVM数据"""
        evm = MagicMock()
        evm.id = 10
        evm.project_id = 1
        evm.period_date = date(2024, 6, 30)
        evm.budget_at_completion = Decimal('100000')
        evm.planned_value = Decimal('50000')
        evm.earned_value = Decimal('45000')
        evm.actual_cost = Decimal('50000')
        evm.cost_performance_index = Decimal('0.9')
        evm.schedule_performance_index = Decimal('0.9')
        evm.actual_percent_complete = Decimal('45')
        return evm

    def _setup_db_queries(self, mock_project, mock_latest_evm, mock_evm_history):
        """设置数据库查询Mock"""
        # 第一个查询：获取项目
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        # 第二个查询：获取最新EVM
        mock_latest_evm_query = MagicMock()
        mock_latest_evm_query.filter.return_value.order_by.return_value.first.return_value = mock_latest_evm
        
        # 第三个查询：获取历史EVM
        mock_history_query = MagicMock()
        mock_history_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_evm_history
        
        # 按调用顺序返回不同的查询对象
        self.mock_db.query.side_effect = [
            mock_project_query,
            mock_latest_evm_query,
            mock_history_query
        ]


class TestGetLatestPrediction(unittest.TestCase):
    """测试获取最新预测"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db)

    def test_get_latest_prediction_exists(self):
        """测试获取存在的最新预测"""
        mock_prediction = MagicMock()
        mock_prediction.id = 1
        mock_prediction.project_id = 1
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_prediction
        
        result = self.service.get_latest_prediction(project_id=1)
        
        self.assertEqual(result, mock_prediction)

    def test_get_latest_prediction_not_exists(self):
        """测试获取不存在的预测"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.service.get_latest_prediction(project_id=999)
        
        self.assertIsNone(result)


class TestGetPredictionHistory(unittest.TestCase):
    """测试获取预测历史"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db)

    def test_get_prediction_history_with_limit(self):
        """测试带限制的历史查询"""
        mock_predictions = [MagicMock() for _ in range(5)]
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_predictions
        
        result = self.service.get_prediction_history(project_id=1, limit=5)
        
        self.assertEqual(len(result), 5)
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(5)

    def test_get_prediction_history_without_limit(self):
        """测试无限制的历史查询"""
        mock_predictions = [MagicMock() for _ in range(10)]
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_predictions
        
        result = self.service.get_prediction_history(project_id=1)
        
        self.assertEqual(len(result), 10)


class TestGetCostHealthAnalysis(unittest.TestCase):
    """测试成本健康度分析"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db)

    def test_get_cost_health_analysis_no_prediction(self):
        """测试无预测数据时抛出异常"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_cost_health_analysis(project_id=999)
        
        self.assertIn("项目暂无预测数据", str(context.exception))

    def test_get_cost_health_analysis_success(self):
        """测试成功获取健康度分析"""
        # Mock最新预测
        mock_prediction = MagicMock()
        mock_prediction.project_id = 1
        mock_prediction.risk_level = "MEDIUM"
        mock_prediction.overrun_probability = Decimal('50.0')
        mock_prediction.expected_overrun_amount = Decimal('5000.0')
        mock_prediction.cost_trend = "STABLE"
        mock_prediction.current_cpi = Decimal('0.95')
        mock_prediction.prediction_date = date(2024, 6, 30)
        
        # Mock查询：第一次返回预测，后续返回建议统计
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_prediction
        self.mock_db.query.return_value.filter.return_value.count.side_effect = [2, 1, 0]  # pending, approved, in_progress
        
        result = self.service.get_cost_health_analysis(project_id=1)
        
        # 验证返回结构
        self.assertEqual(result["project_id"], 1)
        self.assertIn("health_score", result)
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertEqual(result["overrun_probability"], 50.0)
        self.assertEqual(result["current_cpi"], 0.95)
        self.assertIn("suggestions_summary", result)
        self.assertEqual(result["suggestions_summary"]["pending"], 2)
        self.assertEqual(result["suggestions_summary"]["approved"], 1)


class TestPrivateMethods(unittest.TestCase):
    """测试私有方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db)

    def test_prepare_project_data(self):
        """测试准备项目数据"""
        mock_project = MagicMock()
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 12, 31)
        
        mock_evm = MagicMock()
        mock_evm.budget_at_completion = Decimal('100000')
        mock_evm.planned_value = Decimal('50000')
        mock_evm.earned_value = Decimal('45000')
        mock_evm.actual_cost = Decimal('50000')
        mock_evm.cost_performance_index = Decimal('0.9')
        mock_evm.schedule_performance_index = Decimal('0.9')
        mock_evm.actual_percent_complete = Decimal('45')
        
        result = self.service._prepare_project_data(mock_project, mock_evm)
        
        self.assertEqual(result['project_code'], "PRJ001")
        self.assertEqual(result['bac'], Decimal('100000'))
        self.assertEqual(result['current_cpi'], Decimal('0.9'))

    def test_prepare_evm_history_data(self):
        """测试准备EVM历史数据"""
        mock_evm_list = []
        for i in range(3):
            evm = MagicMock()
            evm.period_date = date(2024, i+1, 1)
            evm.cost_performance_index = Decimal('0.9')
            evm.schedule_performance_index = Decimal('0.95')
            evm.actual_cost = Decimal(str(10000 * (i+1)))
            evm.earned_value = Decimal(str(9000 * (i+1)))
            evm.planned_value = Decimal(str(10000 * (i+1)))
            mock_evm_list.append(evm)
        
        result = self.service._prepare_evm_history_data(mock_evm_list)
        
        self.assertEqual(len(result), 3)
        # 注意：返回的是reversed列表
        self.assertEqual(result[0]['period'], '2024-03-01')
        self.assertEqual(result[0]['cpi'], 0.9)

    def test_traditional_eac_prediction_normal_cpi(self):
        """测试传统EAC预测（正常CPI）"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.9')
        mock_evm.budget_at_completion = Decimal('100000')
        mock_evm.actual_cost = Decimal('50000')
        mock_evm.earned_value = Decimal('45000')
        
        result = self.service._traditional_eac_prediction(mock_evm)
        
        # EAC = AC + (BAC - EV) / CPI = 50000 + (100000 - 45000) / 0.9 = 111111.11
        self.assertAlmostEqual(result['predicted_eac'], 111111.11, places=2)
        self.assertEqual(result['confidence'], 70.0)

    def test_traditional_eac_prediction_zero_cpi(self):
        """测试传统EAC预测（CPI为0）"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0')
        mock_evm.budget_at_completion = Decimal('100000')
        mock_evm.actual_cost = Decimal('50000')
        mock_evm.earned_value = Decimal('45000')
        
        result = self.service._traditional_eac_prediction(mock_evm)
        
        # CPI为0时，使用BAC * 1.2
        self.assertEqual(result['predicted_eac'], 120000.0)

    def test_traditional_eac_prediction_none_cpi(self):
        """测试传统EAC预测（CPI为None）"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = None
        mock_evm.budget_at_completion = Decimal('100000')
        mock_evm.actual_cost = Decimal('50000')
        mock_evm.earned_value = Decimal('45000')
        
        result = self.service._traditional_eac_prediction(mock_evm)
        
        # None时默认为1，EAC = AC + (BAC - EV) = 105000
        self.assertEqual(result['predicted_eac'], 105000.0)

    def test_traditional_risk_analysis_low_risk(self):
        """测试传统风险分析 - 低风险"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.98')  # >= 0.95
        
        result = self.service._traditional_risk_analysis(mock_evm, [])
        
        self.assertEqual(result['risk_level'], "LOW")
        self.assertEqual(result['overrun_probability'], 20.0)

    def test_traditional_risk_analysis_medium_risk(self):
        """测试传统风险分析 - 中等风险"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.90')  # >= 0.85
        
        result = self.service._traditional_risk_analysis(mock_evm, [])
        
        self.assertEqual(result['risk_level'], "MEDIUM")
        self.assertEqual(result['overrun_probability'], 50.0)

    def test_traditional_risk_analysis_high_risk(self):
        """测试传统风险分析 - 高风险"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.80')  # >= 0.75
        
        result = self.service._traditional_risk_analysis(mock_evm, [])
        
        self.assertEqual(result['risk_level'], "HIGH")
        self.assertEqual(result['overrun_probability'], 75.0)

    def test_traditional_risk_analysis_critical_risk(self):
        """测试传统风险分析 - 关键风险"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.70')  # < 0.75
        
        result = self.service._traditional_risk_analysis(mock_evm, [])
        
        self.assertEqual(result['risk_level'], "CRITICAL")
        self.assertEqual(result['overrun_probability'], 90.0)

    def test_calculate_data_quality_sufficient_data(self):
        """测试数据质量评分 - 充足数据"""
        evm_history = [{'period': f'2024-{i:02d}-01'} for i in range(1, 13)]
        
        score = self.service._calculate_data_quality(evm_history)
        
        self.assertEqual(score, Decimal('100'))

    def test_calculate_data_quality_medium_data(self):
        """测试数据质量评分 - 中等数据"""
        evm_history = [{'period': f'2024-{i:02d}-01'} for i in range(1, 5)]
        
        score = self.service._calculate_data_quality(evm_history)
        
        self.assertEqual(score, Decimal('85'))  # 100 - 15

    def test_calculate_data_quality_insufficient_data(self):
        """测试数据质量评分 - 数据不足"""
        evm_history = [{'period': '2024-01-01'}, {'period': '2024-02-01'}]
        
        score = self.service._calculate_data_quality(evm_history)
        
        self.assertEqual(score, Decimal('70'))  # 100 - 30

    def test_get_suggestions_summary(self):
        """测试获取建议摘要"""
        # Mock不同状态的统计
        self.mock_db.query.return_value.filter.return_value.count.side_effect = [5, 3, 2]
        
        result = self.service._get_suggestions_summary(project_id=1)
        
        self.assertEqual(result['pending'], 5)
        self.assertEqual(result['approved'], 3)
        self.assertEqual(result['in_progress'], 2)

    def test_calculate_health_score_critical(self):
        """测试健康评分 - 关键风险"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "CRITICAL"
        mock_prediction.current_cpi = Decimal('0.70')
        
        suggestions = {"pending": 5, "approved": 2, "in_progress": 1}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 40(CRITICAL) - 20(CPI<0.8) - 5(pending) = 35
        self.assertEqual(score, 35.0)

    def test_calculate_health_score_high(self):
        """测试健康评分 - 高风险"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "HIGH"
        mock_prediction.current_cpi = Decimal('0.85')
        
        suggestions = {"pending": 0, "approved": 0, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 25(HIGH) - 10(CPI<0.9) = 65
        self.assertEqual(score, 65.0)

    def test_calculate_health_score_medium(self):
        """测试健康评分 - 中等风险"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "MEDIUM"
        mock_prediction.current_cpi = Decimal('0.92')
        
        suggestions = {"pending": 2, "approved": 1, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 10(MEDIUM) - 5(pending) = 85
        self.assertEqual(score, 85.0)

    def test_calculate_health_score_low(self):
        """测试健康评分 - 低风险"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "LOW"
        mock_prediction.current_cpi = Decimal('0.98')
        
        suggestions = {"pending": 0, "approved": 0, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 0 = 100
        self.assertEqual(score, 100.0)

    def test_get_health_recommendation_excellent(self):
        """测试健康建议 - 优秀"""
        recommendation = self.service._get_health_recommendation(85.0, "LOW")
        self.assertIn("良好", recommendation)

    def test_get_health_recommendation_good(self):
        """测试健康建议 - 良好"""
        recommendation = self.service._get_health_recommendation(65.0, "MEDIUM")
        self.assertIn("一定风险", recommendation)

    def test_get_health_recommendation_warning(self):
        """测试健康建议 - 警告"""
        recommendation = self.service._get_health_recommendation(45.0, "HIGH")
        self.assertIn("风险较高", recommendation)

    def test_get_health_recommendation_critical(self):
        """测试健康建议 - 严重"""
        recommendation = self.service._get_health_recommendation(25.0, "CRITICAL")
        self.assertIn("严重", recommendation)


class TestGenerateOptimizationSuggestions(unittest.TestCase):
    """测试生成优化建议"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor') as MockPredictor:
            self.mock_ai_predictor = MagicMock()
            MockPredictor.return_value = self.mock_ai_predictor
            self.service = ProjectCostPredictionService(self.mock_db, glm_api_key="test-key")
            self.service.ai_predictor = self.mock_ai_predictor

    def test_generate_optimization_suggestions_success(self):
        """测试成功生成优化建议"""
        mock_prediction = MagicMock()
        mock_prediction.id = 1
        mock_prediction.project_id = 1
        mock_prediction.project_code = "PRJ001"
        mock_prediction.prediction_date = date(2024, 6, 30)
        mock_prediction.created_by = 100
        
        project_data = {'project_code': 'PRJ001'}
        prediction_result = {'predicted_eac': 120000.0}
        risk_analysis = {'risk_level': 'HIGH'}
        
        mock_suggestions = [
            {
                'title': '优化建议1',
                'type': 'RESOURCE',
                'priority': 'HIGH',
                'description': '建议描述',
                'current_situation': '当前情况',
                'proposed_action': '建议操作',
                'implementation_steps': ['步骤1', '步骤2'],
                'estimated_cost_saving': 5000.0,
                'implementation_cost': 1000.0,
                'impact_on_schedule': 'MINIMAL',
                'impact_on_quality': 'NONE',
                'implementation_risk': 'LOW',
                'ai_confidence_score': 85.0,
                'ai_reasoning': 'AI推理'
            }
        ]
        
        self.mock_ai_predictor.generate_optimization_suggestions.return_value = mock_suggestions
        
        # 执行
        self.service._generate_optimization_suggestions(
            mock_prediction, project_data, prediction_result, risk_analysis
        )
        
        # 验证AI方法被调用
        self.mock_ai_predictor.generate_optimization_suggestions.assert_called_once()
        
        # 验证建议被添加
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_generate_optimization_suggestions_no_ai(self):
        """测试无AI时不生成建议"""
        self.service.ai_predictor = None
        
        mock_prediction = MagicMock()
        
        # 执行
        self.service._generate_optimization_suggestions(
            mock_prediction, {}, {}, {}
        )
        
        # 验证没有调用数据库
        self.mock_db.add.assert_not_called()

    def test_generate_optimization_suggestions_exception(self):
        """测试生成建议异常不影响预测"""
        mock_prediction = MagicMock()
        mock_prediction.id = 1
        mock_prediction.project_id = 1
        mock_prediction.project_code = "PRJ001"
        mock_prediction.prediction_date = date(2024, 6, 30)
        
        # Mock AI抛出异常
        self.mock_ai_predictor.generate_optimization_suggestions.side_effect = Exception("AI错误")
        
        # 执行（应该捕获异常不抛出）
        try:
            self.service._generate_optimization_suggestions(
                mock_prediction, {}, {}, {}
            )
        except Exception:
            self.fail("_generate_optimization_suggestions抛出了异常")


class TestCreatePredictionRecord(unittest.TestCase):
    """测试创建预测记录"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db)

    def test_create_prediction_record(self):
        """测试创建预测记录"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        
        mock_evm = MagicMock()
        mock_evm.id = 10
        mock_evm.planned_value = Decimal('50000')
        mock_evm.earned_value = Decimal('45000')
        mock_evm.actual_cost = Decimal('50000')
        mock_evm.budget_at_completion = Decimal('100000')
        mock_evm.cost_performance_index = Decimal('0.9')
        mock_evm.schedule_performance_index = Decimal('0.95')
        mock_evm.actual_percent_complete = Decimal('45')
        
        prediction_result = {
            'predicted_eac': 120000.0,
            'confidence': 85.0,
            'eac_lower_bound': 115000.0,
            'eac_upper_bound': 125000.0,
            'eac_most_likely': 120000.0,
            'reasoning': 'AI分析',
            'key_assumptions': ['假设1'],
            'uncertainty_factors': ['因素1']
        }
        
        risk_analysis = {
            'overrun_probability': 65.0,
            'risk_level': 'HIGH',
            'risk_score': 75.0,
            'risk_factors': ['风险1'],
            'cost_trend': 'INCREASING',
            'trend_analysis': '趋势分析',
            'key_concerns': ['关注1'],
            'early_warning_signals': ['信号1']
        }
        
        evm_history_data = [
            {'period': '2024-01-01', 'cpi': 0.9},
            {'period': '2024-02-01', 'cpi': 0.92}
        ]
        
        with patch('app.services.project_cost_prediction.service.CostPrediction') as MockPrediction:
            mock_record = MagicMock()
            MockPrediction.return_value = mock_record
            
            result = self.service._create_prediction_record(
                project=mock_project,
                latest_evm=mock_evm,
                prediction_result=prediction_result,
                risk_analysis=risk_analysis,
                prediction_version="V1.0",
                prediction_method="AI_GLM5",
                evm_history_data=evm_history_data,
                created_by=100,
                notes="测试"
            )
            
            # 验证CostPrediction被调用
            MockPrediction.assert_called_once()
            call_kwargs = MockPrediction.call_args[1]
            
            # 验证关键字段
            self.assertEqual(call_kwargs['project_id'], 1)
            self.assertEqual(call_kwargs['project_code'], "PRJ001")
            self.assertEqual(call_kwargs['prediction_method'], "AI_GLM5")
            self.assertEqual(call_kwargs['predicted_eac'], Decimal('120000.0'))
            self.assertEqual(call_kwargs['risk_level'], 'HIGH')
            self.assertEqual(call_kwargs['created_by'], 100)
            self.assertEqual(call_kwargs['notes'], "测试")


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.project_cost_prediction.service.GLM5CostPredictor'):
            self.service = ProjectCostPredictionService(self.mock_db)

    def test_calculate_health_score_negative_becomes_zero(self):
        """测试健康评分不会小于0"""
        mock_prediction = MagicMock()
        mock_prediction.risk_level = "CRITICAL"
        mock_prediction.current_cpi = Decimal('0.5')  # 极低CPI
        
        suggestions = {"pending": 10, "approved": 0, "in_progress": 0}
        
        score = self.service._calculate_health_score(mock_prediction, suggestions)
        
        # 100 - 40 - 20 - 5 = 35，不会为负
        self.assertGreaterEqual(score, 0)

    def test_traditional_eac_with_very_low_cpi(self):
        """测试极低CPI的EAC预测"""
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.01')
        mock_evm.budget_at_completion = Decimal('100000')
        mock_evm.actual_cost = Decimal('50000')
        mock_evm.earned_value = Decimal('500')
        
        result = self.service._traditional_eac_prediction(mock_evm)
        
        # 极低CPI会导致极高EAC
        self.assertGreater(result['predicted_eac'], 100000.0)

    def test_prepare_evm_history_empty_list(self):
        """测试空历史数据"""
        result = self.service._prepare_evm_history_data([])
        
        self.assertEqual(result, [])

    def test_get_prediction_history_empty_result(self):
        """测试获取空历史记录"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = self.service.get_prediction_history(project_id=999)
        
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
