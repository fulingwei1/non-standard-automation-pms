# -*- coding: utf-8 -*-
"""
质量风险管理服务增强测试
测试覆盖所有核心方法和业务逻辑
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.quality_risk_management.service import QualityRiskManagementService
from app.models.quality_risk_detection import (
    QualityRiskDetection,
    QualityTestRecommendation,
)
from app.models.timesheet import Timesheet


class TestQualityRiskManagementService(unittest.TestCase):
    """质量风险管理服务测试类"""
    
    def setUp(self):
        """测试前置准备"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        
        # 创建服务实例
        with patch('app.services.quality_risk_management.service.QualityRiskAnalyzer'), \
             patch('app.services.quality_risk_management.service.TestRecommendationEngine'):
            self.service = QualityRiskManagementService(self.mock_db)
        
        # Mock AI分析器和推荐引擎
        self.service.analyzer = MagicMock()
        self.service.recommendation_engine = MagicMock()
    
    # ==================== analyze_work_logs 测试 ====================
    
    def test_analyze_work_logs_success(self):
        """测试成功分析工作日志"""
        # 准备测试数据
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        current_user_id = 10
        
        # 构造真实的工作日志对象
        work_log1 = Timesheet(
            id=1,
            project_id=project_id,
            user_id=5,
            user_name='张三',
            work_date=date(2024, 1, 2),
            task_name='用户模块',
            work_content='实现登录功能',
            work_result='完成基本登录',
            hours=Decimal('8.0')
        )
        work_log2 = Timesheet(
            id=2,
            project_id=project_id,
            user_id=6,
            user_name='李四',
            work_date=date(2024, 1, 3),
            task_name='用户模块',
            work_content='修复BUG',
            work_result='修复登录问题',
            hours=Decimal('6.0')
        )
        
        # Mock数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [work_log1, work_log2]
        
        # Mock AI分析结果
        ai_result = {
            'risk_signals': ['频繁修复', 'BUG关键词'],
            'risk_keywords': {'BUG': 1, '修复': 1},
            'abnormal_patterns': ['短期内多次修改'],
            'risk_level': 'MEDIUM',
            'risk_score': 65.5,
            'risk_category': 'BUG',
            'predicted_issues': ['可能存在遗漏的BUG'],
            'rework_probability': 40.0,
            'estimated_impact_days': 2,
            'ai_analysis': {'details': 'detailed analysis'},
            'ai_confidence': 85.0,
            'analysis_model': 'gpt-4'
        }
        self.service.analyzer.analyze_work_logs.return_value = ai_result
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            module_name=None,
            user_ids=None,
            current_user_id=current_user_id
        )
        
        # 验证结果
        self.assertIsInstance(result, QualityRiskDetection)
        self.assertEqual(result.project_id, project_id)
        self.assertEqual(result.risk_level, 'MEDIUM')
        self.assertEqual(result.risk_score, 65.5)
        self.assertEqual(result.status, 'DETECTED')
        self.assertEqual(result.created_by, current_user_id)
        
        # 验证数据库操作
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
    
    def test_analyze_work_logs_with_filters(self):
        """测试带过滤条件的工作日志分析"""
        project_id = 1
        module_name = '用户模块'
        user_ids = [5, 6]
        
        work_log = Timesheet(
            id=1,
            project_id=project_id,
            user_id=5,
            user_name='张三',
            work_date=date.today(),
            task_name=module_name,
            work_content='开发功能',
            hours=Decimal('8.0')
        )
        
        # Mock查询链
        mock_query = self.mock_db.query.return_value
        mock_filtered = MagicMock()
        mock_query.filter.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.all.return_value = [work_log]
        
        # Mock AI结果
        self.service.analyzer.analyze_work_logs.return_value = {
            'risk_signals': [],
            'risk_level': 'LOW',
            'risk_score': 20.0,
            'risk_category': None,
            'predicted_issues': [],
        }
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id=project_id,
            start_date=None,  # 测试默认日期
            end_date=None,
            module_name=module_name,
            user_ids=user_ids,
            current_user_id=1
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.module_name, module_name)
    
    def test_analyze_work_logs_no_data(self):
        """测试没有工作日志数据时抛出异常"""
        # Mock空查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.analyze_work_logs(
                project_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 7),
                module_name=None,
                user_ids=None,
                current_user_id=1
            )
        
        self.assertIn('未找到符合条件的工作日志', str(context.exception))
    
    def test_analyze_work_logs_null_fields(self):
        """测试处理空字段的工作日志"""
        # 构造有空字段的工作日志
        work_log = Timesheet(
            id=1,
            project_id=1,
            user_id=5,
            user_name='张三',
            work_date=date.today(),
            task_name='任务',
            work_content=None,  # 空内容
            work_result=None,   # 空结果
            hours=None          # 空小时数
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [work_log]
        
        self.service.analyzer.analyze_work_logs.return_value = {
            'risk_signals': [],
            'risk_level': 'LOW',
            'risk_score': 10.0,
        }
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id=1,
            start_date=date.today(),
            end_date=date.today(),
            module_name=None,
            user_ids=None,
            current_user_id=1
        )
        
        # 验证能正常处理空字段
        self.assertIsNotNone(result)
    
    def test_analyze_work_logs_default_dates(self):
        """测试使用默认日期范围"""
        work_log = Timesheet(
            id=1,
            project_id=1,
            user_id=5,
            user_name='张三',
            work_date=date.today(),
            task_name='任务',
            hours=Decimal('8.0')
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [work_log]
        
        self.service.analyzer.analyze_work_logs.return_value = {
            'risk_signals': [],
            'risk_level': 'LOW',
            'risk_score': 15.0,
        }
        
        # 不传入日期，使用默认值
        result = self.service.analyze_work_logs(
            project_id=1,
            start_date=None,
            end_date=None,
            module_name=None,
            user_ids=None,
            current_user_id=1
        )
        
        # 验证detection_date是今天
        self.assertEqual(result.detection_date, date.today())
    
    # ==================== list_detections 测试 ====================
    
    def test_list_detections_all(self):
        """测试查询所有检测记录"""
        # 构造检测记录
        detection1 = QualityRiskDetection(
            id=1,
            project_id=1,
            detection_date=date(2024, 1, 5),
            risk_level='HIGH',
            risk_score=Decimal('80.0'),
            status='DETECTED'
        )
        detection2 = QualityRiskDetection(
            id=2,
            project_id=2,
            detection_date=date(2024, 1, 6),
            risk_level='MEDIUM',
            risk_score=Decimal('60.0'),
            status='CONFIRMED'
        )
        
        # Mock查询
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [detection1, detection2]
        
        # 执行测试
        results = self.service.list_detections()
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, 1)
        self.assertEqual(results[1].id, 2)
    
    def test_list_detections_with_filters(self):
        """测试带过滤条件查询检测记录"""
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            detection_date=date(2024, 1, 5),
            risk_level='CRITICAL',
            risk_score=Decimal('95.0'),
            status='DETECTED'
        )
        
        # Mock过滤查询
        mock_query = self.mock_db.query.return_value
        mock_filtered = MagicMock()
        mock_query.filter.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.order_by.return_value = mock_filtered
        mock_filtered.offset.return_value = mock_filtered
        mock_filtered.limit.return_value = mock_filtered
        mock_filtered.all.return_value = [detection]
        
        # 执行测试
        results = self.service.list_detections(
            project_id=1,
            risk_level='CRITICAL',
            status='DETECTED',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10)
        )
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].risk_level, 'CRITICAL')
    
    def test_list_detections_pagination(self):
        """测试分页查询"""
        detections = [
            QualityRiskDetection(id=i, project_id=1, risk_level='LOW', 
                                risk_score=Decimal('10.0'), status='DETECTED')
            for i in range(1, 11)
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = detections[5:10]  # 模拟第二页
        
        # 执行测试（第二页，每页5条）
        results = self.service.list_detections(skip=5, limit=5)
        
        # 验证分页
        self.assertEqual(len(results), 5)
        mock_query.offset.assert_called_with(5)
        mock_query.limit.assert_called_with(5)
    
    def test_list_detections_empty(self):
        """测试查询无结果"""
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        results = self.service.list_detections()
        
        self.assertEqual(len(results), 0)
    
    # ==================== get_detection 测试 ====================
    
    def test_get_detection_success(self):
        """测试成功获取检测详情"""
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            risk_level='HIGH',
            risk_score=Decimal('85.0'),
            status='DETECTED'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = detection
        
        result = self.service.get_detection(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.risk_level, 'HIGH')
    
    def test_get_detection_not_found(self):
        """测试获取不存在的检测记录"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.get_detection(999)
        
        self.assertIsNone(result)
    
    # ==================== update_detection 测试 ====================
    
    def test_update_detection_status(self):
        """测试更新检测状态"""
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            risk_level='HIGH',
            risk_score=Decimal('80.0'),
            status='DETECTED'
        )
        
        # Mock查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = detection
        
        # 执行更新
        result = self.service.update_detection(
            detection_id=1,
            status='CONFIRMED',
            current_user_id=10
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'CONFIRMED')
        self.assertEqual(result.confirmed_by, 10)
        self.assertIsNotNone(result.confirmed_at)
        self.mock_db.commit.assert_called_once()
    
    def test_update_detection_with_note(self):
        """测试更新检测并添加备注"""
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            risk_level='HIGH',
            risk_score=Decimal('80.0'),
            status='DETECTED'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = detection
        
        result = self.service.update_detection(
            detection_id=1,
            status='RESOLVED',
            resolution_note='已修复所有问题',
            current_user_id=10
        )
        
        self.assertEqual(result.status, 'RESOLVED')
        self.assertEqual(result.resolution_note, '已修复所有问题')
    
    def test_update_detection_false_positive(self):
        """测试标记为误报"""
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            risk_level='HIGH',
            risk_score=Decimal('80.0'),
            status='DETECTED'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = detection
        
        result = self.service.update_detection(
            detection_id=1,
            status='FALSE_POSITIVE',
            current_user_id=10
        )
        
        self.assertEqual(result.status, 'FALSE_POSITIVE')
        self.assertIsNotNone(result.confirmed_at)
    
    def test_update_detection_not_found(self):
        """测试更新不存在的检测记录"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.update_detection(
            detection_id=999,
            status='CONFIRMED'
        )
        
        self.assertIsNone(result)
        self.mock_db.commit.assert_not_called()
    
    # ==================== generate_test_recommendation 测试 ====================
    
    def test_generate_test_recommendation_success(self):
        """测试成功生成测试推荐"""
        # 构造检测记录
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            risk_level='HIGH',
            risk_score=Decimal('85.0'),
            risk_category='BUG',
            risk_signals=['频繁修复'],
            risk_keywords={'BUG': 2},
            abnormal_patterns=['短期内多次修改'],
            predicted_issues=['可能存在遗漏的BUG'],
            rework_probability=Decimal('60.0'),
            estimated_impact_days=3
        )
        
        # Mock get_detection
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = detection
        
        # Mock推荐引擎结果
        recommendation_data = {
            'focus_areas': ['用户模块', '登录功能'],
            'priority_modules': ['用户模块'],
            'risk_modules': ['登录功能'],
            'test_types': ['功能测试', '回归测试'],
            'test_scenarios': ['测试场景1', '测试场景2'],
            'test_coverage_target': 80.0,
            'recommended_testers': 2,
            'recommended_days': 3,
            'priority_level': 'HIGH',
            'ai_reasoning': '基于高风险评分推荐',
            'risk_summary': '存在较高质量风险'
        }
        self.service.recommendation_engine.generate_recommendations.return_value = recommendation_data
        
        # 执行测试
        result = self.service.generate_test_recommendation(
            detection_id=1,
            current_user_id=10
        )
        
        # 验证结果
        self.assertIsInstance(result, QualityTestRecommendation)
        self.assertEqual(result.project_id, 1)
        self.assertEqual(result.detection_id, 1)
        self.assertEqual(result.priority_level, 'HIGH')
        self.assertEqual(result.recommended_days, 3)
        self.assertEqual(result.status, 'PENDING')
        self.assertEqual(result.created_by, 10)
        
        # 验证数据库操作
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_generate_test_recommendation_not_found(self):
        """测试检测记录不存在时返回None"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.generate_test_recommendation(
            detection_id=999,
            current_user_id=10
        )
        
        self.assertIsNone(result)
        self.mock_db.add.assert_not_called()
    
    def test_generate_test_recommendation_with_null_fields(self):
        """测试处理包含空字段的检测记录"""
        detection = QualityRiskDetection(
            id=1,
            project_id=1,
            risk_level='MEDIUM',
            risk_score=Decimal('50.0'),
            risk_category=None,  # 空字段
            risk_signals=None,
            risk_keywords=None,
            abnormal_patterns=None,
            predicted_issues=None,
            rework_probability=None,
            estimated_impact_days=None
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = detection
        
        recommendation_data = {
            'focus_areas': ['通用测试'],
            'priority_level': 'MEDIUM',
            'recommended_days': 2
        }
        self.service.recommendation_engine.generate_recommendations.return_value = recommendation_data
        
        result = self.service.generate_test_recommendation(
            detection_id=1,
            current_user_id=10
        )
        
        # 验证能处理空字段
        self.assertIsNotNone(result)
    
    # ==================== list_recommendations 测试 ====================
    
    def test_list_recommendations_all(self):
        """测试查询所有推荐"""
        rec1 = QualityTestRecommendation(
            id=1,
            project_id=1,
            priority_level='HIGH',
            status='PENDING'
        )
        rec2 = QualityTestRecommendation(
            id=2,
            project_id=2,
            priority_level='MEDIUM',
            status='ACCEPTED'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [rec1, rec2]
        
        results = self.service.list_recommendations()
        
        self.assertEqual(len(results), 2)
    
    def test_list_recommendations_with_filters(self):
        """测试带过滤条件查询推荐"""
        rec = QualityTestRecommendation(
            id=1,
            project_id=1,
            priority_level='URGENT',
            status='PENDING'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_filtered = MagicMock()
        mock_query.filter.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.order_by.return_value = mock_filtered
        mock_filtered.offset.return_value = mock_filtered
        mock_filtered.limit.return_value = mock_filtered
        mock_filtered.all.return_value = [rec]
        
        results = self.service.list_recommendations(
            project_id=1,
            priority_level='URGENT',
            status='PENDING'
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].priority_level, 'URGENT')
    
    def test_list_recommendations_pagination(self):
        """测试推荐分页"""
        recs = [
            QualityTestRecommendation(id=i, project_id=1, priority_level='LOW', status='PENDING')
            for i in range(1, 11)
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = recs[0:10]
        
        results = self.service.list_recommendations(skip=0, limit=10)
        
        self.assertEqual(len(results), 10)
    
    def test_list_recommendations_empty(self):
        """测试查询无推荐结果"""
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        results = self.service.list_recommendations()
        
        self.assertEqual(len(results), 0)
    
    # ==================== update_recommendation 测试 ====================
    
    def test_update_recommendation_status(self):
        """测试更新推荐状态"""
        rec = QualityTestRecommendation(
            id=1,
            project_id=1,
            priority_level='HIGH',
            status='PENDING'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = rec
        
        result = self.service.update_recommendation(
            recommendation_id=1,
            update_data={'status': 'ACCEPTED', 'acceptance_note': '同意执行'}
        )
        
        self.assertEqual(result.status, 'ACCEPTED')
        self.assertEqual(result.acceptance_note, '同意执行')
        self.mock_db.commit.assert_called_once()
    
    def test_update_recommendation_multiple_fields(self):
        """测试更新多个字段"""
        rec = QualityTestRecommendation(
            id=1,
            project_id=1,
            priority_level='HIGH',
            status='IN_PROGRESS'
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = rec
        
        update_data = {
            'status': 'COMPLETED',
            'actual_test_days': 4,
            'actual_coverage': Decimal('85.5'),
            'bugs_found': 12,
            'critical_bugs_found': 3
        }
        
        result = self.service.update_recommendation(
            recommendation_id=1,
            update_data=update_data
        )
        
        self.assertEqual(result.status, 'COMPLETED')
        self.assertEqual(result.actual_test_days, 4)
        self.assertEqual(result.bugs_found, 12)
    
    def test_update_recommendation_not_found(self):
        """测试更新不存在的推荐"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.update_recommendation(
            recommendation_id=999,
            update_data={'status': 'ACCEPTED'}
        )
        
        self.assertIsNone(result)
        self.mock_db.commit.assert_not_called()
    
    # ==================== generate_quality_report 测试 ====================
    
    def test_generate_quality_report_success(self):
        """测试成功生成质量报告"""
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # 构造检测记录
        detections = [
            QualityRiskDetection(
                id=1,
                project_id=project_id,
                module_name='用户模块',
                detection_date=date(2024, 1, 5),
                risk_level='HIGH',
                risk_score=Decimal('85.0')
            ),
            QualityRiskDetection(
                id=2,
                project_id=project_id,
                module_name='订单模块',
                detection_date=date(2024, 1, 10),
                risk_level='MEDIUM',
                risk_score=Decimal('60.0')
            ),
            QualityRiskDetection(
                id=3,
                project_id=project_id,
                module_name='支付模块',
                detection_date=date(2024, 1, 15),
                risk_level='LOW',
                risk_score=Decimal('25.0')
            )
        ]
        
        # Mock查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = detections
        
        # 执行测试
        report = self.service.generate_quality_report(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            include_recommendations=False
        )
        
        # 验证报告结构
        self.assertEqual(report['project_id'], project_id)
        self.assertEqual(report['total_detections'], 3)
        self.assertIn('HIGH', report['risk_distribution'])
        self.assertEqual(report['risk_distribution']['HIGH'], 1)
        self.assertEqual(report['risk_distribution']['MEDIUM'], 1)
        self.assertEqual(report['risk_distribution']['LOW'], 1)
        self.assertEqual(report['overall_risk_level'], 'LOW')  # 没有严重风险
        self.assertIsNotNone(report['top_risk_modules'])
        self.assertIsNotNone(report['trend_analysis'])
        self.assertIsNotNone(report['summary'])
    
    def test_generate_quality_report_with_recommendations(self):
        """测试生成包含推荐的报告"""
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        detections = [
            QualityRiskDetection(
                id=1,
                project_id=project_id,
                detection_date=date(2024, 1, 5),
                risk_level='CRITICAL',
                risk_score=Decimal('95.0')
            )
        ]
        
        recommendations = [
            QualityTestRecommendation(
                id=1,
                project_id=project_id,
                recommendation_date=date(2024, 1, 6),
                priority_level='URGENT',
                status='PENDING',
                recommended_days=5,
                ai_reasoning='高风险需立即测试'
            )
        ]
        
        # Mock检测查询
        mock_query_detection = MagicMock()
        mock_query_detection.filter.return_value = mock_query_detection
        mock_query_detection.all.return_value = detections
        
        # Mock推荐查询
        mock_query_recommendation = MagicMock()
        mock_query_recommendation.filter.return_value = mock_query_recommendation
        mock_query_recommendation.all.return_value = recommendations
        
        # 设置query返回不同的mock
        self.mock_db.query.side_effect = [mock_query_detection, mock_query_recommendation]
        
        # 执行测试
        report = self.service.generate_quality_report(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            include_recommendations=True
        )
        
        # 验证推荐数据包含在报告中
        self.assertIsNotNone(report['recommendations'])
        self.assertEqual(len(report['recommendations']), 1)
        self.assertEqual(report['recommendations'][0]['priority'], 'URGENT')
    
    def test_generate_quality_report_no_data(self):
        """测试没有检测数据时抛出异常"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        with self.assertRaises(ValueError) as context:
            self.service.generate_quality_report(
                project_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        
        self.assertIn('没有质量风险检测数据', str(context.exception))
    
    def test_generate_quality_report_critical_risk(self):
        """测试包含严重风险的报告"""
        detections = [
            QualityRiskDetection(
                id=1,
                project_id=1,
                detection_date=date.today(),
                risk_level='CRITICAL',
                risk_score=Decimal('98.0')
            )
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = detections
        
        report = self.service.generate_quality_report(
            project_id=1,
            start_date=date.today(),
            end_date=date.today()
        )
        
        # 验证总体风险为CRITICAL
        self.assertEqual(report['overall_risk_level'], 'CRITICAL')
        self.assertIn('严重风险', report['summary'])
    
    def test_generate_quality_report_trend_analysis(self):
        """测试趋势分析数据"""
        detections = [
            QualityRiskDetection(
                id=1,
                project_id=1,
                detection_date=date(2024, 1, 1),
                risk_level='HIGH',
                risk_score=Decimal('80.0')
            ),
            QualityRiskDetection(
                id=2,
                project_id=1,
                detection_date=date(2024, 1, 1),
                risk_level='MEDIUM',
                risk_score=Decimal('60.0')
            ),
            QualityRiskDetection(
                id=3,
                project_id=1,
                detection_date=date(2024, 1, 2),
                risk_level='LOW',
                risk_score=Decimal('30.0')
            )
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = detections
        
        report = self.service.generate_quality_report(
            project_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2)
        )
        
        # 验证趋势数据
        trend = report['trend_analysis']
        self.assertIn('2024-01-01', trend)
        self.assertIn('2024-01-02', trend)
        self.assertEqual(trend['2024-01-01']['count'], 2)
        self.assertEqual(trend['2024-01-02']['count'], 1)
        # 平均分数计算
        self.assertAlmostEqual(trend['2024-01-01']['avg_score'], 70.0, places=1)
    
    # ==================== get_statistics_summary 测试 ====================
    
    def test_get_statistics_summary_success(self):
        """测试成功获取统计摘要"""
        # 构造检测记录
        detections = [
            QualityRiskDetection(
                id=1,
                project_id=1,
                detection_date=date.today(),
                risk_level='HIGH',
                risk_score=Decimal('80.0'),
                status='DETECTED'
            ),
            QualityRiskDetection(
                id=2,
                project_id=1,
                detection_date=date.today() - timedelta(days=5),
                risk_level='MEDIUM',
                risk_score=Decimal('60.0'),
                status='CONFIRMED'
            ),
            QualityRiskDetection(
                id=3,
                project_id=1,
                detection_date=date.today() - timedelta(days=10),
                risk_level='LOW',
                risk_score=Decimal('20.0'),
                status='RESOLVED'
            )
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = detections
        
        # 执行测试
        stats = self.service.get_statistics_summary(project_id=1, days=30)
        
        # 验证统计结果
        self.assertEqual(stats['total_detections'], 3)
        self.assertAlmostEqual(stats['average_risk_score'], 53.33, places=2)
        self.assertEqual(stats['by_risk_level']['HIGH'], 1)
        self.assertEqual(stats['by_risk_level']['MEDIUM'], 1)
        self.assertEqual(stats['by_risk_level']['LOW'], 1)
        self.assertEqual(stats['by_status']['DETECTED'], 1)
        self.assertEqual(stats['by_status']['CONFIRMED'], 1)
        self.assertEqual(stats['by_status']['RESOLVED'], 1)
        self.assertEqual(stats['period_days'], 30)
    
    def test_get_statistics_summary_no_project_filter(self):
        """测试不过滤项目的统计"""
        detections = [
            QualityRiskDetection(
                id=1,
                project_id=1,
                detection_date=date.today(),
                risk_level='HIGH',
                risk_score=Decimal('75.0'),
                status='DETECTED'
            ),
            QualityRiskDetection(
                id=2,
                project_id=2,
                detection_date=date.today(),
                risk_level='MEDIUM',
                risk_score=Decimal('55.0'),
                status='DETECTED'
            )
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = detections
        
        # 不传project_id
        stats = self.service.get_statistics_summary(days=7)
        
        self.assertEqual(stats['total_detections'], 2)
        self.assertEqual(stats['period_days'], 7)
    
    def test_get_statistics_summary_empty(self):
        """测试无数据时的统计"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        stats = self.service.get_statistics_summary(project_id=1, days=30)
        
        # 验证空统计
        self.assertEqual(stats['total_detections'], 0)
        self.assertEqual(stats['average_risk_score'], 0)
        self.assertEqual(stats['by_risk_level'], {})
        self.assertEqual(stats['by_status'], {})
    
    # ==================== 辅助方法测试 ====================
    
    def test_calculate_overall_risk_critical(self):
        """测试计算总体风险 - CRITICAL"""
        risk_distribution = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3}
        
        overall_risk = self.service._calculate_overall_risk(risk_distribution)
        
        self.assertEqual(overall_risk, 'CRITICAL')
    
    def test_calculate_overall_risk_high(self):
        """测试计算总体风险 - HIGH"""
        risk_distribution = {'HIGH': 3, 'MEDIUM': 2}
        
        overall_risk = self.service._calculate_overall_risk(risk_distribution)
        
        self.assertEqual(overall_risk, 'HIGH')
    
    def test_calculate_overall_risk_medium(self):
        """测试计算总体风险 - MEDIUM"""
        risk_distribution = {'MEDIUM': 5, 'LOW': 2}
        
        overall_risk = self.service._calculate_overall_risk(risk_distribution)
        
        self.assertEqual(overall_risk, 'MEDIUM')
    
    def test_calculate_overall_risk_low(self):
        """测试计算总体风险 - LOW"""
        risk_distribution = {'MEDIUM': 2, 'LOW': 5}
        
        overall_risk = self.service._calculate_overall_risk(risk_distribution)
        
        self.assertEqual(overall_risk, 'LOW')
    
    def test_extract_top_risk_modules(self):
        """测试提取高风险模块"""
        detections = [
            QualityRiskDetection(
                id=1,
                module_name='模块A',
                detection_date=date(2024, 1, 1),
                risk_level='CRITICAL',
                risk_score=Decimal('95.0')
            ),
            QualityRiskDetection(
                id=2,
                module_name='模块B',
                detection_date=date(2024, 1, 2),
                risk_level='HIGH',
                risk_score=Decimal('85.0')
            ),
            QualityRiskDetection(
                id=3,
                module_name='模块C',
                detection_date=date(2024, 1, 3),
                risk_level='MEDIUM',
                risk_score=Decimal('60.0')
            )
        ]
        
        top_modules = self.service._extract_top_risk_modules(detections)
        
        # 验证按风险分数降序排列
        self.assertEqual(len(top_modules), 3)
        self.assertEqual(top_modules[0]['module'], '模块A')
        self.assertEqual(top_modules[0]['risk_score'], 95.0)
        self.assertEqual(top_modules[1]['module'], '模块B')
        self.assertEqual(top_modules[2]['module'], '模块C')
    
    def test_extract_top_risk_modules_limit(self):
        """测试提取高风险模块数量限制"""
        detections = [
            QualityRiskDetection(
                id=i,
                module_name=f'模块{i}',
                detection_date=date.today(),
                risk_level='HIGH',
                risk_score=Decimal(str(100 - i * 5))
            )
            for i in range(1, 11)  # 10个模块
        ]
        
        top_modules = self.service._extract_top_risk_modules(detections)
        
        # 验证只返回前5个
        self.assertEqual(len(top_modules), 5)
        self.assertEqual(top_modules[0]['module'], '模块1')
        self.assertEqual(top_modules[4]['module'], '模块5')
    
    def test_analyze_trends(self):
        """测试趋势分析"""
        detections = [
            QualityRiskDetection(
                id=1,
                detection_date=date(2024, 1, 1),
                risk_score=Decimal('80.0')
            ),
            QualityRiskDetection(
                id=2,
                detection_date=date(2024, 1, 1),
                risk_score=Decimal('60.0')
            ),
            QualityRiskDetection(
                id=3,
                detection_date=date(2024, 1, 2),
                risk_score=Decimal('50.0')
            )
        ]
        
        trend_data = self.service._analyze_trends(detections)
        
        # 验证趋势数据
        self.assertIn('2024-01-01', trend_data)
        self.assertIn('2024-01-02', trend_data)
        self.assertEqual(trend_data['2024-01-01']['count'], 2)
        self.assertEqual(trend_data['2024-01-02']['count'], 1)
        self.assertAlmostEqual(trend_data['2024-01-01']['avg_score'], 70.0, places=1)
        self.assertAlmostEqual(trend_data['2024-01-02']['avg_score'], 50.0, places=1)


if __name__ == '__main__':
    unittest.main()
