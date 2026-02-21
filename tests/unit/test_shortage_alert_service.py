# -*- coding: utf-8 -*-
"""
缺料预警服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过

目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.shortage_alerts.service import ShortageAlertService
from app.models.shortage.smart_alert import (
    ShortageAlert,
    ShortageHandlingPlan,
    MaterialDemandForecast
)
from app.models.project import Project
from app.core.exceptions import BusinessException


class TestShortageAlertService(unittest.TestCase):
    """测试缺料预警服务核心功能"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ShortageAlertService(self.db)

    def _create_mock_alert(self, alert_id=1, **kwargs):
        """创建mock预警对象"""
        defaults = {
            'id': alert_id,
            'alert_no': f'SA{alert_id:06d}',
            'project_id': 1,
            'material_id': 100,
            'material_code': 'M001',
            'material_name': '电机',
            'required_qty': Decimal('100'),
            'available_qty': Decimal('50'),
            'shortage_qty': Decimal('50'),
            'in_transit_qty': Decimal('0'),
            'alert_level': 'WARNING',
            'alert_date': date.today(),
            'status': 'PENDING',
            'detected_at': datetime.now(),
            'estimated_cost_impact': Decimal('5000'),
            'estimated_delay_days': 3,
            'created_at': datetime.now(),
        }
        defaults.update(kwargs)
        
        alert = MagicMock(spec=ShortageAlert)
        for key, value in defaults.items():
            setattr(alert, key, value)
        
        return alert

    def _create_mock_project(self, project_id=1, **kwargs):
        """创建mock项目对象"""
        defaults = {
            'id': project_id,
            'project_name': f'测试项目{project_id}',
            'project_code': f'P{project_id:04d}',
        }
        defaults.update(kwargs)
        
        project = MagicMock(spec=Project)
        for key, value in defaults.items():
            setattr(project, key, value)
        
        return project

    # ========== get_alerts_with_filters 测试 ==========

    def test_get_alerts_with_filters_no_filter(self):
        """测试无过滤条件查询"""
        # Mock查询结果
        mock_alerts = [
            self._create_mock_alert(1),
            self._create_mock_alert(2),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        self.db.query.return_value = mock_query
        
        # 执行查询
        alerts, total = self.service.get_alerts_with_filters(page=1, page_size=20)
        
        # 验证结果
        self.assertEqual(len(alerts), 2)
        self.assertEqual(total, 2)
        self.db.query.assert_called_once()

    def test_get_alerts_with_filters_with_project_id(self):
        """测试按项目ID过滤"""
        mock_alerts = [self._create_mock_alert(1, project_id=100)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        self.db.query.return_value = mock_query
        
        alerts, total = self.service.get_alerts_with_filters(
            project_id=100,
            page=1,
            page_size=20
        )
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].project_id, 100)

    def test_get_alerts_with_filters_with_all_filters(self):
        """测试所有过滤条件"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self._create_mock_alert()]
        
        self.db.query.return_value = mock_query
        
        alerts, total = self.service.get_alerts_with_filters(
            project_id=1,
            material_id=100,
            alert_level='WARNING',
            status='PENDING',
            start_date='2026-02-01',
            end_date='2026-02-28',
            page=1,
            page_size=10
        )
        
        self.assertEqual(total, 1)
        # 验证filter被调用（所有条件都会触发filter）
        mock_query.filter.assert_called()

    def test_get_alerts_with_filters_pagination(self):
        """测试分页功能"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        self.service.get_alerts_with_filters(page=3, page_size=20)
        
        # 验证分页参数
        mock_query.offset.assert_called_once_with(40)  # (3-1) * 20
        mock_query.limit.assert_called_once_with(20)

    # ========== get_alert_by_id 测试 ==========

    def test_get_alert_by_id_success(self):
        """测试成功获取预警详情"""
        mock_alert = self._create_mock_alert(999)
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert
        
        self.db.query.return_value = mock_query
        
        alert = self.service.get_alert_by_id(999)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.id, 999)

    def test_get_alert_by_id_not_found(self):
        """测试预警不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        self.db.query.return_value = mock_query
        
        with self.assertRaises(BusinessException) as context:
            self.service.get_alert_by_id(999)
        
        self.assertIn("预警不存在", str(context.exception))

    # ========== trigger_scan 测试 ==========

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_trigger_scan_success(self, mock_engine_class):
        """测试触发扫描成功"""
        # Mock引擎
        mock_engine = MagicMock()
        mock_alerts = [
            self._create_mock_alert(1),
            self._create_mock_alert(2),
        ]
        mock_engine.scan_and_alert.return_value = mock_alerts
        mock_engine_class.return_value = mock_engine
        
        # 执行扫描
        alerts, scan_time = self.service.trigger_scan(days_ahead=7)
        
        # 验证结果
        self.assertEqual(len(alerts), 2)
        self.assertIsInstance(scan_time, datetime)
        mock_engine.scan_and_alert.assert_called_once_with(
            project_id=None,
            material_id=None,
            days_ahead=7
        )

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_trigger_scan_with_filters(self, mock_engine_class):
        """测试带过滤条件的扫描"""
        mock_engine = MagicMock()
        mock_engine.scan_and_alert.return_value = []
        mock_engine_class.return_value = mock_engine
        
        self.service.trigger_scan(
            project_id=100,
            material_id=200,
            days_ahead=14
        )
        
        mock_engine.scan_and_alert.assert_called_once_with(
            project_id=100,
            material_id=200,
            days_ahead=14
        )

    # ========== get_handling_solutions 测试 ==========

    def test_get_handling_solutions_existing_plans(self):
        """测试获取已有处理方案"""
        mock_alert = self._create_mock_alert(1)
        
        # Mock alert查询
        alert_query = MagicMock()
        alert_query.filter.return_value = alert_query
        alert_query.first.return_value = mock_alert
        
        # Mock plans查询
        mock_plans = [
            MagicMock(id=1, alert_id=1, ai_score=Decimal('90')),
            MagicMock(id=2, alert_id=1, ai_score=Decimal('80')),
        ]
        
        plans_query = MagicMock()
        plans_query.filter.return_value = plans_query
        plans_query.order_by.return_value = plans_query
        plans_query.all.return_value = mock_plans
        
        # 配置db.query根据不同的model返回不同的query
        def query_side_effect(model):
            if model == ShortageAlert:
                return alert_query
            elif model == ShortageHandlingPlan:
                return plans_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行查询
        plans = self.service.get_handling_solutions(1)
        
        # 验证结果
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0].ai_score, Decimal('90'))

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_get_handling_solutions_auto_generate(self, mock_engine_class):
        """测试自动生成处理方案"""
        mock_alert = self._create_mock_alert(1)
        
        # Mock alert查询
        alert_query = MagicMock()
        alert_query.filter.return_value = alert_query
        alert_query.first.return_value = mock_alert
        
        # Mock plans查询（返回空列表）
        plans_query = MagicMock()
        plans_query.filter.return_value = plans_query
        plans_query.order_by.return_value = plans_query
        plans_query.all.return_value = []
        
        def query_side_effect(model):
            if model == ShortageAlert:
                return alert_query
            elif model == ShortageHandlingPlan:
                return plans_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # Mock引擎生成方案
        mock_engine = MagicMock()
        generated_plans = [
            MagicMock(id=10, alert_id=1, ai_score=Decimal('95')),
        ]
        mock_engine.generate_solutions.return_value = generated_plans
        mock_engine_class.return_value = mock_engine
        
        # 执行查询
        plans = self.service.get_handling_solutions(1)
        
        # 验证自动生成被调用
        self.assertEqual(len(plans), 1)
        mock_engine.generate_solutions.assert_called_once_with(mock_alert)

    # ========== resolve_alert 测试 ==========

    def test_resolve_alert_success(self):
        """测试成功解决预警"""
        mock_alert = self._create_mock_alert(1, status='PENDING')
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert
        
        self.db.query.return_value = mock_query
        
        # 执行解决
        result = self.service.resolve_alert(
            alert_id=1,
            handler_id=999,
            resolution_type='PURCHASE',
            resolution_note='已下单采购',
            actual_cost_impact=6000.0,
            actual_delay_days=2
        )
        
        # 验证状态更新
        self.assertEqual(result.status, 'RESOLVED')
        self.assertEqual(result.handler_id, 999)
        self.assertEqual(result.resolution_type, 'PURCHASE')
        self.assertEqual(result.resolution_note, '已下单采购')
        self.assertEqual(result.actual_cost_impact, 6000.0)
        self.assertEqual(result.actual_delay_days, 2)
        self.assertIsNotNone(result.resolved_at)
        
        # 验证数据库操作
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_resolve_alert_already_resolved(self):
        """测试重复解决已解决的预警"""
        mock_alert = self._create_mock_alert(1, status='RESOLVED')
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert
        
        self.db.query.return_value = mock_query
        
        with self.assertRaises(BusinessException) as context:
            self.service.resolve_alert(alert_id=1, handler_id=999)
        
        self.assertIn("预警已解决", str(context.exception))

    def test_resolve_alert_minimal_params(self):
        """测试最少参数解决预警"""
        mock_alert = self._create_mock_alert(1, status='PENDING')
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert
        
        self.db.query.return_value = mock_query
        
        result = self.service.resolve_alert(alert_id=1, handler_id=888)
        
        self.assertEqual(result.status, 'RESOLVED')
        self.assertEqual(result.handler_id, 888)

    # ========== get_material_forecast 测试 ==========

    @patch('app.services.shortage_alerts.service.DemandForecastEngine')
    def test_get_material_forecast_default_params(self, mock_engine_class):
        """测试获取物料需求预测（默认参数）"""
        mock_engine = MagicMock()
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_engine.forecast_material_demand.return_value = mock_forecast
        mock_engine_class.return_value = mock_engine
        
        forecast = self.service.get_material_forecast(material_id=100)
        
        self.assertIsNotNone(forecast)
        mock_engine.forecast_material_demand.assert_called_once_with(
            material_id=100,
            forecast_horizon_days=30,
            algorithm='EXP_SMOOTHING',
            historical_days=90,
            project_id=None
        )

    @patch('app.services.shortage_alerts.service.DemandForecastEngine')
    def test_get_material_forecast_custom_params(self, mock_engine_class):
        """测试获取物料需求预测（自定义参数）"""
        mock_engine = MagicMock()
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_engine.forecast_material_demand.return_value = mock_forecast
        mock_engine_class.return_value = mock_engine
        
        forecast = self.service.get_material_forecast(
            material_id=200,
            forecast_horizon_days=60,
            algorithm='ARIMA',
            historical_days=180,
            project_id=50
        )
        
        mock_engine.forecast_material_demand.assert_called_once_with(
            material_id=200,
            forecast_horizon_days=60,
            algorithm='ARIMA',
            historical_days=180,
            project_id=50
        )

    # ========== analyze_shortage_trend 测试 ==========

    def test_analyze_shortage_trend_no_data(self):
        """测试趋势分析（无数据）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_shortage_trend(days=30)
        
        self.assertEqual(result['total_alerts'], 0)
        self.assertEqual(result['by_level'], {})
        self.assertEqual(result['by_status'], {})
        self.assertEqual(result['avg_resolution_hours'], 0)

    def test_analyze_shortage_trend_with_data(self):
        """测试趋势分析（有数据）"""
        # 创建测试数据
        now = datetime.now()
        mock_alerts = [
            self._create_mock_alert(
                1,
                alert_level='URGENT',
                status='RESOLVED',
                alert_date=date.today(),
                detected_at=now - timedelta(hours=10),
                resolved_at=now,
                estimated_cost_impact=Decimal('5000')
            ),
            self._create_mock_alert(
                2,
                alert_level='WARNING',
                status='PENDING',
                alert_date=date.today(),
                detected_at=now - timedelta(hours=5),
                resolved_at=None,
                estimated_cost_impact=Decimal('3000')
            ),
            self._create_mock_alert(
                3,
                alert_level='URGENT',
                status='RESOLVED',
                alert_date=date.today() - timedelta(days=1),
                detected_at=now - timedelta(hours=30),
                resolved_at=now - timedelta(hours=20),
                estimated_cost_impact=Decimal('7000')
            ),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_shortage_trend(days=7)
        
        # 验证统计数据
        self.assertEqual(result['total_alerts'], 3)
        self.assertEqual(result['by_level']['URGENT'], 2)
        self.assertEqual(result['by_level']['WARNING'], 1)
        self.assertEqual(result['by_status']['RESOLVED'], 2)
        self.assertEqual(result['by_status']['PENDING'], 1)
        self.assertEqual(result['avg_resolution_hours'], 10.0)  # (10+10)/2
        self.assertEqual(result['total_cost_impact'], 15000)

    def test_analyze_shortage_trend_with_project_filter(self):
        """测试趋势分析（带项目过滤）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        self.service.analyze_shortage_trend(days=30, project_id=100)
        
        # 验证filter被调用两次（日期过滤 + 项目过滤）
        self.assertEqual(mock_query.filter.call_count, 2)

    # ========== analyze_root_cause 测试 ==========

    def test_analyze_root_cause_no_data(self):
        """测试根因分析（无数据）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_root_cause(days=30)
        
        self.assertEqual(result['total_analyzed'], 0)
        self.assertEqual(len(result['top_causes']), 0)

    def test_analyze_root_cause_with_data(self):
        """测试根因分析（有数据）"""
        mock_alerts = [
            # 供应商交期延误（有在途数量）
            self._create_mock_alert(
                1,
                in_transit_qty=Decimal('50'),
                available_qty=Decimal('0'),
                estimated_delay_days=5,
                estimated_cost_impact=Decimal('5000')
            ),
            self._create_mock_alert(
                2,
                in_transit_qty=Decimal('30'),
                available_qty=Decimal('10'),
                estimated_delay_days=3,
                estimated_cost_impact=Decimal('3000')
            ),
            # 库存管理不当（可用数量为0）
            self._create_mock_alert(
                3,
                in_transit_qty=Decimal('0'),
                available_qty=Decimal('0'),
                estimated_delay_days=2,
                estimated_cost_impact=Decimal('2000')
            ),
            # 采购流程延迟（延期天数>7）
            self._create_mock_alert(
                4,
                in_transit_qty=Decimal('0'),
                available_qty=Decimal('20'),
                estimated_delay_days=10,
                estimated_cost_impact=Decimal('8000')
            ),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_root_cause(days=30)
        
        # 验证分析结果
        self.assertEqual(result['total_analyzed'], 4)
        self.assertGreater(len(result['top_causes']), 0)
        
        # 验证推荐建议
        self.assertIsInstance(result['recommendations'], list)
        self.assertGreater(len(result['recommendations']), 0)
        
        # 验证最大原因
        top_cause = result['top_causes'][0]
        self.assertEqual(top_cause['cause'], '供应商交期延误')
        self.assertEqual(top_cause['count'], 2)

    # ========== analyze_project_impact 测试 ==========

    def test_analyze_project_impact_no_data(self):
        """测试项目影响分析（无数据）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_project_impact()
        
        self.assertEqual(len(result), 0)

    def test_analyze_project_impact_with_data(self):
        """测试项目影响分析（有数据）"""
        # Mock聚合查询结果
        mock_agg_results = [
            MagicMock(
                project_id=1,
                alert_count=5,
                total_shortage_qty=Decimal('200'),
                max_delay_days=7,
                total_cost_impact=Decimal('15000')
            ),
            MagicMock(
                project_id=2,
                alert_count=3,
                total_shortage_qty=Decimal('100'),
                max_delay_days=3,
                total_cost_impact=Decimal('8000')
            ),
        ]
        
        # Mock关键物料查询
        material_query = MagicMock()
        material_query.filter.return_value = material_query
        material_query.limit.return_value = material_query
        material_query.all.side_effect = [
            [('电机',), ('轴承',)],
            [('钢板',)],
        ]
        
        # 项目查询计数器
        project_query_count = [0]
        
        def complex_query_side_effect(*args, **kwargs):
            # 如果是单个参数且是Model类
            if len(args) == 1 and hasattr(args[0], '__name__'):
                if args[0] == Project:
                    query = MagicMock()
                    
                    def filter_side_effect(condition):
                        project_query_count[0] += 1
                        
                        result_query = MagicMock()
                        if project_query_count[0] == 1:
                            result_query.first.return_value = self._create_mock_project(1, project_name='项目A')
                        else:
                            result_query.first.return_value = self._create_mock_project(2, project_name='项目B')
                        return result_query
                    
                    query.filter.side_effect = filter_side_effect
                    return query
                elif args[0] == ShortageAlert.material_name:
                    return material_query
            # 聚合查询（多个参数）
            else:
                query = MagicMock()
                query.filter.return_value = query
                query.group_by.return_value = query
                query.all.return_value = mock_agg_results
                return query
        
        self.db.query.side_effect = complex_query_side_effect
        
        result = self.service.analyze_project_impact()
        
        # 验证结果
        self.assertEqual(len(result), 2)
        
        # 验证排序（按成本影响降序）
        self.assertEqual(result[0]['project_id'], 1)
        self.assertEqual(result[0]['estimated_cost_impact'], 15000)
        self.assertEqual(result[1]['project_id'], 2)
        self.assertEqual(result[1]['estimated_cost_impact'], 8000)

    def test_analyze_project_impact_with_filters(self):
        """测试项目影响分析（带过滤条件）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        self.service.analyze_project_impact(
            alert_level='URGENT',
            status='PENDING'
        )
        
        # 验证filter被调用（status.in_ + alert_level + status额外过滤）
        self.assertGreater(mock_query.filter.call_count, 0)

    # ========== create_notification_subscription 测试 ==========

    def test_create_notification_subscription_minimal(self):
        """测试创建订阅（最少参数）"""
        result = self.service.create_notification_subscription(
            user_id=100,
            alert_levels=['URGENT', 'CRITICAL']
        )
        
        self.assertEqual(result['user_id'], 100)
        self.assertEqual(result['alert_levels'], ['URGENT', 'CRITICAL'])
        self.assertEqual(result['project_ids'], [])
        self.assertEqual(result['material_ids'], [])
        self.assertEqual(result['notification_channels'], ['EMAIL'])
        self.assertTrue(result['enabled'])
        self.assertIn('subscription_id', result)
        self.assertIn('created_at', result)

    def test_create_notification_subscription_full(self):
        """测试创建订阅（完整参数）"""
        result = self.service.create_notification_subscription(
            user_id=200,
            alert_levels=['WARNING', 'CRITICAL'],
            project_ids=[1, 2, 3],
            material_ids=[100, 200],
            notification_channels=['EMAIL', 'SMS', 'WECHAT'],
            enabled=False
        )
        
        self.assertEqual(result['user_id'], 200)
        self.assertEqual(result['project_ids'], [1, 2, 3])
        self.assertEqual(result['material_ids'], [100, 200])
        self.assertEqual(result['notification_channels'], ['EMAIL', 'SMS', 'WECHAT'])
        self.assertFalse(result['enabled'])

    # ========== 边界情况测试 ==========

    def test_analyze_shortage_trend_daily_data(self):
        """测试趋势分析每日数据构建"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        mock_alerts = [
            self._create_mock_alert(1, alert_level='URGENT', alert_date=today),
            self._create_mock_alert(2, alert_level='WARNING', alert_date=today),
            self._create_mock_alert(3, alert_level='CRITICAL', alert_date=yesterday),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_shortage_trend(days=2)
        
        # 验证每日趋势数据
        self.assertIn('trend_data', result)
        trend_data = result['trend_data']
        
        # 应该有3天的数据（包含今天）
        self.assertGreaterEqual(len(trend_data), 2)
        
        # 验证今天的数据
        today_data = [d for d in trend_data if d['date'] == today.isoformat()]
        if today_data:
            self.assertEqual(today_data[0]['count'], 2)
            self.assertEqual(today_data[0]['urgent'], 1)
            self.assertEqual(today_data[0]['warning'], 1)

    def test_analyze_root_cause_recommendations(self):
        """测试根因分析推荐生成"""
        # 创建不同根因的测试数据
        test_cases = [
            # 供应商问题
            {
                'alerts': [
                    self._create_mock_alert(1, in_transit_qty=Decimal('100')),
                    self._create_mock_alert(2, in_transit_qty=Decimal('50')),
                ],
                'expected_keyword': '供应商'
            },
            # 需求预测问题
            {
                'alerts': [
                    self._create_mock_alert(
                        1,
                        in_transit_qty=Decimal('0'),
                        available_qty=Decimal('10'),
                        estimated_delay_days=3
                    ),
                ],
                'expected_keyword': '预测'
            },
            # 库存问题
            {
                'alerts': [
                    self._create_mock_alert(
                        1,
                        in_transit_qty=Decimal('0'),
                        available_qty=Decimal('0'),
                        estimated_delay_days=3
                    ),
                ],
                'expected_keyword': '库存'
            },
            # 采购流程问题
            {
                'alerts': [
                    self._create_mock_alert(
                        1,
                        in_transit_qty=Decimal('0'),
                        available_qty=Decimal('10'),
                        estimated_delay_days=10
                    ),
                ],
                'expected_keyword': '采购'
            },
        ]
        
        for case in test_cases:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = case['alerts']
            
            self.db.query.return_value = mock_query
            
            result = self.service.analyze_root_cause(days=30)
            
            # 验证有推荐建议
            self.assertGreater(len(result['recommendations']), 0)
            
            # 验证推荐与根因相关
            recommendations_text = ' '.join(result['recommendations'])
            self.assertIn(case['expected_keyword'], recommendations_text)


if __name__ == '__main__':
    unittest.main()
