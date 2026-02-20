# -*- coding: utf-8 -*-
"""
质量风险管理服务层单元测试
测试业务逻辑的正确性
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

from app.services.quality_risk_management.service import QualityRiskManagementService


class TestQualityRiskManagementService(unittest.TestCase):
    """质量风险管理服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = QualityRiskManagementService(self.db)
    
    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()
    
    # ==================== 测试质量风险检测 ====================
    
    def test_analyze_work_logs_success(self):
        """测试成功分析工作日志"""
        # 准备数据
        project_id = 1
        current_user_id = 100
        
        # 模拟工作日志
        mock_log1 = MagicMock()
        mock_log1.work_date = date.today()
        mock_log1.user_name = "张三"
        mock_log1.task_name = "登录模块"
        mock_log1.work_content = "修复bug"
        mock_log1.work_result = "完成"
        mock_log1.hours = Decimal('8.0')
        
        mock_log2 = MagicMock()
        mock_log2.work_date = date.today()
        mock_log2.user_name = "李四"
        mock_log2.task_name = "支付模块"
        mock_log2.work_content = "重构代码"
        mock_log2.work_result = "进行中"
        mock_log2.hours = Decimal('6.0')
        
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_log1, mock_log2]
        self.db.query.return_value = mock_query
        
        # 模拟AI分析结果
        mock_analysis_result = {
            'risk_signals': ['频繁修改', '工期延迟'],
            'risk_keywords': {'bug': 3, '重构': 2},
            'abnormal_patterns': ['代码频繁变更'],
            'risk_level': 'HIGH',
            'risk_score': 75.5,
            'risk_category': 'TECHNICAL',
            'predicted_issues': ['可能需要额外测试'],
            'rework_probability': 0.6,
            'estimated_impact_days': 3,
            'ai_analysis': '检测到高风险信号',
            'ai_confidence': 0.85,
            'analysis_model': 'gpt-4'
        }
        
        with patch.object(
            self.service.analyzer, 'analyze_work_logs', return_value=mock_analysis_result
        ):
            # 执行测试
            result = self.service.analyze_work_logs(
                project_id=project_id,
                start_date=None,
                end_date=None,
                module_name=None,
                user_ids=None,
                current_user_id=current_user_id
            )
        
        # 验证结果
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.assertEqual(result.status, 'DETECTED')
    
    def test_analyze_work_logs_no_data(self):
        """测试分析工作日志时无数据"""
        # 模拟数据库查询返回空
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query
        
        # 执行并验证异常
        with self.assertRaises(ValueError) as context:
            self.service.analyze_work_logs(
                project_id=1,
                start_date=None,
                end_date=None,
                module_name=None,
                user_ids=None,
                current_user_id=100
            )
        
        self.assertIn("未找到符合条件的工作日志", str(context.exception))
    
    def test_list_detections_with_filters(self):
        """测试带过滤条件的检测记录列表查询"""
        # 准备数据
        mock_detection1 = MagicMock()
        mock_detection1.id = 1
        mock_detection1.risk_level = 'HIGH'
        
        mock_detection2 = MagicMock()
        mock_detection2.id = 2
        mock_detection2.risk_level = 'MEDIUM'
        
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_detection1, mock_detection2]
        self.db.query.return_value = mock_query
        
        # 执行测试
        result = self.service.list_detections(
            project_id=1,
            risk_level='HIGH',
            status='DETECTED',
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            skip=0,
            limit=20
        )
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
    
    def test_get_detection_found(self):
        """测试获取存在的检测记录"""
        # 准备数据
        mock_detection = MagicMock()
        mock_detection.id = 1
        mock_detection.risk_level = 'HIGH'
        
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        self.db.query.return_value = mock_query
        
        # 执行测试
        result = self.service.get_detection(1)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
    
    def test_update_detection_with_confirmation(self):
        """测试更新检测记录并确认"""
        # 准备数据
        mock_detection = MagicMock()
        mock_detection.id = 1
        mock_detection.status = 'DETECTED'
        
        # 模拟 get_detection 返回
        with patch.object(self.service, 'get_detection', return_value=mock_detection):
            # 执行测试
            result = self.service.update_detection(
                detection_id=1,
                status='CONFIRMED',
                resolution_note='已确认风险',
                current_user_id=100
            )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'CONFIRMED')
        self.assertEqual(result.confirmed_by, 100)
        self.assertIsNotNone(result.confirmed_at)
        self.db.commit.assert_called_once()
    
    # ==================== 测试测试推荐 ====================
    
    def test_generate_test_recommendation_success(self):
        """测试成功生成测试推荐"""
        # 准备检测记录
        mock_detection = MagicMock()
        mock_detection.id = 1
        mock_detection.project_id = 1
        mock_detection.risk_level = 'HIGH'
        mock_detection.risk_score = Decimal('80.0')
        mock_detection.risk_category = 'TECHNICAL'
        mock_detection.risk_signals = ['代码复杂度高']
        mock_detection.risk_keywords = {'bug': 5}
        mock_detection.abnormal_patterns = ['频繁修改']
        mock_detection.predicted_issues = ['需要额外测试']
        mock_detection.rework_probability = Decimal('0.7')
        mock_detection.estimated_impact_days = 5
        
        # 模拟推荐数据
        mock_recommendation_data = {
            'focus_areas': ['登录模块', '支付模块'],
            'priority_modules': ['支付模块'],
            'risk_modules': ['登录模块'],
            'test_types': ['功能测试', '集成测试'],
            'test_scenarios': ['场景1', '场景2'],
            'test_coverage_target': 85.0,
            'recommended_testers': 3,
            'recommended_days': 5,
            'priority_level': 'HIGH',
            'ai_reasoning': '基于风险分析',
            'risk_summary': '高风险项目'
        }
        
        # Mock get_detection
        with patch.object(self.service, 'get_detection', return_value=mock_detection):
            # Mock recommendation_engine
            with patch.object(
                self.service.recommendation_engine,
                'generate_recommendations',
                return_value=mock_recommendation_data
            ):
                # 执行测试
                result = self.service.generate_test_recommendation(
                    detection_id=1,
                    current_user_id=100
                )
        
        # 验证结果
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.assertEqual(result.status, 'PENDING')
    
    def test_update_recommendation_success(self):
        """测试成功更新测试推荐"""
        # 准备数据
        mock_recommendation = MagicMock()
        mock_recommendation.id = 1
        mock_recommendation.status = 'PENDING'
        
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_recommendation
        self.db.query.return_value = mock_query
        
        # 执行测试
        update_data = {'status': 'ACCEPTED'}
        result = self.service.update_recommendation(
            recommendation_id=1,
            update_data=update_data
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'ACCEPTED')
        self.db.commit.assert_called_once()
    
    # ==================== 测试质量报告 ====================
    
    def test_generate_quality_report_success(self):
        """测试成功生成质量报告"""
        # 准备检测数据
        mock_detection1 = MagicMock()
        mock_detection1.risk_level = 'HIGH'
        mock_detection1.risk_score = Decimal('85.0')
        mock_detection1.module_name = '登录模块'
        mock_detection1.detection_date = date.today()
        
        mock_detection2 = MagicMock()
        mock_detection2.risk_level = 'MEDIUM'
        mock_detection2.risk_score = Decimal('55.0')
        mock_detection2.module_name = '支付模块'
        mock_detection2.detection_date = date.today()
        
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_detection1, mock_detection2]
        self.db.query.return_value = mock_query
        
        # 执行测试
        result = self.service.generate_quality_report(
            project_id=1,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            include_recommendations=False
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['total_detections'], 2)
        self.assertIn('overall_risk_level', result)
        self.assertIn('risk_distribution', result)
        self.assertIn('trend_analysis', result)
    
    def test_get_statistics_summary_success(self):
        """测试成功获取统计摘要"""
        # 准备检测数据
        mock_detection1 = MagicMock()
        mock_detection1.risk_level = 'HIGH'
        mock_detection1.risk_score = Decimal('80.0')
        mock_detection1.status = 'DETECTED'
        
        mock_detection2 = MagicMock()
        mock_detection2.risk_level = 'MEDIUM'
        mock_detection2.risk_score = Decimal('60.0')
        mock_detection2.status = 'CONFIRMED'
        
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_detection1, mock_detection2]
        self.db.query.return_value = mock_query
        
        # 执行测试
        result = self.service.get_statistics_summary(
            project_id=1,
            days=30
        )
        
        # 验证结果
        self.assertEqual(result['total_detections'], 2)
        self.assertEqual(result['average_risk_score'], 70.0)
        self.assertIn('by_risk_level', result)
        self.assertIn('by_status', result)
        self.assertEqual(result['period_days'], 30)
    
    # ==================== 测试辅助方法 ====================
    
    def test_calculate_overall_risk_critical(self):
        """测试计算总体风险等级 - CRITICAL"""
        risk_distribution = {
            'CRITICAL': 1,
            'HIGH': 2,
            'MEDIUM': 3,
            'LOW': 1
        }
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'CRITICAL')
    
    def test_calculate_overall_risk_high(self):
        """测试计算总体风险等级 - HIGH"""
        risk_distribution = {
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'HIGH')
    
    def test_calculate_overall_risk_medium(self):
        """测试计算总体风险等级 - MEDIUM"""
        risk_distribution = {
            'MEDIUM': 5,
            'LOW': 2
        }
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'MEDIUM')
    
    def test_calculate_overall_risk_low(self):
        """测试计算总体风险等级 - LOW"""
        risk_distribution = {
            'LOW': 3
        }
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'LOW')


if __name__ == '__main__':
    unittest.main()
