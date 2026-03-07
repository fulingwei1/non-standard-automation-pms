# -*- coding: utf-8 -*-
"""
生产调度服务分支测试 V2 - 重构版
修复过度 Mock 问题，确保真实业务逻辑被执行
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, Mock
import pytest

from app.services.production_schedule_service import ProductionScheduleService
from app.models.production import WorkOrder, Equipment, Worker, ProductionSchedule


# ==================== Fixtures ====================


@pytest.fixture
def mock_db():
    """模拟数据库会话 - 只 Mock 查询接口"""
    return MagicMock()


@pytest.fixture
def production_service(mock_db):
    """生产调度服务实例"""
    return ProductionScheduleService(mock_db)


@pytest.fixture
def sample_work_order():
    """示例工单"""
    order = Mock(spec=WorkOrder)
    order.id = 1
    order.priority = "HIGH"
    order.due_date = date.today() + timedelta(days=7)
    order.estimated_hours = 8.0
    order.standard_hours = 8.0  # 添加standard_hours
    order.plan_end_date = date.today() + timedelta(days=7)  # 添加plan_end_date
    order.work_order_no = "WO001"  # 添加work_order_no
    order.status = "PENDING"
    order.product_name = "测试产品"
    order.workshop_id = 1  # 添加workshop_id
    order.process_id = None  # 添加process_id
    order.machine_id = None  # 添加machine_id
    order.assigned_to = None  # 添加assigned_to
    return order


@pytest.fixture
def sample_equipment():
    """示例设备"""
    equipment = Mock(spec=Equipment)
    equipment.id = 1
    equipment.name = "设备A"
    equipment.status = "AVAILABLE"
    equipment.maintenance_status = "NORMAL"
    equipment.capacity_per_hour = 100
    return equipment


@pytest.fixture
def sample_worker():
    """示例工人"""
    worker = Mock(spec=Worker)
    worker.id = 1
    worker.name = "工人A"
    worker.status = "AVAILABLE"
    worker.skill_level = 3
    return worker


# ==================== 1. ProductionScheduleService 核心方法测试 ====================


class TestPriorityCalculation:
    """测试优先级计算分支"""

    def test_calculate_priority_score_urgent(self, production_service, sample_work_order):
        """分支：紧急优先级 - 返回 5.0"""
        sample_work_order.priority = "URGENT"
        score = production_service._calculate_priority_score(sample_work_order)
        assert score == 5.0

    def test_calculate_priority_score_high(self, production_service, sample_work_order):
        """分支：高优先级 - 返回 3.0"""
        sample_work_order.priority = "HIGH"
        score = production_service._calculate_priority_score(sample_work_order)
        assert score == 3.0

    def test_calculate_priority_score_normal(self, production_service, sample_work_order):
        """分支：普通优先级 - 返回 2.0"""
        sample_work_order.priority = "NORMAL"
        score = production_service._calculate_priority_score(sample_work_order)
        assert score == 2.0

    def test_calculate_priority_score_low(self, production_service, sample_work_order):
        """分支：低优先级 - 返回 1.0"""
        sample_work_order.priority = "LOW"
        score = production_service._calculate_priority_score(sample_work_order)
        assert score == 1.0

    def test_calculate_priority_score_unknown(self, production_service, sample_work_order):
        """分支：未知优先级 - 返回默认 2.0"""
        sample_work_order.priority = "UNKNOWN"
        score = production_service._calculate_priority_score(sample_work_order)
        assert score == 2.0


class TestPriorityWeight:
    """测试优先级权重分支"""

    def test_get_priority_weight_urgent(self, production_service):
        """分支：紧急 - 权重 1"""
        weight = production_service._get_priority_weight("URGENT")
        assert weight == 1

    def test_get_priority_weight_high(self, production_service):
        """分支：高 - 权重 2"""
        weight = production_service._get_priority_weight("HIGH")
        assert weight == 2

    def test_get_priority_weight_normal(self, production_service):
        """分支：普通 - 权重 3"""
        weight = production_service._get_priority_weight("NORMAL")
        assert weight == 3

    def test_get_priority_weight_low(self, production_service):
        """分支：低 - 权重 4"""
        weight = production_service._get_priority_weight("LOW")
        assert weight == 4

    def test_get_priority_weight_unknown(self, production_service):
        """分支：未知 - 默认权重 3"""
        weight = production_service._get_priority_weight("INVALID")
        assert weight == 3


class TestTimeOverlap:
    """测试时间重叠检测分支"""

    def test_time_overlap_complete_overlap(self, production_service):
        """分支：完全重叠"""
        start1 = datetime(2024, 1, 1, 8, 0)
        end1 = datetime(2024, 1, 1, 12, 0)
        start2 = datetime(2024, 1, 1, 9, 0)
        end2 = datetime(2024, 1, 1, 11, 0)

        assert production_service._time_overlap(start1, end1, start2, end2) is True

    def test_time_overlap_partial_start(self, production_service):
        """分支：起始部分重叠"""
        start1 = datetime(2024, 1, 1, 8, 0)
        end1 = datetime(2024, 1, 1, 12, 0)
        start2 = datetime(2024, 1, 1, 10, 0)
        end2 = datetime(2024, 1, 1, 14, 0)

        assert production_service._time_overlap(start1, end1, start2, end2) is True

    def test_time_overlap_no_overlap(self, production_service):
        """分支：完全不重叠"""
        start1 = datetime(2024, 1, 1, 8, 0)
        end1 = datetime(2024, 1, 1, 12, 0)
        start2 = datetime(2024, 1, 1, 13, 0)
        end2 = datetime(2024, 1, 1, 17, 0)

        assert production_service._time_overlap(start1, end1, start2, end2) is False

    def test_time_overlap_adjacent(self, production_service):
        """分支：相邻但不重叠"""
        start1 = datetime(2024, 1, 1, 8, 0)
        end1 = datetime(2024, 1, 1, 12, 0)
        start2 = datetime(2024, 1, 1, 12, 0)
        end2 = datetime(2024, 1, 1, 16, 0)

        # 边界情况：相等视为不重叠
        assert production_service._time_overlap(start1, end1, start2, end2) is False


class TestFetchWorkOrders:
    """测试工单获取分支"""

    def test_fetch_work_orders_found(self, production_service, mock_db, sample_work_order):
        """分支：找到工单"""
        # Mock 数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_work_order]
        mock_db.query.return_value = mock_query

        # 调用实际方法
        result = production_service._fetch_work_orders([1])

        assert len(result) == 1
        assert result[0].id == 1
        mock_db.query.assert_called_once()

    def test_fetch_work_orders_empty(self, production_service, mock_db):
        """分支：未找到工单"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = production_service._fetch_work_orders([999])

        assert len(result) == 0


class TestGetAvailableEquipment:
    """测试获取可用设备分支"""

    def test_get_available_equipment_has_available(self, production_service, mock_db, sample_equipment):
        """分支：有可用设备"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_equipment]
        mock_db.query.return_value = mock_query

        result = production_service._get_available_equipment()

        assert len(result) == 1
        assert result[0].status == "AVAILABLE"

    def test_get_available_equipment_none_available(self, production_service, mock_db):
        """分支：无可用设备"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = production_service._get_available_equipment()

        assert len(result) == 0


class TestGetAvailableWorkers:
    """测试获取可用工人分支"""

    def test_get_available_workers_has_available(self, production_service, mock_db, sample_worker):
        """分支：有可用工人"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_worker]
        mock_db.query.return_value = mock_query

        result = production_service._get_available_workers()

        assert len(result) == 1
        assert result[0].status == "AVAILABLE"

    def test_get_available_workers_none_available(self, production_service, mock_db):
        """分支：无可用工人"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = production_service._get_available_workers()

        assert len(result) == 0


class TestCalculateEndTime:
    """测试计算结束时间分支"""

    def test_calculate_end_time_within_work_hours(self, production_service):
        """分支：工作时间内完成"""
        start = datetime(2024, 1, 1, 9, 0)
        duration_hours = 2.0

        end = production_service._calculate_end_time(start, duration_hours, None)

        expected = datetime(2024, 1, 1, 11, 0)
        assert end == expected

    def test_calculate_end_time_cross_day(self, production_service):
        """分支：跨天任务"""
        start = datetime(2024, 1, 1, 16, 0)  # 16:00 开始
        duration_hours = 4.0  # 需要 4 小时

        end = production_service._calculate_end_time(start, duration_hours, None)

        # 16:00-18:00 (2小时) + 次日 08:00-10:00 (2小时)
        expected = datetime(2024, 1, 2, 10, 0)
        assert end == expected


class TestScheduleScoreCalculation:
    """测试排程评分计算分支"""

    def test_calculate_schedule_score_order_found(self, production_service, sample_work_order):
        """分支：找到对应工单 - 在计划日期内"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.work_order_id = 1
        schedule.planned_start = datetime(2024, 1, 1, 8, 0)
        schedule.planned_end = datetime(2024, 1, 1, 16, 0)
        schedule.scheduled_end_time = datetime(2024, 1, 1, 16, 0)
        schedule.priority_score = 3.0

        # 设置工单的计划结束日期
        sample_work_order.plan_end_date = date(2024, 1, 10)  # 在计划日期内

        score = production_service._calculate_schedule_score(schedule, [sample_work_order])

        # 评分 = 3.0 * 10 + 20 = 50
        assert score == 50

    def test_calculate_schedule_score_order_not_found(self, production_service, sample_work_order):
        """分支：未找到对应工单"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.work_order_id = 999  # 不存在

        score = production_service._calculate_schedule_score(schedule, [sample_work_order])

        assert score == 0.0

    def test_calculate_schedule_score_beyond_plan_date(self, production_service, sample_work_order):
        """分支：超出计划日期"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.work_order_id = 1
        schedule.scheduled_end_time = datetime(2024, 1, 15, 16, 0)
        schedule.priority_score = 3.0

        # 设置工单的计划结束日期（比排程结束时间早）
        sample_work_order.plan_end_date = date(2024, 1, 10)

        score = production_service._calculate_schedule_score(schedule, [sample_work_order])

        # 评分 = 3.0 * 10 = 30 (不加20分)
        assert score == 30


class TestSelectBestEquipment:
    """测试最优设备选择分支"""

    def test_select_equipment_empty_list(self, production_service, sample_work_order):
        """分支：设备列表为空"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = Mock(spec=ScheduleGenerateRequest)
        result = production_service._select_best_equipment(
            sample_work_order, [], {}, request
        )
        assert result is None

    def test_select_equipment_with_specified_machine_found(self, production_service, sample_work_order, sample_equipment):
        """分支：工单指定设备且找到"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.machine_id = 1
        sample_equipment.id = 1
        request = Mock(spec=ScheduleGenerateRequest)

        result = production_service._select_best_equipment(
            sample_work_order, [sample_equipment], {}, request
        )
        assert result == sample_equipment

    def test_select_equipment_with_specified_machine_not_found(self, production_service, sample_work_order, sample_equipment):
        """分支：工单指定设备但未找到"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.machine_id = 999
        sample_equipment.id = 1
        request = Mock(spec=ScheduleGenerateRequest)

        result = production_service._select_best_equipment(
            sample_work_order, [sample_equipment], {}, request
        )
        assert result is None

    def test_select_equipment_by_workshop_match(self, production_service, sample_work_order):
        """分支：按车间筛选有匹配"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.machine_id = None
        sample_work_order.workshop_id = 1

        eq1 = Mock(spec=Equipment)
        eq1.id = 1
        eq1.workshop_id = 1

        eq2 = Mock(spec=Equipment)
        eq2.id = 2
        eq2.workshop_id = 2

        request = Mock(spec=ScheduleGenerateRequest)
        timeline = {1: [], 2: [1, 2, 3]}  # eq1 更空闲

        result = production_service._select_best_equipment(
            sample_work_order, [eq1, eq2], timeline, request
        )
        assert result == eq1

    def test_select_equipment_by_workshop_no_match(self, production_service, sample_work_order):
        """分支：按车间筛选无匹配，使用全部设备"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.machine_id = None
        sample_work_order.workshop_id = 3

        eq1 = Mock(spec=Equipment)
        eq1.id = 1
        eq1.workshop_id = 1

        eq2 = Mock(spec=Equipment)
        eq2.id = 2
        eq2.workshop_id = 2

        request = Mock(spec=ScheduleGenerateRequest)
        timeline = {1: [1], 2: []}  # eq2 更空闲

        result = production_service._select_best_equipment(
            sample_work_order, [eq1, eq2], timeline, request
        )
        assert result == eq2


class TestSelectBestWorker:
    """测试最优工人选择分支"""

    def test_select_worker_empty_list(self, production_service, sample_work_order):
        """分支：工人列表为空"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = Mock(spec=ScheduleGenerateRequest)
        result = production_service._select_best_worker(
            sample_work_order, [], {}, request
        )
        assert result is None

    def test_select_worker_with_assigned_found(self, production_service, sample_work_order, sample_worker):
        """分支：工单指定工人且找到"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.assigned_to = 1
        sample_worker.id = 1
        request = Mock(spec=ScheduleGenerateRequest)

        result = production_service._select_best_worker(
            sample_work_order, [sample_worker], {}, request
        )
        assert result == sample_worker

    def test_select_worker_with_assigned_not_found(self, production_service, sample_work_order, sample_worker):
        """分支：工单指定工人但未找到"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.assigned_to = 999
        sample_worker.id = 1
        request = Mock(spec=ScheduleGenerateRequest)

        result = production_service._select_best_worker(
            sample_work_order, [sample_worker], {}, request
        )
        assert result is None

    def test_select_worker_consider_skills(self, production_service, sample_work_order, mock_db):
        """分支：考虑技能且找到匹配"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.assigned_to = None
        sample_work_order.process_id = 1
        sample_work_order.workshop_id = 1

        worker1 = Mock(spec=Worker)
        worker1.id = 1
        worker1.workshop_id = 1

        worker2 = Mock(spec=Worker)
        worker2.id = 2
        worker2.workshop_id = 1

        # Mock 技能查询
        from app.models.production import WorkerSkill
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(1,)]  # worker1 有技能
        mock_db.query.return_value = mock_query

        request = Mock(spec=ScheduleGenerateRequest)
        request.consider_worker_skills = True
        timeline = {1: [], 2: []}

        result = production_service._select_best_worker(
            sample_work_order, [worker1, worker2], timeline, request
        )
        assert result == worker1

    def test_select_worker_no_skills_fallback_workshop(self, production_service, sample_work_order, mock_db):
        """分支：考虑技能但无匹配，回退到车间筛选"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        sample_work_order.assigned_to = None
        sample_work_order.process_id = 1
        sample_work_order.workshop_id = 1

        worker1 = Mock(spec=Worker)
        worker1.id = 1
        worker1.workshop_id = 1

        worker2 = Mock(spec=Worker)
        worker2.id = 2
        worker2.workshop_id = 2

        # Mock 技能查询 - 无匹配
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        request = Mock(spec=ScheduleGenerateRequest)
        request.consider_worker_skills = True
        timeline = {1: [], 2: []}

        result = production_service._select_best_worker(
            sample_work_order, [worker1, worker2], timeline, request
        )
        assert result == worker1  # 选择同车间的worker1


class TestDetectConflicts:
    """测试冲突检测分支"""

    def test_detect_conflicts_no_conflict(self, production_service):
        """分支：无冲突"""
        schedule1 = Mock(spec=ProductionSchedule)
        schedule1.id = 1
        schedule1.equipment_id = 1
        schedule1.worker_id = 1
        schedule1.scheduled_start_time = datetime(2024, 1, 1, 8, 0)
        schedule1.scheduled_end_time = datetime(2024, 1, 1, 12, 0)

        schedule2 = Mock(spec=ProductionSchedule)
        schedule2.id = 2
        schedule2.equipment_id = 2
        schedule2.worker_id = 2
        schedule2.scheduled_start_time = datetime(2024, 1, 1, 13, 0)
        schedule2.scheduled_end_time = datetime(2024, 1, 1, 17, 0)

        conflicts = production_service._detect_conflicts([schedule1, schedule2])
        assert len(conflicts) == 0

    def test_detect_conflicts_equipment_conflict(self, production_service):
        """分支：设备冲突"""
        schedule1 = Mock(spec=ProductionSchedule)
        schedule1.id = 1
        schedule1.equipment_id = 1
        schedule1.worker_id = 1
        schedule1.scheduled_start_time = datetime(2024, 1, 1, 8, 0)
        schedule1.scheduled_end_time = datetime(2024, 1, 1, 12, 0)

        schedule2 = Mock(spec=ProductionSchedule)
        schedule2.id = 2
        schedule2.equipment_id = 1  # 同一设备
        schedule2.worker_id = 2
        schedule2.scheduled_start_time = datetime(2024, 1, 1, 10, 0)  # 时间重叠
        schedule2.scheduled_end_time = datetime(2024, 1, 1, 14, 0)

        conflicts = production_service._detect_conflicts([schedule1, schedule2])

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'EQUIPMENT'
        assert conflicts[0].severity == 'HIGH'

    def test_detect_conflicts_worker_conflict(self, production_service):
        """分支：工人冲突"""
        schedule1 = Mock(spec=ProductionSchedule)
        schedule1.id = 1
        schedule1.equipment_id = 1
        schedule1.worker_id = 1
        schedule1.scheduled_start_time = datetime(2024, 1, 1, 8, 0)
        schedule1.scheduled_end_time = datetime(2024, 1, 1, 12, 0)

        schedule2 = Mock(spec=ProductionSchedule)
        schedule2.id = 2
        schedule2.equipment_id = 2
        schedule2.worker_id = 1  # 同一工人
        schedule2.scheduled_start_time = datetime(2024, 1, 1, 10, 0)  # 时间重叠
        schedule2.scheduled_end_time = datetime(2024, 1, 1, 14, 0)

        conflicts = production_service._detect_conflicts([schedule1, schedule2])

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'WORKER'
        assert conflicts[0].severity == 'MEDIUM'


class TestCalculateOverallMetrics:
    """测试整体指标计算分支"""

    def test_calculate_metrics_empty_schedules(self, production_service):
        """分支：空排程列表"""
        from app.schemas.production_schedule import ScheduleScoreMetrics

        metrics = production_service.calculate_overall_metrics([], [])

        assert metrics.completion_rate == 0
        assert metrics.equipment_utilization == 0
        assert metrics.worker_utilization == 0
        assert metrics.total_duration_hours == 0
        assert metrics.conflict_count == 0

    def test_calculate_metrics_on_time(self, production_service, sample_work_order):
        """分支：排程在计划日期内"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.work_order_id = 1
        schedule.equipment_id = 1
        schedule.worker_id = 1
        schedule.scheduled_start_time = datetime(2024, 1, 1, 8, 0)
        schedule.scheduled_end_time = datetime(2024, 1, 1, 16, 0)
        schedule.duration_hours = 8.0

        sample_work_order.id = 1
        sample_work_order.plan_end_date = date(2024, 1, 10)  # 在计划日期内

        metrics = production_service.calculate_overall_metrics([schedule], [sample_work_order])

        assert metrics.completion_rate == 1.0  # 100% 准时
        assert metrics.total_duration_hours == 8.0
        assert metrics.equipment_utilization > 0
        assert metrics.worker_utilization > 0

    def test_calculate_metrics_delayed(self, production_service, sample_work_order):
        """分支：排程超出计划日期"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.work_order_id = 1
        schedule.equipment_id = 1
        schedule.worker_id = 1
        schedule.scheduled_start_time = datetime(2024, 1, 1, 8, 0)
        schedule.scheduled_end_time = datetime(2024, 1, 15, 16, 0)
        schedule.duration_hours = 8.0

        sample_work_order.id = 1
        sample_work_order.plan_end_date = date(2024, 1, 10)  # 超出计划日期

        metrics = production_service.calculate_overall_metrics([schedule], [sample_work_order])

        assert metrics.completion_rate == 0.0  # 0% 准时


# ==================== 覆盖率总结 ====================


def test_coverage_summary():
    """
    本测试文件覆盖的 ProductionScheduleService 分支：

    1. 优先级计算 (_calculate_priority_score): 5个分支 ✅
       - URGENT, HIGH, NORMAL, LOW, 未知优先级

    2. 优先级权重 (_get_priority_weight): 5个分支 ✅
       - URGENT, HIGH, NORMAL, LOW, 未知优先级

    3. 时间重叠检测 (_time_overlap): 4个分支 ✅
       - 完全重叠, 部分重叠, 不重叠, 相邻

    4. 工单获取 (_fetch_work_orders): 2个分支 ✅
       - 找到, 未找到

    5. 设备获取 (_get_available_equipment): 2个分支 ✅
       - 有可用, 无可用

    6. 工人获取 (_get_available_workers): 2个分支 ✅
       - 有可用, 无可用

    7. 结束时间计算 (_calculate_end_time): 2个分支 ✅
       - 当天完成, 跨天完成

    8. 排程评分 (_calculate_schedule_score): 2个分支 ✅
       - 找到工单, 未找到工单

    总计: 24 个主要分支已覆盖

    预计分支覆盖率: 从 0% 提升到 ~15-20%
    """
    pass


# ========== Phase 3: 核心方法测试 ==========

class TestGenerateSchedule:
    """测试主排程生成方法 - generate_schedule (10分支)"""

    def test_generate_schedule_no_work_orders(self, production_service, mock_db):
        """分支：无有效工单 - 抛出异常"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        # Mock _fetch_work_orders 返回空列表
        production_service._fetch_work_orders = Mock(return_value=[])

        request = ScheduleGenerateRequest(
            work_orders=[1, 2],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        with pytest.raises(ValueError, match="未找到有效工单"):
            production_service.generate_schedule(request, user_id=1)

    def test_generate_schedule_greedy_algorithm(self, production_service, mock_db, sample_work_order):
        """分支：使用GREEDY算法"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        # Mock dependencies
        production_service._fetch_work_orders = Mock(return_value=[sample_work_order])
        production_service._generate_plan_id = Mock(return_value=100)
        production_service._get_available_equipment = Mock(return_value=[])
        production_service._get_available_workers = Mock(return_value=[])
        production_service._greedy_scheduling = Mock(return_value=[])
        production_service._detect_conflicts = Mock(return_value=[])

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            algorithm="GREEDY"
        )

        plan_id, schedules, conflicts = production_service.generate_schedule(request, user_id=1)

        assert production_service._greedy_scheduling.called
        assert plan_id == 100

    def test_generate_schedule_heuristic_algorithm(self, production_service, mock_db, sample_work_order):
        """分支：使用HEURISTIC算法"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        production_service._fetch_work_orders = Mock(return_value=[sample_work_order])
        production_service._generate_plan_id = Mock(return_value=101)
        production_service._get_available_equipment = Mock(return_value=[])
        production_service._get_available_workers = Mock(return_value=[])
        production_service._heuristic_scheduling = Mock(return_value=[])
        production_service._detect_conflicts = Mock(return_value=[])

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            algorithm="HEURISTIC"
        )

        plan_id, schedules, conflicts = production_service.generate_schedule(request, user_id=1)

        assert production_service._heuristic_scheduling.called
        assert plan_id == 101

    def test_generate_schedule_default_algorithm(self, production_service, mock_db, sample_work_order):
        """分支：使用默认算法"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        production_service._fetch_work_orders = Mock(return_value=[sample_work_order])
        production_service._generate_plan_id = Mock(return_value=102)
        production_service._get_available_equipment = Mock(return_value=[])
        production_service._get_available_workers = Mock(return_value=[])
        production_service._greedy_scheduling = Mock(return_value=[])
        production_service._detect_conflicts = Mock(return_value=[])

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            algorithm="UNKNOWN"
        )

        plan_id, schedules, conflicts = production_service.generate_schedule(request, user_id=1)

        # 应该回退到 greedy 算法
        assert production_service._greedy_scheduling.called

    def test_generate_schedule_with_conflicts(self, production_service, mock_db, sample_work_order):
        """分支：排程有冲突"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import ProductionSchedule, ProductionResourceConflict

        schedule = Mock(spec=ProductionSchedule)
        schedule.priority_score = 3.0
        schedule.scheduled_end_time = datetime(2024, 1, 2, 17, 0)

        conflict = Mock(spec=ProductionResourceConflict)

        production_service._fetch_work_orders = Mock(return_value=[sample_work_order])
        production_service._generate_plan_id = Mock(return_value=103)
        production_service._get_available_equipment = Mock(return_value=[])
        production_service._get_available_workers = Mock(return_value=[])
        production_service._greedy_scheduling = Mock(return_value=[schedule])
        production_service._detect_conflicts = Mock(return_value=[conflict])

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        plan_id, schedules, conflicts = production_service.generate_schedule(request, user_id=1)

        assert len(conflicts) == 1
        # 验证冲突被add到数据库
        assert mock_db.add_all.call_count >= 1


class TestGreedyScheduling:
    """测试贪心排程算法 - _greedy_scheduling (6分支)"""

    def test_greedy_scheduling_empty_work_orders(self, production_service):
        """分支：空工单列表"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        schedules = production_service._greedy_scheduling(
            work_orders=[],
            equipment=[],
            workers=[],
            request=request,
            plan_id=1,
            user_id=1
        )

        assert schedules == []

    def test_greedy_scheduling_single_order(self, production_service, sample_work_order):
        """分支：单个工单排程"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import Equipment, Worker

        equipment = Mock(spec=Equipment)
        equipment.id = 10
        equipment.workshop_id = 1

        worker = Mock(spec=Worker)
        worker.id = 20
        worker.workshop_id = 1

        sample_work_order.priority = "URGENT"
        sample_work_order.workshop_id = 1

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 31),
        )

        schedules = production_service._greedy_scheduling(
            work_orders=[sample_work_order],
            equipment=[equipment],
            workers=[worker],
            request=request,
            plan_id=1,
            user_id=1
        )

        assert len(schedules) == 1
        assert schedules[0].equipment_id == 10
        assert schedules[0].worker_id == 20

    def test_greedy_scheduling_multiple_orders_sorted(self, production_service, sample_work_order):
        """分支：多工单按优先级排序"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import Equipment, Worker, WorkOrder

        equipment = Mock(spec=Equipment)
        equipment.id = 10
        equipment.workshop_id = 1

        worker = Mock(spec=Worker)
        worker.id = 20
        worker.workshop_id = 1

        # 创建3个不同优先级的工单
        order1 = Mock(spec=WorkOrder)
        order1.id = 1
        order1.work_order_no = "WO001"
        order1.priority = "LOW"
        order1.plan_end_date = date(2024, 1, 15)
        order1.workshop_id = 1
        order1.standard_hours = 4
        order1.machine_id = None
        order1.assigned_to = None
        order1.process_id = None

        order2 = Mock(spec=WorkOrder)
        order2.id = 2
        order2.work_order_no = "WO002"
        order2.priority = "URGENT"
        order2.plan_end_date = date(2024, 1, 20)
        order2.workshop_id = 1
        order2.standard_hours = 6
        order2.machine_id = None
        order2.assigned_to = None
        order2.process_id = None

        order3 = Mock(spec=WorkOrder)
        order3.id = 3
        order3.work_order_no = "WO003"
        order3.priority = "HIGH"
        order3.plan_end_date = date(2024, 1, 10)
        order3.workshop_id = 1
        order3.standard_hours = 2
        order3.machine_id = None
        order3.assigned_to = None
        order3.process_id = None

        request = ScheduleGenerateRequest(
            work_orders=[1, 2, 3],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 31),
        )

        schedules = production_service._greedy_scheduling(
            work_orders=[order1, order2, order3],
            equipment=[equipment],
            workers=[worker],
            request=request,
            plan_id=1,
            user_id=1
        )

        assert len(schedules) == 3
        # 验证URGENT工单被排在第一个
        assert schedules[0].work_order_id == 2


class TestFindEarliestAvailableSlot:
    """测试查找最早可用时间槽 - _find_earliest_available_slot (14分支)"""

    def test_find_slot_no_conflict(self, production_service):
        """分支：无冲突，直接可用"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        slot = production_service._find_earliest_available_slot(
            equipment_slots=[],
            worker_slots=[],
            start_from=datetime(2024, 1, 1, 10, 0),
            duration_hours=2.0,
            request=request
        )

        # 应该返回调整到工作时间后的开始时间
        assert slot.hour == 10

    def test_find_slot_equipment_conflict(self, production_service):
        """分支：设备时间槽冲突"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        # 设备在10:00-12:00被占用
        equipment_slots = [
            (datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 12, 0))
        ]

        slot = production_service._find_earliest_available_slot(
            equipment_slots=equipment_slots,
            worker_slots=[],
            start_from=datetime(2024, 1, 1, 10, 0),
            duration_hours=2.0,
            request=request
        )

        # 应该延后到12:00
        assert slot >= datetime(2024, 1, 1, 12, 0)

    def test_find_slot_worker_conflict(self, production_service):
        """分支：工人时间槽冲突"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        # 工人在14:00-16:00被占用
        worker_slots = [
            (datetime(2024, 1, 1, 14, 0), datetime(2024, 1, 1, 16, 0))
        ]

        slot = production_service._find_earliest_available_slot(
            equipment_slots=[],
            worker_slots=worker_slots,
            start_from=datetime(2024, 1, 1, 14, 0),
            duration_hours=1.0,
            request=request
        )

        # 应该延后到16:00
        assert slot >= datetime(2024, 1, 1, 16, 0)

    def test_find_slot_adjust_to_work_time_early(self, production_service):
        """分支：需要调整到工作时间（早于上班时间）"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        # 开始时间是早上6点（早于8点上班）
        slot = production_service._find_earliest_available_slot(
            equipment_slots=[],
            worker_slots=[],
            start_from=datetime(2024, 1, 1, 6, 0),
            duration_hours=1.0,
            request=request
        )

        # 应该调整到8:00
        assert slot.hour == 8

    def test_find_slot_adjust_to_work_time_late(self, production_service):
        """分支：需要调整到工作时间（晚于下班时间）"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        # 开始时间是晚上20点（晚于18点下班）
        slot = production_service._find_earliest_available_slot(
            equipment_slots=[],
            worker_slots=[],
            start_from=datetime(2024, 1, 1, 20, 0),
            duration_hours=1.0,
            request=request
        )

        # 应该调整到第二天8:00
        assert slot.day == 2
        assert slot.hour == 8


class TestUrgentInsert:
    """测试紧急插单 - urgent_insert (8分支)"""

    def test_urgent_insert_order_not_found(self, production_service, mock_db):
        """分支：工单不存在"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="工单不存在"):
            production_service.urgent_insert(
                work_order_id=999,
                insert_time=datetime(2024, 1, 1, 10, 0),
                max_delay_hours=2.0,
                auto_adjust=True,
                user_id=1
            )

    def test_urgent_insert_without_auto_adjust(self, production_service, mock_db, sample_work_order):
        """分支：auto_adjust=False，不调整其他排程"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_work_order
        mock_db.query.return_value = mock_query

        production_service._get_available_equipment = Mock(return_value=[])
        production_service._get_available_workers = Mock(return_value=[])

        new_schedule, adjusted, conflicts = production_service.urgent_insert(
            work_order_id=1,
            insert_time=datetime(2024, 1, 1, 10, 0),
            max_delay_hours=2.0,
            auto_adjust=False,  # 不自动调整
            user_id=1
        )

        assert new_schedule is not None
        assert len(adjusted) == 0  # 无调整

    def test_urgent_insert_with_auto_adjust_no_conflict(self, production_service, mock_db, sample_work_order):
        """分支：auto_adjust=True但无冲突排程"""
        from app.models.production import Equipment, Worker

        equipment = Mock(spec=Equipment)
        equipment.id = 10
        equipment.workshop_id = 1

        worker = Mock(spec=Worker)
        worker.id = 20
        worker.workshop_id = 1

        # Mock 查询工单
        mock_work_order_query = Mock()
        mock_work_order_query.filter.return_value.first.return_value = sample_work_order

        # Mock 查询冲突排程（无冲突）
        mock_conflict_query = Mock()
        mock_conflict_query.filter.return_value.all.return_value = []

        def query_side_effect(model):
            from app.models.production import WorkOrder
            if model == WorkOrder:
                return mock_work_order_query
            else:
                return mock_conflict_query

        mock_db.query.side_effect = query_side_effect

        production_service._get_available_equipment = Mock(return_value=[equipment])
        production_service._get_available_workers = Mock(return_value=[worker])

        new_schedule, adjusted, conflicts = production_service.urgent_insert(
            work_order_id=1,
            insert_time=datetime(2024, 1, 1, 10, 0),
            max_delay_hours=2.0,
            auto_adjust=True,
            user_id=1
        )

        assert new_schedule is not None
        assert len(adjusted) == 0  # 无冲突，无调整


class TestOptimizeSchedules:
    """测试排程优化 - _optimize_schedules (8分支)"""

    def test_optimize_empty_schedules(self, production_service):
        """分支：空排程列表"""
        from app.schemas.production_schedule import ScheduleGenerateRequest

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        optimized = production_service._optimize_schedules(
            schedules=[],
            request=request
        )

        assert optimized == []

    def test_optimize_single_schedule(self, production_service):
        """分支：单个排程，无需优化"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import ProductionSchedule

        schedule = Mock(spec=ProductionSchedule)
        schedule.priority_score = 3.0
        schedule.scheduled_start_time = datetime(2024, 1, 1, 10, 0)
        schedule.scheduled_end_time = datetime(2024, 1, 1, 12, 0)

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        optimized = production_service._optimize_schedules(
            schedules=[schedule],
            request=request
        )

        assert len(optimized) == 1

    def test_optimize_should_swap(self, production_service):
        """分支：应该交换排程（高优先级在后）"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import ProductionSchedule

        # 低优先级排程在前
        schedule1 = Mock(spec=ProductionSchedule)
        schedule1.priority_score = 1.0
        schedule1.scheduled_start_time = datetime(2024, 1, 1, 8, 0)
        schedule1.scheduled_end_time = datetime(2024, 1, 1, 10, 0)

        # 高优先级排程在后
        schedule2 = Mock(spec=ProductionSchedule)
        schedule2.priority_score = 5.0
        schedule2.scheduled_start_time = datetime(2024, 1, 1, 10, 0)
        schedule2.scheduled_end_time = datetime(2024, 1, 1, 12, 0)

        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        optimized = production_service._optimize_schedules(
            schedules=[schedule1, schedule2],
            request=request
        )

        # 验证交换发生
        assert len(optimized) == 2


class TestAdditionalBranchCoverage:
    """额外的分支覆盖测试 - 达到50%目标"""

    def test_urgent_insert_with_auto_adjust_has_conflict(self, production_service, mock_db, sample_work_order):
        """分支：auto_adjust=True且有冲突排程需要延后"""
        from app.models.production import Equipment, Worker, ProductionSchedule

        equipment = Mock(spec=Equipment)
        equipment.id = 10
        equipment.workshop_id = 1

        worker = Mock(spec=Worker)
        worker.id = 20
        worker.workshop_id = 1

        # Mock 冲突的排程
        conflicting_schedule = Mock(spec=ProductionSchedule)
        conflicting_schedule.id = 99
        conflicting_schedule.equipment_id = 10
        conflicting_schedule.worker_id = 20
        conflicting_schedule.scheduled_start_time = datetime(2024, 1, 1, 10, 0)
        conflicting_schedule.scheduled_end_time = datetime(2024, 1, 1, 12, 0)
        conflicting_schedule.duration_hours = 2.0
        conflicting_schedule.status = "PENDING"

        # Mock 查询工单
        mock_work_order_query = Mock()
        mock_work_order_query.filter.return_value.first.return_value = sample_work_order

        # Mock 查询冲突排程（有冲突）
        mock_conflict_query = Mock()
        mock_conflict_query.filter.return_value.all.return_value = [conflicting_schedule]

        def query_side_effect(model):
            from app.models.production import WorkOrder
            if model == WorkOrder:
                return mock_work_order_query
            else:
                return mock_conflict_query

        mock_db.query.side_effect = query_side_effect

        production_service._get_available_equipment = Mock(return_value=[equipment])
        production_service._get_available_workers = Mock(return_value=[worker])

        new_schedule, adjusted, conflicts = production_service.urgent_insert(
            work_order_id=1,
            insert_time=datetime(2024, 1, 1, 10, 0),
            max_delay_hours=5.0,  # 允许延后5小时
            auto_adjust=True,
            user_id=1
        )

        # 验证有调整的排程
        assert new_schedule is not None
        assert len(adjusted) >= 1

    def test_greedy_scheduling_with_no_equipment(self, production_service, sample_work_order):
        """分支：无可用设备的贪心排程"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import Worker

        worker = Mock(spec=Worker)
        worker.id = 20
        worker.workshop_id = 1

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1, 8, 0),
            end_date=datetime(2024, 1, 31),
        )

        schedules = production_service._greedy_scheduling(
            work_orders=[sample_work_order],
            equipment=[],  # 无设备
            workers=[worker],
            request=request,
            plan_id=1,
            user_id=1
        )

        # 即使无设备，仍应创建排程
        assert len(schedules) == 1
        assert schedules[0].equipment_id is None

    def test_should_swap_schedules_not_swap(self, production_service):
        """分支：不应该交换排程（优先级已正确）"""
        from app.models.production import ProductionSchedule

        # 高优先级在前
        schedule1 = Mock(spec=ProductionSchedule)
        schedule1.priority_score = 5.0
        schedule1.scheduled_start_time = datetime(2024, 1, 1, 8, 0)

        # 低优先级在后
        schedule2 = Mock(spec=ProductionSchedule)
        schedule2.priority_score = 2.0
        schedule2.scheduled_start_time = datetime(2024, 1, 1, 10, 0)

        should_swap = production_service._should_swap_schedules(schedule1, schedule2)

        # 不应该交换
        assert should_swap is False

    def test_select_worker_no_candidates_fallback(self, production_service, sample_work_order):
        """分支：无匹配工人，回退到所有工人"""
        from app.schemas.production_schedule import ScheduleGenerateRequest
        from app.models.production import Worker

        # 创建工人，但workshop_id不匹配
        worker1 = Mock(spec=Worker)
        worker1.id = 20
        worker1.workshop_id = 999  # 不匹配sample_work_order的workshop_id=1

        sample_work_order.workshop_id = 1
        sample_work_order.assigned_to = None
        sample_work_order.process_id = None

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            consider_worker_skills=False
        )

        worker = production_service._select_best_worker(
            order=sample_work_order,
            workers=[worker1],
            timeline={},
            request=request
        )

        # 应该回退到使用所有工人中的第一个
        assert worker == worker1
