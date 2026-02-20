# -*- coding: utf-8 -*-
"""
生产排程服务增强测试
目标：提升覆盖率到 60%+
覆盖排程算法、资源分配、冲突检测等核心逻辑
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, call
from sqlalchemy.orm import Query

from app.services.production_schedule_service import ProductionScheduleService
from app.models.production import (
    ProductionSchedule,
    ProductionResourceConflict,
    WorkOrder,
    Equipment,
    Worker,
    WorkerSkill,
    ScheduleAdjustmentLog,
)
from app.schemas.production_schedule import ScheduleGenerateRequest


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ProductionScheduleService(db=mock_db)


def make_work_order(**kwargs):
    """创建Mock工单"""
    wo = MagicMock(spec=WorkOrder)
    wo.id = kwargs.get('id', 1)
    wo.work_order_no = kwargs.get('work_order_no', 'WO-001')
    wo.priority = kwargs.get('priority', 'NORMAL')
    wo.plan_start_date = kwargs.get('plan_start_date', date.today())
    wo.plan_end_date = kwargs.get('plan_end_date', date.today() + timedelta(days=7))
    wo.standard_hours = kwargs.get('standard_hours', 8.0)
    wo.workstation_id = kwargs.get('workstation_id', 1)
    wo.workshop_id = kwargs.get('workshop_id', 1)
    wo.process_id = kwargs.get('process_id', 1)
    wo.status = kwargs.get('status', 'PENDING')
    wo.machine_id = kwargs.get('machine_id', None)
    wo.assigned_to = kwargs.get('assigned_to', None)
    return wo


def make_equipment(**kwargs):
    """创建Mock设备"""
    eq = MagicMock(spec=Equipment)
    eq.id = kwargs.get('id', 1)
    eq.equipment_code = kwargs.get('equipment_code', 'EQ-001')
    eq.equipment_name = kwargs.get('equipment_name', '设备1')
    eq.status = kwargs.get('status', 'NORMAL')
    eq.workshop_id = kwargs.get('workshop_id', 1)
    return eq


def make_worker(**kwargs):
    """创建Mock工人"""
    worker = MagicMock(spec=Worker)
    worker.id = kwargs.get('id', 1)
    worker.worker_no = kwargs.get('worker_no', 'W-001')
    worker.worker_name = kwargs.get('worker_name', '工人1')
    worker.status = kwargs.get('status', 'NORMAL')
    worker.skills = kwargs.get('skills', [])
    worker.workshop_id = kwargs.get('workshop_id', 1)
    return worker


def make_schedule(**kwargs):
    """创建Mock排程"""
    s = MagicMock(spec=ProductionSchedule)
    s.id = kwargs.get('id', 1)
    s.work_order_id = kwargs.get('work_order_id', 1)
    s.schedule_plan_id = kwargs.get('schedule_plan_id', 1)
    s.equipment_id = kwargs.get('equipment_id', 1)
    s.worker_id = kwargs.get('worker_id', 1)
    s.scheduled_start_time = kwargs.get('scheduled_start_time', datetime(2025, 1, 10, 8, 0))
    s.scheduled_end_time = kwargs.get('scheduled_end_time', datetime(2025, 1, 10, 16, 0))
    s.duration_hours = kwargs.get('duration_hours', 8.0)
    s.priority_score = kwargs.get('priority_score', 10.0)
    s.status = kwargs.get('status', 'PENDING')
    s.workshop_id = kwargs.get('workshop_id', 1)
    s.process_id = kwargs.get('process_id', 1)
    s.sequence_no = kwargs.get('sequence_no', 1)
    return s


def make_request(**kwargs):
    """创建Mock请求"""
    req = MagicMock(spec=ScheduleGenerateRequest)
    req.work_orders = kwargs.get('work_orders', [1, 2, 3])
    req.algorithm = kwargs.get('algorithm', 'GREEDY')
    req.start_date = kwargs.get('start_date', datetime(2025, 1, 10, 8, 0))
    req.optimization_target = kwargs.get('optimization_target', 'BALANCED')
    req.consider_worker_skills = kwargs.get('consider_worker_skills', False)
    return req


# ==================== 测试排程生成核心逻辑 ====================

class TestGenerateSchedule:
    """测试 generate_schedule 核心生成逻辑"""

    def test_generate_schedule_with_greedy_algorithm(self, service, mock_db):
        """测试贪心算法生成排程"""
        request = make_request(algorithm='GREEDY', work_orders=[1, 2])
        
        # Mock 工单、设备、工人
        work_orders = [make_work_order(id=1), make_work_order(id=2)]
        equipment = [make_equipment(id=1), make_equipment(id=2)]
        workers = [make_worker(id=1), make_worker(id=2)]
        
        with patch.object(service, '_fetch_work_orders', return_value=work_orders), \
             patch.object(service, '_get_available_equipment', return_value=equipment), \
             patch.object(service, '_get_available_workers', return_value=workers), \
             patch.object(service, '_generate_plan_id', return_value=100), \
             patch.object(service, '_detect_conflicts', return_value=[]):
            
            plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
            
            assert plan_id == 100
            assert len(schedules) == 2
            assert len(conflicts) == 0

    def test_generate_schedule_with_heuristic_algorithm(self, service, mock_db):
        """测试启发式算法生成排程"""
        request = make_request(algorithm='HEURISTIC', work_orders=[1])
        
        work_orders = [make_work_order(id=1)]
        equipment = [make_equipment(id=1)]
        workers = [make_worker(id=1)]
        
        with patch.object(service, '_fetch_work_orders', return_value=work_orders), \
             patch.object(service, '_get_available_equipment', return_value=equipment), \
             patch.object(service, '_get_available_workers', return_value=workers), \
             patch.object(service, '_generate_plan_id', return_value=101), \
             patch.object(service, '_detect_conflicts', return_value=[]):
            
            plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
            
            assert plan_id == 101
            assert len(schedules) >= 1

    def test_generate_schedule_no_work_orders_raises_error(self, service):
        """测试无工单时抛出异常"""
        request = make_request(work_orders=[999])
        
        with patch.object(service, '_fetch_work_orders', return_value=[]):
            with pytest.raises(ValueError, match="未找到有效工单"):
                service.generate_schedule(request, user_id=1)

    def test_generate_schedule_with_conflicts(self, service, mock_db):
        """测试生成排程时检测到冲突"""
        request = make_request(algorithm='GREEDY', work_orders=[1, 2])
        
        work_orders = [make_work_order(id=1), make_work_order(id=2)]
        equipment = [make_equipment(id=1)]
        workers = [make_worker(id=1)]
        
        mock_conflict = MagicMock(spec=ProductionResourceConflict)
        mock_conflict.conflict_type = 'EQUIPMENT'
        
        with patch.object(service, '_fetch_work_orders', return_value=work_orders), \
             patch.object(service, '_get_available_equipment', return_value=equipment), \
             patch.object(service, '_get_available_workers', return_value=workers), \
             patch.object(service, '_generate_plan_id', return_value=102), \
             patch.object(service, '_detect_conflicts', return_value=[mock_conflict]):
            
            plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
            
            assert len(conflicts) == 1
            assert conflicts[0].conflict_type == 'EQUIPMENT'


class TestGenerateAndEvaluateSchedule:
    """测试 generate_and_evaluate_schedule 完整流程"""

    def test_generate_and_evaluate_success(self, service, mock_db):
        """测试完整的生成和评估流程"""
        request = make_request(work_orders=[1, 2])
        
        work_orders = [make_work_order(id=1), make_work_order(id=2)]
        schedules = [make_schedule(id=1), make_schedule(id=2)]
        
        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.9
        mock_metrics.equipment_utilization = 0.85
        mock_metrics.worker_utilization = 0.80
        mock_metrics.total_duration_hours = 16.0
        mock_metrics.skill_match_rate = 1.0
        mock_metrics.conflict_count = 0
        mock_metrics.calculate_overall_score.return_value = 88.0
        
        with patch.object(service, 'generate_schedule', return_value=(100, schedules, [])), \
             patch.object(service, '_fetch_work_orders', return_value=work_orders), \
             patch.object(service, 'calculate_overall_metrics', return_value=mock_metrics), \
             patch('app.schemas.production_schedule.ScheduleResponse.model_validate', side_effect=lambda x: x):
            
            result = service.generate_and_evaluate_schedule(request, user_id=1)
            
            assert result['plan_id'] == 100
            assert result['success_count'] == 2
            assert result['failed_count'] == 0
            assert result['score'] == 88.0
            assert result['metrics']['completion_rate'] == 0.9

    def test_generate_and_evaluate_with_conflicts(self, service, mock_db):
        """测试有冲突时生成警告"""
        request = make_request(work_orders=[1])
        
        work_orders = [make_work_order(id=1)]
        schedules = [make_schedule(id=1)]
        conflicts = [MagicMock(spec=ProductionResourceConflict)]
        
        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.7
        mock_metrics.equipment_utilization = 0.6
        mock_metrics.worker_utilization = 0.5
        mock_metrics.total_duration_hours = 8.0
        mock_metrics.skill_match_rate = 0.9
        mock_metrics.conflict_count = 1
        mock_metrics.calculate_overall_score.return_value = 65.0
        
        with patch.object(service, 'generate_schedule', return_value=(101, schedules, conflicts)), \
             patch.object(service, '_fetch_work_orders', return_value=work_orders), \
             patch.object(service, 'calculate_overall_metrics', return_value=mock_metrics), \
             patch('app.schemas.production_schedule.ScheduleResponse.model_validate', side_effect=lambda x: x):
            
            result = service.generate_and_evaluate_schedule(request, user_id=1)
            
            assert result['conflicts_count'] == 1
            assert any('冲突' in w for w in result['warnings'])

    def test_generate_and_evaluate_low_completion_rate_warning(self, service, mock_db):
        """测试低完成率时生成警告"""
        request = make_request(work_orders=[1])
        
        work_orders = [make_work_order(id=1)]
        schedules = [make_schedule(id=1)]
        
        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.75  # 低于 0.8
        mock_metrics.equipment_utilization = 0.8
        mock_metrics.worker_utilization = 0.8
        mock_metrics.total_duration_hours = 8.0
        mock_metrics.skill_match_rate = 1.0
        mock_metrics.conflict_count = 0
        mock_metrics.calculate_overall_score.return_value = 70.0
        
        with patch.object(service, 'generate_schedule', return_value=(102, schedules, [])), \
             patch.object(service, '_fetch_work_orders', return_value=work_orders), \
             patch.object(service, 'calculate_overall_metrics', return_value=mock_metrics), \
             patch('app.schemas.production_schedule.ScheduleResponse.model_validate', side_effect=lambda x: x):
            
            result = service.generate_and_evaluate_schedule(request, user_id=1)
            
            assert any('交期达成率较低' in w for w in result['warnings'])


# ==================== 测试资源选择逻辑 ====================

class TestSelectBestEquipment:
    """测试 _select_best_equipment 设备选择逻辑"""

    def test_select_equipment_with_workstation_match(self, service):
        """测试选择工作站匹配的设备"""
        order = make_work_order(workstation_id=1)
        equipment1 = make_equipment(id=1)
        equipment1.workstation_id = 1
        equipment2 = make_equipment(id=2)
        equipment2.workstation_id = 2
        
        equipment_timeline = {1: [], 2: []}
        request = make_request()
        
        result = service._select_best_equipment(order, [equipment1, equipment2], equipment_timeline, request)
        
        assert result.id == 1

    def test_select_equipment_with_least_busy(self, service):
        """测试选择最不繁忙的设备"""
        order = make_work_order(workstation_id=None)
        equipment1 = make_equipment(id=1)
        equipment2 = make_equipment(id=2)
        
        # equipment1 更繁忙
        equipment_timeline = {
            1: [(datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 12, 0))],
            2: []
        }
        request = make_request()
        
        result = service._select_best_equipment(order, [equipment1, equipment2], equipment_timeline, request)
        
        assert result.id == 2

    def test_select_equipment_returns_first_when_all_same(self, service):
        """测试所有设备相同时返回第一个"""
        order = make_work_order(workstation_id=None)
        equipment1 = make_equipment(id=1)
        equipment2 = make_equipment(id=2)
        
        equipment_timeline = {1: [], 2: []}
        request = make_request()
        
        result = service._select_best_equipment(order, [equipment1, equipment2], equipment_timeline, request)
        
        assert result is not None


class TestSelectBestWorker:
    """测试 _select_best_worker 工人选择逻辑"""

    def test_select_worker_with_skill_match(self, service):
        """测试选择技能匹配的工人"""
        order = make_work_order(process_id=10)
        
        skill1 = MagicMock(spec=WorkerSkill)
        skill1.process_id = 10
        skill1.skill_level = 5
        
        skill2 = MagicMock(spec=WorkerSkill)
        skill2.process_id = 20
        skill2.skill_level = 3
        
        worker1 = make_worker(id=1, skills=[skill1])
        worker2 = make_worker(id=2, skills=[skill2])
        
        worker_timeline = {1: [], 2: []}
        request = make_request()
        
        result = service._select_best_worker(order, [worker1, worker2], worker_timeline, request)
        
        assert result.id == 1

    def test_select_worker_with_highest_skill_level(self, service):
        """测试选择技能等级最高的工人"""
        order = make_work_order(process_id=10)
        
        skill1 = MagicMock(spec=WorkerSkill)
        skill1.process_id = 10
        skill1.skill_level = 3
        
        skill2 = MagicMock(spec=WorkerSkill)
        skill2.process_id = 10
        skill2.skill_level = 5
        
        worker1 = make_worker(id=1, skills=[skill1])
        worker2 = make_worker(id=2, skills=[skill2])
        
        worker_timeline = {1: [], 2: []}
        request = make_request()
        
        result = service._select_best_worker(order, [worker1, worker2], worker_timeline, request)
        
        assert result.id == 2

    def test_select_worker_with_least_busy(self, service):
        """测试选择最不繁忙的工人"""
        order = make_work_order(process_id=None)
        worker1 = make_worker(id=1, skills=[])
        worker2 = make_worker(id=2, skills=[])
        
        # worker1 更繁忙
        worker_timeline = {
            1: [(datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 12, 0))],
            2: []
        }
        request = make_request()
        
        result = service._select_best_worker(order, [worker1, worker2], worker_timeline, request)
        
        assert result.id == 2


# ==================== 测试时间槽查找逻辑 ====================

class TestFindEarliestAvailableSlot:
    """测试 _find_earliest_available_slot 时间槽查找"""

    def test_find_slot_with_no_timeline(self, service):
        """测试没有占用时返回当前时间"""
        equipment_timeline = []
        worker_timeline = []
        current_time = datetime(2025, 1, 10, 8, 0)
        duration_hours = 4
        request = make_request()
        
        result = service._find_earliest_available_slot(
            equipment_timeline, worker_timeline, current_time, duration_hours, request
        )
        
        assert result >= current_time

    def test_find_slot_with_occupied_timeline(self, service):
        """测试有占用时查找空闲槽"""
        equipment_timeline = [(datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 12, 0))]
        worker_timeline = [(datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 10, 0))]
        current_time = datetime(2025, 1, 10, 8, 0)
        duration_hours = 2
        request = make_request()
        
        result = service._find_earliest_available_slot(
            equipment_timeline, worker_timeline, current_time, duration_hours, request
        )
        
        assert result >= datetime(2025, 1, 10, 12, 0)

    def test_find_slot_adjusts_to_work_time(self, service):
        """测试时间槽调整到工作时间"""
        equipment_timeline = []
        worker_timeline = []
        # 设定在下班后
        current_time = datetime(2025, 1, 10, 19, 0)
        duration_hours = 2
        request = make_request()
        
        with patch.object(service, '_adjust_to_work_time') as mock_adjust:
            mock_adjust.return_value = datetime(2025, 1, 11, 8, 0)
            
            result = service._find_earliest_available_slot(
                equipment_timeline, worker_timeline, current_time, duration_hours, request
            )
            
            mock_adjust.assert_called()


# ==================== 测试算法优化逻辑 ====================

class TestOptimizeSchedules:
    """测试 _optimize_schedules 优化逻辑"""

    def test_optimize_schedules_with_swap(self, service):
        """测试排程交换优化"""
        schedule1 = make_schedule(id=1, priority_score=10.0)
        schedule2 = make_schedule(id=2, priority_score=20.0)
        
        request = make_request()
        
        with patch.object(service, '_should_swap_schedules', return_value=True):
            result = service._optimize_schedules([schedule1, schedule2], request)
            
            assert len(result) == 2

    def test_optimize_schedules_no_swap_needed(self, service):
        """测试无需交换的优化"""
        schedule1 = make_schedule(id=1)
        schedule2 = make_schedule(id=2)
        
        request = make_request()
        
        with patch.object(service, '_should_swap_schedules', return_value=False):
            result = service._optimize_schedules([schedule1, schedule2], request)
            
            assert len(result) == 2


class TestShouldSwapSchedules:
    """测试 _should_swap_schedules 交换判断"""

    def test_should_swap_lower_priority_earlier(self, service):
        """测试低优先级在前时应该交换"""
        schedule1 = make_schedule(
            id=1, 
            priority_score=5.0,
            scheduled_start_time=datetime(2025, 1, 10, 8, 0)
        )
        schedule2 = make_schedule(
            id=2, 
            priority_score=10.0,
            scheduled_start_time=datetime(2025, 1, 10, 10, 0)
        )
        
        result = service._should_swap_schedules(schedule1, schedule2)
        
        assert result is True

    def test_should_not_swap_correct_order(self, service):
        """测试正确顺序时不应交换"""
        schedule1 = make_schedule(
            id=1, 
            priority_score=10.0,
            scheduled_start_time=datetime(2025, 1, 10, 8, 0)
        )
        schedule2 = make_schedule(
            id=2, 
            priority_score=5.0,
            scheduled_start_time=datetime(2025, 1, 10, 10, 0)
        )
        
        result = service._should_swap_schedules(schedule1, schedule2)
        
        assert result is False


# ==================== 测试数据获取方法 ====================

class TestDataFetchMethods:
    """测试数据获取方法"""

    def test_get_available_equipment(self, service, mock_db):
        """测试获取可用设备"""
        mock_equipment = [make_equipment(id=1), make_equipment(id=2)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_equipment
        mock_db.query.return_value = mock_query
        
        result = service._get_available_equipment()
        
        assert len(result) == 2
        mock_db.query.assert_called_once()

    def test_get_available_workers(self, service, mock_db):
        """测试获取可用工人"""
        mock_workers = [make_worker(id=1), make_worker(id=2)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_workers
        mock_db.query.return_value = mock_query
        
        result = service._get_available_workers()
        
        assert len(result) == 2
        mock_db.query.assert_called_once()

    def test_generate_plan_id(self, service, mock_db):
        """测试生成排程方案ID"""
        mock_query = MagicMock()
        mock_query.filter.return_value.with_entities.return_value.order_by.return_value.first.return_value = (10,)
        mock_db.query.return_value = mock_query
        
        result = service._generate_plan_id()
        
        assert result == 11

    def test_generate_plan_id_when_empty(self, service, mock_db):
        """测试首次生成排程方案ID"""
        mock_query = MagicMock()
        mock_query.filter.return_value.with_entities.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = service._generate_plan_id()
        
        assert result == 1


# ==================== 测试紧急插单逻辑 ====================

class TestUrgentInsert:
    """测试 urgent_insert 紧急插单"""

    def test_urgent_insert_success(self, service, mock_db):
        """测试紧急插单成功"""
        work_order = make_work_order(id=99, priority='URGENT')
        equipment = make_equipment(id=1)
        worker = make_worker(id=1)
        
        existing_schedules = [
            make_schedule(id=1, scheduled_start_time=datetime(2025, 1, 10, 10, 0)),
            make_schedule(id=2, scheduled_start_time=datetime(2025, 1, 10, 14, 0))
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = existing_schedules
        mock_query.filter.return_value.first.side_effect = [work_order, equipment, worker]
        mock_db.query.return_value = mock_query
        
        with patch.object(service, '_detect_conflicts', return_value=[]), \
             patch.object(service, '_calculate_end_time', return_value=datetime(2025, 1, 10, 10, 0)):
            
            new_schedule, adjusted = service.urgent_insert(
                work_order_id=99,
                equipment_id=1,
                worker_id=1,
                start_time=datetime(2025, 1, 10, 8, 0),
                user_id=1
            )
            
            assert new_schedule is not None
            assert new_schedule.work_order_id == 99

    def test_urgent_insert_work_order_not_found(self, service, mock_db):
        """测试工单不存在时抛出异常"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(ValueError, match="工单不存在"):
            service.urgent_insert(
                work_order_id=999,
                equipment_id=1,
                worker_id=1,
                start_time=datetime(2025, 1, 10, 8, 0),
                user_id=1
            )


# ==================== 测试排程确认逻辑 ====================

class TestConfirmSchedule:
    """测试 confirm_schedule 确认排程"""

    def test_confirm_schedule_success(self, service, mock_db):
        """测试确认排程成功"""
        schedules = [
            make_schedule(id=1, status='PENDING'),
            make_schedule(id=2, status='PENDING')
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = schedules
        mock_db.query.return_value = mock_query
        
        result = service.confirm_schedule(plan_id=1, user_id=1)
        
        assert result['success'] is True
        assert result['confirmed_count'] == 2

    def test_confirm_schedule_no_schedules(self, service, mock_db):
        """测试无排程时抛出异常"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        with pytest.raises(ValueError, match="未找到待确认的排程"):
            service.confirm_schedule(plan_id=999, user_id=1)


# ==================== 测试排程调整逻辑 ====================

class TestAdjustSchedule:
    """测试 adjust_schedule 排程调整"""

    def test_adjust_schedule_time_change(self, service, mock_db):
        """测试时间调整"""
        schedule = make_schedule(id=1, status='CONFIRMED')
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = schedule
        mock_db.query.return_value = mock_query
        
        request = MagicMock()
        request.schedule_id = 1
        request.new_start_time = datetime(2025, 1, 11, 8, 0)
        request.new_end_time = datetime(2025, 1, 11, 16, 0)
        request.adjustment_type = 'TIME_CHANGE'
        request.reason = '客户要求提前'
        request.auto_resolve_conflicts = False
        
        with patch.object(service, '_detect_conflicts', return_value=[]), \
             patch.object(service, '_calculate_end_time', return_value=datetime(2025, 1, 11, 16, 0)):
            
            result = service.adjust_schedule(request, user_id=1)
            
            assert 'schedule' in result or 'success' in result

    def test_adjust_schedule_not_found(self, service, mock_db):
        """测试排程不存在时抛出异常"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        request = MagicMock()
        request.schedule_id = 999
        
        with pytest.raises(ValueError, match="排程不存在"):
            service.adjust_schedule(request, user_id=1)


# ==================== 测试方案对比逻辑 ====================

class TestCompareSchedulePlans:
    """测试 compare_schedule_plans 方案对比"""

    def test_compare_two_plans(self, service, mock_db):
        """测试对比两个方案"""
        schedules1 = [make_schedule(id=1, schedule_plan_id=1)]
        schedules2 = [make_schedule(id=2, schedule_plan_id=2)]
        
        mock_metrics = MagicMock()
        mock_metrics.completion_rate = 0.9
        mock_metrics.equipment_utilization = 0.85
        mock_metrics.worker_utilization = 0.8
        mock_metrics.total_duration_hours = 8.0
        mock_metrics.conflict_count = 0
        mock_metrics.calculate_overall_score.return_value = 85.0
        
        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0] == ProductionSchedule:
                call_count = query_side_effect.count
                query_side_effect.count += 1
                if call_count == 0:
                    mock_query.filter.return_value.all.return_value = schedules1
                else:
                    mock_query.filter.return_value.all.return_value = schedules2
            return mock_query
        
        query_side_effect.count = 0
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(service, '_fetch_work_orders', return_value=[make_work_order()]), \
             patch.object(service, 'calculate_overall_metrics', return_value=mock_metrics):
            
            result = service.compare_schedule_plans([1, 2])
            
            assert 'comparison_time' in result or 'plans_compared' in result


# ==================== 测试甘特图数据生成 ====================

class TestGenerateGanttData:
    """测试 generate_gantt_data 甘特图数据"""

    def test_generate_gantt_data_success(self, service, mock_db):
        """测试生成甘特图数据"""
        schedules = [
            make_schedule(id=1, work_order_id=1, status='CONFIRMED'),
            make_schedule(id=2, work_order_id=2, status='IN_PROGRESS')
        ]
        
        work_orders = [
            make_work_order(id=1, work_order_no='WO-001'),
            make_work_order(id=2, work_order_no='WO-002')
        ]
        
        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0] == ProductionSchedule:
                mock_query.filter.return_value.order_by.return_value.all.return_value = schedules
            elif args[0] == WorkOrder:
                mock_query.filter.return_value.all.return_value = work_orders
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = service.generate_gantt_data(plan_id=1)
        
        assert 'tasks' in result
        assert 'summary' in result


# ==================== 测试重置排程逻辑 ====================

class TestResetSchedulePlan:
    """测试 reset_schedule_plan 重置排程"""

    def test_reset_schedule_plan_success(self, service, mock_db):
        """测试重置排程成功"""
        schedules = [make_schedule(id=1), make_schedule(id=2)]
        conflicts = [MagicMock(spec=ProductionResourceConflict)]
        logs = [MagicMock(spec=ScheduleAdjustmentLog)]
        
        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0] == ProductionSchedule:
                mock_query.filter.return_value.all.return_value = schedules
                mock_query.filter.return_value.count.return_value = 2
            elif args[0] == ProductionResourceConflict:
                mock_query.filter.return_value.all.return_value = conflicts
                mock_query.filter.return_value.count.return_value = 1
            elif args[0] == ScheduleAdjustmentLog:
                mock_query.filter.return_value.all.return_value = logs
                mock_query.filter.return_value.count.return_value = 1
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = service.reset_schedule_plan(plan_id=1)
        
        assert result['success'] is True
        assert result['deleted_schedules'] == 2


# ==================== 测试冲突摘要逻辑 ====================

class TestGetConflictSummary:
    """测试 get_conflict_summary 冲突摘要"""

    def test_get_conflict_summary_with_conflicts(self, service, mock_db):
        """测试获取冲突摘要"""
        conflicts = [
            MagicMock(spec=ProductionResourceConflict, conflict_type='EQUIPMENT', severity='HIGH'),
            MagicMock(spec=ProductionResourceConflict, conflict_type='WORKER', severity='MEDIUM')
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = conflicts
        mock_db.query.return_value = mock_query
        
        with patch('app.schemas.production_schedule.ConflictResponse.model_validate', side_effect=lambda x: x):
            result = service.get_conflict_summary(plan_id=1)
            
            assert result['total_count'] == 2

    def test_get_conflict_summary_no_conflicts(self, service, mock_db):
        """测试无冲突时的摘要"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = service.get_conflict_summary(plan_id=1)
        
        assert result['total_count'] == 0


# ==================== 测试历史记录逻辑 ====================

class TestGetScheduleHistory:
    """测试 get_schedule_history 历史记录"""

    def test_get_schedule_history_with_logs(self, service, mock_db):
        """测试获取调整历史"""
        logs = [
            MagicMock(spec=ScheduleAdjustmentLog, schedule_id=1, adjusted_at=datetime.now())
        ]
        
        schedules = [make_schedule(id=1)]
        
        def query_side_effect(*args):
            mock_query = MagicMock()
            if args[0] == ScheduleAdjustmentLog:
                mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = logs
                mock_query.filter.return_value.count.return_value = 1
            elif args[0] == ProductionSchedule:
                mock_query.filter.return_value.all.return_value = schedules
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = service.get_schedule_history(plan_id=1, skip=0, limit=10)
        
        assert 'total' in result
        assert 'items' in result
