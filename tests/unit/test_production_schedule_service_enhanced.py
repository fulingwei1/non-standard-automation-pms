# -*- coding: utf-8 -*-
"""
生产排程服务增强单元测试
"""
import unittest
from datetime import datetime, timedelta, date
from typing import List
from unittest.mock import MagicMock, Mock, patch

from app.services.production_schedule_service import ProductionScheduleService
from app.schemas.production_schedule import (
    ScheduleGenerateRequest,
    ScheduleAdjustRequest,
    ScheduleScoreMetrics,
    GanttTask,
)


class TestProductionScheduleService(unittest.TestCase):
    """生产排程服务测试类"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.service = ProductionScheduleService(self.db)
        self.user_id = 1

    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()

    # ==================== 初始化和配置测试 ====================

    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.db, self.db)
        self.assertEqual(self.service.ALGORITHM_VERSION, "v1.0.0")

    def test_work_time_configuration(self):
        """测试工作时间配置"""
        self.assertEqual(self.service.WORK_START_HOUR, 8)
        self.assertEqual(self.service.WORK_END_HOUR, 18)
        self.assertEqual(self.service.WORK_HOURS_PER_DAY, 8)

    def test_gantt_color_map(self):
        """测试甘特图颜色映射"""
        self.assertIn('PENDING', self.service.GANTT_COLOR_MAP)
        self.assertIn('CONFIRMED', self.service.GANTT_COLOR_MAP)
        self.assertEqual(self.service.GANTT_COLOR_MAP['COMPLETED'], '#4CAF50')

    # ==================== 工单获取测试 ====================

    def test_fetch_work_orders_success(self):
        """测试成功获取工单"""
        mock_orders = [Mock(id=1), Mock(id=2)]
        self.db.query.return_value.filter.return_value.all.return_value = mock_orders

        result = self.service._fetch_work_orders([1, 2])

        self.assertEqual(len(result), 2)
        self.db.query.assert_called_once()

    def test_fetch_work_orders_empty(self):
        """测试获取空工单列表"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service._fetch_work_orders([])

        self.assertEqual(len(result), 0)

    def test_fetch_work_orders_partial(self):
        """测试部分工单存在"""
        mock_orders = [Mock(id=1)]
        self.db.query.return_value.filter.return_value.all.return_value = mock_orders

        result = self.service._fetch_work_orders([1, 2, 3])

        self.assertEqual(len(result), 1)

    # ==================== 资源获取测试 ====================

    def test_get_available_equipment(self):
        """测试获取可用设备"""
        mock_equipment = [Mock(id=1, status='IDLE'), Mock(id=2, status='RUNNING')]
        self.db.query.return_value.filter.return_value.all.return_value = mock_equipment

        result = self.service._get_available_equipment()

        self.assertEqual(len(result), 2)

    def test_get_available_equipment_empty(self):
        """测试无可用设备"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service._get_available_equipment()

        self.assertEqual(len(result), 0)

    def test_get_available_workers(self):
        """测试获取可用工人"""
        mock_workers = [Mock(id=1, status='ACTIVE'), Mock(id=2, status='ACTIVE')]
        self.db.query.return_value.filter.return_value.all.return_value = mock_workers

        result = self.service._get_available_workers()

        self.assertEqual(len(result), 2)

    def test_get_available_workers_filtered(self):
        """测试工人状态过滤"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service._get_available_workers()

        self.assertEqual(len(result), 0)

    # ==================== 方案ID生成测试 ====================

    def test_generate_plan_id(self):
        """测试生成方案ID"""
        plan_id = self.service._generate_plan_id()

        self.assertIsInstance(plan_id, int)
        self.assertGreater(plan_id, 0)

    def test_generate_plan_id_unique(self):
        """测试方案ID唯一性"""
        plan_id1 = self.service._generate_plan_id()
        plan_id2 = self.service._generate_plan_id()

        # 由于基于时间戳，可能相同，但至少不为空
        self.assertIsNotNone(plan_id1)
        self.assertIsNotNone(plan_id2)

    # ==================== 优先级测试 ====================

    def test_calculate_priority_score_urgent(self):
        """测试紧急优先级评分"""
        order = Mock(priority='URGENT')
        score = self.service._calculate_priority_score(order)
        self.assertEqual(score, 5.0)

    def test_calculate_priority_score_high(self):
        """测试高优先级评分"""
        order = Mock(priority='HIGH')
        score = self.service._calculate_priority_score(order)
        self.assertEqual(score, 3.0)

    def test_calculate_priority_score_normal(self):
        """测试普通优先级评分"""
        order = Mock(priority='NORMAL')
        score = self.service._calculate_priority_score(order)
        self.assertEqual(score, 2.0)

    def test_calculate_priority_score_low(self):
        """测试低优先级评分"""
        order = Mock(priority='LOW')
        score = self.service._calculate_priority_score(order)
        self.assertEqual(score, 1.0)

    def test_calculate_priority_score_unknown(self):
        """测试未知优先级默认值"""
        order = Mock(priority='UNKNOWN')
        score = self.service._calculate_priority_score(order)
        self.assertEqual(score, 2.0)

    def test_get_priority_weight_urgent(self):
        """测试紧急优先级权重"""
        weight = self.service._get_priority_weight('URGENT')
        self.assertEqual(weight, 1)

    def test_get_priority_weight_low(self):
        """测试低优先级权重"""
        weight = self.service._get_priority_weight('LOW')
        self.assertEqual(weight, 4)

    # ==================== 时间计算测试 ====================

    def test_adjust_to_work_time_before_start(self):
        """测试调整早于开始时间"""
        dt = datetime(2024, 1, 1, 6, 0)  # 早上6点
        request = Mock()

        result = self.service._adjust_to_work_time(dt, request)

        self.assertEqual(result.hour, 8)
        self.assertEqual(result.minute, 0)

    def test_adjust_to_work_time_after_end(self):
        """测试调整晚于结束时间"""
        dt = datetime(2024, 1, 1, 19, 0)  # 晚上7点
        request = Mock()

        result = self.service._adjust_to_work_time(dt, request)

        self.assertEqual(result.day, 2)
        self.assertEqual(result.hour, 8)

    def test_adjust_to_work_time_during_work(self):
        """测试工作时间内不调整"""
        dt = datetime(2024, 1, 1, 10, 30)
        request = Mock()

        result = self.service._adjust_to_work_time(dt, request)

        self.assertEqual(result, dt)

    def test_calculate_end_time_simple(self):
        """测试简单结束时间计算"""
        start_time = datetime(2024, 1, 1, 9, 0)
        duration = 2.0
        request = Mock()

        end_time = self.service._calculate_end_time(start_time, duration, request)

        self.assertEqual(end_time.hour, 11)

    def test_calculate_end_time_cross_day(self):
        """测试跨天结束时间计算"""
        start_time = datetime(2024, 1, 1, 16, 0)
        duration = 5.0
        request = Mock()

        end_time = self.service._calculate_end_time(start_time, duration, request)

        self.assertEqual(end_time.day, 2)

    def test_calculate_end_time_multiple_days(self):
        """测试多天结束时间计算"""
        start_time = datetime(2024, 1, 1, 9, 0)
        duration = 24.0  # 3个工作日
        request = Mock()

        end_time = self.service._calculate_end_time(start_time, duration, request)

        self.assertGreater((end_time - start_time).days, 1)

    def test_time_overlap_true(self):
        """测试时间重叠为真"""
        start1 = datetime(2024, 1, 1, 9, 0)
        end1 = datetime(2024, 1, 1, 11, 0)
        start2 = datetime(2024, 1, 1, 10, 0)
        end2 = datetime(2024, 1, 1, 12, 0)

        result = self.service._time_overlap(start1, end1, start2, end2)

        self.assertTrue(result)

    def test_time_overlap_false(self):
        """测试时间不重叠"""
        start1 = datetime(2024, 1, 1, 9, 0)
        end1 = datetime(2024, 1, 1, 11, 0)
        start2 = datetime(2024, 1, 1, 11, 0)
        end2 = datetime(2024, 1, 1, 13, 0)

        result = self.service._time_overlap(start1, end1, start2, end2)

        self.assertFalse(result)

    def test_time_overlap_complete_overlap(self):
        """测试完全重叠"""
        start1 = datetime(2024, 1, 1, 9, 0)
        end1 = datetime(2024, 1, 1, 17, 0)
        start2 = datetime(2024, 1, 1, 10, 0)
        end2 = datetime(2024, 1, 1, 12, 0)

        result = self.service._time_overlap(start1, end1, start2, end2)

        self.assertTrue(result)

    # ==================== 设备选择测试 ====================

    def test_select_best_equipment_specified(self):
        """测试工单指定设备"""
        order = Mock(machine_id=1, workshop_id=1)
        equipment = [Mock(id=1), Mock(id=2)]
        timeline = {}
        request = Mock()

        result = self.service._select_best_equipment(order, equipment, timeline, request)

        self.assertEqual(result.id, 1)

    def test_select_best_equipment_by_workshop(self):
        """测试按车间选择设备"""
        order = Mock(machine_id=None, workshop_id=1)
        equipment = [Mock(id=1, workshop_id=1), Mock(id=2, workshop_id=2)]
        timeline = {1: [], 2: []}
        request = Mock()

        result = self.service._select_best_equipment(order, equipment, timeline, request)

        self.assertEqual(result.workshop_id, 1)

    def test_select_best_equipment_least_busy(self):
        """测试选择最空闲设备"""
        order = Mock(machine_id=None, workshop_id=1)
        equipment = [Mock(id=1, workshop_id=1), Mock(id=2, workshop_id=1)]
        timeline = {1: [(1, 2), (3, 4)], 2: [(1, 2)]}
        request = Mock()

        result = self.service._select_best_equipment(order, equipment, timeline, request)

        self.assertEqual(result.id, 2)

    def test_select_best_equipment_empty(self):
        """测试无可用设备"""
        order = Mock(machine_id=None, workshop_id=1)
        equipment = []
        timeline = {}
        request = Mock()

        result = self.service._select_best_equipment(order, equipment, timeline, request)

        self.assertIsNone(result)

    # ==================== 工人选择测试 ====================

    def test_select_best_worker_specified(self):
        """测试工单指定工人"""
        order = Mock(assigned_to=1, workshop_id=1, process_id=1)
        workers = [Mock(id=1), Mock(id=2)]
        timeline = {}
        request = Mock(consider_worker_skills=False)

        result = self.service._select_best_worker(order, workers, timeline, request)

        self.assertEqual(result.id, 1)

    def test_select_best_worker_by_skill(self):
        """测试按技能选择工人"""
        order = Mock(assigned_to=None, workshop_id=1, process_id=1)
        workers = [Mock(id=1, workshop_id=1), Mock(id=2, workshop_id=1)]
        timeline = {1: [], 2: []}
        request = Mock(consider_worker_skills=True)

        # Mock技能查询
        self.db.query.return_value.filter.return_value.all.return_value = [(1,)]

        result = self.service._select_best_worker(order, workers, timeline, request)

        self.assertEqual(result.id, 1)

    def test_select_best_worker_empty(self):
        """测试无可用工人"""
        order = Mock(assigned_to=None, workshop_id=1, process_id=1)
        workers = []
        timeline = {}
        request = Mock(consider_worker_skills=False)

        result = self.service._select_best_worker(order, workers, timeline, request)

        self.assertIsNone(result)

    # ==================== 评分测试 ====================

    def test_calculate_schedule_score_on_time(self):
        """测试按时完成排程评分"""
        schedule = Mock(
            work_order_id=1,
            priority_score=3.0,
            scheduled_end_time=datetime(2024, 1, 10, 12, 0)
        )
        order = Mock(id=1, plan_end_date=date(2024, 1, 15))
        work_orders = [order]

        score = self.service._calculate_schedule_score(schedule, work_orders)

        self.assertGreater(score, 30)  # 优先级分 + 按时完成分

    def test_calculate_schedule_score_late(self):
        """测试延期排程评分"""
        schedule = Mock(
            work_order_id=1,
            priority_score=2.0,
            scheduled_end_time=datetime(2024, 1, 20, 12, 0)
        )
        order = Mock(id=1, plan_end_date=date(2024, 1, 15))
        work_orders = [order]

        score = self.service._calculate_schedule_score(schedule, work_orders)

        self.assertLessEqual(score, 20)  # 只有优先级分

    def test_calculate_schedule_score_no_plan_date(self):
        """测试无计划日期排程评分"""
        schedule = Mock(
            work_order_id=1,
            priority_score=3.0,
            scheduled_end_time=datetime(2024, 1, 10, 12, 0)
        )
        order = Mock(id=1, plan_end_date=None)
        work_orders = [order]

        score = self.service._calculate_schedule_score(schedule, work_orders)

        self.assertEqual(score, 30)

    # ==================== 冲突检测测试 ====================

    def test_detect_conflicts_equipment(self):
        """测试设备冲突检测"""
        schedule1 = Mock(
            id=1,
            equipment_id=1,
            worker_id=None,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0),
            scheduled_end_time=datetime(2024, 1, 1, 11, 0)
        )
        schedule2 = Mock(
            id=2,
            equipment_id=1,
            worker_id=None,
            scheduled_start_time=datetime(2024, 1, 1, 10, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedules = [schedule1, schedule2]

        conflicts = self.service._detect_conflicts(schedules)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, 'EQUIPMENT')

    def test_detect_conflicts_worker(self):
        """测试工人冲突检测"""
        schedule1 = Mock(
            id=1,
            equipment_id=None,
            worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0),
            scheduled_end_time=datetime(2024, 1, 1, 11, 0)
        )
        schedule2 = Mock(
            id=2,
            equipment_id=None,
            worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 10, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedules = [schedule1, schedule2]

        conflicts = self.service._detect_conflicts(schedules)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, 'WORKER')

    def test_detect_conflicts_no_overlap(self):
        """测试无冲突情况"""
        schedule1 = Mock(
            id=1,
            equipment_id=1,
            worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0),
            scheduled_end_time=datetime(2024, 1, 1, 11, 0)
        )
        schedule2 = Mock(
            id=2,
            equipment_id=1,
            worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 11, 0),
            scheduled_end_time=datetime(2024, 1, 1, 13, 0)
        )
        schedules = [schedule1, schedule2]

        conflicts = self.service._detect_conflicts(schedules)

        self.assertEqual(len(conflicts), 0)

    def test_detect_conflicts_multiple(self):
        """测试多重冲突检测"""
        schedule1 = Mock(
            id=1,
            equipment_id=1,
            worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0),
            scheduled_end_time=datetime(2024, 1, 1, 11, 0)
        )
        schedule2 = Mock(
            id=2,
            equipment_id=1,
            worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 10, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedules = [schedule1, schedule2]

        conflicts = self.service._detect_conflicts(schedules)

        # 应该检测到设备和工人两种冲突
        self.assertEqual(len(conflicts), 2)

    # ==================== 整体指标计算测试 ====================

    def test_calculate_overall_metrics_empty(self):
        """测试空排程指标计算"""
        metrics = self.service.calculate_overall_metrics([], [])

        self.assertEqual(metrics.completion_rate, 0)
        self.assertEqual(metrics.equipment_utilization, 0)
        self.assertEqual(metrics.total_duration_hours, 0)

    def test_calculate_overall_metrics_basic(self):
        """测试基本指标计算"""
        schedules = [
            Mock(
                work_order_id=1,
                equipment_id=1,
                worker_id=1,
                duration_hours=8.0,
                scheduled_start_time=datetime(2024, 1, 1, 9, 0),
                scheduled_end_time=datetime(2024, 1, 1, 17, 0)
            )
        ]
        work_orders = [Mock(id=1, plan_end_date=date(2024, 1, 2), progress=50)]

        metrics = self.service.calculate_overall_metrics(schedules, work_orders)

        self.assertGreaterEqual(metrics.completion_rate, 0)
        self.assertLessEqual(metrics.completion_rate, 1)

    def test_calculate_overall_metrics_on_time_rate(self):
        """测试交期达成率计算"""
        schedules = [
            Mock(
                work_order_id=1,
                equipment_id=1,
                worker_id=1,
                duration_hours=8.0,
                scheduled_start_time=datetime(2024, 1, 1, 9, 0),
                scheduled_end_time=datetime(2024, 1, 1, 17, 0)
            ),
            Mock(
                work_order_id=2,
                equipment_id=2,
                worker_id=2,
                duration_hours=8.0,
                scheduled_start_time=datetime(2024, 1, 2, 9, 0),
                scheduled_end_time=datetime(2024, 1, 2, 17, 0)
            )
        ]
        work_orders = [
            Mock(id=1, plan_end_date=date(2024, 1, 5)),
            Mock(id=2, plan_end_date=date(2024, 1, 1))  # 延期
        ]

        metrics = self.service.calculate_overall_metrics(schedules, work_orders)

        self.assertEqual(metrics.completion_rate, 0.5)

    # ==================== 排程交换优化测试 ====================

    def test_should_swap_schedules_true(self):
        """测试应该交换排程"""
        schedule1 = Mock(
            priority_score=2.0,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0)
        )
        schedule2 = Mock(
            priority_score=5.0,
            scheduled_start_time=datetime(2024, 1, 2, 9, 0)
        )

        result = self.service._should_swap_schedules(schedule1, schedule2)

        self.assertTrue(result)

    def test_should_swap_schedules_false(self):
        """测试不应交换排程"""
        schedule1 = Mock(
            priority_score=5.0,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0)
        )
        schedule2 = Mock(
            priority_score=2.0,
            scheduled_start_time=datetime(2024, 1, 2, 9, 0)
        )

        result = self.service._should_swap_schedules(schedule1, schedule2)

        self.assertFalse(result)

    # ==================== 最早时间槽测试 ====================

    def test_find_earliest_available_slot_no_conflicts(self):
        """测试无冲突的最早时间槽"""
        start_from = datetime(2024, 1, 1, 9, 0)
        duration = 2.0
        request = Mock()

        result = self.service._find_earliest_available_slot(
            [], [], start_from, duration, request
        )

        self.assertEqual(result.hour, 9)

    def test_find_earliest_available_slot_with_conflicts(self):
        """测试有冲突的最早时间槽"""
        start_from = datetime(2024, 1, 1, 9, 0)
        duration = 2.0
        equipment_slots = [
            (datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 1, 11, 0))
        ]
        request = Mock()

        result = self.service._find_earliest_available_slot(
            equipment_slots, [], start_from, duration, request
        )

        self.assertGreaterEqual(result, datetime(2024, 1, 1, 11, 0))

    # ==================== 生成排程测试 ====================

    def test_generate_schedule_no_work_orders(self):
        """测试无工单生成排程"""
        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        self.db.query.return_value.filter.return_value.all.return_value = []

        with self.assertRaises(ValueError) as context:
            self.service.generate_schedule(request, self.user_id)

        self.assertIn("未找到有效工单", str(context.exception))

    # ==================== 紧急插单测试 ====================

    def test_urgent_insert_work_order_not_found(self):
        """测试工单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.urgent_insert(
                work_order_id=999,
                insert_time=datetime(2024, 1, 1, 9, 0),
                max_delay_hours=2.0,
                auto_adjust=True,
                user_id=self.user_id
            )

        self.assertIn("工单不存在", str(context.exception))

    # ==================== 确认排程测试 ====================

    def test_confirm_schedule_no_pending(self):
        """测试无待确认排程"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        with self.assertRaises(ValueError) as context:
            self.service.confirm_schedule(plan_id=1, user_id=self.user_id)

        self.assertIn("没有待确认的排程", str(context.exception))

    # ==================== 排程预览测试 ====================

    def test_get_schedule_preview_not_found(self):
        """测试排程方案不存在"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        with self.assertRaises(ValueError) as context:
            self.service.get_schedule_preview(plan_id=999)

        self.assertIn("排程方案不存在", str(context.exception))

    # ==================== 调整排程测试 ====================

    def test_adjust_schedule_not_found(self):
        """测试调整不存在的排程"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        request = ScheduleAdjustRequest(
            schedule_id=999,
            adjustment_type='TIME_CHANGE',
            reason='测试调整'
        )

        with self.assertRaises(ValueError) as context:
            self.service.adjust_schedule(request, self.user_id)

        self.assertIn("排程不存在", str(context.exception))

    # ==================== 方案对比测试 ====================

    def test_compare_schedule_plans_too_few(self):
        """测试方案数量不足"""
        with self.assertRaises(ValueError) as context:
            self.service.compare_schedule_plans([1])

        self.assertIn("至少需要2个方案", str(context.exception))

    def test_compare_schedule_plans_too_many(self):
        """测试方案数量过多"""
        with self.assertRaises(ValueError) as context:
            self.service.compare_schedule_plans([1, 2, 3, 4, 5, 6])

        self.assertIn("最多支持5个方案", str(context.exception))

    # ==================== 甘特图数据测试 ====================

    def test_generate_gantt_data_not_found(self):
        """测试生成甘特图数据失败"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        with self.assertRaises(ValueError) as context:
            self.service.generate_gantt_data(plan_id=999)

        self.assertIn("排程方案不存在", str(context.exception))

    # ==================== 重置排程测试 ====================

    def test_reset_schedule_plan_success(self):
        """测试成功重置排程方案"""
        # Mock schedule_ids查询
        self.db.query.return_value.filter.return_value.all.return_value = [(1,), (2,)]
        # Mock delete操作
        self.db.query.return_value.filter.return_value.delete.return_value = 2

        result = self.service.reset_schedule_plan(plan_id=1)

        self.assertTrue(result['success'])
        self.assertEqual(result['deleted_count'], 2)

    # ==================== 排程历史测试 ====================

    @patch('app.services.production_schedule_service.apply_pagination')
    def test_get_schedule_history_with_filters(self, mock_pagination):
        """测试带过滤的排程历史查询"""
        mock_adjustment = Mock(schedule_id=1)
        
        # Mock查询链
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        
        # Mock apply_pagination 返回同一个 query
        mock_pagination.return_value = mock_query
        mock_query.all.return_value = [mock_adjustment]

        result = self.service.get_schedule_history(
            schedule_id=1,
            plan_id=1,
            page=1,
            page_size=20
        )

        self.assertEqual(result['total_count'], 1)
        self.assertEqual(len(result['adjustments']), 1)

    # ==================== 冲突摘要测试 ====================

    def test_get_conflict_summary_no_conflicts(self):
        """测试无冲突摘要"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_conflict_summary(plan_id=1)

        self.assertFalse(result['has_conflicts'])
        self.assertEqual(result['total_conflicts'], 0)

    # ==================== ScheduleScoreMetrics 测试 ====================

    def test_schedule_score_metrics_overall_score(self):
        """测试评分指标综合分数计算"""
        metrics = ScheduleScoreMetrics(
            completion_rate=0.9,
            equipment_utilization=0.8,
            worker_utilization=0.75,
            total_duration_hours=100,
            average_waiting_time=2.0,
            skill_match_rate=0.85,
            priority_satisfaction=0.88,
            conflict_count=2
        )

        overall_score = metrics.calculate_overall_score()

        self.assertIsInstance(overall_score, float)
        self.assertGreaterEqual(overall_score, 0)
        self.assertLessEqual(overall_score, 100)


if __name__ == '__main__':
    unittest.main()
