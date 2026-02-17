# -*- coding: utf-8 -*-
"""
生产排程服务 N2 深度覆盖测试
覆盖: _should_swap_schedules, _select_best_equipment, _select_best_worker,
      calculate_overall_metrics, _calculate_schedule_score, _fetch_work_orders,
      _generate_plan_id, _get_available_equipment/workers, 算法分支
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.production_schedule_service import ProductionScheduleService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ProductionScheduleService(db=mock_db)


def make_schedule(id=1, equipment_id=None, worker_id=None,
                  start=None, end=None, work_order_id=1,
                  priority_score=2.0, duration_hours=8.0):
    s = MagicMock()
    s.id = id
    s.equipment_id = equipment_id
    s.worker_id = worker_id
    s.scheduled_start_time = start or datetime(2025, 1, 10, 8, 0)
    s.scheduled_end_time = end or datetime(2025, 1, 10, 16, 0)
    s.work_order_id = work_order_id
    s.priority_score = priority_score
    s.duration_hours = duration_hours
    return s


def make_work_order(id=1, priority="NORMAL", plan_end_date=None,
                    workshop_id=1, process_id=1, standard_hours=8,
                    machine_id=None, assigned_to=None, work_order_no="WO-001",
                    material_id=1):
    wo = MagicMock()
    wo.id = id
    wo.priority = priority
    wo.plan_end_date = plan_end_date
    wo.workshop_id = workshop_id
    wo.process_id = process_id
    wo.standard_hours = standard_hours
    wo.machine_id = machine_id
    wo.assigned_to = assigned_to
    wo.work_order_no = work_order_no
    wo.material_id = material_id
    return wo


def make_equipment(id=1, workshop_id=1, is_active=True, status="IDLE"):
    eq = MagicMock()
    eq.id = id
    eq.workshop_id = workshop_id
    eq.is_active = is_active
    eq.status = status
    return eq


def make_worker(id=1, workshop_id=1, is_active=True, status="ACTIVE"):
    w = MagicMock()
    w.id = id
    w.workshop_id = workshop_id
    w.is_active = is_active
    w.status = status
    return w


# ======================= _should_swap_schedules =======================

class TestShouldSwapSchedules:
    """测试 _should_swap_schedules 分支逻辑"""

    def test_no_swap_when_priority_equal(self, service):
        s1 = make_schedule(priority_score=2.0, start=datetime(2025, 1, 10, 8, 0))
        s2 = make_schedule(priority_score=2.0, start=datetime(2025, 1, 10, 12, 0))
        assert service._should_swap_schedules(s1, s2) is False

    def test_no_swap_when_low_priority_starts_earlier(self, service):
        """低优先级在前，不应交换（高优先级在后，应该交换 → True）"""
        # s1 priority_score < s2 means s1 is lower priority than s2
        s1 = make_schedule(priority_score=1.0, start=datetime(2025, 1, 10, 8, 0))
        s2 = make_schedule(priority_score=3.0, start=datetime(2025, 1, 10, 12, 0))
        # s1.priority_score(1.0) < s2.priority_score(3.0) and s1 starts before s2 → True
        assert service._should_swap_schedules(s1, s2) is True

    def test_no_swap_when_priority_order_already_correct(self, service):
        """高优先级在前，不需要交换"""
        s1 = make_schedule(priority_score=3.0, start=datetime(2025, 1, 10, 8, 0))
        s2 = make_schedule(priority_score=1.0, start=datetime(2025, 1, 10, 12, 0))
        assert service._should_swap_schedules(s1, s2) is False

    def test_no_swap_when_lower_priority_starts_later(self, service):
        """低优先级排在后面，不需要交换"""
        s1 = make_schedule(priority_score=1.0, start=datetime(2025, 1, 10, 12, 0))
        s2 = make_schedule(priority_score=3.0, start=datetime(2025, 1, 10, 8, 0))
        assert service._should_swap_schedules(s1, s2) is False


# ======================= _select_best_equipment =======================

class TestSelectBestEquipment:
    """测试设备选择逻辑"""

    def test_returns_none_when_no_equipment(self, service):
        order = make_work_order()
        result = service._select_best_equipment(order, [], {}, MagicMock())
        assert result is None

    def test_returns_specified_equipment_when_machine_id_set(self, service):
        eq1 = make_equipment(id=5)
        eq2 = make_equipment(id=6)
        order = make_work_order(machine_id=5)
        result = service._select_best_equipment(order, [eq1, eq2], {}, MagicMock())
        assert result is eq1

    def test_returns_none_when_machine_id_not_found(self, service):
        eq1 = make_equipment(id=5)
        order = make_work_order(machine_id=99)
        result = service._select_best_equipment(order, [eq1], {}, MagicMock())
        assert result is None

    def test_selects_workshop_filtered_equipment(self, service):
        """优先选同车间设备"""
        eq1 = make_equipment(id=1, workshop_id=10)
        eq2 = make_equipment(id=2, workshop_id=20)
        order = make_work_order(workshop_id=10, machine_id=None)
        timeline = {1: [], 2: []}
        result = service._select_best_equipment(order, [eq1, eq2], timeline, MagicMock())
        assert result is eq1

    def test_fallback_to_all_when_no_workshop_match(self, service):
        """无同车间设备时回退到全部设备"""
        eq1 = make_equipment(id=1, workshop_id=99)
        order = make_work_order(workshop_id=10, machine_id=None)
        timeline = {1: []}
        result = service._select_best_equipment(order, [eq1], timeline, MagicMock())
        assert result is eq1

    def test_selects_least_busy_equipment(self, service):
        """选择占用时间最少的设备"""
        eq1 = make_equipment(id=1, workshop_id=1)
        eq2 = make_equipment(id=2, workshop_id=1)
        order = make_work_order(workshop_id=1, machine_id=None)
        # eq1 has 2 slots, eq2 has 0
        timeline = {1: [("a", "b"), ("c", "d")], 2: []}
        result = service._select_best_equipment(order, [eq1, eq2], timeline, MagicMock())
        assert result is eq2


# ======================= _select_best_worker =======================

class TestSelectBestWorker:
    """测试工人选择逻辑"""

    def test_returns_none_when_no_workers(self, service):
        order = make_work_order()
        result = service._select_best_worker(order, [], {}, MagicMock())
        assert result is None

    def test_returns_assigned_worker_when_specified(self, service):
        w1 = make_worker(id=3)
        order = make_work_order(assigned_to=3)
        result = service._select_best_worker(order, [w1], {}, MagicMock())
        assert result is w1

    def test_returns_none_when_assigned_worker_not_found(self, service):
        w1 = make_worker(id=3)
        order = make_work_order(assigned_to=99)
        result = service._select_best_worker(order, [w1], {}, MagicMock())
        assert result is None

    def test_considers_skills_when_flag_set(self, service):
        """consider_worker_skills=True 时按工序技能筛选"""
        w1 = make_worker(id=1, workshop_id=1)
        w2 = make_worker(id=2, workshop_id=1)
        order = make_work_order(assigned_to=None, process_id=5, workshop_id=1)

        request = MagicMock()
        request.consider_worker_skills = True

        # DB query返回工人1有技能
        service.db.query.return_value.filter.return_value.all.return_value = [(1,)]

        timeline = {1: [], 2: [("a", "b")]}
        result = service._select_best_worker(order, [w1, w2], timeline, request)
        # w1 is skilled and has fewer slots → should return w1
        assert result is w1

    def test_fallback_workshop_when_no_skilled_workers(self, service):
        """技能筛选为空时，按车间筛选"""
        w1 = make_worker(id=1, workshop_id=1)
        w2 = make_worker(id=2, workshop_id=2)
        order = make_work_order(assigned_to=None, process_id=5, workshop_id=1)

        request = MagicMock()
        request.consider_worker_skills = True

        # 无技能工人
        service.db.query.return_value.filter.return_value.all.return_value = []
        timeline = {1: [], 2: []}
        result = service._select_best_worker(order, [w1, w2], timeline, request)
        # Workshop filter: w1 (workshop_id=1)
        assert result is w1

    def test_fallback_all_when_no_workshop_match(self, service):
        """无同车间工人时回退到全部"""
        w1 = make_worker(id=1, workshop_id=99)
        order = make_work_order(assigned_to=None, process_id=5, workshop_id=1)
        request = MagicMock()
        request.consider_worker_skills = False
        timeline = {1: []}
        result = service._select_best_worker(order, [w1], timeline, request)
        assert result is w1


# ======================= _calculate_priority_score =======================

class TestCalculatePriorityScore:
    @pytest.mark.parametrize("priority,expected", [
        ("URGENT", 5.0),
        ("HIGH", 3.0),
        ("NORMAL", 2.0),
        ("LOW", 1.0),
        ("UNKNOWN", 2.0),
    ])
    def test_all_priorities(self, service, priority, expected):
        order = make_work_order(priority=priority)
        assert service._calculate_priority_score(order) == expected


# ======================= _get_priority_weight =======================

class TestGetPriorityWeight:
    @pytest.mark.parametrize("priority,expected", [
        ("URGENT", 1),
        ("HIGH", 2),
        ("NORMAL", 3),
        ("LOW", 4),
        ("UNKNOWN", 3),
    ])
    def test_all_weights(self, service, priority, expected):
        assert service._get_priority_weight(priority) == expected


# ======================= _calculate_schedule_score =======================

class TestCalculateScheduleScore:
    def test_order_not_found_returns_zero(self, service):
        schedule = make_schedule(work_order_id=99)
        result = service._calculate_schedule_score(schedule, [])
        assert result == 0.0

    def test_on_time_adds_bonus(self, service):
        order = make_work_order(id=1, plan_end_date=date(2025, 1, 11))
        schedule = make_schedule(work_order_id=1, priority_score=3.0)
        schedule.scheduled_end_time = datetime(2025, 1, 10, 16, 0)
        result = service._calculate_schedule_score(schedule, [order])
        # 3.0 * 10 + 20 = 50 (capped at 100)
        assert result == 50.0

    def test_late_no_bonus(self, service):
        order = make_work_order(id=1, plan_end_date=date(2025, 1, 9))
        schedule = make_schedule(work_order_id=1, priority_score=2.0)
        schedule.scheduled_end_time = datetime(2025, 1, 10, 16, 0)
        result = service._calculate_schedule_score(schedule, [order])
        assert result == 20.0  # 2.0 * 10

    def test_no_plan_end_date_no_bonus(self, service):
        order = make_work_order(id=1, plan_end_date=None)
        schedule = make_schedule(work_order_id=1, priority_score=5.0)
        schedule.scheduled_end_time = datetime(2025, 1, 10, 16, 0)
        result = service._calculate_schedule_score(schedule, [order])
        assert result == 50.0  # 5.0 * 10

    def test_score_capped_at_100(self, service):
        order = make_work_order(id=1, plan_end_date=date(2025, 1, 11))
        schedule = make_schedule(work_order_id=1, priority_score=9.0)
        schedule.scheduled_end_time = datetime(2025, 1, 10, 16, 0)
        result = service._calculate_schedule_score(schedule, [order])
        assert result == 100.0  # 9 * 10 + 20 = 110 → capped at 100


# ======================= calculate_overall_metrics =======================

class TestCalculateOverallMetrics:
    def test_empty_schedules_returns_zeroed_metrics(self, service):
        from app.schemas.production_schedule import ScheduleScoreMetrics
        result = service.calculate_overall_metrics([], [])
        assert result.completion_rate == 0
        assert result.equipment_utilization == 0
        assert result.worker_utilization == 0
        assert result.total_duration_hours == 0
        assert result.conflict_count == 0

    def test_metrics_with_on_time_schedules(self, service):
        order = make_work_order(id=1, plan_end_date=date(2025, 1, 11))
        s = make_schedule(work_order_id=1, equipment_id=1, worker_id=1, duration_hours=4.0)
        s.scheduled_start_time = datetime(2025, 1, 10, 8, 0)
        s.scheduled_end_time = datetime(2025, 1, 10, 12, 0)
        # Mock detect_conflicts to return empty
        service._detect_conflicts = MagicMock(return_value=[])
        result = service.calculate_overall_metrics([s], [order])
        assert result.completion_rate == 1.0  # 1/1 on time
        assert result.conflict_count == 0

    def test_metrics_with_late_schedule(self, service):
        order = make_work_order(id=1, plan_end_date=date(2025, 1, 9))
        s = make_schedule(work_order_id=1, equipment_id=1, worker_id=1, duration_hours=8.0)
        s.scheduled_start_time = datetime(2025, 1, 10, 8, 0)
        s.scheduled_end_time = datetime(2025, 1, 10, 16, 0)
        service._detect_conflicts = MagicMock(return_value=[])
        result = service.calculate_overall_metrics([s], [order])
        assert result.completion_rate == 0.0  # late

    def test_utilization_capped_at_1(self, service):
        """设备利用率不超过1.0"""
        order = make_work_order(id=1, plan_end_date=None)
        # Very long duration
        s = make_schedule(work_order_id=1, equipment_id=1, worker_id=1, duration_hours=1000.0)
        s.scheduled_start_time = datetime(2025, 1, 1, 8, 0)
        s.scheduled_end_time = datetime(2025, 6, 1, 8, 0)
        service._detect_conflicts = MagicMock(return_value=[])
        result = service.calculate_overall_metrics([s], [order])
        assert result.equipment_utilization <= 1.0


# ======================= _generate_plan_id =======================

class TestGeneratePlanId:
    def test_returns_integer(self, service):
        plan_id = service._generate_plan_id()
        assert isinstance(plan_id, int)
        assert plan_id > 0


# ======================= _get_available_equipment/workers =======================

class TestGetAvailableResources:
    def test_get_available_equipment_calls_db(self, service):
        mock_eq = [make_equipment(id=1)]
        service.db.query.return_value.filter.return_value.all.return_value = mock_eq
        result = service._get_available_equipment()
        assert result == mock_eq

    def test_get_available_workers_calls_db(self, service):
        mock_workers = [make_worker(id=1)]
        service.db.query.return_value.filter.return_value.all.return_value = mock_workers
        result = service._get_available_workers()
        assert result == mock_workers


# ======================= _find_earliest_available_slot =======================

class TestFindEarliestAvailableSlot:
    def test_returns_start_when_no_conflicts(self, service):
        request = MagicMock()
        start = datetime(2025, 1, 10, 8, 0)
        result = service._find_earliest_available_slot([], [], start, 4, request)
        assert result == start

    def test_skips_conflicting_equipment_slot(self, service):
        request = MagicMock()
        start = datetime(2025, 1, 10, 8, 0)
        # Equipment occupied 8-12
        eq_slots = [(datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 12, 0))]
        result = service._find_earliest_available_slot(eq_slots, [], start, 4, request)
        # Should push past 12:00
        assert result >= datetime(2025, 1, 10, 12, 0)

    def test_skips_conflicting_worker_slot(self, service):
        request = MagicMock()
        start = datetime(2025, 1, 10, 8, 0)
        worker_slots = [(datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 10, 0))]
        result = service._find_earliest_available_slot([], worker_slots, start, 2, request)
        assert result >= datetime(2025, 1, 10, 10, 0)


# ======================= _optimize_schedules =======================

class TestOptimizeSchedules:
    def test_single_schedule_unchanged(self, service):
        s = make_schedule(id=1, priority_score=2.0)
        result = service._optimize_schedules([s], MagicMock())
        assert len(result) == 1

    def test_empty_schedules_unchanged(self, service):
        result = service._optimize_schedules([], MagicMock())
        assert result == []

    def test_two_schedules_returns_same_count(self, service):
        s1 = make_schedule(id=1, priority_score=1.0, start=datetime(2025, 1, 10, 8, 0))
        s2 = make_schedule(id=2, priority_score=3.0, start=datetime(2025, 1, 10, 12, 0))
        result = service._optimize_schedules([s1, s2], MagicMock())
        assert len(result) == 2
