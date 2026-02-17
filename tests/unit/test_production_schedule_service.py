# -*- coding: utf-8 -*-
"""
生产排程服务单元测试
覆盖时间计算、冲突检测、优先级评分等核心算法
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.production_schedule_service import ProductionScheduleService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ProductionScheduleService(db=mock_db)


def make_schedule(id=1, equipment_id=None, worker_id=None,
                  start=None, end=None, work_order_id=1, priority_score=2.0):
    s = MagicMock()
    s.id = id
    s.equipment_id = equipment_id
    s.worker_id = worker_id
    s.scheduled_start_time = start
    s.scheduled_end_time = end
    s.work_order_id = work_order_id
    s.priority_score = priority_score
    return s


class TestCalculateEndTime:
    """_calculate_end_time 工作时间计算"""

    def test_within_same_day(self, service):
        request = MagicMock()
        start = datetime(2025, 1, 10, 9, 0, 0)
        end = service._calculate_end_time(start, duration_hours=4, request=request)
        assert end == datetime(2025, 1, 10, 13, 0, 0)

    def test_spans_to_next_day(self, service):
        request = MagicMock()
        # 从 16:00 开始干 4小时（当天只剩2小时工作时间）→ 第二天8:00再干2小时→10:00结束
        start = datetime(2025, 1, 10, 16, 0, 0)
        end = service._calculate_end_time(start, duration_hours=4, request=request)
        assert end == datetime(2025, 1, 11, 10, 0, 0)

    def test_starts_after_work_hours_shifts_to_next_day(self, service):
        request = MagicMock()
        # 从 19:00 开始（已下班），应跳到第二天8:00
        start = datetime(2025, 1, 10, 19, 0, 0)
        end = service._calculate_end_time(start, duration_hours=2, request=request)
        assert end == datetime(2025, 1, 11, 10, 0, 0)

    def test_zero_duration_returns_start(self, service):
        request = MagicMock()
        start = datetime(2025, 1, 10, 9, 0, 0)
        end = service._calculate_end_time(start, duration_hours=0, request=request)
        assert end == start


class TestAdjustToWorkTime:
    """_adjust_to_work_time 调整到工作时间"""

    def test_before_work_hours_adjusted(self, service):
        request = MagicMock()
        dt = datetime(2025, 1, 10, 6, 30, 0)
        result = service._adjust_to_work_time(dt, request=request)
        assert result.hour == service.WORK_START_HOUR
        assert result.minute == 0

    def test_during_work_hours_unchanged(self, service):
        request = MagicMock()
        dt = datetime(2025, 1, 10, 10, 30, 0)
        result = service._adjust_to_work_time(dt, request=request)
        assert result == dt

    def test_after_work_hours_moves_to_next_day(self, service):
        request = MagicMock()
        dt = datetime(2025, 1, 10, 19, 0, 0)
        result = service._adjust_to_work_time(dt, request=request)
        assert result.day == 11
        assert result.hour == service.WORK_START_HOUR


class TestTimeOverlap:
    """_time_overlap 时间重叠检测"""

    def test_non_overlapping_times(self, service):
        s1, e1 = datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 10, 0)
        s2, e2 = datetime(2025, 1, 10, 10, 0), datetime(2025, 1, 10, 12, 0)
        assert service._time_overlap(s1, e1, s2, e2) is False

    def test_overlapping_times(self, service):
        s1, e1 = datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 11, 0)
        s2, e2 = datetime(2025, 1, 10, 10, 0), datetime(2025, 1, 10, 13, 0)
        assert service._time_overlap(s1, e1, s2, e2) is True

    def test_contained_interval_overlaps(self, service):
        s1, e1 = datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 18, 0)
        s2, e2 = datetime(2025, 1, 10, 10, 0), datetime(2025, 1, 10, 12, 0)
        assert service._time_overlap(s1, e1, s2, e2) is True


class TestDetectConflicts:
    """_detect_conflicts 资源冲突检测"""

    def test_no_conflict_different_equipment(self, service):
        t1 = datetime(2025, 1, 10, 8, 0)
        t2 = datetime(2025, 1, 10, 10, 0)
        s1 = make_schedule(id=1, equipment_id=1, start=t1, end=t2)
        s2 = make_schedule(id=2, equipment_id=2, start=t1, end=t2)
        conflicts = service._detect_conflicts([s1, s2])
        assert len(conflicts) == 0

    def test_equipment_conflict_detected(self, service):
        t1 = datetime(2025, 1, 10, 8, 0)
        t2 = datetime(2025, 1, 10, 10, 0)
        s1 = make_schedule(id=1, equipment_id=5, start=t1, end=t2)
        s2 = make_schedule(id=2, equipment_id=5,
                           start=datetime(2025, 1, 10, 9, 0),
                           end=datetime(2025, 1, 10, 11, 0))
        conflicts = service._detect_conflicts([s1, s2])
        equipment_conflicts = [c for c in conflicts if c.conflict_type == "EQUIPMENT"]
        assert len(equipment_conflicts) >= 1

    def test_worker_conflict_detected(self, service):
        t1 = datetime(2025, 1, 10, 8, 0)
        t2 = datetime(2025, 1, 10, 10, 0)
        s1 = make_schedule(id=1, worker_id=3, start=t1, end=t2)
        s2 = make_schedule(id=2, worker_id=3,
                           start=datetime(2025, 1, 10, 9, 0),
                           end=datetime(2025, 1, 10, 11, 0))
        conflicts = service._detect_conflicts([s1, s2])
        worker_conflicts = [c for c in conflicts if c.conflict_type == "WORKER"]
        assert len(worker_conflicts) >= 1

    def test_no_conflict_non_overlapping_times(self, service):
        s1 = make_schedule(id=1, equipment_id=1,
                           start=datetime(2025, 1, 10, 8, 0),
                           end=datetime(2025, 1, 10, 10, 0))
        s2 = make_schedule(id=2, equipment_id=1,
                           start=datetime(2025, 1, 10, 10, 0),
                           end=datetime(2025, 1, 10, 12, 0))
        conflicts = service._detect_conflicts([s1, s2])
        assert len(conflicts) == 0


class TestPriorityScoreAndWeight:
    """_calculate_priority_score / _get_priority_weight"""

    def test_priority_score_urgent(self, service):
        order = MagicMock(priority="URGENT")
        assert service._calculate_priority_score(order) == 5.0

    def test_priority_score_default(self, service):
        order = MagicMock(priority="UNKNOWN")
        assert service._calculate_priority_score(order) == 2.0

    def test_priority_weight_order(self, service):
        assert service._get_priority_weight("URGENT") < service._get_priority_weight("LOW")
