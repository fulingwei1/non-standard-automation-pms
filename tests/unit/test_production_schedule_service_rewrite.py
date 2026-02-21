# -*- coding: utf-8 -*-
"""
生产排程服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta, date
from typing import List

from app.services.production_schedule_service import ProductionScheduleService
from app.models.production import (
    Equipment,
    ProductionSchedule,
    ProductionResourceConflict,
    ScheduleAdjustmentLog,
    Worker,
    WorkerSkill,
    WorkOrder,
)
from app.schemas.production_schedule import (
    ScheduleGenerateRequest,
    ScheduleAdjustRequest,
)


class TestProductionScheduleServiceCore(unittest.TestCase):
    """测试核心排程方法"""

    def setUp(self):
        """初始化测试"""
        self.db = MagicMock()
        
        # Mock db.add to auto-populate required fields
        def mock_add(obj):
            if hasattr(obj, '__tablename__') and obj.__tablename__ == 'production_schedules':
                # Auto-populate ORM fields that would normally be set by the database
                if not hasattr(obj, 'id') or obj.id is None:
                    obj.id = 1
                if not hasattr(obj, 'created_at') or obj.created_at is None:
                    obj.created_at = datetime.now()
                if not hasattr(obj, 'updated_at') or obj.updated_at is None:
                    obj.updated_at = datetime.now()
                if not hasattr(obj, 'is_manually_adjusted') or obj.is_manually_adjusted is None:
                    obj.is_manually_adjusted = False
        
        self.db.add.side_effect = mock_add
        self.service = ProductionScheduleService(self.db)
        self.user_id = 1

    def _create_mock_work_order(self, id, work_order_no, priority="NORMAL", plan_end_date=None,
                                standard_hours=8, workshop_id=1, process_id=1,
                                machine_id=None, assigned_to=None, task_name="测试任务"):
        """创建模拟工单"""
        order = MagicMock(spec=WorkOrder)
        order.id = id
        order.work_order_no = work_order_no
        order.priority = priority
        order.plan_end_date = plan_end_date
        order.standard_hours = standard_hours
        order.workshop_id = workshop_id
        order.process_id = process_id
        order.machine_id = machine_id
        order.assigned_to = assigned_to
        order.task_name = task_name
        order.progress = 0
        return order

    def _create_mock_equipment(self, id, workshop_id=1, is_active=True, status="IDLE"):
        """创建模拟设备"""
        eq = MagicMock(spec=Equipment)
        eq.id = id
        eq.workshop_id = workshop_id
        eq.is_active = is_active
        eq.status = status
        return eq

    def _create_mock_worker(self, id, workshop_id=1, is_active=True, status="ACTIVE"):
        """创建模拟工人"""
        worker = MagicMock(spec=Worker)
        worker.id = id
        worker.workshop_id = workshop_id
        worker.is_active = is_active
        worker.status = status
        return worker

    def _create_mock_schedule(self, id, work_order_id, equipment_id=None, worker_id=None,
                             scheduled_start_time=None, scheduled_end_time=None,
                             duration_hours=8, status="PENDING", schedule_plan_id=1):
        """创建模拟排程"""
        schedule = MagicMock(spec=ProductionSchedule)
        schedule.id = id
        schedule.work_order_id = work_order_id
        schedule.equipment_id = equipment_id
        schedule.worker_id = worker_id
        schedule.scheduled_start_time = scheduled_start_time or datetime.now()
        schedule.scheduled_end_time = scheduled_end_time or (datetime.now() + timedelta(hours=duration_hours))
        schedule.duration_hours = duration_hours
        schedule.status = status
        schedule.schedule_plan_id = schedule_plan_id
        schedule.priority_score = 2.0
        schedule.workshop_id = 1
        schedule.process_id = 1
        # Pydantic验证需要的字段
        schedule.is_manually_adjusted = False
        schedule.created_at = datetime.now()
        schedule.updated_at = datetime.now()
        schedule.remark = ""
        schedule.algorithm_version = "v1.0"
        schedule.constraints_met = {}
        schedule.adjustment_reason = ""
        return schedule

    # ==================== 辅助方法测试 ====================

    def test_get_priority_weight(self):
        """测试优先级权重计算"""
        self.assertEqual(self.service._get_priority_weight("URGENT"), 1)
        self.assertEqual(self.service._get_priority_weight("HIGH"), 2)
        self.assertEqual(self.service._get_priority_weight("NORMAL"), 3)
        self.assertEqual(self.service._get_priority_weight("LOW"), 4)
        self.assertEqual(self.service._get_priority_weight("UNKNOWN"), 3)  # 默认

    def test_calculate_priority_score(self):
        """测试优先级评分"""
        order_urgent = self._create_mock_work_order(1, "WO001", priority="URGENT")
        order_high = self._create_mock_work_order(2, "WO002", priority="HIGH")
        order_normal = self._create_mock_work_order(3, "WO003", priority="NORMAL")
        order_low = self._create_mock_work_order(4, "WO004", priority="LOW")

        self.assertEqual(self.service._calculate_priority_score(order_urgent), 5.0)
        self.assertEqual(self.service._calculate_priority_score(order_high), 3.0)
        self.assertEqual(self.service._calculate_priority_score(order_normal), 2.0)
        self.assertEqual(self.service._calculate_priority_score(order_low), 1.0)

    def test_generate_plan_id(self):
        """测试生成排程方案ID"""
        plan_id = self.service._generate_plan_id()
        self.assertIsInstance(plan_id, int)
        self.assertGreater(plan_id, 0)

    def test_time_overlap(self):
        """测试时间重叠检测"""
        start1 = datetime(2024, 1, 1, 8, 0)
        end1 = datetime(2024, 1, 1, 12, 0)
        start2 = datetime(2024, 1, 1, 10, 0)
        end2 = datetime(2024, 1, 1, 14, 0)
        start3 = datetime(2024, 1, 1, 13, 0)
        end3 = datetime(2024, 1, 1, 17, 0)

        # 重叠
        self.assertTrue(self.service._time_overlap(start1, end1, start2, end2))
        # 不重叠
        self.assertFalse(self.service._time_overlap(start1, end1, start3, end3))

    def test_adjust_to_work_time_before_work(self):
        """测试调整到工作时间-上班前"""
        dt = datetime(2024, 1, 1, 6, 0)  # 06:00
        result = self.service._adjust_to_work_time(dt, MagicMock())
        self.assertEqual(result.hour, self.service.WORK_START_HOUR)
        self.assertEqual(result.minute, 0)

    def test_adjust_to_work_time_after_work(self):
        """测试调整到工作时间-下班后"""
        dt = datetime(2024, 1, 1, 19, 0)  # 19:00
        result = self.service._adjust_to_work_time(dt, MagicMock())
        self.assertEqual(result.hour, self.service.WORK_START_HOUR)
        self.assertEqual(result.day, 2)  # 第二天

    def test_adjust_to_work_time_during_work(self):
        """测试调整到工作时间-工作时段"""
        dt = datetime(2024, 1, 1, 10, 30)  # 10:30
        result = self.service._adjust_to_work_time(dt, MagicMock())
        self.assertEqual(result, dt)  # 不调整

    def test_calculate_end_time_same_day(self):
        """测试计算结束时间-同一天"""
        start_time = datetime(2024, 1, 1, 8, 0)
        duration_hours = 4.0
        result = self.service._calculate_end_time(start_time, duration_hours, MagicMock())
        expected = datetime(2024, 1, 1, 12, 0)
        self.assertEqual(result, expected)

    def test_calculate_end_time_cross_day(self):
        """测试计算结束时间-跨天"""
        start_time = datetime(2024, 1, 1, 16, 0)  # 16:00开始
        duration_hours = 6.0  # 需要6小时
        result = self.service._calculate_end_time(start_time, duration_hours, MagicMock())
        # 当天剩余2小时，第二天需要4小时
        expected = datetime(2024, 1, 2, 12, 0)  # 第二天12:00
        self.assertEqual(result, expected)

    def test_calculate_end_time_after_work_hours(self):
        """测试计算结束时间-下班后开始"""
        start_time = datetime(2024, 1, 1, 19, 0)  # 19:00
        duration_hours = 4.0
        result = self.service._calculate_end_time(start_time, duration_hours, MagicMock())
        # 应该跳到第二天8:00开始
        expected = datetime(2024, 1, 2, 12, 0)
        self.assertEqual(result, expected)

    # ==================== 资源获取测试 ====================

    def test_fetch_work_orders(self):
        """测试获取工单列表"""
        order1 = self._create_mock_work_order(1, "WO001")
        order2 = self._create_mock_work_order(2, "WO002")
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [order1, order2]
        self.db.query.return_value = mock_query

        result = self.service._fetch_work_orders([1, 2])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)

    def test_get_available_equipment(self):
        """测试获取可用设备"""
        eq1 = self._create_mock_equipment(1, status="IDLE")
        eq2 = self._create_mock_equipment(2, status="RUNNING")
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [eq1, eq2]
        self.db.query.return_value = mock_query

        result = self.service._get_available_equipment()
        
        self.assertEqual(len(result), 2)

    def test_get_available_workers(self):
        """测试获取可用工人"""
        worker1 = self._create_mock_worker(1)
        worker2 = self._create_mock_worker(2)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [worker1, worker2]
        self.db.query.return_value = mock_query

        result = self.service._get_available_workers()
        
        self.assertEqual(len(result), 2)

    # ==================== 资源选择测试 ====================

    def test_select_best_equipment_with_specific_machine(self):
        """测试选择设备-工单指定设备"""
        eq1 = self._create_mock_equipment(1)
        eq2 = self._create_mock_equipment(2)
        equipment = [eq1, eq2]
        
        order = self._create_mock_work_order(1, "WO001", machine_id=2)
        
        result = self.service._select_best_equipment(order, equipment, {}, MagicMock())
        self.assertEqual(result.id, 2)

    def test_select_best_equipment_by_workshop(self):
        """测试选择设备-按车间筛选"""
        eq1 = self._create_mock_equipment(1, workshop_id=1)
        eq2 = self._create_mock_equipment(2, workshop_id=2)
        equipment = [eq1, eq2]
        
        order = self._create_mock_work_order(1, "WO001", workshop_id=2)
        
        result = self.service._select_best_equipment(order, equipment, {}, MagicMock())
        self.assertEqual(result.id, 2)

    def test_select_best_equipment_least_busy(self):
        """测试选择设备-选最空闲的"""
        eq1 = self._create_mock_equipment(1)
        eq2 = self._create_mock_equipment(2)
        equipment = [eq1, eq2]
        
        # eq1有2个排程，eq2有1个排程
        timeline = {
            1: [(datetime.now(), datetime.now()), (datetime.now(), datetime.now())],
            2: [(datetime.now(), datetime.now())],
        }
        
        order = self._create_mock_work_order(1, "WO001")
        
        result = self.service._select_best_equipment(order, equipment, timeline, MagicMock())
        self.assertEqual(result.id, 2)  # 选择更空闲的eq2

    def test_select_best_equipment_empty_list(self):
        """测试选择设备-空列表"""
        order = self._create_mock_work_order(1, "WO001")
        result = self.service._select_best_equipment(order, [], {}, MagicMock())
        self.assertIsNone(result)

    def test_select_best_worker_with_specific_worker(self):
        """测试选择工人-工单指定工人"""
        worker1 = self._create_mock_worker(1)
        worker2 = self._create_mock_worker(2)
        workers = [worker1, worker2]
        
        order = self._create_mock_work_order(1, "WO001", assigned_to=2)
        
        result = self.service._select_best_worker(order, workers, {}, MagicMock())
        self.assertEqual(result.id, 2)

    def test_select_best_worker_with_skills(self):
        """测试选择工人-考虑技能"""
        worker1 = self._create_mock_worker(1, workshop_id=1)
        worker2 = self._create_mock_worker(2, workshop_id=1)
        workers = [worker1, worker2]
        
        # Mock技能查询
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [(1,)]  # worker1有该技能
        self.db.query.return_value = mock_query
        
        order = self._create_mock_work_order(1, "WO001", process_id=1, workshop_id=1)
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            consider_worker_skills=True
        )
        
        result = self.service._select_best_worker(order, workers, {}, request)
        self.assertEqual(result.id, 1)

    def test_select_best_worker_by_workshop(self):
        """测试选择工人-按车间筛选"""
        worker1 = self._create_mock_worker(1, workshop_id=1)
        worker2 = self._create_mock_worker(2, workshop_id=2)
        workers = [worker1, worker2]
        
        order = self._create_mock_work_order(1, "WO001", workshop_id=2)
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        result = self.service._select_best_worker(order, workers, {}, request)
        self.assertEqual(result.id, 2)

    def test_select_best_worker_empty_list(self):
        """测试选择工人-空列表"""
        order = self._create_mock_work_order(1, "WO001")
        result = self.service._select_best_worker(order, [], {}, MagicMock())
        self.assertIsNone(result)

    # ==================== 时间槽查找测试 ====================

    def test_find_earliest_available_slot_no_conflict(self):
        """测试查找最早时间槽-无冲突"""
        start_from = datetime(2024, 1, 1, 8, 0)
        duration_hours = 4.0
        
        result = self.service._find_earliest_available_slot(
            [], [], start_from, duration_hours, MagicMock()
        )
        
        self.assertEqual(result.hour, 8)
        self.assertEqual(result.minute, 0)

    def test_find_earliest_available_slot_with_conflict(self):
        """测试查找最早时间槽-有冲突"""
        start_from = datetime(2024, 1, 1, 8, 0)
        duration_hours = 4.0
        
        # 有一个冲突时间段
        equipment_slots = [
            (datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 1, 12, 0))
        ]
        
        result = self.service._find_earliest_available_slot(
            equipment_slots, [], start_from, duration_hours, MagicMock()
        )
        
        # 应该安排在12:00之后
        self.assertGreaterEqual(result, datetime(2024, 1, 1, 12, 0))

    # ==================== 冲突检测测试 ====================

    def test_detect_conflicts_no_conflict(self):
        """测试冲突检测-无冲突"""
        schedule1 = self._create_mock_schedule(
            1, 1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedule2 = self._create_mock_schedule(
            2, 2,
            scheduled_start_time=datetime(2024, 1, 1, 13, 0),
            scheduled_end_time=datetime(2024, 1, 1, 17, 0)
        )
        
        conflicts = self.service._detect_conflicts([schedule1, schedule2])
        self.assertEqual(len(conflicts), 0)

    def test_detect_conflicts_equipment_conflict(self):
        """测试冲突检测-设备冲突"""
        schedule1 = self._create_mock_schedule(
            1, 1, equipment_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedule2 = self._create_mock_schedule(
            2, 2, equipment_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 10, 0),
            scheduled_end_time=datetime(2024, 1, 1, 14, 0)
        )
        
        conflicts = self.service._detect_conflicts([schedule1, schedule2])
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, 'EQUIPMENT')
        self.assertEqual(conflicts[0].severity, 'HIGH')

    def test_detect_conflicts_worker_conflict(self):
        """测试冲突检测-工人冲突"""
        schedule1 = self._create_mock_schedule(
            1, 1, worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedule2 = self._create_mock_schedule(
            2, 2, worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 10, 0),
            scheduled_end_time=datetime(2024, 1, 1, 14, 0)
        )
        
        conflicts = self.service._detect_conflicts([schedule1, schedule2])
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, 'WORKER')
        self.assertEqual(conflicts[0].severity, 'MEDIUM')

    def test_detect_conflicts_multiple(self):
        """测试冲突检测-多个冲突"""
        schedule1 = self._create_mock_schedule(
            1, 1, equipment_id=1, worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedule2 = self._create_mock_schedule(
            2, 2, equipment_id=1, worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 10, 0),
            scheduled_end_time=datetime(2024, 1, 1, 14, 0)
        )
        
        conflicts = self.service._detect_conflicts([schedule1, schedule2])
        
        # 应该有2个冲突：设备+工人
        self.assertEqual(len(conflicts), 2)

    # ==================== 评分测试 ====================

    def test_calculate_schedule_score_on_time(self):
        """测试排程评分-按时完成"""
        order = self._create_mock_work_order(
            1, "WO001",
            priority="HIGH",
            plan_end_date=date(2024, 1, 10)
        )
        schedule = self._create_mock_schedule(
            1, 1,
            scheduled_end_time=datetime(2024, 1, 9, 17, 0)
        )
        schedule.priority_score = 3.0
        
        score = self.service._calculate_schedule_score(schedule, [order])
        
        # 基础分30 + 按时完成20 = 50
        self.assertEqual(score, 50)

    def test_calculate_schedule_score_delayed(self):
        """测试排程评分-延期"""
        order = self._create_mock_work_order(
            1, "WO001",
            priority="HIGH",
            plan_end_date=date(2024, 1, 5)
        )
        schedule = self._create_mock_schedule(
            1, 1,
            scheduled_end_time=datetime(2024, 1, 10, 17, 0)
        )
        schedule.priority_score = 3.0
        
        score = self.service._calculate_schedule_score(schedule, [order])
        
        # 只有基础分30
        self.assertEqual(score, 30)

    def test_calculate_overall_metrics_empty(self):
        """测试整体指标计算-空排程"""
        metrics = self.service.calculate_overall_metrics([], [])
        
        self.assertEqual(metrics.completion_rate, 0)
        self.assertEqual(metrics.equipment_utilization, 0)
        self.assertEqual(metrics.total_duration_hours, 0)

    def test_calculate_overall_metrics_normal(self):
        """测试整体指标计算-正常情况"""
        order1 = self._create_mock_work_order(1, "WO001", plan_end_date=date(2024, 1, 10))
        order2 = self._create_mock_work_order(2, "WO002", plan_end_date=date(2024, 1, 15))
        
        schedule1 = self._create_mock_schedule(
            1, 1, equipment_id=1, worker_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 16, 0),
            duration_hours=8
        )
        schedule2 = self._create_mock_schedule(
            2, 2, equipment_id=2, worker_id=2,
            scheduled_start_time=datetime(2024, 1, 2, 8, 0),
            scheduled_end_time=datetime(2024, 1, 2, 16, 0),
            duration_hours=8
        )
        
        metrics = self.service.calculate_overall_metrics([schedule1, schedule2], [order1, order2])
        
        self.assertEqual(metrics.completion_rate, 1.0)  # 都按时
        self.assertGreater(metrics.equipment_utilization, 0)
        self.assertEqual(metrics.total_duration_hours, 32.0)  # 1天8小时 + 跨天24小时

    # ==================== 贪心算法测试 ====================

    def test_greedy_scheduling_basic(self):
        """测试贪心算法-基础场景"""
        order = self._create_mock_work_order(1, "WO001", priority="HIGH")
        equipment = [self._create_mock_equipment(1)]
        workers = [self._create_mock_worker(1)]
        
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0)
        )
        
        schedules = self.service._greedy_scheduling(
            [order], equipment, workers, request, 1, self.user_id
        )
        
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].work_order_id, 1)
        self.assertEqual(schedules[0].equipment_id, 1)
        self.assertEqual(schedules[0].worker_id, 1)

    def test_greedy_scheduling_priority_order(self):
        """测试贪心算法-优先级排序"""
        order1 = self._create_mock_work_order(1, "WO001", priority="LOW")
        order2 = self._create_mock_work_order(2, "WO002", priority="URGENT")
        order3 = self._create_mock_work_order(3, "WO003", priority="HIGH")
        
        equipment = [self._create_mock_equipment(1)]
        workers = [self._create_mock_worker(1)]
        
        request = ScheduleGenerateRequest(
            work_orders=[1, 2, 3],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0)
        )
        
        schedules = self.service._greedy_scheduling(
            [order1, order2, order3], equipment, workers, request, 1, self.user_id
        )
        
        # 应该按优先级排序：URGENT -> HIGH -> LOW
        self.assertEqual(schedules[0].work_order_id, 2)  # URGENT
        self.assertEqual(schedules[1].work_order_id, 3)  # HIGH
        self.assertEqual(schedules[2].work_order_id, 1)  # LOW

    def test_greedy_scheduling_no_resources(self):
        """测试贪心算法-无资源"""
        order = self._create_mock_work_order(1, "WO001")
        
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0)
        )
        
        schedules = self.service._greedy_scheduling(
            [order], [], [], request, 1, self.user_id
        )
        
        # 应该也能创建排程，只是没有资源
        self.assertEqual(len(schedules), 1)
        self.assertIsNone(schedules[0].equipment_id)
        self.assertIsNone(schedules[0].worker_id)

    # ==================== 启发式算法测试 ====================

    def test_heuristic_scheduling(self):
        """测试启发式算法"""
        order = self._create_mock_work_order(1, "WO001", priority="HIGH")
        equipment = [self._create_mock_equipment(1)]
        workers = [self._create_mock_worker(1)]
        
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0)
        )
        
        schedules = self.service._heuristic_scheduling(
            [order], equipment, workers, request, 1, self.user_id
        )
        
        self.assertEqual(len(schedules), 1)

    def test_optimize_schedules(self):
        """测试排程优化"""
        schedule1 = self._create_mock_schedule(
            1, 1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedule1.priority_score = 5.0  # 高优先级但排在前面
        
        schedule2 = self._create_mock_schedule(
            2, 2,
            scheduled_start_time=datetime(2024, 1, 1, 13, 0),
            scheduled_end_time=datetime(2024, 1, 1, 17, 0)
        )
        schedule2.priority_score = 2.0  # 低优先级排在后面
        
        optimized = self.service._optimize_schedules([schedule1, schedule2], MagicMock())
        
        # 由于schedule1优先级高且已经在前面，不需要交换
        self.assertEqual(len(optimized), 2)

    def test_should_swap_schedules(self):
        """测试是否应该交换排程"""
        schedule1 = self._create_mock_schedule(
            1, 1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 12, 0)
        )
        schedule1.priority_score = 2.0  # 低优先级在前
        
        schedule2 = self._create_mock_schedule(
            2, 2,
            scheduled_start_time=datetime(2024, 1, 1, 13, 0),
            scheduled_end_time=datetime(2024, 1, 1, 17, 0)
        )
        schedule2.priority_score = 5.0  # 高优先级在后
        
        # 应该交换
        result = self.service._should_swap_schedules(schedule1, schedule2)
        self.assertTrue(result)

    # ==================== 生成排程主流程测试 ====================

    def test_generate_schedule_success(self):
        """测试生成排程-成功场景"""
        order = self._create_mock_work_order(1, "WO001", priority="HIGH")
        equipment = self._create_mock_equipment(1)
        worker = self._create_mock_worker(1)
        
        # Mock数据库查询
        mock_query_work_orders = MagicMock()
        mock_query_work_orders.filter.return_value.all.return_value = [order]
        
        mock_query_equipment = MagicMock()
        mock_query_equipment.filter.return_value.all.return_value = [equipment]
        
        mock_query_workers = MagicMock()
        mock_query_workers.filter.return_value.all.return_value = [worker]
        
        # Mock WorkerSkill查询
        mock_query_worker_skills = MagicMock()
        mock_query_worker_skills.filter.return_value.all.return_value = [(1,)]  # 返回元组列表
        
        self.db.query.side_effect = [
            mock_query_work_orders,
            mock_query_equipment,
            mock_query_workers,
            mock_query_worker_skills,  # 添加WorkerSkill查询
        ]
        
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0),
            algorithm="GREEDY"
        )
        
        plan_id, schedules, conflicts = self.service.generate_schedule(request, self.user_id)
        
        self.assertIsNotNone(plan_id)
        self.assertEqual(len(schedules), 1)
        self.db.add_all.assert_called()
        self.db.flush.assert_called()

    def test_generate_schedule_no_work_orders(self):
        """测试生成排程-无工单"""
        # Mock空工单列表
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        with self.assertRaises(ValueError) as context:
            self.service.generate_schedule(request, self.user_id)
        
        self.assertIn("未找到有效工单", str(context.exception))

    def test_generate_schedule_heuristic_algorithm(self):
        """测试生成排程-启发式算法"""
        order = self._create_mock_work_order(1, "WO001")
        equipment = self._create_mock_equipment(1)
        worker = self._create_mock_worker(1)
        
        # Mock数据库查询
        mock_query_work_orders = MagicMock()
        mock_query_work_orders.filter.return_value.all.return_value = [order]
        
        mock_query_equipment = MagicMock()
        mock_query_equipment.filter.return_value.all.return_value = [equipment]
        
        mock_query_workers = MagicMock()
        mock_query_workers.filter.return_value.all.return_value = [worker]
        
        # Mock WorkerSkill查询 - 启发式算法会调用_greedy_scheduling
        mock_query_worker_skills = MagicMock()
        mock_query_worker_skills.filter.return_value.all.return_value = [(1,)]
        
        self.db.query.side_effect = [
            mock_query_work_orders,
            mock_query_equipment,
            mock_query_workers,
            mock_query_worker_skills,  # 添加WorkerSkill查询
        ]
        
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0),
            algorithm="HEURISTIC"
        )
        
        plan_id, schedules, conflicts = self.service.generate_schedule(request, self.user_id)
        
        self.assertEqual(len(schedules), 1)

    def test_generate_and_evaluate_schedule(self):
        """测试生成并评估排程"""
        order = self._create_mock_work_order(1, "WO001", plan_end_date=date(2024, 1, 10))
        equipment = self._create_mock_equipment(1)
        worker = self._create_mock_worker(1)
        
        # Mock数据库查询
        mock_query_work_orders = MagicMock()
        mock_query_work_orders.filter.return_value.all.return_value = [order]
        
        mock_query_equipment = MagicMock()
        mock_query_equipment.filter.return_value.all.return_value = [equipment]
        
        mock_query_workers = MagicMock()
        mock_query_workers.filter.return_value.all.return_value = [worker]
        
        # Mock WorkerSkill查询
        mock_query_worker_skills = MagicMock()
        mock_query_worker_skills.filter.return_value.all.return_value = [(1,)]
        
        self.db.query.side_effect = [
            mock_query_work_orders,
            mock_query_equipment,
            mock_query_workers,
            mock_query_worker_skills,  # 添加WorkerSkill查询
            mock_query_work_orders,  # 第二次获取工单用于评估
        ]
        
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 10, 18, 0)
        )
        
        result = self.service.generate_and_evaluate_schedule(request, self.user_id)
        
        self.assertIn("plan_id", result)
        self.assertIn("schedules", result)
        self.assertIn("metrics", result)
        self.assertEqual(result["success_count"], 1)
        self.db.commit.assert_called()

    # ==================== 紧急插单测试 ====================

    def test_urgent_insert_basic(self):
        """测试紧急插单-基础场景"""
        order = self._create_mock_work_order(1, "WO001", priority="URGENT")
        equipment = self._create_mock_equipment(1)
        worker = self._create_mock_worker(1)
        
        # Mock查询
        mock_query_order = MagicMock()
        mock_query_order.filter.return_value.first.return_value = order
        
        mock_query_equipment = MagicMock()
        mock_query_equipment.filter.return_value.all.return_value = [equipment]
        
        mock_query_workers = MagicMock()
        mock_query_workers.filter.return_value.all.return_value = [worker]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [
            mock_query_order,
            mock_query_equipment,
            mock_query_workers,
            mock_query_conflicts,
        ]
        
        insert_time = datetime(2024, 1, 1, 10, 0)
        
        new_schedule, adjusted, conflicts = self.service.urgent_insert(
            work_order_id=1,
            insert_time=insert_time,
            max_delay_hours=4,
            auto_adjust=False,
            user_id=self.user_id
        )
        
        self.assertIsNotNone(new_schedule)
        self.assertEqual(new_schedule.work_order_id, 1)
        self.assertTrue(new_schedule.is_urgent)
        self.assertEqual(len(adjusted), 0)

    def test_urgent_insert_with_auto_adjust(self):
        """测试紧急插单-自动调整"""
        order = self._create_mock_work_order(1, "WO001", priority="URGENT")
        equipment = self._create_mock_equipment(1)
        worker = self._create_mock_worker(1)
        
        # 已有排程会冲突
        existing_schedule = self._create_mock_schedule(
            2, 2, equipment_id=1,
            scheduled_start_time=datetime(2024, 1, 1, 9, 0),
            scheduled_end_time=datetime(2024, 1, 1, 13, 0),
            status="PENDING"
        )
        existing_schedule.duration_hours = 4.0
        
        # Mock查询
        mock_query_order = MagicMock()
        mock_query_order.filter.return_value.first.return_value = order
        
        mock_query_equipment = MagicMock()
        mock_query_equipment.filter.return_value.all.return_value = [equipment]
        
        mock_query_workers = MagicMock()
        mock_query_workers.filter.return_value.all.return_value = [worker]
        
        # Mock WorkerSkill查询
        mock_query_worker_skills = MagicMock()
        mock_query_worker_skills.filter.return_value.all.return_value = [(1,)]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.all.return_value = [existing_schedule]
        
        self.db.query.side_effect = [
            mock_query_order,
            mock_query_equipment,
            mock_query_workers,
            mock_query_worker_skills,  # 添加WorkerSkill查询
            mock_query_conflicts,
        ]
        
        insert_time = datetime(2024, 1, 1, 10, 0)
        
        new_schedule, adjusted, conflicts = self.service.urgent_insert(
            work_order_id=1,
            insert_time=insert_time,
            max_delay_hours=10,
            auto_adjust=True,
            user_id=self.user_id
        )
        
        self.assertIsNotNone(new_schedule)
        self.assertEqual(len(adjusted), 1)
        # 冲突的排程应该被延后
        self.assertGreater(adjusted[0].scheduled_start_time, insert_time)

    def test_urgent_insert_work_order_not_found(self):
        """测试紧急插单-工单不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.urgent_insert(
                work_order_id=999,
                insert_time=datetime.now(),
                max_delay_hours=4,
                auto_adjust=False,
                user_id=self.user_id
            )
        
        self.assertIn("工单不存在", str(context.exception))

    def test_execute_urgent_insert_with_logging(self):
        """测试紧急插单并记录日志"""
        order = self._create_mock_work_order(1, "WO001")
        equipment = self._create_mock_equipment(1)
        worker = self._create_mock_worker(1)
        
        # Mock查询
        mock_query_order = MagicMock()
        mock_query_order.filter.return_value.first.return_value = order
        
        mock_query_equipment = MagicMock()
        mock_query_equipment.filter.return_value.all.return_value = [equipment]
        
        mock_query_workers = MagicMock()
        mock_query_workers.filter.return_value.all.return_value = [worker]
        
        # Mock WorkerSkill查询
        mock_query_worker_skills = MagicMock()
        mock_query_worker_skills.filter.return_value.all.return_value = [(1,)]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [
            mock_query_order,
            mock_query_equipment,
            mock_query_workers,
            mock_query_worker_skills,  # 添加WorkerSkill查询
            mock_query_conflicts,
        ]
        
        result = self.service.execute_urgent_insert_with_logging(
            work_order_id=1,
            insert_time=datetime(2024, 1, 1, 10, 0),
            max_delay_hours=4,
            auto_adjust=False,
            user_id=self.user_id
        )
        
        self.assertTrue(result["success"])
        self.assertIn("schedule", result)
        self.db.add.assert_called()
        self.db.commit.assert_called()

    # ==================== 排程预览测试 ====================

    def test_get_schedule_preview(self):
        """测试排程预览"""
        schedule = self._create_mock_schedule(1, 1, schedule_plan_id=100)
        order = self._create_mock_work_order(1, "WO001", plan_end_date=date(2024, 1, 10))
        
        # Mock查询
        mock_query_schedules = MagicMock()
        mock_query_schedules.filter.return_value.all.return_value = [schedule]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.all.return_value = []
        
        mock_query_orders = MagicMock()
        mock_query_orders.filter.return_value.all.return_value = [order]
        
        self.db.query.side_effect = [
            mock_query_schedules,
            mock_query_conflicts,
            mock_query_orders,
        ]
        
        result = self.service.get_schedule_preview(plan_id=100)
        
        self.assertEqual(result["plan_id"], 100)
        self.assertIn("schedules", result)
        self.assertIn("statistics", result)
        self.assertIn("optimization_suggestions", result)

    def test_get_schedule_preview_not_found(self):
        """测试排程预览-方案不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.get_schedule_preview(plan_id=999)
        
        self.assertIn("排程方案不存在", str(context.exception))

    # ==================== 确认排程测试 ====================

    def test_confirm_schedule_success(self):
        """测试确认排程-成功"""
        schedule = self._create_mock_schedule(1, 1, status="PENDING", schedule_plan_id=100)
        
        # Mock查询
        mock_query_schedules = MagicMock()
        mock_query_schedules.filter.return_value.all.return_value = [schedule]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.count.return_value = 0
        
        self.db.query.side_effect = [
            mock_query_schedules,
            mock_query_conflicts,
        ]
        
        result = self.service.confirm_schedule(plan_id=100, user_id=self.user_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["confirmed_count"], 1)
        self.assertEqual(schedule.status, "CONFIRMED")
        self.db.commit.assert_called()

    def test_confirm_schedule_no_pending(self):
        """测试确认排程-无待确认排程"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.confirm_schedule(plan_id=100, user_id=self.user_id)
        
        self.assertIn("没有待确认的排程", str(context.exception))

    def test_confirm_schedule_with_conflicts(self):
        """测试确认排程-存在冲突"""
        schedule = self._create_mock_schedule(1, 1, status="PENDING")
        
        # Mock查询
        mock_query_schedules = MagicMock()
        mock_query_schedules.filter.return_value.all.return_value = [schedule]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.count.return_value = 2  # 有冲突
        
        self.db.query.side_effect = [
            mock_query_schedules,
            mock_query_conflicts,
        ]
        
        with self.assertRaises(RuntimeError) as context:
            self.service.confirm_schedule(plan_id=100, user_id=self.user_id)
        
        self.assertIn("高优先级冲突", str(context.exception))

    # ==================== 调整排程测试 ====================

    def test_adjust_schedule_time(self):
        """测试调整排程-时间调整"""
        schedule = self._create_mock_schedule(
            1, 1,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 16, 0)
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = schedule
        self.db.query.return_value = mock_query
        
        new_start = datetime(2024, 1, 2, 8, 0)
        new_end = datetime(2024, 1, 2, 16, 0)
        
        request = ScheduleAdjustRequest(
            schedule_id=1,
            adjustment_type="TIME_CHANGE",
            new_start_time=new_start,
            new_end_time=new_end,
            reason="客户要求延期",
            auto_resolve_conflicts=False
        )
        
        result = self.service.adjust_schedule(request, self.user_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(schedule.scheduled_start_time, new_start)
        self.assertEqual(schedule.scheduled_end_time, new_end)
        self.assertTrue(schedule.is_manually_adjusted)
        self.db.add.assert_called()
        self.db.commit.assert_called()

    def test_adjust_schedule_resource(self):
        """测试调整排程-资源调整"""
        schedule = self._create_mock_schedule(1, 1, equipment_id=1, worker_id=1)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = schedule
        self.db.query.return_value = mock_query
        
        request = ScheduleAdjustRequest(
            schedule_id=1,
            adjustment_type="RESOURCE_CHANGE",
            new_equipment_id=2,
            new_worker_id=2,
            reason="资源调配",
            auto_resolve_conflicts=False
        )
        
        result = self.service.adjust_schedule(request, self.user_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(schedule.equipment_id, 2)
        self.assertEqual(schedule.worker_id, 2)

    def test_adjust_schedule_not_found(self):
        """测试调整排程-排程不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        request = ScheduleAdjustRequest(
            schedule_id=999,
            adjustment_type="TIME_CHANGE",
            reason="测试"
        )
        
        with self.assertRaises(ValueError) as context:
            self.service.adjust_schedule(request, self.user_id)
        
        self.assertIn("排程不存在", str(context.exception))

    # ==================== 冲突摘要测试 ====================

    def test_get_conflict_summary_by_plan(self):
        """测试冲突摘要-按方案"""
        schedule = self._create_mock_schedule(1, 1, schedule_plan_id=100)
        conflict1 = MagicMock(spec=ProductionResourceConflict)
        conflict1.conflict_type = "EQUIPMENT"
        conflict1.severity = "HIGH"
        conflict1.status = "UNRESOLVED"
        
        # Mock查询 - 需要返回实际的元组列表，而不是Mock对象
        mock_query_schedules = MagicMock()
        # 注意：这里的all()返回的应该是元组列表
        mock_all_result = [(1,)]  # 正确的格式
        mock_query_schedules.filter.return_value.all.return_value = mock_all_result
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.all.return_value = [conflict1]
        
        # 明确指定side_effect
        self.db.query.side_effect = [
            mock_query_schedules,  # 第一次查询schedule_id
            mock_query_conflicts,  # 第二次查询conflicts
        ]
        
        result = self.service.get_conflict_summary(plan_id=100)
        
        self.assertTrue(result["has_conflicts"])
        self.assertEqual(result["total_conflicts"], 1)
        self.assertEqual(result["conflicts_by_type"]["EQUIPMENT"], 1)

    def test_get_conflict_summary_no_conflicts(self):
        """测试冲突摘要-无冲突"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        result = self.service.get_conflict_summary(schedule_id=1)
        
        self.assertFalse(result["has_conflicts"])
        self.assertEqual(result["total_conflicts"], 0)

    # ==================== 方案对比测试 ====================

    def test_compare_schedule_plans(self):
        """测试方案对比"""
        # 方案1
        schedule1 = self._create_mock_schedule(1, 1, schedule_plan_id=100)
        order1 = self._create_mock_work_order(1, "WO001", plan_end_date=date(2024, 1, 10))
        
        # 方案2
        schedule2 = self._create_mock_schedule(2, 2, schedule_plan_id=101)
        order2 = self._create_mock_work_order(2, "WO002", plan_end_date=date(2024, 1, 10))
        
        # Mock查询
        mock_query_schedules_1 = MagicMock()
        mock_query_schedules_1.filter.return_value.all.return_value = [schedule1]
        
        mock_query_orders_1 = MagicMock()
        mock_query_orders_1.filter.return_value.all.return_value = [order1]
        
        mock_query_schedules_2 = MagicMock()
        mock_query_schedules_2.filter.return_value.all.return_value = [schedule2]
        
        mock_query_orders_2 = MagicMock()
        mock_query_orders_2.filter.return_value.all.return_value = [order2]
        
        self.db.query.side_effect = [
            mock_query_schedules_1,
            mock_query_orders_1,
            mock_query_schedules_2,
            mock_query_orders_2,
        ]
        
        result = self.service.compare_schedule_plans([100, 101])
        
        self.assertEqual(result["plans_compared"], 2)
        self.assertIn("best_plan_id", result)
        self.assertEqual(len(result["results"]), 2)
        # 检查排名
        self.assertEqual(result["results"][0]["rank"], 1)
        self.assertEqual(result["results"][1]["rank"], 2)

    def test_compare_schedule_plans_too_few(self):
        """测试方案对比-方案太少"""
        with self.assertRaises(ValueError) as context:
            self.service.compare_schedule_plans([100])
        
        self.assertIn("至少需要2个方案", str(context.exception))

    def test_compare_schedule_plans_too_many(self):
        """测试方案对比-方案太多"""
        with self.assertRaises(ValueError) as context:
            self.service.compare_schedule_plans([100, 101, 102, 103, 104, 105])
        
        self.assertIn("最多支持5个方案", str(context.exception))

    # ==================== 甘特图测试 ====================

    def test_generate_gantt_data(self):
        """测试生成甘特图数据"""
        schedule = self._create_mock_schedule(
            1, 1, equipment_id=1, worker_id=1, schedule_plan_id=100,
            scheduled_start_time=datetime(2024, 1, 1, 8, 0),
            scheduled_end_time=datetime(2024, 1, 1, 16, 0),
            status="CONFIRMED"
        )
        order = self._create_mock_work_order(1, "WO001", task_name="加工零件A")
        order.priority = "HIGH"
        order.progress = 50
        
        # Mock查询
        mock_query_schedules = MagicMock()
        mock_query_schedules.filter.return_value.all.return_value = [schedule]
        
        mock_query_orders = MagicMock()
        mock_query_orders.filter.return_value.all.return_value = [order]
        
        self.db.query.side_effect = [
            mock_query_schedules,
            mock_query_orders,
        ]
        
        result = self.service.generate_gantt_data(plan_id=100)
        
        self.assertEqual(result["total_tasks"], 1)
        self.assertIn("tasks", result)
        self.assertIn("resources", result)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0].name, "加工零件A")

    def test_generate_gantt_data_not_found(self):
        """测试生成甘特图-方案不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.generate_gantt_data(plan_id=999)
        
        self.assertIn("排程方案不存在", str(context.exception))

    # ==================== 重置排程测试 ====================

    def test_reset_schedule_plan(self):
        """测试重置排程方案"""
        # Mock查询
        mock_query_schedule_ids = MagicMock()
        mock_query_schedule_ids.filter.return_value.all.return_value = [(1,), (2,)]
        
        mock_query_conflicts = MagicMock()
        mock_query_conflicts.filter.return_value.delete.return_value = 1
        
        mock_query_logs = MagicMock()
        mock_query_logs.filter.return_value.delete.return_value = 2
        
        mock_query_schedules = MagicMock()
        mock_query_schedules.filter.return_value.delete.return_value = 2
        
        self.db.query.side_effect = [
            mock_query_schedule_ids,
            mock_query_conflicts,
            mock_query_logs,
            mock_query_schedules,
        ]
        
        result = self.service.reset_schedule_plan(plan_id=100)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["deleted_count"], 2)
        self.db.commit.assert_called()

    # ==================== 排程历史测试 ====================

    def test_get_schedule_history(self):
        """测试查询排程历史"""
        log = MagicMock(spec=ScheduleAdjustmentLog)
        log.schedule_id = 1
        log.adjustment_type = "TIME_CHANGE"
        
        schedule = self._create_mock_schedule(1, 1)
        
        # Mock查询 - 需要模拟完整的查询链
        mock_query_logs = MagicMock()
        
        # 创建filter后的query对象
        mock_filtered_query = MagicMock()
        mock_filtered_query.count.return_value = 1
        
        # 创建order_by后的query对象
        mock_ordered_query = MagicMock()
        mock_filtered_query.order_by.return_value = mock_ordered_query
        
        # 创建offset/limit后的query对象
        mock_paginated_query = MagicMock()
        mock_ordered_query.offset.return_value.limit.return_value = mock_paginated_query
        mock_paginated_query.all.return_value = [log]
        
        # 设置filter返回
        mock_query_logs.filter.return_value = mock_filtered_query
        
        # Mock schedules查询
        mock_query_schedules = MagicMock()
        mock_query_schedules.filter.return_value.all.return_value = [schedule]
        
        self.db.query.side_effect = [
            mock_query_logs,      # 第一次：ScheduleAdjustmentLog查询
            mock_query_schedules, # 第二次：ProductionSchedule查询
        ]
        
        result = self.service.get_schedule_history(schedule_id=1, page=1, page_size=20)
        
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["page"], 1)
        self.assertEqual(len(result["adjustments"]), 1)
        self.assertEqual(len(result["schedules"]), 1)


if __name__ == "__main__":
    unittest.main()
