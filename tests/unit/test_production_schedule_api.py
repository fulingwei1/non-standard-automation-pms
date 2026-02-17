# -*- coding: utf-8 -*-
"""
生产排程 API 端点单元测试
Covers: app/api/v1/endpoints/production/schedule.py
方式A：直接调用 async 函数（用 pytest-anyio 或直接 asyncio.run）
注意：所有 Query() 默认值需显式传入
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.production.schedule import (
    adjust_schedule,
    check_conflicts,
    compare_schedules,
    confirm_schedule,
    generate_schedule,
    get_gantt_data,
    get_schedule_history,
    preview_schedule,
    reset_schedule,
    urgent_insert,
)
from app.models.production import (
    ProductionResourceConflict,
    ProductionSchedule,
    ScheduleAdjustmentLog,
    WorkOrder,
)


# ==================== Helpers ====================

def run_async(coro):
    """在同步测试中运行 async 函数"""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    return user


def _make_query_mock(count=0, items=None, first_val=None, scalar_val=None):
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.count.return_value = count
    q.scalar.return_value = scalar_val if scalar_val is not None else count
    q.offset.return_value = q
    q.limit.return_value = q
    q.all.return_value = items or []
    q.first.return_value = first_val
    q.delete.return_value = count
    q.in_.return_value = q
    return q


def _make_schedule(id=1, plan_id=1, status="PENDING", wo_id=1):
    s = MagicMock(spec=ProductionSchedule)
    s.id = id
    s.schedule_plan_id = plan_id
    s.work_order_id = wo_id
    s.status = status
    s.scheduled_start_time = datetime(2025, 1, 1, 8, 0)
    s.scheduled_end_time = datetime(2025, 1, 1, 16, 0)
    s.equipment_id = 1
    s.worker_id = 1
    s.duration_hours = 8.0
    s.is_manually_adjusted = False
    return s


def _make_work_order(id=1):
    wo = MagicMock(spec=WorkOrder)
    wo.id = id
    wo.work_order_no = f"WO-{id:03d}"
    wo.task_name = f"任务{id}"
    wo.priority = "NORMAL"  # GanttTask.priority 是 str
    wo.progress = 0
    return wo


# ==================== generate_schedule ====================

class TestGenerateSchedule:

    def test_generate_success(self, mock_db, mock_user):
        """正常生成排程"""
        mock_request = MagicMock()
        mock_request.work_orders = [1, 2]

        mock_schedule = _make_schedule()

        # mock metrics
        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.9
        mock_metrics.equipment_utilization = 0.8
        mock_metrics.worker_utilization = 0.7
        mock_metrics.total_duration_hours = 16.0
        mock_metrics.skill_match_rate = 1.0
        mock_metrics.conflict_count = 0
        mock_metrics.calculate_overall_score.return_value = 85.0

        mock_service = MagicMock()
        mock_service.generate_schedule.return_value = (1, [mock_schedule], [])
        mock_service._fetch_work_orders.return_value = [_make_work_order()]
        mock_service.calculate_overall_metrics.return_value = mock_metrics

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ), patch(
            "app.api.v1.endpoints.production.schedule.ScheduleResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(generate_schedule(
                request=mock_request,
                db=mock_db,
                current_user=mock_user,
            ))
        assert result is not None
        assert result.plan_id == 1

    def test_generate_with_conflicts(self, mock_db, mock_user):
        """生成排程含冲突时有警告"""
        mock_request = MagicMock()
        mock_request.work_orders = [1]

        mock_conflict = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.7
        mock_metrics.equipment_utilization = 0.6
        mock_metrics.worker_utilization = 0.5
        mock_metrics.total_duration_hours = 8.0
        mock_metrics.skill_match_rate = 0.9
        mock_metrics.conflict_count = 1
        mock_metrics.calculate_overall_score.return_value = 65.0

        mock_service = MagicMock()
        mock_service.generate_schedule.return_value = (2, [], [mock_conflict])
        mock_service._fetch_work_orders.return_value = []
        mock_service.calculate_overall_metrics.return_value = mock_metrics

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ), patch(
            "app.api.v1.endpoints.production.schedule.ScheduleResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(generate_schedule(
                request=mock_request,
                db=mock_db,
                current_user=mock_user,
            ))
        assert result is not None
        assert len(result.warnings) > 0  # 应有冲突警告

    def test_generate_value_error_raises_400(self, mock_db, mock_user):
        """service 抛出 ValueError 时应返回 400"""
        mock_request = MagicMock()
        mock_request.work_orders = []

        mock_service = MagicMock()
        mock_service.generate_schedule.side_effect = ValueError("工单列表不能为空")

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ):
            with pytest.raises(HTTPException) as exc:
                run_async(generate_schedule(
                    request=mock_request,
                    db=mock_db,
                    current_user=mock_user,
                ))
        assert exc.value.status_code == 400

    def test_generate_unexpected_error_raises_500(self, mock_db, mock_user):
        """意外错误应返回 500"""
        mock_request = MagicMock()
        mock_request.work_orders = [1]

        mock_service = MagicMock()
        mock_service.generate_schedule.side_effect = RuntimeError("数据库错误")

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ):
            with pytest.raises(HTTPException) as exc:
                run_async(generate_schedule(
                    request=mock_request,
                    db=mock_db,
                    current_user=mock_user,
                ))
        assert exc.value.status_code == 500


# ==================== preview_schedule ====================

class TestPreviewSchedule:

    def test_preview_plan_not_found(self, mock_db, mock_user):
        """方案不存在时抛出 404"""
        sched_q = _make_query_mock(items=[])
        mock_db.query.return_value = sched_q

        with pytest.raises(HTTPException) as exc:
            run_async(preview_schedule(plan_id=999, db=mock_db, current_user=mock_user))
        assert exc.value.status_code == 404

    def test_preview_success(self, mock_db, mock_user):
        """正常预览"""
        mock_schedule = _make_schedule(status="PENDING")

        mock_metrics = MagicMock()
        mock_metrics.total_duration_hours = 8.0
        mock_metrics.completion_rate = 0.9
        mock_metrics.equipment_utilization = 0.8

        mock_service = MagicMock()
        mock_service._fetch_work_orders.return_value = []
        mock_service.calculate_overall_metrics.return_value = mock_metrics

        sched_q = _make_query_mock(items=[mock_schedule])
        conflict_q = _make_query_mock(items=[])

        def q_side(model):
            if model is ProductionSchedule:
                return sched_q
            if model is ProductionResourceConflict:
                return conflict_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ), patch(
            "app.api.v1.endpoints.production.schedule.ScheduleResponse.model_validate",
            return_value=MagicMock()
        ), patch(
            "app.api.v1.endpoints.production.schedule.ConflictResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(preview_schedule(
                plan_id=1, db=mock_db, current_user=mock_user
            ))
        assert result is not None
        assert result.plan_id == 1


# ==================== confirm_schedule ====================

class TestConfirmSchedule:

    def test_confirm_no_pending_raises_404(self, mock_db, mock_user):
        """无待确认排程时抛出 404"""
        q = _make_query_mock(items=[])
        mock_db.query.return_value = q

        with pytest.raises(HTTPException) as exc:
            run_async(confirm_schedule(plan_id=1, db=mock_db, current_user=mock_user))
        assert exc.value.status_code == 404

    def test_confirm_with_high_conflicts_raises_400(self, mock_db, mock_user):
        """高优先级冲突时抛出 400"""
        mock_schedule = _make_schedule(status="PENDING")
        sched_q = _make_query_mock(items=[mock_schedule])
        conflict_q = _make_query_mock(count=2)

        def q_side(model):
            if model is ProductionSchedule:
                return sched_q
            if model is ProductionResourceConflict:
                return conflict_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with pytest.raises(HTTPException) as exc:
            run_async(confirm_schedule(plan_id=1, db=mock_db, current_user=mock_user))
        assert exc.value.status_code == 400

    def test_confirm_success(self, mock_db, mock_user):
        """无冲突时成功确认"""
        mock_schedule = _make_schedule(status="PENDING")
        sched_q = _make_query_mock(items=[mock_schedule])
        conflict_q = _make_query_mock(count=0)

        def q_side(model):
            if model is ProductionSchedule:
                return sched_q
            if model is ProductionResourceConflict:
                return conflict_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        result = run_async(confirm_schedule(plan_id=1, db=mock_db, current_user=mock_user))
        assert result["success"] is True
        assert result["confirmed_count"] == 1


# ==================== check_conflicts ====================

class TestCheckConflicts:

    def test_no_conflicts(self, mock_db, mock_user):
        """无冲突"""
        conflict_q = _make_query_mock(items=[])
        sched_q = _make_query_mock(items=[])

        def q_side(model):
            if model is ProductionResourceConflict:
                return conflict_q
            if model is ProductionSchedule:
                return sched_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.ConflictResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(check_conflicts(
                plan_id=1, schedule_id=None, status=None,
                db=mock_db, current_user=mock_user,
            ))
        assert result.has_conflicts is False
        assert result.total_conflicts == 0

    def test_with_conflicts(self, mock_db, mock_user):
        """有冲突时正确统计"""
        mock_conflict = MagicMock()
        mock_conflict.conflict_type = "EQUIPMENT"
        mock_conflict.severity = "HIGH"

        conflict_q = _make_query_mock(items=[mock_conflict])
        sched_q = _make_query_mock(items=[])

        def q_side(model):
            if model is ProductionResourceConflict:
                return conflict_q
            if model is ProductionSchedule:
                return sched_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.ConflictResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(check_conflicts(
                plan_id=None, schedule_id=1, status=None,
                db=mock_db, current_user=mock_user,
            ))
        assert result.has_conflicts is True
        assert result.total_conflicts == 1

    def test_filter_by_status(self, mock_db, mock_user):
        """按状态筛选冲突"""
        conflict_q = _make_query_mock(items=[])

        def q_side(model):
            if model is ProductionResourceConflict:
                return conflict_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.ConflictResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(check_conflicts(
                plan_id=None, schedule_id=None, status="UNRESOLVED",
                db=mock_db, current_user=mock_user,
            ))
        assert result is not None


# ==================== adjust_schedule ====================

class TestAdjustSchedule:

    def test_schedule_not_found_raises_404(self, mock_db, mock_user):
        """排程不存在时抛出 404"""
        q = _make_query_mock(first_val=None)
        mock_db.query.return_value = q

        mock_request = MagicMock()
        mock_request.schedule_id = 999

        with pytest.raises(HTTPException) as exc:
            run_async(adjust_schedule(
                request=mock_request, db=mock_db, current_user=mock_user
            ))
        assert exc.value.status_code == 404

    def test_adjust_start_time(self, mock_db, mock_user):
        """调整开始时间"""
        mock_schedule = _make_schedule()
        q = _make_query_mock(first_val=mock_schedule)
        mock_db.query.return_value = q

        mock_request = MagicMock()
        mock_request.schedule_id = 1
        mock_request.new_start_time = datetime(2025, 1, 2, 9, 0)
        mock_request.new_end_time = None
        mock_request.new_equipment_id = None
        mock_request.new_worker_id = None
        mock_request.reason = "手动调整"
        mock_request.adjustment_type = "TIME_CHANGE"
        mock_request.auto_resolve_conflicts = False

        result = run_async(adjust_schedule(
            request=mock_request, db=mock_db, current_user=mock_user
        ))
        assert result["success"] is True
        assert "开始时间" in result["changes"]

    def test_adjust_equipment(self, mock_db, mock_user):
        """调整设备"""
        mock_schedule = _make_schedule()
        q = _make_query_mock(first_val=mock_schedule)
        mock_db.query.return_value = q

        mock_request = MagicMock()
        mock_request.schedule_id = 1
        mock_request.new_start_time = None
        mock_request.new_end_time = None
        mock_request.new_equipment_id = 5
        mock_request.new_worker_id = None
        mock_request.reason = "设备替换"
        mock_request.adjustment_type = "RESOURCE_CHANGE"
        mock_request.auto_resolve_conflicts = False

        result = run_async(adjust_schedule(
            request=mock_request, db=mock_db, current_user=mock_user
        ))
        assert result["success"] is True
        assert "设备" in result["changes"]

    def test_adjust_with_auto_resolve(self, mock_db, mock_user):
        """调整时自动解决冲突"""
        mock_schedule = _make_schedule()
        q = _make_query_mock(first_val=mock_schedule)
        mock_db.query.return_value = q

        mock_request = MagicMock()
        mock_request.schedule_id = 1
        mock_request.new_start_time = datetime(2025, 1, 3, 8, 0)
        mock_request.new_end_time = None
        mock_request.new_equipment_id = None
        mock_request.new_worker_id = None
        mock_request.reason = "冲突解决"
        mock_request.adjustment_type = "TIME_CHANGE"
        mock_request.auto_resolve_conflicts = True

        mock_service = MagicMock()
        mock_service._detect_conflicts.return_value = []

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ):
            result = run_async(adjust_schedule(
                request=mock_request, db=mock_db, current_user=mock_user
            ))
        assert result["success"] is True


# ==================== reset_schedule ====================

class TestResetSchedule:

    def test_reset_success(self, mock_db, mock_user):
        """成功重置排程"""
        sched_q = _make_query_mock(count=3)
        conflict_q = _make_query_mock(count=1)
        log_q = _make_query_mock(count=2)

        call_count = [0]

        def q_side(model):
            call_count[0] += 1
            if model is ProductionSchedule:
                return sched_q
            if model is ProductionResourceConflict:
                return conflict_q
            if model is ScheduleAdjustmentLog:
                return log_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        result = run_async(reset_schedule(plan_id=1, db=mock_db, current_user=mock_user))
        assert result["success"] is True
        assert result["plan_id"] == 1


# ==================== get_schedule_history ====================

class TestGetScheduleHistory:

    def test_history_empty(self, mock_db, mock_user):
        """无历史记录"""
        log_q = _make_query_mock(count=0, items=[])
        sched_q = _make_query_mock(items=[])

        def q_side(model):
            if model is ScheduleAdjustmentLog:
                return log_q
            if model is ProductionSchedule:
                return sched_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.AdjustmentLogResponse.model_validate",
            return_value=MagicMock()
        ), patch(
            "app.api.v1.endpoints.production.schedule.ScheduleResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(get_schedule_history(
                schedule_id=None, plan_id=None,
                page=1, page_size=20,
                db=mock_db, current_user=mock_user,
            ))
        assert result is not None
        assert result.total_count == 0

    def test_history_with_data(self, mock_db, mock_user):
        """有调整历史"""
        mock_log = MagicMock(spec=ScheduleAdjustmentLog)
        mock_log.schedule_id = 1
        mock_log.schedule_plan_id = 1
        mock_log.adjusted_at = datetime(2025, 1, 1)

        log_q = _make_query_mock(count=1, items=[mock_log])
        sched_q = _make_query_mock(items=[_make_schedule()])

        def q_side(model):
            if model is ScheduleAdjustmentLog:
                return log_q
            if model is ProductionSchedule:
                return sched_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.AdjustmentLogResponse.model_validate",
            return_value=MagicMock()
        ), patch(
            "app.api.v1.endpoints.production.schedule.ScheduleResponse.model_validate",
            return_value=MagicMock()
        ):
            result = run_async(get_schedule_history(
                schedule_id=1, plan_id=None,
                page=1, page_size=20,
                db=mock_db, current_user=mock_user,
            ))
        assert result is not None
        assert result.total_count == 1


# ==================== compare_schedules ====================

class TestCompareSchedules:

    def test_compare_too_few_plans_raises_400(self, mock_db, mock_user):
        """少于2个方案时抛出 400"""
        with pytest.raises(HTTPException) as exc:
            run_async(compare_schedules(
                plan_ids="1", db=mock_db, current_user=mock_user
            ))
        assert exc.value.status_code == 400

    def test_compare_too_many_plans_raises_400(self, mock_db, mock_user):
        """超过5个方案时抛出 400"""
        with pytest.raises(HTTPException) as exc:
            run_async(compare_schedules(
                plan_ids="1,2,3,4,5,6", db=mock_db, current_user=mock_user
            ))
        assert exc.value.status_code == 400

    def test_compare_two_plans(self, mock_db, mock_user):
        """对比两个方案"""
        mock_schedule1 = _make_schedule(id=1, plan_id=1, wo_id=1)
        mock_schedule2 = _make_schedule(id=2, plan_id=2, wo_id=2)

        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.9
        mock_metrics.equipment_utilization = 0.8
        mock_metrics.worker_utilization = 0.7
        mock_metrics.total_duration_hours = 16.0
        mock_metrics.conflict_count = 0
        mock_metrics.calculate_overall_score.return_value = 80.0

        mock_service = MagicMock()
        mock_service._fetch_work_orders.return_value = []
        mock_service.calculate_overall_metrics.return_value = mock_metrics

        call_count = [0]

        def q_side(model):
            if model is ProductionSchedule:
                q = _make_query_mock()
                call_count[0] += 1
                if call_count[0] % 2 == 1:
                    q.filter.return_value.all.return_value = [mock_schedule1]
                else:
                    q.filter.return_value.all.return_value = [mock_schedule2]
                return q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        with patch(
            "app.api.v1.endpoints.production.schedule.ProductionScheduleService",
            return_value=mock_service
        ):
            result = run_async(compare_schedules(
                plan_ids="1,2", db=mock_db, current_user=mock_user
            ))
        assert result is not None
        assert result.plans_compared <= 2


# ==================== get_gantt_data ====================

class TestGetGanttData:

    def test_gantt_plan_not_found_raises_404(self, mock_db, mock_user):
        """甘特图方案不存在时抛出 404"""
        q = _make_query_mock(items=[])
        mock_db.query.return_value = q

        with pytest.raises(HTTPException) as exc:
            run_async(get_gantt_data(plan_id=999, db=mock_db, current_user=mock_user))
        assert exc.value.status_code == 404

    def test_gantt_success(self, mock_db, mock_user):
        """正常获取甘特图数据"""
        mock_schedule = _make_schedule()
        mock_wo = _make_work_order(id=1)

        sched_q = _make_query_mock(items=[mock_schedule])
        wo_q = _make_query_mock(items=[mock_wo])

        def q_side(model):
            if model is ProductionSchedule:
                return sched_q
            if model is WorkOrder:
                return wo_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        result = run_async(get_gantt_data(plan_id=1, db=mock_db, current_user=mock_user))
        assert result is not None
        assert result.total_tasks >= 0

    def test_gantt_schedule_without_work_order(self, mock_db, mock_user):
        """排程对应的工单不存在时跳过该排程"""
        mock_schedule = _make_schedule(wo_id=999)

        sched_q = _make_query_mock(items=[mock_schedule])
        wo_q = _make_query_mock(items=[])  # 工单不存在

        def q_side(model):
            if model is ProductionSchedule:
                return sched_q
            if model is WorkOrder:
                return wo_q
            return _make_query_mock()

        mock_db.query.side_effect = q_side

        result = run_async(get_gantt_data(plan_id=1, db=mock_db, current_user=mock_user))
        assert result.total_tasks == 0
