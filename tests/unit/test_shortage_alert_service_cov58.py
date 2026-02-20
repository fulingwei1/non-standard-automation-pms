# -*- coding: utf-8 -*-
"""
ShortageAlertService 单元测试

覆盖目标: 58%+
测试用例数: 8+
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from typing import List

from app.services.shortage_alerts import ShortageAlertService
from app.models.shortage.smart_alert import ShortageAlert, ShortageHandlingPlan
from app.core.exceptions import BusinessException


class TestShortageAlertService(unittest.TestCase):
    """ShortageAlertService 测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.db_mock = MagicMock()
        self.service = ShortageAlertService(self.db_mock)
    
    def test_init_service(self):
        """测试1: 服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.db, self.db_mock)
    
    def test_get_alerts_with_filters_no_filters(self):
        """测试2: 获取预警列表 - 无过滤条件"""
        # Mock 数据
        mock_alerts = [
            MagicMock(id=1, alert_level='CRITICAL', created_at=datetime.now()),
            MagicMock(id=2, alert_level='WARNING', created_at=datetime.now())
        ]
        
        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_alerts
        
        self.db_mock.query.return_value = mock_query
        
        # 执行
        alerts, total = self.service.get_alerts_with_filters(page=1, page_size=20)
        
        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(alerts), 2)
        self.db_mock.query.assert_called_once()
    
    def test_get_alerts_with_filters_with_project_id(self):
        """测试3: 获取预警列表 - 带项目ID过滤"""
        mock_alerts = [MagicMock(id=1, project_id=100)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_alerts
        
        self.db_mock.query.return_value = mock_query
        
        # 执行
        alerts, total = self.service.get_alerts_with_filters(
            project_id=100,
            page=1,
            page_size=20
        )
        
        # 验证
        self.assertEqual(total, 1)
        mock_query.filter.assert_called_once()
    
    def test_get_alert_by_id_exists(self):
        """测试4: 获取预警详情 - 存在"""
        mock_alert = MagicMock(id=1, alert_no='ALT-001')
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_alert
        
        self.db_mock.query.return_value = mock_query
        
        # 执行
        alert = self.service.get_alert_by_id(1)
        
        # 验证
        self.assertEqual(alert.id, 1)
        self.assertEqual(alert.alert_no, 'ALT-001')
    
    def test_get_alert_by_id_not_exists(self):
        """测试5: 获取预警详情 - 不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        self.db_mock.query.return_value = mock_query
        
        # 执行 & 验证
        with self.assertRaises(BusinessException) as context:
            self.service.get_alert_by_id(999)
        
        self.assertEqual(str(context.exception), "预警不存在")
    
    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_trigger_scan(self, mock_engine_class):
        """测试6: 触发缺料扫描"""
        # Mock SmartAlertEngine
        mock_engine = MagicMock()
        mock_alerts = [
            MagicMock(id=1, alert_level='CRITICAL'),
            MagicMock(id=2, alert_level='WARNING')
        ]
        mock_engine.scan_and_alert.return_value = mock_alerts
        mock_engine_class.return_value = mock_engine
        
        # 执行
        alerts, scanned_at = self.service.trigger_scan(
            project_id=100,
            material_id=200,
            days_ahead=7
        )
        
        # 验证
        self.assertEqual(len(alerts), 2)
        self.assertIsInstance(scanned_at, datetime)
        mock_engine.scan_and_alert.assert_called_once_with(
            project_id=100,
            material_id=200,
            days_ahead=7
        )
    
    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_get_handling_solutions_with_existing_plans(self, mock_engine_class):
        """测试7: 获取处理方案 - 已有方案"""
        # Mock alert
        mock_alert = MagicMock(id=1)
        mock_query_alert = MagicMock()
        mock_query_alert.filter.return_value.first.return_value = mock_alert
        
        # Mock plans
        mock_plans = [
            MagicMock(id=1, ai_score=0.9),
            MagicMock(id=2, ai_score=0.8)
        ]
        mock_query_plans = MagicMock()
        mock_query_plans.filter.return_value.order_by.return_value.all.return_value = mock_plans
        
        # 配置 db.query 根据不同的模型返回不同的 query
        def query_side_effect(model):
            if model == ShortageAlert:
                return mock_query_alert
            elif model == ShortageHandlingPlan:
                return mock_query_plans
            return MagicMock()
        
        self.db_mock.query.side_effect = query_side_effect
        
        # 执行
        plans = self.service.get_handling_solutions(1)
        
        # 验证
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0].ai_score, 0.9)
    
    @patch('app.services.shortage_alerts.service.SmartAlertEngine')
    def test_get_handling_solutions_generate_new(self, mock_engine_class):
        """测试8: 获取处理方案 - 自动生成新方案"""
        # Mock alert
        mock_alert = MagicMock(id=1)
        mock_query_alert = MagicMock()
        mock_query_alert.filter.return_value.first.return_value = mock_alert
        
        # Mock 无现有方案
        mock_query_plans = MagicMock()
        mock_query_plans.filter.return_value.order_by.return_value.all.return_value = []
        
        # Mock SmartAlertEngine
        mock_engine = MagicMock()
        mock_new_plans = [MagicMock(id=10, ai_score=0.95)]
        mock_engine.generate_solutions.return_value = mock_new_plans
        mock_engine_class.return_value = mock_engine
        
        def query_side_effect(model):
            if model == ShortageAlert:
                return mock_query_alert
            elif model == ShortageHandlingPlan:
                return mock_query_plans
            return MagicMock()
        
        self.db_mock.query.side_effect = query_side_effect
        
        # 执行
        plans = self.service.get_handling_solutions(1)
        
        # 验证
        self.assertEqual(len(plans), 1)
        mock_engine.generate_solutions.assert_called_once_with(mock_alert)
    
    def test_resolve_alert_success(self):
        """测试9: 标记预警已解决 - 成功"""
        # Mock alert
        mock_alert = MagicMock(id=1, status='PENDING')
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_alert
        
        self.db_mock.query.return_value = mock_query
        
        # 执行
        result = self.service.resolve_alert(
            alert_id=1,
            handler_id=100,
            resolution_type='PURCHASE',
            resolution_note='已采购',
            actual_cost_impact=1000.0,
            actual_delay_days=2
        )
        
        # 验证
        self.assertEqual(mock_alert.status, 'RESOLVED')
        self.assertEqual(mock_alert.handler_id, 100)
        self.assertEqual(mock_alert.resolution_type, 'PURCHASE')
        self.assertIsNotNone(mock_alert.resolved_at)
        self.db_mock.commit.assert_called_once()
        self.db_mock.refresh.assert_called_once_with(mock_alert)
    
    def test_resolve_alert_already_resolved(self):
        """测试10: 标记预警已解决 - 已解决"""
        # Mock alert
        mock_alert = MagicMock(id=1, status='RESOLVED')
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_alert
        
        self.db_mock.query.return_value = mock_query
        
        # 执行 & 验证
        with self.assertRaises(BusinessException) as context:
            self.service.resolve_alert(alert_id=1, handler_id=100)
        
        self.assertEqual(str(context.exception), "预警已解决")
    
    @patch('app.services.shortage_alerts.service.DemandForecastEngine')
    def test_get_material_forecast(self, mock_engine_class):
        """测试11: 获取物料需求预测"""
        # Mock DemandForecastEngine
        mock_engine = MagicMock()
        mock_forecast = MagicMock(
            material_id=100,
            forecast_horizon_days=30,
            algorithm='EXP_SMOOTHING'
        )
        mock_engine.forecast_material_demand.return_value = mock_forecast
        mock_engine_class.return_value = mock_engine
        
        # 执行
        forecast = self.service.get_material_forecast(
            material_id=100,
            forecast_horizon_days=30,
            algorithm='EXP_SMOOTHING',
            historical_days=90
        )
        
        # 验证
        self.assertEqual(forecast.material_id, 100)
        mock_engine.forecast_material_demand.assert_called_once_with(
            material_id=100,
            forecast_horizon_days=30,
            algorithm='EXP_SMOOTHING',
            historical_days=90,
            project_id=None
        )
    
    def test_analyze_shortage_trend(self):
        """测试12: 缺料趋势分析"""
        # Mock alerts
        now = datetime.now()
        mock_alerts = [
            MagicMock(
                alert_level='CRITICAL',
                status='RESOLVED',
                alert_date=now.date(),
                detected_at=now - timedelta(hours=10),
                resolved_at=now,
                estimated_cost_impact=1000.0,
                in_transit_qty=0,
                available_qty=10,
                estimated_delay_days=5
            ),
            MagicMock(
                alert_level='WARNING',
                status='PENDING',
                alert_date=now.date(),
                detected_at=None,
                resolved_at=None,
                estimated_cost_impact=500.0,
                in_transit_qty=0,
                available_qty=5,
                estimated_delay_days=2
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        self.db_mock.query.return_value = mock_query
        
        # 执行
        result = self.service.analyze_shortage_trend(days=30)
        
        # 验证
        self.assertEqual(result['total_alerts'], 2)
        self.assertIn('CRITICAL', result['by_level'])
        self.assertIn('WARNING', result['by_level'])
        self.assertIn('RESOLVED', result['by_status'])
        self.assertIn('PENDING', result['by_status'])
        self.assertEqual(result['total_cost_impact'], 1500.0)
        self.assertIsInstance(result['trend_data'], list)
    
    def test_analyze_root_cause(self):
        """测试13: 根因分析"""
        now = datetime.now()
        mock_alerts = [
            MagicMock(
                alert_date=now.date(),
                in_transit_qty=100,
                available_qty=10,
                estimated_delay_days=3,
                estimated_cost_impact=1000.0,
                alert_no='ALT-001'
            ),
            MagicMock(
                alert_date=now.date(),
                in_transit_qty=0,
                available_qty=0,
                estimated_delay_days=5,
                estimated_cost_impact=2000.0,
                alert_no='ALT-002'
            ),
            MagicMock(
                alert_date=now.date(),
                in_transit_qty=0,
                available_qty=20,
                estimated_delay_days=10,
                estimated_cost_impact=1500.0,
                alert_no='ALT-003'
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_alerts
        
        self.db_mock.query.return_value = mock_query
        
        # 执行
        result = self.service.analyze_root_cause(days=30)
        
        # 验证
        self.assertEqual(result['total_analyzed'], 3)
        self.assertIsInstance(result['top_causes'], list)
        self.assertGreater(len(result['top_causes']), 0)
        self.assertIsInstance(result['recommendations'], list)
        
        # 验证根因包含预期的分类
        causes = [c['cause'] for c in result['top_causes']]
        self.assertTrue(
            any('供应商' in c or '库存' in c or '采购' in c or '预测' in c for c in causes)
        )
    
    @patch('app.services.shortage_alerts.service.Project')
    def test_analyze_project_impact(self, mock_project_class):
        """测试14: 项目影响分析"""
        # Mock aggregation results
        mock_results = [
            MagicMock(
                project_id=1,
                alert_count=5,
                total_shortage_qty=100,
                max_delay_days=7,
                total_cost_impact=5000.0
            ),
            MagicMock(
                project_id=2,
                alert_count=3,
                total_shortage_qty=50,
                max_delay_days=3,
                total_cost_impact=2000.0
            )
        ]
        
        # Mock project query
        mock_project1 = MagicMock(id=1, project_name='项目A')
        mock_project2 = MagicMock(id=2, project_name='项目B')
        
        # Mock critical materials query
        mock_materials_query = MagicMock()
        mock_materials_query.limit.return_value.all.return_value = [('物料1',), ('物料2',)]
        
        mock_query_alert = MagicMock()
        mock_query_alert.filter.return_value.group_by.return_value.all.return_value = mock_results
        
        mock_query_project = MagicMock()
        
        mock_query_materials = MagicMock()
        mock_query_materials.filter.return_value = mock_materials_query
        
        # 配置 db.query 多次调用
        call_count = [0]
        
        def query_side_effect(model_or_args):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第一次：主查询
                return mock_query_alert
            elif call_count[0] in [2, 4]:
                # 项目查询
                if call_count[0] == 2:
                    mock_query_project.filter.return_value.first.return_value = mock_project1
                else:
                    mock_query_project.filter.return_value.first.return_value = mock_project2
                return mock_query_project
            else:
                # 物料查询
                return mock_query_materials
        
        self.db_mock.query.side_effect = query_side_effect
        
        # 执行
        items = self.service.analyze_project_impact()
        
        # 验证
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['project_id'], 1)  # 按成本排序
        self.assertEqual(items[0]['estimated_cost_impact'], 5000.0)
    
    def test_create_notification_subscription(self):
        """测试15: 创建通知订阅"""
        # 执行
        result = self.service.create_notification_subscription(
            user_id=100,
            alert_levels=['CRITICAL', 'URGENT'],
            project_ids=[1, 2],
            material_ids=[10, 20],
            notification_channels=['EMAIL', 'SMS'],
            enabled=True
        )
        
        # 验证
        self.assertIn('subscription_id', result)
        self.assertEqual(result['user_id'], 100)
        self.assertEqual(result['alert_levels'], ['CRITICAL', 'URGENT'])
        self.assertEqual(result['project_ids'], [1, 2])
        self.assertEqual(result['material_ids'], [10, 20])
        self.assertEqual(result['notification_channels'], ['EMAIL', 'SMS'])
        self.assertTrue(result['enabled'])
        self.assertIsInstance(result['created_at'], datetime)


if __name__ == '__main__':
    unittest.main()
