# -*- coding: utf-8 -*-
"""PROD-18: production scheduling must respect work-order dependencies."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.production import ProductionSchedule, WorkOrder
from app.schemas.production_schedule import ScheduleGenerateRequest
from app.services.production_schedule_service import ProductionScheduleService


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows


class _GanttDb:
    def __init__(self, schedules, work_orders):
        self.schedules = schedules
        self.work_orders = work_orders

    def query(self, model):
        if model is ProductionSchedule:
            return _Query(self.schedules)
        if model is WorkOrder:
            return _Query(self.work_orders)
        return _Query([])


def _work_order(work_order_id, priority, work_order_no, hours=8):
    return SimpleNamespace(
        id=work_order_id,
        work_order_no=work_order_no,
        task_name=f"任务{work_order_no}",
        priority=priority,
        plan_end_date=None,
        standard_hours=hours,
        workshop_id=1,
        process_id=1,
        machine_id=None,
        assigned_to=None,
        progress=0,
    )


def _resource(resource_id):
    return SimpleNamespace(id=resource_id, workshop_id=1, is_active=True, status="IDLE")


def test_greedy_scheduling_delays_successor_until_predecessor_finishes():
    service = ProductionScheduleService(MagicMock())
    start = datetime(2026, 7, 6, 8, 0)
    predecessor = _work_order(1, "LOW", "WO-PRE", hours=8)
    successor = _work_order(2, "URGENT", "WO-NEXT", hours=4)
    request = ScheduleGenerateRequest(
        work_orders=[predecessor.id, successor.id],
        start_date=start,
        end_date=start + timedelta(days=3),
        algorithm="GREEDY",
        constraints={"dependencies": {str(successor.id): [predecessor.id]}},
    )

    schedules = service._greedy_scheduling(
        [successor, predecessor],
        [_resource(1)],
        [_resource(1)],
        request,
        plan_id=9001,
        user_id=1,
    )
    by_work_order = {schedule.work_order_id: schedule for schedule in schedules}

    assert by_work_order[predecessor.id].scheduled_end_time <= by_work_order[
        successor.id
    ].scheduled_start_time
    assert by_work_order[successor.id].constraints_met["dependencies"]["predecessors"] == [
        predecessor.id
    ]


def test_gantt_data_maps_work_order_dependencies_to_schedule_task_ids():
    start = datetime(2026, 7, 6, 8, 0)
    parent_schedule = SimpleNamespace(
        id=101,
        work_order_id=1,
        equipment_id=1,
        worker_id=1,
        scheduled_start_time=start,
        scheduled_end_time=start + timedelta(hours=8),
        duration_hours=8,
        status="PENDING",
        constraints_met={},
    )
    child_schedule = SimpleNamespace(
        id=102,
        work_order_id=2,
        equipment_id=1,
        worker_id=1,
        scheduled_start_time=start + timedelta(hours=8),
        scheduled_end_time=start + timedelta(hours=12),
        duration_hours=4,
        status="PENDING",
        constraints_met={"dependencies": {"predecessors": [1]}},
    )
    db = _GanttDb(
        schedules=[parent_schedule, child_schedule],
        work_orders=[
            _work_order(1, "LOW", "WO-PRE"),
            _work_order(2, "URGENT", "WO-NEXT"),
        ],
    )

    gantt = ProductionScheduleService(db).generate_gantt_data(plan_id=9001)
    child_task = next(task for task in gantt["tasks"] if task.id == child_schedule.id)

    assert child_task.dependencies == [parent_schedule.id]
