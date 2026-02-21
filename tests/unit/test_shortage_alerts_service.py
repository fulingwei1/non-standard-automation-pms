# -*- coding: utf-8 -*-
"""
缺料预警服务单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
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


class TestShortageAlertServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试正常初始化"""
        mock_db = MagicMock()
        service = ShortageAlertService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestGetAlertsWithFilters(unittest.TestCase):
    """测试获取预警列表（多维度筛选和分页）"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_get_alerts_no_filters(self):
        """测试无筛选条件"""
        # 创建mock数据
        mock_alert1 = MagicMock(spec=ShortageAlert)
        mock_alert2 = MagicMock(spec=ShortageAlert)
        
        # 设置query链
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_alert1, mock_alert2]

        # 执行测试
        alerts, total = self.service.get_alerts_with_filters()

        # 验证
        self.assertEqual(len(alerts), 2)
        self.assertEqual(total, 2)
        self.mock_db.query.assert_called_once()

    def test_get_alerts_with_project_filter(self):
        """测试按项目筛选"""
        mock_alert = MagicMock(spec=ShortageAlert)
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_alert]

        alerts, total = self.service.get_alerts_with_filters(project_id=1)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(total, 1)
        mock_query.filter.assert_called()

    def test_get_alerts_with_all_filters(self):
        """测试所有筛选条件"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        alerts, total = self.service.get_alerts_with_filters(
            project_id=1,
            material_id=100,
            alert_level='CRITICAL',
            status='PENDING',
            start_date='2024-01-01',
            end_date='2024-12-31',
            page=2,
            page_size=10
        )

        self.assertEqual(len(alerts), 0)
        self.assertEqual(total, 0)
        mock_query.filter.assert_called()
        mock_query.offset.assert_called_with(10)  # (2-1)*10
        mock_query.limit.assert_called_with(10)

    def test_get_alerts_pagination(self):
        """测试分页功能"""
        # 模拟总共25条数据，取第2页，每页10条
        mock_alerts = [MagicMock(spec=ShortageAlert) for _ in range(10)]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 25
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts

        alerts, total = self.service.get_alerts_with_filters(page=2, page_size=10)

        self.assertEqual(len(alerts), 10)
        self.assertEqual(total, 25)
        mock_query.offset.assert_called_with(10)


class TestGetAlertById(unittest.TestCase):
    """测试获取预警详情"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_get_alert_by_id_success(self):
        """测试成功获取预警"""
        mock_alert = MagicMock(spec=ShortageAlert)
        mock_alert.id = 1
        mock_alert.alert_no = 'SA202401010001'
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert

        result = self.service.get_alert_by_id(1)

        self.assertEqual(result, mock_alert)
        self.assertEqual(result.id, 1)

    def test_get_alert_by_id_not_found(self):
        """测试预警不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with self.assertRaises(BusinessException) as context:
            self.service.get_alert_by_id(999)
        
        self.assertEqual(context.exception.message, "预警不存在")


class TestTriggerScan(unittest.TestCase):
    """测试触发缺料扫描"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_trigger_scan_without_filters(self, mock_engine_class):
        """测试无过滤条件的扫描"""
        # Mock引擎实例
        mock_engine = MagicMock()
        mock_alert1 = MagicMock(spec=ShortageAlert)
        mock_alert2 = MagicMock(spec=ShortageAlert)
        mock_engine.scan_and_alert.return_value = [mock_alert1, mock_alert2]
        mock_engine_class.return_value = mock_engine

        # 执行扫描
        alerts, scan_time = self.service.trigger_scan()

        # 验证
        self.assertEqual(len(alerts), 2)
        self.assertIsInstance(scan_time, datetime)
        mock_engine_class.assert_called_once_with(self.mock_db)
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

        alerts, scan_time = self.service.trigger_scan(
            project_id=1,
            material_id=100,
            days_ahead=14
        )

        self.assertEqual(len(alerts), 0)
        mock_engine.scan_and_alert.assert_called_once_with(
            project_id=1,
            material_id=100,
            days_ahead=14
        )


class TestGetHandlingSolutions(unittest.TestCase):
    """测试获取处理方案"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_get_solutions_existing(self, mock_engine_class):
        """测试获取已有方案"""
        # Mock alert
        mock_alert = MagicMock(spec=ShortageAlert)
        mock_alert.id = 1
        
        # Mock existing plans
        mock_plan1 = MagicMock(spec=ShortageHandlingPlan)
        mock_plan1.ai_score = Decimal('95.5')
        mock_plan2 = MagicMock(spec=ShortageHandlingPlan)
        mock_plan2.ai_score = Decimal('87.3')
        
        # Setup query chains
        alert_query = MagicMock()
        alert_query.filter.return_value = alert_query
        alert_query.first.return_value = mock_alert
        
        plan_query = MagicMock()
        plan_query.filter.return_value = plan_query
        plan_query.order_by.return_value = plan_query
        plan_query.all.return_value = [mock_plan1, mock_plan2]
        
        # Configure db.query to return different mocks
        def query_side_effect(model):
            if model == ShortageAlert:
                return alert_query
            elif model == ShortageHandlingPlan:
                return plan_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        plans = self.service.get_handling_solutions(1)

        # 验证
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0].ai_score, Decimal('95.5'))

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_get_solutions_auto_generate(self, mock_engine_class):
        """测试自动生成方案"""
        # Mock alert
        mock_alert = MagicMock(spec=ShortageAlert)
        mock_alert.id = 1
        
        # Mock no existing plans
        alert_query = MagicMock()
        alert_query.filter.return_value = alert_query
        alert_query.first.return_value = mock_alert
        
        plan_query = MagicMock()
        plan_query.filter.return_value = plan_query
        plan_query.order_by.return_value = plan_query
        plan_query.all.return_value = []  # 无现有方案
        
        def query_side_effect(model):
            if model == ShortageAlert:
                return alert_query
            elif model == ShortageHandlingPlan:
                return plan_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        # Mock engine生成方案
        mock_engine = MagicMock()
        mock_new_plan = MagicMock(spec=ShortageHandlingPlan)
        mock_engine.generate_solutions.return_value = [mock_new_plan]
        mock_engine_class.return_value = mock_engine

        # 执行测试
        plans = self.service.get_handling_solutions(1)

        # 验证
        self.assertEqual(len(plans), 1)
        mock_engine.generate_solutions.assert_called_once_with(mock_alert)

    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_get_solutions_alert_not_found(self, mock_engine_class):
        """测试预警不存在"""
        alert_query = MagicMock()
        alert_query.filter.return_value = alert_query
        alert_query.first.return_value = None
        
        self.mock_db.query.return_value = alert_query

        with self.assertRaises(BusinessException):
            self.service.get_handling_solutions(999)


class TestResolveAlert(unittest.TestCase):
    """测试标记预警已解决"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_resolve_alert_success(self):
        """测试成功解决预警"""
        # Mock alert
        mock_alert = MagicMock(spec=ShortageAlert)
        mock_alert.id = 1
        mock_alert.status = 'PENDING'
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert

        # 执行测试
        result = self.service.resolve_alert(
            alert_id=1,
            handler_id=10,
            resolution_type='PURCHASE',
            resolution_note='紧急采购完成',
            actual_cost_impact=1500.0,
            actual_delay_days=2
        )

        # 验证
        self.assertEqual(result.status, 'RESOLVED')
        self.assertEqual(result.handler_id, 10)
        self.assertEqual(result.resolution_type, 'PURCHASE')
        self.assertEqual(result.resolution_note, '紧急采购完成')
        self.assertEqual(result.actual_cost_impact, 1500.0)
        self.assertEqual(result.actual_delay_days, 2)
        self.assertIsNotNone(result.resolved_at)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_alert)

    def test_resolve_alert_already_resolved(self):
        """测试预警已解决"""
        mock_alert = MagicMock(spec=ShortageAlert)
        mock_alert.status = 'RESOLVED'
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert

        with self.assertRaises(BusinessException) as context:
            self.service.resolve_alert(alert_id=1, handler_id=10)
        
        self.assertEqual(context.exception.message, "预警已解决")

    def test_resolve_alert_minimal_params(self):
        """测试最少参数解决预警"""
        mock_alert = MagicMock(spec=ShortageAlert)
        mock_alert.status = 'PROCESSING'
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_alert

        result = self.service.resolve_alert(alert_id=1, handler_id=10)

        self.assertEqual(result.status, 'RESOLVED')
        self.assertEqual(result.handler_id, 10)


class TestGetMaterialForecast(unittest.TestCase):
    """测试获取物料需求预测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    @patch('app.services.shortage_alerts.service.DemandForecastEngine')
    def test_get_material_forecast_default_params(self, mock_engine_class):
        """测试默认参数预测"""
        mock_engine = MagicMock()
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_forecast.forecasted_demand = Decimal('1000')
        mock_engine.forecast_material_demand.return_value = mock_forecast
        mock_engine_class.return_value = mock_engine

        result = self.service.get_material_forecast(material_id=100)

        self.assertEqual(result, mock_forecast)
        mock_engine.forecast_material_demand.assert_called_once_with(
            material_id=100,
            forecast_horizon_days=30,
            algorithm='EXP_SMOOTHING',
            historical_days=90,
            project_id=None
        )

    @patch('app.services.shortage_alerts.service.DemandForecastEngine')
    def test_get_material_forecast_custom_params(self, mock_engine_class):
        """测试自定义参数预测"""
        mock_engine = MagicMock()
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_engine.forecast_material_demand.return_value = mock_forecast
        mock_engine_class.return_value = mock_engine

        result = self.service.get_material_forecast(
            material_id=200,
            forecast_horizon_days=60,
            algorithm='ARIMA',
            historical_days=180,
            project_id=5
        )

        mock_engine.forecast_material_demand.assert_called_once_with(
            material_id=200,
            forecast_horizon_days=60,
            algorithm='ARIMA',
            historical_days=180,
            project_id=5
        )


class TestAnalyzeShortageTrend(unittest.TestCase):
    """测试缺料趋势分析"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_analyze_shortage_trend_with_data(self):
        """测试有数据的趋势分析"""
        # 创建mock alerts
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        mock_alert1 = MagicMock(spec=ShortageAlert)
        mock_alert1.alert_level = 'CRITICAL'
        mock_alert1.status = 'RESOLVED'
        mock_alert1.alert_date = today
        mock_alert1.detected_at = datetime.now() - timedelta(hours=5)
        mock_alert1.resolved_at = datetime.now()
        mock_alert1.estimated_cost_impact = Decimal('1000')
        
        mock_alert2 = MagicMock(spec=ShortageAlert)
        mock_alert2.alert_level = 'WARNING'
        mock_alert2.status = 'PENDING'
        mock_alert2.alert_date = yesterday
        mock_alert2.detected_at = None
        mock_alert2.resolved_at = None
        mock_alert2.estimated_cost_impact = Decimal('500')
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_alert1, mock_alert2]

        # 执行测试
        result = self.service.analyze_shortage_trend(days=30)

        # 验证
        self.assertEqual(result['total_alerts'], 2)
        self.assertEqual(result['by_level']['CRITICAL'], 1)
        self.assertEqual(result['by_level']['WARNING'], 1)
        self.assertEqual(result['by_status']['RESOLVED'], 1)
        self.assertEqual(result['by_status']['PENDING'], 1)
        self.assertGreater(result['avg_resolution_hours'], 0)
        self.assertEqual(result['total_cost_impact'], 1500)
        self.assertIsInstance(result['trend_data'], list)

    def test_analyze_shortage_trend_no_data(self):
        """测试无数据的趋势分析"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.analyze_shortage_trend(days=7)

        self.assertEqual(result['total_alerts'], 0)
        self.assertEqual(result['by_level'], {})
        self.assertEqual(result['by_status'], {})
        self.assertEqual(result['avg_resolution_hours'], 0)
        self.assertEqual(result['total_cost_impact'], 0)

    def test_analyze_shortage_trend_with_project_filter(self):
        """测试带项目筛选的趋势分析"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.analyze_shortage_trend(days=30, project_id=1)

        # 验证filter被调用了两次（日期+项目）
        self.assertEqual(mock_query.filter.call_count, 2)


class TestAnalyzeRootCause(unittest.TestCase):
    """测试缺料根因分析"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_analyze_root_cause_with_data(self):
        """测试有数据的根因分析"""
        # 创建不同类型的alerts
        alert1 = MagicMock(spec=ShortageAlert)
        alert1.in_transit_qty = Decimal('100')  # 供应商交期延误
        alert1.available_qty = Decimal('50')
        alert1.estimated_delay_days = 5
        alert1.estimated_cost_impact = Decimal('1000')
        alert1.alert_no = 'SA001'
        
        alert2 = MagicMock(spec=ShortageAlert)
        alert2.in_transit_qty = Decimal('0')
        alert2.available_qty = Decimal('0')  # 库存管理不当
        alert2.estimated_delay_days = 3
        alert2.estimated_cost_impact = Decimal('800')
        alert2.alert_no = 'SA002'
        
        alert3 = MagicMock(spec=ShortageAlert)
        alert3.in_transit_qty = Decimal('0')
        alert3.available_qty = Decimal('10')
        alert3.estimated_delay_days = 10  # 采购流程延迟
        alert3.estimated_cost_impact = Decimal('1200')
        alert3.alert_no = 'SA003'
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [alert1, alert2, alert3]

        # 执行测试
        result = self.service.analyze_root_cause(days=30)

        # 验证
        self.assertEqual(result['total_analyzed'], 3)
        self.assertIsInstance(result['top_causes'], list)
        self.assertGreater(len(result['top_causes']), 0)
        self.assertIsInstance(result['recommendations'], list)
        
        # 验证根因数据结构
        for cause in result['top_causes']:
            self.assertIn('cause', cause)
            self.assertIn('count', cause)
            self.assertIn('percentage', cause)
            self.assertIn('avg_cost_impact', cause)
            self.assertIn('examples', cause)

    def test_analyze_root_cause_no_data(self):
        """测试无数据的根因分析"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.analyze_root_cause(days=7)

        self.assertEqual(result['total_analyzed'], 0)
        self.assertEqual(len(result['top_causes']), 0)
        self.assertEqual(len(result['recommendations']), 0)

    def test_analyze_root_cause_recommendations(self):
        """测试改进建议生成"""
        # 创建供应商延误为主的场景
        alerts = []
        for i in range(5):
            alert = MagicMock(spec=ShortageAlert)
            alert.in_transit_qty = Decimal('100')
            alert.available_qty = Decimal('50')
            alert.estimated_delay_days = 5
            alert.estimated_cost_impact = Decimal('1000')
            alert.alert_no = f'SA00{i}'
            alerts.append(alert)
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = alerts

        result = self.service.analyze_root_cause(days=30)

        # 验证建议包含供应商相关内容
        recommendations = result['recommendations']
        self.assertGreater(len(recommendations), 0)
        has_supplier_recommendation = any(
            '供应商' in rec for rec in recommendations
        )
        self.assertTrue(has_supplier_recommendation)


class TestAnalyzeProjectImpact(unittest.TestCase):
    """测试项目影响分析"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_analyze_project_impact_basic(self):
        """测试基本项目影响分析"""
        # Mock query结果
        mock_row1 = MagicMock()
        mock_row1.project_id = 1
        mock_row1.alert_count = 5
        mock_row1.total_shortage_qty = Decimal('1000')
        mock_row1.max_delay_days = 7
        mock_row1.total_cost_impact = Decimal('5000')
        
        mock_row2 = MagicMock()
        mock_row2.project_id = 2
        mock_row2.alert_count = 3
        mock_row2.total_shortage_qty = Decimal('500')
        mock_row2.max_delay_days = 3
        mock_row2.total_cost_impact = Decimal('2000')
        
        # Mock projects
        mock_project1 = MagicMock(spec=Project)
        mock_project1.project_name = '项目A'
        
        mock_project2 = MagicMock(spec=Project)
        mock_project2.project_name = '项目B'
        
        # Setup query chains
        agg_query = MagicMock()
        agg_query.filter.return_value = agg_query
        agg_query.group_by.return_value = agg_query
        agg_query.all.return_value = [mock_row1, mock_row2]
        
        project_query1 = MagicMock()
        project_query1.filter.return_value = project_query1
        project_query1.first.return_value = mock_project1
        
        project_query2 = MagicMock()
        project_query2.filter.return_value = project_query2
        project_query2.first.return_value = mock_project2
        
        material_query = MagicMock()
        material_query.filter.return_value = material_query
        material_query.limit.return_value = material_query
        material_query.all.return_value = [('物料A',), ('物料B',)]
        
        # Configure query side effects - 简化mock策略
        call_count = [0]
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            # 第1次调用是聚合查询
            if call_count[0] == 1:
                return agg_query
            # 第2, 4次调用是查询项目
            elif call_count[0] in [2, 4]:
                return project_query1 if call_count[0] == 2 else project_query2
            # 第3, 5次调用是查询关键物料
            else:
                return material_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.service.analyze_project_impact()

        # 验证
        self.assertEqual(len(result), 2)
        # 应按成本影响排序，项目1排第一
        self.assertEqual(result[0]['project_id'], 1)
        self.assertEqual(result[0]['alert_count'], 5)
        self.assertEqual(result[0]['estimated_cost_impact'], Decimal('5000'))

    def test_analyze_project_impact_with_filters(self):
        """测试带筛选条件的项目影响分析"""
        agg_query = MagicMock()
        agg_query.filter.return_value = agg_query
        agg_query.group_by.return_value = agg_query
        agg_query.all.return_value = []
        
        self.mock_db.query.return_value = agg_query

        result = self.service.analyze_project_impact(
            alert_level='CRITICAL',
            status='PENDING'
        )

        self.assertEqual(len(result), 0)
        # 验证filter被调用了多次
        self.assertGreater(agg_query.filter.call_count, 0)


class TestCreateNotificationSubscription(unittest.TestCase):
    """测试创建预警通知订阅"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ShortageAlertService(self.mock_db)

    def test_create_subscription_minimal(self):
        """测试最少参数创建订阅"""
        result = self.service.create_notification_subscription(
            user_id=1,
            alert_levels=['CRITICAL', 'URGENT']
        )

        self.assertIsNotNone(result['subscription_id'])
        self.assertEqual(result['user_id'], 1)
        self.assertEqual(result['alert_levels'], ['CRITICAL', 'URGENT'])
        self.assertEqual(result['project_ids'], [])
        self.assertEqual(result['material_ids'], [])
        self.assertEqual(result['notification_channels'], ['EMAIL'])
        self.assertTrue(result['enabled'])

    def test_create_subscription_full_params(self):
        """测试完整参数创建订阅"""
        result = self.service.create_notification_subscription(
            user_id=2,
            alert_levels=['WARNING', 'INFO'],
            project_ids=[1, 2, 3],
            material_ids=[100, 200],
            notification_channels=['EMAIL', 'SMS', 'WECHAT'],
            enabled=False
        )

        self.assertEqual(result['user_id'], 2)
        self.assertEqual(result['project_ids'], [1, 2, 3])
        self.assertEqual(result['material_ids'], [100, 200])
        self.assertEqual(result['notification_channels'], ['EMAIL', 'SMS', 'WECHAT'])
        self.assertFalse(result['enabled'])


if __name__ == "__main__":
    unittest.main()
