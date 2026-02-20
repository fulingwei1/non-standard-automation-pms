# -*- coding: utf-8 -*-
"""
项目成本预测服务单元测试
覆盖率目标: 57%+
"""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.project_cost_prediction.service import ProjectCostPredictionService


class TestProjectCostPredictionService(unittest.TestCase):
    """项目成本预测服务测试套件"""
    
    def setUp(self):
        """测试前置准备"""
        self.mock_db = MagicMock()
        self.service = ProjectCostPredictionService(self.mock_db)
    
    def test_init_without_api_key(self):
        """测试1: 初始化服务（无API密钥）"""
        service = ProjectCostPredictionService(self.mock_db)
        
        self.assertIsNotNone(service.db)
        self.assertIsNotNone(service.calculator)
        # AI预测器应为None（API密钥未配置）
        self.assertIsNone(service.ai_predictor)
    
    def test_get_latest_prediction_success(self):
        """测试2: 获取最新预测 - 成功"""
        # Mock数据
        mock_prediction = MagicMock()
        mock_prediction.id = 1
        mock_prediction.project_id = 100
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_prediction
        
        # 执行
        result = self.service.get_latest_prediction(project_id=100)
        
        # 验证
        self.assertEqual(result.id, 1)
        self.assertEqual(result.project_id, 100)
        self.mock_db.query.assert_called_once()
    
    def test_get_latest_prediction_not_found(self):
        """测试3: 获取最新预测 - 未找到"""
        # Mock返回None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        
        # 执行
        result = self.service.get_latest_prediction(project_id=999)
        
        # 验证
        self.assertIsNone(result)
    
    def test_get_prediction_history_with_limit(self):
        """测试4: 获取预测历史 - 带限制"""
        # Mock数据
        mock_predictions = [MagicMock(), MagicMock(), MagicMock()]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_predictions
        
        # 执行
        result = self.service.get_prediction_history(project_id=100, limit=3)
        
        # 验证
        self.assertEqual(len(result), 3)
        mock_query.filter.return_value.order_by.return_value.limit.assert_called_with(3)
    
    def test_get_prediction_history_without_limit(self):
        """测试5: 获取预测历史 - 无限制"""
        # Mock数据
        mock_predictions = [MagicMock() for _ in range(10)]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_predictions
        
        # 执行
        result = self.service.get_prediction_history(project_id=100)
        
        # 验证
        self.assertEqual(len(result), 10)
    
    def test_traditional_eac_prediction_with_valid_cpi(self):
        """测试6: 传统EAC预测 - CPI有效"""
        # Mock EVM数据
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.9')
        mock_evm.budget_at_completion = Decimal('1000000')
        mock_evm.actual_cost = Decimal('500000')
        mock_evm.earned_value = Decimal('450000')
        
        # 执行
        result = self.service._traditional_eac_prediction(mock_evm)
        
        # 验证
        self.assertIn('predicted_eac', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['confidence'], 70.0)
        self.assertGreater(result['predicted_eac'], 0)
    
    def test_traditional_eac_prediction_with_zero_cpi(self):
        """测试7: 传统EAC预测 - CPI为0"""
        # Mock EVM数据
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0')
        mock_evm.budget_at_completion = Decimal('1000000')
        mock_evm.actual_cost = Decimal('500000')
        mock_evm.earned_value = Decimal('0')
        
        # 执行
        result = self.service._traditional_eac_prediction(mock_evm)
        
        # 验证
        # CPI为0时，应使用BAC*1.2作为EAC
        expected_eac = float(Decimal('1000000') * Decimal('1.2'))
        self.assertEqual(result['predicted_eac'], expected_eac)
    
    def test_traditional_risk_analysis_low_risk(self):
        """测试8: 传统风险分析 - 低风险"""
        # Mock EVM数据
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.96')
        
        mock_history = []
        
        # 执行
        result = self.service._traditional_risk_analysis(mock_evm, mock_history)
        
        # 验证
        self.assertEqual(result['risk_level'], 'LOW')
        self.assertEqual(result['overrun_probability'], 20.0)
    
    def test_traditional_risk_analysis_medium_risk(self):
        """测试9: 传统风险分析 - 中等风险"""
        # Mock EVM数据
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.88')
        
        mock_history = []
        
        # 执行
        result = self.service._traditional_risk_analysis(mock_evm, mock_history)
        
        # 验证
        self.assertEqual(result['risk_level'], 'MEDIUM')
        self.assertEqual(result['overrun_probability'], 50.0)
    
    def test_traditional_risk_analysis_high_risk(self):
        """测试10: 传统风险分析 - 高风险"""
        # Mock EVM数据
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.78')
        
        mock_history = []
        
        # 执行
        result = self.service._traditional_risk_analysis(mock_evm, mock_history)
        
        # 验证
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertEqual(result['overrun_probability'], 75.0)
    
    def test_traditional_risk_analysis_critical_risk(self):
        """测试11: 传统风险分析 - 严重风险"""
        # Mock EVM数据
        mock_evm = MagicMock()
        mock_evm.cost_performance_index = Decimal('0.65')
        
        mock_history = []
        
        # 执行
        result = self.service._traditional_risk_analysis(mock_evm, mock_history)
        
        # 验证
        self.assertEqual(result['risk_level'], 'CRITICAL')
        self.assertEqual(result['overrun_probability'], 90.0)
    
    def test_calculate_data_quality_sufficient_history(self):
        """测试12: 计算数据质量 - 充足历史"""
        # Mock历史数据（10条）
        mock_history = [{'period': f'2024-{i:02d}', 'cpi': 0.9} for i in range(1, 11)]
        
        # 执行
        result = self.service._calculate_data_quality(mock_history)
        
        # 验证
        # 历史数据>=6，不扣分
        self.assertEqual(result, Decimal('100'))
    
    def test_calculate_data_quality_limited_history(self):
        """测试13: 计算数据质量 - 有限历史"""
        # Mock历史数据（4条）
        mock_history = [{'period': f'2024-{i:02d}', 'cpi': 0.9} for i in range(1, 5)]
        
        # 执行
        result = self.service._calculate_data_quality(mock_history)
        
        # 验证
        # 历史数据3-5条，扣15分
        self.assertEqual(result, Decimal('85'))
    
    def test_calculate_data_quality_insufficient_history(self):
        """测试14: 计算数据质量 - 不足历史"""
        # Mock历史数据（2条）
        mock_history = [{'period': '2024-01', 'cpi': 0.9}, {'period': '2024-02', 'cpi': 0.88}]
        
        # 执行
        result = self.service._calculate_data_quality(mock_history)
        
        # 验证
        # 历史数据<3，扣30分
        self.assertEqual(result, Decimal('70'))
    
    def test_get_suggestions_summary(self):
        """测试15: 获取优化建议摘要"""
        # Mock查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.count.side_effect = [2, 1, 3]  # pending, approved, in_progress
        
        # 执行
        result = self.service._get_suggestions_summary(project_id=100)
        
        # 验证
        self.assertEqual(result['pending'], 2)
        self.assertEqual(result['approved'], 1)
        self.assertEqual(result['in_progress'], 3)
    
    def test_calculate_health_score_critical_risk(self):
        """测试16: 计算健康评分 - 严重风险"""
        # Mock预测数据
        mock_prediction = MagicMock()
        mock_prediction.risk_level = 'CRITICAL'
        mock_prediction.current_cpi = Decimal('0.75')
        
        suggestions_summary = {'pending': 0, 'approved': 0, 'in_progress': 0}
        
        # 执行
        result = self.service._calculate_health_score(mock_prediction, suggestions_summary)
        
        # 验证
        # 严重风险扣40分，CPI<0.8扣20分
        self.assertEqual(result, 40.0)
    
    def test_calculate_health_score_high_risk(self):
        """测试17: 计算健康评分 - 高风险"""
        # Mock预测数据
        mock_prediction = MagicMock()
        mock_prediction.risk_level = 'HIGH'
        mock_prediction.current_cpi = Decimal('0.85')
        
        suggestions_summary = {'pending': 0, 'approved': 0, 'in_progress': 0}
        
        # 执行
        result = self.service._calculate_health_score(mock_prediction, suggestions_summary)
        
        # 验证
        # 高风险扣25分，CPI<0.9扣10分
        self.assertEqual(result, 65.0)
    
    def test_calculate_health_score_with_pending_suggestions(self):
        """测试18: 计算健康评分 - 有待处理建议"""
        # Mock预测数据
        mock_prediction = MagicMock()
        mock_prediction.risk_level = 'LOW'
        mock_prediction.current_cpi = Decimal('0.95')
        
        suggestions_summary = {'pending': 3, 'approved': 0, 'in_progress': 0}
        
        # 执行
        result = self.service._calculate_health_score(mock_prediction, suggestions_summary)
        
        # 验证
        # 有待处理建议扣5分
        self.assertEqual(result, 95.0)
    
    def test_get_health_recommendation_excellent(self):
        """测试19: 健康建议 - 优秀"""
        result = self.service._get_health_recommendation(85.0, 'LOW')
        self.assertEqual(result, "项目成本状况良好，继续保持。")
    
    def test_get_health_recommendation_fair(self):
        """测试20: 健康建议 - 一般"""
        result = self.service._get_health_recommendation(65.0, 'MEDIUM')
        self.assertEqual(result, "项目成本存在一定风险，建议关注优化建议。")
    
    def test_get_health_recommendation_poor(self):
        """测试21: 健康建议 - 较差"""
        result = self.service._get_health_recommendation(45.0, 'HIGH')
        self.assertEqual(result, "项目成本风险较高，建议立即采取优化措施。")
    
    def test_get_health_recommendation_critical(self):
        """测试22: 健康建议 - 严重"""
        result = self.service._get_health_recommendation(25.0, 'CRITICAL')
        self.assertEqual(result, "项目成本风险严重，需要紧急干预！")
    
    def test_prepare_project_data(self):
        """测试23: 准备项目数据"""
        # Mock项目和EVM数据
        mock_project = MagicMock()
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 12, 31)
        
        mock_evm = MagicMock()
        mock_evm.budget_at_completion = Decimal('1000000')
        mock_evm.planned_value = Decimal('500000')
        mock_evm.earned_value = Decimal('450000')
        mock_evm.actual_cost = Decimal('480000')
        mock_evm.cost_performance_index = Decimal('0.94')
        mock_evm.schedule_performance_index = Decimal('0.90')
        mock_evm.actual_percent_complete = Decimal('45')
        
        # 执行
        result = self.service._prepare_project_data(mock_project, mock_evm)
        
        # 验证
        self.assertEqual(result['project_code'], 'PRJ001')
        self.assertEqual(result['project_name'], '测试项目')
        self.assertEqual(result['bac'], Decimal('1000000'))
        self.assertEqual(result['current_cpi'], Decimal('0.94'))
    
    def test_prepare_evm_history_data(self):
        """测试24: 准备EVM历史数据"""
        # Mock EVM历史
        mock_evm_1 = MagicMock()
        mock_evm_1.period_date = date(2024, 1, 31)
        mock_evm_1.cost_performance_index = Decimal('0.95')
        mock_evm_1.schedule_performance_index = Decimal('0.98')
        mock_evm_1.actual_cost = Decimal('100000')
        mock_evm_1.earned_value = Decimal('95000')
        mock_evm_1.planned_value = Decimal('97000')
        
        mock_evm_2 = MagicMock()
        mock_evm_2.period_date = date(2024, 2, 28)
        mock_evm_2.cost_performance_index = Decimal('0.92')
        mock_evm_2.schedule_performance_index = Decimal('0.95')
        mock_evm_2.actual_cost = Decimal('200000')
        mock_evm_2.earned_value = Decimal('184000')
        mock_evm_2.planned_value = Decimal('194000')
        
        mock_history = [mock_evm_1, mock_evm_2]
        
        # 执行
        result = self.service._prepare_evm_history_data(mock_history)
        
        # 验证
        self.assertEqual(len(result), 2)
        # 注意：reversed会反转顺序
        self.assertEqual(result[0]['period'], '2024-02-28')
        self.assertEqual(result[1]['period'], '2024-01-31')


if __name__ == '__main__':
    unittest.main()
