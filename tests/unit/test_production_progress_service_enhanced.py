# -*- coding: utf-8 -*-
"""
生产进度跟踪服务增强测试
测试覆盖所有核心算法和业务方法
"""
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.models.production import (
    ProductionProgressLog,
    ProgressAlert,
    WorkOrder,
    Workstation,
    WorkstationStatus,
)
from app.schemas.production_progress import (
    ProductionProgressLogCreate,
    ProgressAlertCreate,
)
from app.services.production_progress_service import ProductionProgressService


class TestProductionProgressService(unittest.TestCase):
    """生产进度跟踪服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ProductionProgressService(self.db)
        self.today = date.today()

    # ==================== 核心算法1: 进度偏差计算引擎测试 ====================

    def test_calculate_progress_deviation_normal(self):
        """测试正常进度偏差计算"""
        # Mock工单数据
        work_order = Mock()
        work_order.id = 1
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        # 测试：10天中已过5天，计划进度50%，实际60%
        plan, deviation, is_delayed = self.service.calculate_progress_deviation(1, 60)

        self.assertEqual(plan, 50)
        self.assertEqual(deviation, 10)
        self.assertFalse(is_delayed)

    def test_calculate_progress_deviation_delayed(self):
        """测试延期场景（偏差超过-5%）"""
        work_order = Mock()
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        # 实际进度40%，计划50%，偏差-10%
        plan, deviation, is_delayed = self.service.calculate_progress_deviation(1, 40)

        self.assertEqual(plan, 50)
        self.assertEqual(deviation, -10)
        self.assertTrue(is_delayed)

    def test_calculate_progress_deviation_work_order_not_found(self):
        """测试工单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        plan, deviation, is_delayed = self.service.calculate_progress_deviation(999, 50)

        self.assertEqual(plan, 0)
        self.assertEqual(deviation, 0)
        self.assertFalse(is_delayed)

    def test_calculate_progress_deviation_with_custom_date(self):
        """测试自定义日期计算"""
        work_order = Mock()
        work_order.plan_start_date = date(2024, 1, 1)
        work_order.plan_end_date = date(2024, 1, 11)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        # 2024-01-06 是第5天，计划进度50%
        plan, deviation, is_delayed = self.service.calculate_progress_deviation(
            1, 60, date(2024, 1, 6)
        )

        self.assertEqual(plan, 50)
        self.assertEqual(deviation, 10)

    def test_calculate_planned_progress_before_start(self):
        """测试计划开始前进度为0"""
        work_order = Mock()
        work_order.plan_start_date = self.today + timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=10)

        progress = self.service._calculate_planned_progress(work_order, self.today)

        self.assertEqual(progress, 0)

    def test_calculate_planned_progress_after_end(self):
        """测试计划结束后进度为100"""
        work_order = Mock()
        work_order.plan_start_date = self.today - timedelta(days=10)
        work_order.plan_end_date = self.today - timedelta(days=5)

        progress = self.service._calculate_planned_progress(work_order, self.today)

        self.assertEqual(progress, 100)

    def test_calculate_planned_progress_no_dates(self):
        """测试没有计划日期"""
        work_order = Mock()
        work_order.plan_start_date = None
        work_order.plan_end_date = None

        progress = self.service._calculate_planned_progress(work_order, self.today)

        self.assertEqual(progress, 0)

    def test_calculate_planned_progress_same_day(self):
        """测试开始和结束同一天（边界条件）"""
        work_order = Mock()
        work_order.plan_start_date = self.today
        work_order.plan_end_date = self.today

        progress = self.service._calculate_planned_progress(work_order, self.today)

        self.assertEqual(progress, 100)

    def test_calculate_deviation_percentage_normal(self):
        """测试偏差百分比计算"""
        result = self.service.calculate_deviation_percentage(10, 50)

        self.assertEqual(result, Decimal('20'))

    def test_calculate_deviation_percentage_zero_plan(self):
        """测试计划进度为0的情况"""
        result = self.service.calculate_deviation_percentage(10, 0)

        self.assertEqual(result, Decimal('0'))

    # ==================== 核心算法2: 瓶颈工位识别算法测试 ====================

    def test_identify_bottlenecks_normal(self):
        """测试正常瓶颈识别"""
        # Mock工位状态和工位
        ws_status = Mock()
        ws_status.workstation_id = 1
        ws_status.capacity_utilization = Decimal('95')
        ws_status.work_hours_today = Decimal('7.6')
        ws_status.idle_hours_today = Decimal('0.4')
        ws_status.alert_count = 2

        workstation = Mock()
        workstation.id = 1
        workstation.workstation_code = 'WS001'
        workstation.workstation_name = '焊接工位1'

        # Mock查询结果
        query_mock = self.db.query.return_value
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [(ws_status, workstation)]

        # Mock工单统计
        self.db.query.return_value.filter.return_value.scalar.side_effect = [2, 3]

        bottlenecks = self.service.identify_bottlenecks()

        self.assertEqual(len(bottlenecks), 1)
        self.assertEqual(bottlenecks[0]['workstation_id'], 1)
        self.assertEqual(bottlenecks[0]['bottleneck_level'], 2)
        self.assertEqual(bottlenecks[0]['current_work_order_count'], 2)
        self.assertEqual(bottlenecks[0]['pending_work_order_count'], 3)

    def test_identify_bottlenecks_with_workshop_filter(self):
        """测试按车间筛选瓶颈"""
        query_mock = self.db.query.return_value
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        self.service.identify_bottlenecks(workshop_id=1)

        # 验证过滤条件被调用
        self.assertTrue(query_mock.filter.called)

    def test_identify_bottlenecks_min_level_filter(self):
        """测试最小瓶颈等级过滤"""
        ws_status = Mock()
        ws_status.workstation_id = 1
        ws_status.capacity_utilization = Decimal('92')

        workstation = Mock()
        workstation.id = 1
        workstation.workstation_code = 'WS001'
        workstation.workstation_name = '工位1'

        query_mock = self.db.query.return_value
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [(ws_status, workstation)]

        self.db.query.return_value.filter.return_value.scalar.side_effect = [1, 0]

        # 最小等级为2，但实际只有1级，应该过滤掉
        bottlenecks = self.service.identify_bottlenecks(min_level=2)

        self.assertEqual(len(bottlenecks), 0)

    def test_identify_bottlenecks_sorted_by_level(self):
        """测试瓶颈按等级和利用率排序"""
        # 创建多个瓶颈
        ws1_status = Mock()
        ws1_status.workstation_id = 1
        ws1_status.capacity_utilization = Decimal('99')

        ws2_status = Mock()
        ws2_status.workstation_id = 2
        ws2_status.capacity_utilization = Decimal('96')

        ws1 = Mock()
        ws1.id = 1
        ws1.workstation_code = 'WS001'
        ws1.workstation_name = '工位1'

        ws2 = Mock()
        ws2.id = 2
        ws2.workstation_code = 'WS002'
        ws2.workstation_name = '工位2'

        query_mock = self.db.query.return_value
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [(ws1_status, ws1), (ws2_status, ws2)]

        # ws1: 99%利用率+4个排队=3级
        # ws2: 96%利用率+1个排队=2级
        self.db.query.return_value.filter.return_value.scalar.side_effect = [1, 4, 1, 1]

        bottlenecks = self.service.identify_bottlenecks()

        # ws1应该排在前面
        self.assertEqual(len(bottlenecks), 2)
        self.assertEqual(bottlenecks[0]['workstation_id'], 1)
        self.assertEqual(bottlenecks[0]['bottleneck_level'], 3)

    def test_calculate_bottleneck_level_critical(self):
        """测试严重瓶颈等级（3级）"""
        ws_status = Mock()
        ws_status.capacity_utilization = Decimal('99')

        self.db.query.return_value.filter.return_value.scalar.return_value = 5

        level, reason = self.service._calculate_bottleneck_level(ws_status, 1)

        self.assertEqual(level, 3)
        self.assertIn('99.0%', reason)
        self.assertIn('5个', reason)

    def test_calculate_bottleneck_level_warning(self):
        """测试中度瓶颈等级（2级）"""
        ws_status = Mock()
        ws_status.capacity_utilization = Decimal('96')

        self.db.query.return_value.filter.return_value.scalar.return_value = 2

        level, reason = self.service._calculate_bottleneck_level(ws_status, 1)

        self.assertEqual(level, 2)

    def test_calculate_bottleneck_level_info(self):
        """测试轻度瓶颈等级（1级）"""
        ws_status = Mock()
        ws_status.capacity_utilization = Decimal('92')

        self.db.query.return_value.filter.return_value.scalar.return_value = 0

        level, reason = self.service._calculate_bottleneck_level(ws_status, 1)

        self.assertEqual(level, 1)

    def test_calculate_bottleneck_level_normal(self):
        """测试非瓶颈（0级）"""
        ws_status = Mock()
        ws_status.capacity_utilization = Decimal('85')

        self.db.query.return_value.filter.return_value.scalar.return_value = 0

        level, reason = self.service._calculate_bottleneck_level(ws_status, 1)

        self.assertEqual(level, 0)
        self.assertEqual(reason, '正常')

    # ==================== 核心算法3: 进度预警规则引擎测试 ====================

    def test_evaluate_alert_rules_delay_critical(self):
        """测试严重延期预警（偏差<-20%）"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 30
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 98
        work_order.standard_hours = None
        work_order.actual_hours = None
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        alerts = self.service.evaluate_alert_rules(1, 1)

        # 应该有严重延期预警（进度30% vs 计划50%）
        delay_alerts = [a for a in alerts if a.alert_type == 'DELAY']
        self.assertTrue(len(delay_alerts) > 0)
        self.assertEqual(delay_alerts[0].alert_level, 'CRITICAL')

    def test_evaluate_alert_rules_delay_warning(self):
        """测试延期预警（-20% < 偏差 < -10%）"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 38
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 98
        work_order.standard_hours = None
        work_order.actual_hours = None
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        alerts = self.service.evaluate_alert_rules(1, 1)

        delay_alerts = [a for a in alerts if a.alert_type == 'DELAY']
        self.assertTrue(len(delay_alerts) > 0)
        self.assertEqual(delay_alerts[0].alert_level, 'WARNING')

    def test_evaluate_alert_rules_bottleneck(self):
        """测试瓶颈预警"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 50
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 98
        work_order.standard_hours = None
        work_order.actual_hours = None
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        ws_status = Mock()
        ws_status.is_bottleneck = True
        ws_status.bottleneck_level = 3
        ws_status.capacity_utilization = Decimal('99')

        # Mock查询返回值列表
        self.db.query.return_value.filter.return_value.first.side_effect = [
            work_order,  # 第1次：获取工单
            work_order,  # 第2次：calculate_progress_deviation中获取工单
            ws_status    # 第3次：获取工位状态
        ]

        alerts = self.service.evaluate_alert_rules(1, 1)

        bottleneck_alerts = [a for a in alerts if a.alert_type == 'BOTTLENECK']
        self.assertTrue(len(bottleneck_alerts) > 0)
        self.assertEqual(bottleneck_alerts[0].alert_level, 'CRITICAL')

    def test_evaluate_alert_rules_quality_critical(self):
        """测试质量预警（合格率<90%为严重）"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 50
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 85  # 85%合格率
        work_order.standard_hours = None
        work_order.actual_hours = None
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        alerts = self.service.evaluate_alert_rules(1, 1)

        quality_alerts = [a for a in alerts if a.alert_type == 'QUALITY']
        self.assertTrue(len(quality_alerts) > 0)
        self.assertEqual(quality_alerts[0].alert_level, 'CRITICAL')

    def test_evaluate_alert_rules_quality_warning(self):
        """测试质量预警（90%<=合格率<95%为警告）"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 50
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 92  # 92%合格率
        work_order.standard_hours = None
        work_order.actual_hours = None
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        alerts = self.service.evaluate_alert_rules(1, 1)

        quality_alerts = [a for a in alerts if a.alert_type == 'QUALITY']
        self.assertTrue(len(quality_alerts) > 0)
        self.assertEqual(quality_alerts[0].alert_level, 'WARNING')

    def test_evaluate_alert_rules_efficiency(self):
        """测试效率预警（效率<80%）"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 50
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 98
        work_order.standard_hours = Decimal('8')
        work_order.actual_hours = Decimal('12')  # 效率66.7%
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        alerts = self.service.evaluate_alert_rules(1, 1)

        efficiency_alerts = [a for a in alerts if a.alert_type == 'EFFICIENCY']
        self.assertTrue(len(efficiency_alerts) > 0)
        self.assertEqual(efficiency_alerts[0].alert_level, 'WARNING')

    def test_evaluate_alert_rules_work_order_not_found(self):
        """测试工单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        alerts = self.service.evaluate_alert_rules(999, 1)

        self.assertEqual(len(alerts), 0)

    def test_evaluate_alert_rules_no_alerts(self):
        """测试无预警情况"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.progress = 50
        work_order.workstation_id = 1
        work_order.completed_qty = 100
        work_order.qualified_qty = 100  # 100%合格率
        work_order.standard_hours = Decimal('8')
        work_order.actual_hours = Decimal('7')  # 效率114%
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        self.db.query.return_value.filter.return_value.first.return_value = work_order

        alerts = self.service.evaluate_alert_rules(1, 1)

        self.assertEqual(len(alerts), 0)

    # ==================== 业务方法测试 ====================

    def test_create_progress_log_first_log(self):
        """测试创建第一条进度日志"""
        work_order = Mock()
        work_order.id = 1
        work_order.status = 'PENDING'
        work_order.progress = 0
        work_order.completed_qty = 0
        work_order.qualified_qty = 0
        work_order.defect_qty = 0
        work_order.actual_hours = Decimal('0')
        work_order.workstation_id = 1
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        log_data = ProductionProgressLogCreate(
            work_order_id=1,
            workstation_id=1,
            current_progress=20,
            completed_qty=20,
            qualified_qty=20,
            defect_qty=0,
            work_hours=Decimal('2'),
            status='IN_PROGRESS',
            note='开始生产'
        )

        # Mock查询
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [work_order, None]  # 工单存在，无历史日志
        filter_mock.order_by.return_value.first.return_value = None

        result = self.service.create_progress_log(log_data, 1)

        self.db.add.assert_called()
        self.db.commit.assert_called()

    def test_create_progress_log_with_previous(self):
        """测试创建有历史记录的进度日志"""
        work_order = Mock()
        work_order.id = 1
        work_order.status = 'IN_PROGRESS'
        work_order.progress = 20
        work_order.completed_qty = 20
        work_order.qualified_qty = 20
        work_order.defect_qty = 0
        work_order.actual_hours = Decimal('2')
        work_order.workstation_id = 1
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)

        last_log = Mock()
        last_log.current_progress = 20
        last_log.status = 'IN_PROGRESS'
        last_log.cumulative_hours = Decimal('2')

        log_data = ProductionProgressLogCreate(
            work_order_id=1,
            workstation_id=1,
            current_progress=50,
            completed_qty=50,
            qualified_qty=50,
            defect_qty=0,
            work_hours=Decimal('3'),
            status='IN_PROGRESS',
            note='进度更新'
        )

        # Mock查询
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [work_order, None]
        filter_mock.order_by.return_value.first.return_value = last_log

        result = self.service.create_progress_log(log_data, 1)

        self.db.add.assert_called()
        self.db.commit.assert_called()

    def test_create_progress_log_work_order_not_found(self):
        """测试工单不存在时抛出异常"""
        log_data = ProductionProgressLogCreate(
            work_order_id=999,
            workstation_id=1,
            current_progress=20,
            completed_qty=20,
            qualified_qty=20,
            defect_qty=0,
            status='IN_PROGRESS'
        )

        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.create_progress_log(log_data, 1)

        self.assertEqual(str(context.exception), '工单不存在')

    def test_update_workstation_status_new(self):
        """测试创建新工位状态"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.scalar.return_value = Decimal('7.5')

        self.service._update_workstation_status(1, 1)

        self.db.add.assert_called()

    def test_update_workstation_status_existing(self):
        """测试更新现有工位状态"""
        ws_status = Mock()
        ws_status.workstation_id = 1
        ws_status.planned_hours_today = Decimal('8')
        ws_status.work_hours_today = Decimal('0')

        self.db.query.return_value.filter.return_value.first.return_value = ws_status
        self.db.query.return_value.filter.return_value.scalar.return_value = Decimal('7.5')

        self.service._update_workstation_status(1, 1)

        self.assertEqual(ws_status.current_state, 'BUSY')
        self.assertEqual(ws_status.current_work_order_id, 1)

    def test_get_realtime_overview(self):
        """测试获取实时总览"""
        # Mock查询结果
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.side_effect = [100, 30, 5, 10, 20, 5, 8, 15, 3]
        query_mock.distinct.return_value.count.return_value = 10

        query_mock.scalar.side_effect = [
            Decimal('65'),  # 平均进度
            Decimal('85'),  # 平均产能利用率
            Decimal('92'),  # 平均效率
        ]

        overview = self.service.get_realtime_overview()

        self.assertEqual(overview.total_work_orders, 100)
        self.assertEqual(overview.in_progress, 30)
        self.assertEqual(overview.overall_progress, Decimal('65'))

    def test_get_work_order_timeline(self):
        """测试获取工单时间线"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.task_name = '测试任务'
        work_order.progress = 50
        work_order.status = 'IN_PROGRESS'
        work_order.plan_start_date = self.today
        work_order.plan_end_date = self.today + timedelta(days=10)
        work_order.actual_start_time = datetime.now()
        work_order.actual_end_time = None

        logs = [Mock(), Mock()]
        alerts = [Mock()]

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = work_order
        filter_mock.order_by.return_value.all.side_effect = [logs, alerts]

        timeline = self.service.get_work_order_timeline(1)

        self.assertIsNotNone(timeline)
        self.assertEqual(timeline.work_order_id, 1)
        self.assertEqual(len(timeline.timeline), 2)
        self.assertEqual(len(timeline.alerts), 1)

    def test_get_work_order_timeline_not_found(self):
        """测试工单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        timeline = self.service.get_work_order_timeline(999)

        self.assertIsNone(timeline)

    def test_get_workstation_realtime(self):
        """测试获取工位实时状态"""
        ws_status = Mock()
        ws_status.workstation_id = 1

        self.db.query.return_value.filter.return_value.first.return_value = ws_status

        result = self.service.get_workstation_realtime(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.workstation_id, 1)

    def test_get_progress_deviations(self):
        """测试获取进度偏差列表"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.task_name = '测试任务'
        work_order.progress = 30
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)
        work_order.actual_start_time = datetime.now() - timedelta(days=5)

        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [work_order]

        deviations = self.service.get_progress_deviations(only_delayed=True)

        self.assertTrue(len(deviations) > 0)
        self.assertEqual(deviations[0].work_order_id, 1)

    def test_get_progress_deviations_min_deviation_filter(self):
        """测试最小偏差过滤"""
        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = 'WO001'
        work_order.task_name = '测试任务'
        work_order.progress = 45  # 偏差仅-5%
        work_order.plan_start_date = self.today - timedelta(days=5)
        work_order.plan_end_date = self.today + timedelta(days=5)
        work_order.actual_start_time = datetime.now() - timedelta(days=5)

        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [work_order]

        # 最小偏差10%，应过滤掉偏差5%的工单
        deviations = self.service.get_progress_deviations(min_deviation=10)

        self.assertEqual(len(deviations), 0)

    def test_dismiss_alert(self):
        """测试关闭预警"""
        alert = Mock()
        alert.id = 1

        self.db.query.return_value.filter.return_value.first.return_value = alert

        result = self.service.dismiss_alert(1, 1, '已处理')

        self.assertTrue(result)
        self.assertEqual(alert.status, 'DISMISSED')
        self.assertIsNotNone(alert.dismissed_at)
        self.assertEqual(alert.dismissed_by, 1)
        self.assertEqual(alert.resolution_note, '已处理')
        self.db.commit.assert_called()

    def test_dismiss_alert_not_found(self):
        """测试关闭不存在的预警"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.dismiss_alert(999, 1)

        self.assertFalse(result)

    def test_get_alerts_with_filters(self):
        """测试带过滤条件获取预警"""
        alerts = [Mock(), Mock()]

        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = alerts

        result = self.service.get_alerts(
            work_order_id=1,
            workstation_id=1,
            alert_type='DELAY',
            alert_level='CRITICAL',
            status='ACTIVE'
        )

        self.assertEqual(len(result), 2)

    def test_get_alerts_default_active_only(self):
        """测试默认只返回活跃预警"""
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = []

        self.service.get_alerts()

        # 验证默认过滤ACTIVE状态
        filter_calls = query_mock.filter.call_args_list
        self.assertTrue(len(filter_calls) > 0)


if __name__ == '__main__':
    unittest.main()
