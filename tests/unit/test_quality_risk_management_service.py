# -*- coding: utf-8 -*-
"""
质量风险管理服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.services.quality_risk_management.service import QualityRiskManagementService
from app.models.quality_risk_detection import QualityRiskDetection, QualityTestRecommendation
from app.models.timesheet import Timesheet


class TestQualityRiskManagementService(unittest.TestCase):
    """测试质量风险管理服务核心功能"""

    def setUp(self):
        """设置测试环境"""
        # Mock数据库session
        self.db = MagicMock()
        
        # Mock AI服务
        with patch('app.services.quality_risk_management.service.QualityRiskAnalyzer') as mock_analyzer, \
             patch('app.services.quality_risk_management.service.TestRecommendationEngine') as mock_engine:
            self.mock_analyzer_class = mock_analyzer
            self.mock_engine_class = mock_engine
            self.service = QualityRiskManagementService(self.db)

    # ==================== analyze_work_logs 测试 ====================

    def test_analyze_work_logs_success(self):
        """测试成功分析工作日志"""
        # 准备测试数据
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        current_user_id = 100
        
        # Mock工作日志查询
        mock_timesheets = [
            self._create_mock_timesheet(1, project_id, date(2024, 1, 1), "张三", "开发模块A", "编写代码", "完成功能", 8),
            self._create_mock_timesheet(2, project_id, date(2024, 1, 2), "李四", "开发模块B", "修复bug", "紧急修复", 6),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = mock_timesheets
        
        # Mock AI分析结果
        mock_analysis_result = {
            'risk_signals': ['频繁修复', '紧急处理'],
            'risk_keywords': {'bug': 1, '修复': 2},
            'abnormal_patterns': ['短时间内多次返工'],
            'risk_level': 'HIGH',
            'risk_score': 75.5,
            'risk_category': 'BUG',
            'predicted_issues': ['可能存在未发现的缺陷'],
            'rework_probability': 0.65,
            'estimated_impact_days': 3,
            'ai_analysis': 'AI分析摘要',
            'ai_confidence': 0.85,
            'analysis_model': 'gpt-4'
        }
        self.service.analyzer.analyze_work_logs.return_value = mock_analysis_result
        
        # Mock数据库操作
        mock_detection = MagicMock(spec=QualityRiskDetection)
        mock_detection.id = 1
        mock_detection.risk_level = 'HIGH'
        self.db.add.return_value = None
        self.db.commit.return_value = None
        self.db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id, start_date, end_date, None, None, current_user_id
        )
        
        # 验证
        self.db.query.assert_called()
        self.service.analyzer.analyze_work_logs.assert_called_once()
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_analyze_work_logs_with_module_filter(self):
        """测试带模块名称过滤的分析"""
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        module_name = "模块A"
        current_user_id = 100
        
        # Mock查询链
        mock_query = MagicMock()
        mock_filter_chain = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter_chain
        mock_filter_chain.filter.return_value = mock_filter_chain
        mock_filter_chain.all.return_value = [
            self._create_mock_timesheet(1, project_id, date(2024, 1, 1), "张三", "模块A", "开发", "完成", 8)
        ]
        
        # Mock AI分析
        self.service.analyzer.analyze_work_logs.return_value = {
            'risk_level': 'LOW',
            'risk_score': 30.0,
        }
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id, start_date, end_date, module_name, None, current_user_id
        )
        
        # 验证filter被调用多次（包含module_name过滤）
        self.assertGreaterEqual(mock_filter_chain.filter.call_count, 1)

    def test_analyze_work_logs_with_user_filter(self):
        """测试带用户过滤的分析"""
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        user_ids = [10, 20]
        current_user_id = 100
        
        # Mock查询链
        mock_query = MagicMock()
        mock_filter_chain = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter_chain
        mock_filter_chain.filter.return_value = mock_filter_chain
        mock_filter_chain.all.return_value = [
            self._create_mock_timesheet(1, project_id, date(2024, 1, 1), "张三", "模块A", "开发", "完成", 8)
        ]
        
        # Mock AI分析
        self.service.analyzer.analyze_work_logs.return_value = {
            'risk_level': 'MEDIUM',
            'risk_score': 50.0,
        }
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id, start_date, end_date, None, user_ids, current_user_id
        )
        
        # 验证
        self.assertGreaterEqual(mock_filter_chain.filter.call_count, 1)

    def test_analyze_work_logs_default_dates(self):
        """测试使用默认日期范围"""
        project_id = 1
        current_user_id = 100
        
        # Mock查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            self._create_mock_timesheet(1, project_id, date.today(), "张三", "模块A", "开发", "完成", 8)
        ]
        
        # Mock AI分析
        self.service.analyzer.analyze_work_logs.return_value = {
            'risk_level': 'LOW',
            'risk_score': 25.0,
        }
        
        # 执行测试（不传start_date和end_date）
        result = self.service.analyze_work_logs(
            project_id, None, None, None, None, current_user_id
        )
        
        # 验证默认日期范围被使用
        self.db.query.assert_called()

    def test_analyze_work_logs_no_data_found(self):
        """测试未找到工作日志的情况"""
        project_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        current_user_id = 100
        
        # Mock空结果
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # 执行测试，应该抛出ValueError
        with self.assertRaises(ValueError) as context:
            self.service.analyze_work_logs(
                project_id, start_date, end_date, None, None, current_user_id
            )
        
        self.assertIn("未找到符合条件的工作日志", str(context.exception))

    # ==================== list_detections 测试 ====================

    def test_list_detections_no_filter(self):
        """测试无过滤条件查询检测记录"""
        # Mock查询结果
        mock_detections = [
            self._create_mock_detection(1, 1, 'HIGH', 'DETECTED', date(2024, 1, 1)),
            self._create_mock_detection(2, 1, 'MEDIUM', 'CONFIRMED', date(2024, 1, 2)),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        # 执行测试
        result = self.service.list_detections()
        
        # 验证
        self.assertEqual(len(result), 2)
        self.db.query.assert_called_once()

    def test_list_detections_with_filters(self):
        """测试带过滤条件查询"""
        project_id = 1
        risk_level = 'HIGH'
        status = 'DETECTED'
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # Mock查询链
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            self._create_mock_detection(1, project_id, risk_level, status, start_date)
        ]
        
        # 执行测试
        result = self.service.list_detections(
            project_id=project_id,
            risk_level=risk_level,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=10
        )
        
        # 验证filter被调用多次
        self.assertGreaterEqual(mock_query.filter.call_count, 4)
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)

    def test_list_detections_pagination(self):
        """测试分页功能"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # 执行测试
        result = self.service.list_detections(skip=20, limit=50)
        
        # 验证分页参数
        mock_query.offset.assert_called_once_with(20)
        mock_query.limit.assert_called_once_with(50)

    # ==================== get_detection 测试 ====================

    def test_get_detection_found(self):
        """测试成功获取检测记录"""
        detection_id = 1
        mock_detection = self._create_mock_detection(detection_id, 1, 'HIGH', 'DETECTED', date.today())
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        # 执行测试
        result = self.service.get_detection(detection_id)
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.id, detection_id)

    def test_get_detection_not_found(self):
        """测试获取不存在的检测记录"""
        detection_id = 999
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 执行测试
        result = self.service.get_detection(detection_id)
        
        # 验证
        self.assertIsNone(result)

    # ==================== update_detection 测试 ====================

    def test_update_detection_status(self):
        """测试更新检测状态"""
        detection_id = 1
        new_status = 'CONFIRMED'
        current_user_id = 100
        
        # Mock原记录
        mock_detection = self._create_mock_detection(detection_id, 1, 'HIGH', 'DETECTED', date.today())
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        # 执行测试
        result = self.service.update_detection(
            detection_id, status=new_status, current_user_id=current_user_id
        )
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.status, new_status)
        self.assertEqual(result.confirmed_by, current_user_id)
        self.assertIsNotNone(result.confirmed_at)
        self.db.commit.assert_called_once()

    def test_update_detection_resolution_note(self):
        """测试更新解决备注"""
        detection_id = 1
        resolution_note = "已修复问题"
        
        mock_detection = self._create_mock_detection(detection_id, 1, 'HIGH', 'DETECTED', date.today())
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        # 执行测试
        result = self.service.update_detection(
            detection_id, resolution_note=resolution_note
        )
        
        # 验证
        self.assertEqual(result.resolution_note, resolution_note)
        self.db.commit.assert_called_once()

    def test_update_detection_not_found(self):
        """测试更新不存在的检测记录"""
        detection_id = 999
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 执行测试
        result = self.service.update_detection(detection_id, status='CONFIRMED')
        
        # 验证
        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    # ==================== generate_test_recommendation 测试 ====================

    def test_generate_test_recommendation_success(self):
        """测试成功生成测试推荐"""
        detection_id = 1
        current_user_id = 100
        
        # Mock检测记录
        mock_detection = self._create_mock_detection(1, 10, 'HIGH', 'DETECTED', date.today())
        mock_detection.risk_score = 75.5
        mock_detection.risk_category = 'BUG'
        mock_detection.risk_signals = ['频繁修复']
        mock_detection.risk_keywords = {'bug': 3}
        mock_detection.abnormal_patterns = ['返工频繁']
        mock_detection.predicted_issues = ['潜在缺陷']
        mock_detection.rework_probability = 0.65
        mock_detection.estimated_impact_days = 3
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        # Mock推荐引擎结果
        mock_recommendation_data = {
            'focus_areas': ['模块A', '模块B'],
            'priority_modules': ['模块A'],
            'risk_modules': ['模块B'],
            'test_types': ['单元测试', '集成测试'],
            'test_scenarios': ['场景1', '场景2'],
            'test_coverage_target': 80.0,
            'recommended_testers': ['测试员A'],
            'recommended_days': 3,
            'priority_level': 'HIGH',
            'ai_reasoning': 'AI推荐理由',
            'risk_summary': '风险摘要'
        }
        self.service.recommendation_engine.generate_recommendations.return_value = mock_recommendation_data
        
        # 执行测试
        result = self.service.generate_test_recommendation(detection_id, current_user_id)
        
        # 验证
        self.service.recommendation_engine.generate_recommendations.assert_called_once()
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_generate_test_recommendation_detection_not_found(self):
        """测试检测记录不存在时生成推荐"""
        detection_id = 999
        current_user_id = 100
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 执行测试
        result = self.service.generate_test_recommendation(detection_id, current_user_id)
        
        # 验证
        self.assertIsNone(result)
        self.db.add.assert_not_called()

    # ==================== list_recommendations 测试 ====================

    def test_list_recommendations_no_filter(self):
        """测试无过滤条件查询推荐"""
        mock_recommendations = [
            self._create_mock_recommendation(1, 10, 1, 'HIGH', 'PENDING'),
            self._create_mock_recommendation(2, 10, 2, 'MEDIUM', 'ACCEPTED'),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_recommendations
        
        # 执行测试
        result = self.service.list_recommendations()
        
        # 验证
        self.assertEqual(len(result), 2)

    def test_list_recommendations_with_filters(self):
        """测试带过滤条件查询推荐"""
        project_id = 10
        priority_level = 'HIGH'
        status = 'PENDING'
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            self._create_mock_recommendation(1, project_id, 1, priority_level, status)
        ]
        
        # 执行测试
        result = self.service.list_recommendations(
            project_id=project_id,
            priority_level=priority_level,
            status=status
        )
        
        # 验证
        self.assertGreaterEqual(mock_query.filter.call_count, 3)

    # ==================== update_recommendation 测试 ====================

    def test_update_recommendation_success(self):
        """测试成功更新推荐"""
        recommendation_id = 1
        update_data = {
            'status': 'ACCEPTED',
            'recommended_days': 5
        }
        
        mock_recommendation = self._create_mock_recommendation(recommendation_id, 10, 1, 'HIGH', 'PENDING')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_recommendation
        
        # 执行测试
        result = self.service.update_recommendation(recommendation_id, update_data)
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'ACCEPTED')
        self.assertEqual(result.recommended_days, 5)
        self.db.commit.assert_called_once()

    def test_update_recommendation_not_found(self):
        """测试更新不存在的推荐"""
        recommendation_id = 999
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 执行测试
        result = self.service.update_recommendation(recommendation_id, {'status': 'ACCEPTED'})
        
        # 验证
        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    # ==================== generate_quality_report 测试 ====================

    def test_generate_quality_report_success(self):
        """测试成功生成质量报告"""
        project_id = 10
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # Mock检测记录
        mock_detections = [
            self._create_mock_detection(1, project_id, 'HIGH', 'DETECTED', date(2024, 1, 1), 'ModuleA', 80.0),
            self._create_mock_detection(2, project_id, 'MEDIUM', 'CONFIRMED', date(2024, 1, 15), 'ModuleB', 60.0),
            self._create_mock_detection(3, project_id, 'LOW', 'RESOLVED', date(2024, 1, 20), 'ModuleC', 30.0),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        # 执行测试
        report = self.service.generate_quality_report(
            project_id, start_date, end_date, include_recommendations=False
        )
        
        # 验证
        self.assertEqual(report['project_id'], project_id)
        self.assertEqual(report['total_detections'], 3)
        self.assertIn('risk_distribution', report)
        self.assertIn('top_risk_modules', report)
        self.assertIn('trend_analysis', report)
        self.assertIn('summary', report)

    def test_generate_quality_report_with_recommendations(self):
        """测试生成包含推荐的质量报告"""
        project_id = 10
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # Mock检测记录
        mock_detections = [
            self._create_mock_detection(1, project_id, 'HIGH', 'DETECTED', date(2024, 1, 1), 'ModuleA', 80.0),
        ]
        
        # Mock推荐记录
        mock_recommendations = [
            self._create_mock_recommendation(1, project_id, 1, 'HIGH', 'PENDING'),
        ]
        
        # 设置query的返回值 - 需要根据调用顺序返回不同结果
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 第一次调用返回detections，第二次调用返回recommendations
        mock_query.all.side_effect = [mock_detections, mock_recommendations]
        
        # 执行测试
        report = self.service.generate_quality_report(
            project_id, start_date, end_date, include_recommendations=True
        )
        
        # 验证
        self.assertIn('recommendations', report)
        self.assertIsNotNone(report['recommendations'])

    def test_generate_quality_report_no_data(self):
        """测试没有检测数据时生成报告"""
        project_id = 10
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # 执行测试，应该抛出ValueError
        with self.assertRaises(ValueError) as context:
            self.service.generate_quality_report(project_id, start_date, end_date)
        
        self.assertIn("没有质量风险检测数据", str(context.exception))

    # ==================== _calculate_overall_risk 测试 ====================

    def test_calculate_overall_risk_critical(self):
        """测试计算CRITICAL风险等级"""
        risk_distribution = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3}
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'CRITICAL')

    def test_calculate_overall_risk_high(self):
        """测试计算HIGH风险等级"""
        risk_distribution = {'HIGH': 3, 'MEDIUM': 5}
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'HIGH')

    def test_calculate_overall_risk_medium(self):
        """测试计算MEDIUM风险等级"""
        risk_distribution = {'MEDIUM': 5, 'LOW': 2}
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'MEDIUM')

    def test_calculate_overall_risk_low(self):
        """测试计算LOW风险等级"""
        risk_distribution = {'LOW': 10}
        result = self.service._calculate_overall_risk(risk_distribution)
        self.assertEqual(result, 'LOW')

    # ==================== _extract_top_risk_modules 测试 ====================

    def test_extract_top_risk_modules(self):
        """测试提取高风险模块"""
        detections = [
            self._create_mock_detection(1, 1, 'HIGH', 'DETECTED', date.today(), 'ModuleA', 90.0),
            self._create_mock_detection(2, 1, 'MEDIUM', 'DETECTED', date.today(), 'ModuleB', 70.0),
            self._create_mock_detection(3, 1, 'LOW', 'DETECTED', date.today(), 'ModuleC', 40.0),
            self._create_mock_detection(4, 1, 'CRITICAL', 'DETECTED', date.today(), 'ModuleD', 95.0),
            self._create_mock_detection(5, 1, 'MEDIUM', 'DETECTED', date.today(), 'ModuleE', 60.0),
            self._create_mock_detection(6, 1, 'LOW', 'DETECTED', date.today(), 'ModuleF', 30.0),
        ]
        
        result = self.service._extract_top_risk_modules(detections)
        
        # 验证返回最多5个模块，且按分数降序排列
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]['module'], 'ModuleD')
        self.assertEqual(result[0]['risk_score'], 95.0)

    def test_extract_top_risk_modules_no_module_name(self):
        """测试提取模块时处理空模块名"""
        detections = [
            self._create_mock_detection(1, 1, 'HIGH', 'DETECTED', date.today(), None, 80.0),
        ]
        
        result = self.service._extract_top_risk_modules(detections)
        
        self.assertEqual(result[0]['module'], '未知模块')

    # ==================== _analyze_trends 测试 ====================

    def test_analyze_trends(self):
        """测试趋势分析"""
        detections = [
            self._create_mock_detection(1, 1, 'HIGH', 'DETECTED', date(2024, 1, 1), 'ModuleA', 80.0),
            self._create_mock_detection(2, 1, 'MEDIUM', 'DETECTED', date(2024, 1, 1), 'ModuleB', 60.0),
            self._create_mock_detection(3, 1, 'LOW', 'DETECTED', date(2024, 1, 2), 'ModuleC', 40.0),
        ]
        
        result = self.service._analyze_trends(detections)
        
        # 验证
        self.assertIn('2024-01-01', result)
        self.assertIn('2024-01-02', result)
        self.assertEqual(result['2024-01-01']['count'], 2)
        self.assertEqual(result['2024-01-01']['avg_score'], 70.0)
        self.assertEqual(result['2024-01-02']['count'], 1)
        self.assertEqual(result['2024-01-02']['avg_score'], 40.0)

    # ==================== _get_recommendations_data 测试 ====================

    def test_get_recommendations_data(self):
        """测试获取推荐数据"""
        project_id = 10
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_recommendations = [
            self._create_mock_recommendation(1, project_id, 1, 'HIGH', 'PENDING'),
            self._create_mock_recommendation(2, project_id, 2, 'MEDIUM', 'ACCEPTED'),
        ]
        mock_recommendations[0].recommended_days = 3
        mock_recommendations[0].ai_reasoning = "AI理由1"
        mock_recommendations[1].recommended_days = 2
        mock_recommendations[1].ai_reasoning = "AI理由2"
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_recommendations
        
        # 执行测试
        result = self.service._get_recommendations_data(project_id, start_date, end_date)
        
        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['priority'], 'HIGH')

    # ==================== _generate_report_summary 测试 ====================

    def test_generate_report_summary_with_critical(self):
        """测试生成包含严重风险的报告摘要"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        detections = [MagicMock(), MagicMock(), MagicMock()]
        overall_risk = 'CRITICAL'
        risk_distribution = {'CRITICAL': 2, 'HIGH': 1}
        
        summary = self.service._generate_report_summary(
            start_date, end_date, detections, overall_risk, risk_distribution
        )
        
        # 验证摘要包含关键信息
        self.assertIn('2024-01-01至2024-01-31', summary)
        self.assertIn('3个质量风险', summary)
        self.assertIn('CRITICAL', summary)
        self.assertIn('2个严重风险', summary)

    def test_generate_report_summary_no_critical(self):
        """测试生成无严重风险的报告摘要"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        detections = [MagicMock()]
        overall_risk = 'LOW'
        risk_distribution = {'LOW': 1}
        
        summary = self.service._generate_report_summary(
            start_date, end_date, detections, overall_risk, risk_distribution
        )
        
        # 验证摘要不包含严重风险提示
        self.assertNotIn('严重风险', summary)

    # ==================== get_statistics_summary 测试 ====================

    def test_get_statistics_summary_no_filter(self):
        """测试获取统计摘要（无项目过滤）"""
        mock_detections = [
            self._create_mock_detection(1, 1, 'HIGH', 'DETECTED', date.today(), 'ModuleA', 80.0),
            self._create_mock_detection(2, 2, 'MEDIUM', 'CONFIRMED', date.today(), 'ModuleB', 60.0),
            self._create_mock_detection(3, 1, 'LOW', 'RESOLVED', date.today(), 'ModuleC', 40.0),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        # 执行测试
        result = self.service.get_statistics_summary(days=30)
        
        # 验证
        self.assertEqual(result['total_detections'], 3)
        self.assertEqual(result['average_risk_score'], 60.0)
        self.assertEqual(result['by_risk_level']['HIGH'], 1)
        self.assertEqual(result['by_risk_level']['MEDIUM'], 1)
        self.assertEqual(result['by_risk_level']['LOW'], 1)
        self.assertEqual(result['by_status']['DETECTED'], 1)
        self.assertEqual(result['by_status']['CONFIRMED'], 1)
        self.assertEqual(result['by_status']['RESOLVED'], 1)

    def test_get_statistics_summary_with_project_filter(self):
        """测试获取统计摘要（带项目过滤）"""
        project_id = 1
        
        mock_detections = [
            self._create_mock_detection(1, project_id, 'HIGH', 'DETECTED', date.today(), 'ModuleA', 80.0),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        # 执行测试
        result = self.service.get_statistics_summary(project_id=project_id, days=30)
        
        # 验证
        self.assertEqual(result['total_detections'], 1)
        self.assertGreaterEqual(mock_query.filter.call_count, 2)

    def test_get_statistics_summary_empty(self):
        """测试空统计结果"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # 执行测试
        result = self.service.get_statistics_summary()
        
        # 验证
        self.assertEqual(result['total_detections'], 0)
        self.assertEqual(result['average_risk_score'], 0)

    # ==================== 辅助方法 ====================

    def _create_mock_timesheet(self, id, project_id, work_date, user_name, task_name, work_content, work_result, hours):
        """创建mock工作日志"""
        mock = MagicMock(spec=Timesheet)
        mock.id = id
        mock.project_id = project_id
        mock.work_date = work_date
        mock.user_name = user_name
        mock.task_name = task_name
        mock.work_content = work_content
        mock.work_result = work_result
        mock.hours = Decimal(str(hours))
        return mock

    def _create_mock_detection(self, id, project_id, risk_level, status, detection_date, module_name=None, risk_score=50.0):
        """创建mock检测记录"""
        mock = MagicMock(spec=QualityRiskDetection)
        mock.id = id
        mock.project_id = project_id
        mock.risk_level = risk_level
        mock.status = status
        mock.detection_date = detection_date
        mock.module_name = module_name
        mock.risk_score = Decimal(str(risk_score))
        mock.risk_category = None
        mock.risk_signals = []
        mock.risk_keywords = {}
        mock.abnormal_patterns = []
        mock.predicted_issues = []
        mock.rework_probability = None
        mock.estimated_impact_days = None
        mock.confirmed_by = None
        mock.confirmed_at = None
        mock.resolution_note = None
        return mock

    def _create_mock_recommendation(self, id, project_id, detection_id, priority_level, status):
        """创建mock测试推荐"""
        mock = MagicMock(spec=QualityTestRecommendation)
        mock.id = id
        mock.project_id = project_id
        mock.detection_id = detection_id
        mock.priority_level = priority_level
        mock.status = status
        mock.recommendation_date = date.today()
        mock.recommended_days = None
        mock.ai_reasoning = None
        return mock


if __name__ == "__main__":
    unittest.main()
