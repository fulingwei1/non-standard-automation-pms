# -*- coding: utf-8 -*-
"""
质量风险管理服务单元测试

目标：
1. 只mock外部依赖（db操作、AI服务）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.services.quality_risk_management.service import QualityRiskManagementService
from app.models.quality_risk_detection import (
    QualityRiskDetection,
    QualityTestRecommendation,
)
from app.models.timesheet import Timesheet


class TestQualityRiskManagementService(unittest.TestCase):
    """测试质量风险管理服务"""

    def setUp(self):
        """测试前准备"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        
        # Mock AI分析器
        with patch('app.services.quality_risk_management.service.QualityRiskAnalyzer') as mock_analyzer_cls, \
             patch('app.services.quality_risk_management.service.TestRecommendationEngine') as mock_engine_cls:
            self.mock_analyzer = MagicMock()
            self.mock_engine = MagicMock()
            mock_analyzer_cls.return_value = self.mock_analyzer
            mock_engine_cls.return_value = self.mock_engine
            
            self.service = QualityRiskManagementService(self.mock_db)

    # ==================== 质量风险检测业务逻辑测试 ====================

    def test_analyze_work_logs_success(self):
        """测试成功分析工作日志"""
        # 准备mock数据
        mock_logs = [
            self._create_mock_timesheet(
                work_date=date(2024, 1, 10),
                user_name="张三",
                task_name="用户登录模块",
                work_content="实现登录功能",
                work_result="完成",
                hours=Decimal("8.0")
            ),
            self._create_mock_timesheet(
                work_date=date(2024, 1, 11),
                user_name="李四",
                task_name="用户登录模块",
                work_content="修复bug",
                work_result="有问题",
                hours=Decimal("4.0")
            ),
        ]
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_logs
        
        # Mock AI分析结果
        ai_result = {
            'risk_signals': ['频繁返工', '代码变更过多'],
            'risk_keywords': {'bug': 3, '问题': 2},
            'abnormal_patterns': ['工时异常'],
            'risk_level': 'HIGH',
            'risk_score': 75.5,
            'risk_category': '代码质量',
            'predicted_issues': ['可能存在逻辑错误'],
            'rework_probability': 0.6,
            'estimated_impact_days': 2,
            'ai_analysis': 'AI分析结果',
            'ai_confidence': 0.85,
            'analysis_model': 'gpt-4'
        }
        self.mock_analyzer.analyze_work_logs.return_value = ai_result
        
        # 执行测试
        result = self.service.analyze_work_logs(
            project_id=1,
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 15),
            module_name="用户登录",
            user_ids=[1, 2],
            current_user_id=1
        )
        
        # 验证
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        
        # 验证AI分析器被调用
        self.mock_analyzer.analyze_work_logs.assert_called_once()
        call_args = self.mock_analyzer.analyze_work_logs.call_args[0][0]
        self.assertEqual(len(call_args), 2)

    def test_analyze_work_logs_with_default_dates(self):
        """测试使用默认日期范围"""
        mock_logs = [self._create_mock_timesheet()]
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_logs
        
        ai_result = self._create_mock_ai_result()
        self.mock_analyzer.analyze_work_logs.return_value = ai_result
        
        # 不传入日期参数
        result = self.service.analyze_work_logs(
            project_id=1,
            start_date=None,
            end_date=None,
            module_name=None,
            user_ids=None,
            current_user_id=1
        )
        
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()

    def test_analyze_work_logs_no_data(self):
        """测试没有工作日志时抛出异常"""
        # Mock空查询结果
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # 验证抛出ValueError
        with self.assertRaises(ValueError) as cm:
            self.service.analyze_work_logs(
                project_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                module_name=None,
                user_ids=None,
                current_user_id=1
            )
        
        self.assertEqual(str(cm.exception), "未找到符合条件的工作日志")

    def test_list_detections_with_filters(self):
        """测试带过滤条件查询检测列表"""
        mock_detections = [
            self._create_mock_detection(id=1, risk_level='HIGH'),
            self._create_mock_detection(id=2, risk_level='MEDIUM'),
        ]
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        result = self.service.list_detections(
            project_id=1,
            risk_level='HIGH',
            status='DETECTED',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            skip=0,
            limit=10
        )
        
        self.assertEqual(len(result), 2)
        # 验证filter被调用多次
        self.assertGreaterEqual(mock_query.filter.call_count, 4)

    def test_list_detections_without_filters(self):
        """测试不带过滤条件查询"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.list_detections()
        
        self.assertEqual(result, [])
        self.mock_db.query.assert_called_once()

    def test_get_detection_success(self):
        """测试获取检测详情成功"""
        mock_detection = self._create_mock_detection(id=1)
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        result = self.service.get_detection(1)
        
        self.assertEqual(result, mock_detection)

    def test_get_detection_not_found(self):
        """测试检测记录不存在"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.get_detection(999)
        
        self.assertIsNone(result)

    def test_update_detection_success(self):
        """测试更新检测状态成功"""
        mock_detection = self._create_mock_detection(id=1, status='DETECTED')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        result = self.service.update_detection(
            detection_id=1,
            status='CONFIRMED',
            resolution_note='已确认',
            current_user_id=2
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'CONFIRMED')
        self.assertEqual(result.resolution_note, '已确认')
        self.assertEqual(result.confirmed_by, 2)
        self.assertIsNotNone(result.confirmed_at)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_update_detection_not_found(self):
        """测试更新不存在的检测记录"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.update_detection(
            detection_id=999,
            status='CONFIRMED'
        )
        
        self.assertIsNone(result)
        self.mock_db.commit.assert_not_called()

    def test_update_detection_only_note(self):
        """测试只更新备注"""
        mock_detection = self._create_mock_detection(id=1, status='DETECTED')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        result = self.service.update_detection(
            detection_id=1,
            resolution_note='只是备注'
        )
        
        self.assertEqual(result.resolution_note, '只是备注')
        self.assertEqual(result.status, 'DETECTED')  # 状态未变

    # ==================== 测试推荐业务逻辑测试 ====================

    def test_generate_test_recommendation_success(self):
        """测试生成测试推荐成功"""
        mock_detection = self._create_mock_detection(id=1)
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detection
        
        # Mock推荐引擎结果
        recommendation_data = {
            'focus_areas': ['登录模块', '认证模块'],
            'priority_modules': ['用户管理'],
            'risk_modules': ['登录'],
            'test_types': ['功能测试', '集成测试'],
            'test_scenarios': ['场景1', '场景2'],
            'test_coverage_target': 0.8,
            'recommended_testers': ['测试员1'],
            'recommended_days': 3,
            'priority_level': 'HIGH',
            'ai_reasoning': '推荐理由',
            'risk_summary': '风险摘要'
        }
        self.mock_engine.generate_recommendations.return_value = recommendation_data
        
        result = self.service.generate_test_recommendation(
            detection_id=1,
            current_user_id=1
        )
        
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_engine.generate_recommendations.assert_called_once()

    def test_generate_test_recommendation_detection_not_found(self):
        """测试检测记录不存在时返回None"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.generate_test_recommendation(
            detection_id=999,
            current_user_id=1
        )
        
        self.assertIsNone(result)
        self.mock_db.add.assert_not_called()

    def test_list_recommendations_with_filters(self):
        """测试带过滤条件查询推荐列表"""
        mock_recommendations = [
            self._create_mock_recommendation(id=1),
            self._create_mock_recommendation(id=2),
        ]
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_recommendations
        
        result = self.service.list_recommendations(
            project_id=1,
            priority_level='HIGH',
            status='PENDING',
            skip=0,
            limit=10
        )
        
        self.assertEqual(len(result), 2)

    def test_update_recommendation_success(self):
        """测试更新推荐成功"""
        mock_recommendation = self._create_mock_recommendation(id=1, status='PENDING')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_recommendation
        
        update_data = {
            'status': 'ACCEPTED',
            'recommended_days': 5
        }
        
        result = self.service.update_recommendation(
            recommendation_id=1,
            update_data=update_data
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'ACCEPTED')
        self.assertEqual(result.recommended_days, 5)
        self.mock_db.commit.assert_called_once()

    def test_update_recommendation_not_found(self):
        """测试更新不存在的推荐"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.update_recommendation(
            recommendation_id=999,
            update_data={'status': 'ACCEPTED'}
        )
        
        self.assertIsNone(result)

    def test_update_recommendation_ignore_invalid_fields(self):
        """测试更新推荐时忽略无效字段"""
        mock_recommendation = self._create_mock_recommendation(id=1)
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_recommendation
        
        update_data = {
            'status': 'ACCEPTED',
            'invalid_field': 'should_be_ignored'
        }
        
        result = self.service.update_recommendation(
            recommendation_id=1,
            update_data=update_data
        )
        
        self.assertEqual(result.status, 'ACCEPTED')
        self.assertFalse(hasattr(result, 'invalid_field'))

    # ==================== 质量报告业务逻辑测试 ====================

    def test_generate_quality_report_success(self):
        """测试生成质量报告成功"""
        mock_detections = [
            self._create_mock_detection(id=1, risk_level='HIGH', risk_score=80),
            self._create_mock_detection(id=2, risk_level='MEDIUM', risk_score=50),
            self._create_mock_detection(id=3, risk_level='HIGH', risk_score=75),
            self._create_mock_detection(id=4, risk_level='HIGH', risk_score=70),
        ]
        
        # Mock检测记录查询
        mock_detection_query = MagicMock()
        
        # Mock推荐记录查询
        mock_recommendation_query = MagicMock()
        
        def query_side_effect(model):
            if model == QualityRiskDetection:
                return mock_detection_query
            elif model == QualityTestRecommendation:
                return mock_recommendation_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        mock_detection_query.filter.return_value = mock_detection_query
        mock_detection_query.all.return_value = mock_detections
        
        mock_recommendation_query.filter.return_value = mock_recommendation_query
        mock_recommendation_query.all.return_value = []
        
        result = self.service.generate_quality_report(
            project_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            include_recommendations=True
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['total_detections'], 4)
        self.assertEqual(result['overall_risk_level'], 'HIGH')
        self.assertEqual(result['risk_distribution']['HIGH'], 3)
        self.assertEqual(result['risk_distribution']['MEDIUM'], 1)
        self.assertIn('top_risk_modules', result)
        self.assertIn('trend_analysis', result)
        self.assertIn('summary', result)

    def test_generate_quality_report_no_data(self):
        """测试没有检测数据时抛出异常"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        with self.assertRaises(ValueError) as cm:
            self.service.generate_quality_report(
                project_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        
        self.assertIn("没有质量风险检测数据", str(cm.exception))

    def test_generate_quality_report_without_recommendations(self):
        """测试不包含推荐的报告"""
        mock_detections = [self._create_mock_detection(id=1)]
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        result = self.service.generate_quality_report(
            project_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            include_recommendations=False
        )
        
        self.assertIsNone(result['recommendations'])

    def test_calculate_overall_risk_critical(self):
        """测试计算总体风险等级 - CRITICAL"""
        risk_distribution = {
            'CRITICAL': 1,
            'HIGH': 2,
            'MEDIUM': 3
        }
        
        result = self.service._calculate_overall_risk(risk_distribution)
        
        self.assertEqual(result, 'CRITICAL')

    def test_calculate_overall_risk_high(self):
        """测试计算总体风险等级 - HIGH"""
        risk_distribution = {
            'HIGH': 3,
            'MEDIUM': 2
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
            'MEDIUM': 2,
            'LOW': 5
        }
        
        result = self.service._calculate_overall_risk(risk_distribution)
        
        self.assertEqual(result, 'LOW')

    def test_extract_top_risk_modules(self):
        """测试提取高风险模块"""
        detections = [
            self._create_mock_detection(id=1, module_name='模块A', risk_score=90, risk_level='CRITICAL'),
            self._create_mock_detection(id=2, module_name='模块B', risk_score=75, risk_level='HIGH'),
            self._create_mock_detection(id=3, module_name='模块C', risk_score=60, risk_level='MEDIUM'),
            self._create_mock_detection(id=4, module_name='模块D', risk_score=80, risk_level='HIGH'),
            self._create_mock_detection(id=5, module_name='模块E', risk_score=70, risk_level='MEDIUM'),
            self._create_mock_detection(id=6, module_name='模块F', risk_score=50, risk_level='LOW'),
        ]
        
        result = self.service._extract_top_risk_modules(detections)
        
        self.assertEqual(len(result), 5)  # 最多返回5个
        self.assertEqual(result[0]['module'], '模块A')
        self.assertEqual(result[0]['risk_score'], 90.0)
        self.assertEqual(result[1]['module'], '模块D')

    def test_extract_top_risk_modules_none_module_name(self):
        """测试模块名为None的情况"""
        detections = [
            self._create_mock_detection(id=1, module_name=None, risk_score=80),
        ]
        
        result = self.service._extract_top_risk_modules(detections)
        
        self.assertEqual(result[0]['module'], '未知模块')

    def test_analyze_trends(self):
        """测试趋势分析"""
        detections = [
            self._create_mock_detection(id=1, detection_date=date(2024, 1, 10), risk_score=80),
            self._create_mock_detection(id=2, detection_date=date(2024, 1, 10), risk_score=60),
            self._create_mock_detection(id=3, detection_date=date(2024, 1, 11), risk_score=70),
        ]
        
        result = self.service._analyze_trends(detections)
        
        self.assertIn('2024-01-10', result)
        self.assertIn('2024-01-11', result)
        self.assertEqual(result['2024-01-10']['count'], 2)
        self.assertEqual(result['2024-01-10']['avg_score'], 70.0)  # (80+60)/2
        self.assertEqual(result['2024-01-11']['count'], 1)
        self.assertEqual(result['2024-01-11']['avg_score'], 70.0)

    def test_get_recommendations_data(self):
        """测试获取推荐数据"""
        mock_recommendations = [
            self._create_mock_recommendation(
                id=1, 
                priority_level='HIGH',
                status='PENDING',
                recommended_days=3,
                ai_reasoning='理由1'
            ),
            self._create_mock_recommendation(
                id=2,
                priority_level='MEDIUM',
                status='ACCEPTED',
                recommended_days=2,
                ai_reasoning='理由2'
            ),
        ]
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_recommendations
        
        result = self.service._get_recommendations_data(
            project_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['priority'], 'HIGH')

    def test_generate_report_summary(self):
        """测试生成报告摘要"""
        detections = [
            self._create_mock_detection(id=1, risk_level='CRITICAL'),
            self._create_mock_detection(id=2, risk_level='HIGH'),
        ]
        risk_distribution = {'CRITICAL': 1, 'HIGH': 1}
        
        result = self.service._generate_report_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            detections=detections,
            overall_risk='CRITICAL',
            risk_distribution=risk_distribution
        )
        
        self.assertIn('2024-01-01至2024-01-31', result)
        self.assertIn('共检测到2个质量风险', result)
        self.assertIn('总体风险等级为CRITICAL', result)
        self.assertIn('1个严重风险', result)

    # ==================== 统计分析业务逻辑测试 ====================

    def test_get_statistics_summary_with_project(self):
        """测试获取指定项目的统计摘要"""
        mock_detections = [
            self._create_mock_detection(id=1, risk_level='HIGH', risk_score=80, status='DETECTED'),
            self._create_mock_detection(id=2, risk_level='MEDIUM', risk_score=50, status='CONFIRMED'),
            self._create_mock_detection(id=3, risk_level='HIGH', risk_score=70, status='DETECTED'),
        ]
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_detections
        
        result = self.service.get_statistics_summary(
            project_id=1,
            days=30
        )
        
        self.assertEqual(result['total_detections'], 3)
        self.assertEqual(result['average_risk_score'], 66.67)  # (80+50+70)/3
        self.assertEqual(result['by_risk_level']['HIGH'], 2)
        self.assertEqual(result['by_risk_level']['MEDIUM'], 1)
        self.assertEqual(result['by_status']['DETECTED'], 2)
        self.assertEqual(result['by_status']['CONFIRMED'], 1)
        self.assertEqual(result['period_days'], 30)

    def test_get_statistics_summary_without_project(self):
        """测试获取全部项目的统计摘要"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_statistics_summary(days=7)
        
        self.assertEqual(result['total_detections'], 0)
        self.assertEqual(result['average_risk_score'], 0)
        self.assertEqual(result['period_days'], 7)

    def test_get_statistics_summary_empty(self):
        """测试空统计数据"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_statistics_summary()
        
        self.assertEqual(result['total_detections'], 0)
        self.assertEqual(result['average_risk_score'], 0)
        self.assertEqual(result['by_risk_level'], {})
        self.assertEqual(result['by_status'], {})

    # ==================== 辅助方法 ====================

    def _create_mock_timesheet(
        self,
        work_date=None,
        user_name="测试用户",
        task_name="测试任务",
        work_content="测试内容",
        work_result="完成",
        hours=None
    ):
        """创建Mock工时记录"""
        mock = MagicMock(spec=Timesheet)
        mock.work_date = work_date or date.today()
        mock.user_name = user_name
        mock.task_name = task_name
        mock.work_content = work_content
        mock.work_result = work_result
        mock.hours = hours or Decimal("8.0")
        return mock

    def _create_mock_detection(
        self,
        id=1,
        project_id=1,
        module_name="测试模块",
        detection_date=None,
        risk_level='MEDIUM',
        risk_score=50.0,
        risk_category='代码质量',
        status='DETECTED',
        rework_probability=None,
        estimated_impact_days=None
    ):
        """创建Mock检测记录"""
        mock = MagicMock(spec=QualityRiskDetection)
        mock.id = id
        mock.project_id = project_id
        mock.module_name = module_name
        mock.detection_date = detection_date or date.today()
        mock.risk_level = risk_level
        mock.risk_score = Decimal(str(risk_score))
        mock.risk_category = risk_category
        mock.risk_signals = []
        mock.risk_keywords = {}
        mock.abnormal_patterns = []
        mock.predicted_issues = []
        mock.rework_probability = Decimal(str(rework_probability)) if rework_probability else Decimal("0.5")
        mock.estimated_impact_days = estimated_impact_days or 1
        mock.status = status
        mock.resolution_note = None
        mock.confirmed_by = None
        mock.confirmed_at = None
        return mock

    def _create_mock_recommendation(
        self,
        id=1,
        project_id=1,
        detection_id=1,
        priority_level='MEDIUM',
        status='PENDING',
        recommended_days=None,
        ai_reasoning=None
    ):
        """创建Mock推荐记录"""
        mock = MagicMock(spec=QualityTestRecommendation)
        mock.id = id
        mock.project_id = project_id
        mock.detection_id = detection_id
        mock.recommendation_date = date.today()
        mock.focus_areas = []
        mock.priority_level = priority_level
        mock.status = status
        mock.recommended_days = recommended_days
        mock.ai_reasoning = ai_reasoning
        return mock

    def _create_mock_ai_result(self):
        """创建Mock AI分析结果"""
        return {
            'risk_signals': [],
            'risk_keywords': {},
            'abnormal_patterns': [],
            'risk_level': 'MEDIUM',
            'risk_score': 50.0,
            'risk_category': '代码质量',
            'predicted_issues': [],
            'rework_probability': 0.5,
            'estimated_impact_days': 1,
            'ai_analysis': 'AI分析',
            'ai_confidence': 0.8,
            'analysis_model': 'gpt-4'
        }


if __name__ == "__main__":
    unittest.main()
