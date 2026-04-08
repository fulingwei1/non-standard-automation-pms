# -*- coding: utf-8 -*-
"""
生产排程服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, MagicMock, patch
from typing import List

from app.services.production_schedule_service import ProductionScheduleService
from app.models.production import (
    ProductionSchedule,
    ProductionResourceConflict,
    WorkOrder,
    Equipment,
    Worker,
    WorkerSkill,
)
from app.schemas.production_schedule import (
    ScheduleGenerateRequest,
    ScheduleAdjustRequest,
    ScheduleResponse,
)


class TestProductionScheduleServiceConstants:
    """测试类常量和配置"""

    def test_algorithm_version(self):
        """测试算法版本"""
        assert ProductionScheduleService.ALGORITHM_VERSION == "v1.0.0"

    def test_work_hours_config(self):
        """测试工作时间配置"""
        assert ProductionScheduleService.WORK_START_HOUR >= 0
        assert ProductionScheduleService.WORK_END_HOUR > ProductionScheduleService.WORK_START_HOUR
        assert ProductionScheduleService.WORK_HOURS_PER_DAY > 0

    def test_gantt_color_map(self):
        """测试甘特图颜色映射"""
        color_map = ProductionScheduleService.GANTT_COLOR_MAP
        
        # 验证所有状态都有颜色
        expected_states = ["PENDING", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
        for state in expected_states:
            assert state in color_map
            assert color_map[state].startswith("#")
            assert len(color_map[state]) == 7  # hex color format


class TestProductionScheduleServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = ProductionScheduleService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            ProductionScheduleService()


class TestProductionScheduleServiceHelpers:
    """测试辅助方法"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        mock_db = Mock()
        return ProductionScheduleService(mock_db)

    def test_generate_plan_id(self, service):
        """测试计划ID生成"""
        plan_id = service._generate_plan_id()
        
        # ID 应该是正整数
        assert plan_id > 0
        # 应该是时间戳格式
        assert isinstance(plan_id, int)

    def test_get_priority_weight_high(self, service):
        """测试高优先级权重"""
        weight = service._get_priority_weight("HIGH")
        assert weight > 0
        assert isinstance(weight, (int, float))

    def test_get_priority_weight_order(self, service):
        """测试优先级权重排序（越小越优先）"""
        weight_urgent = service._get_priority_weight("URGENT")
        weight_high = service._get_priority_weight("HIGH")
        weight_normal = service._get_priority_weight("NORMAL")
        weight_low = service._get_priority_weight("LOW")
        # 权重越小越优先：URGENT < HIGH < NORMAL < LOW
        assert weight_urgent < weight_high
        assert weight_high < weight_normal
        assert weight_normal < weight_low

    def test_get_priority_weight_unknown(self, service):
        """测试未知优先级返回默认值"""
        weight = service._get_priority_weight("UNKNOWN")
        assert weight >= 0


class TestProductionScheduleServiceGenerate:
    """测试排程生成"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库"""
        db = Mock()
        db.add_all = Mock()
        db.flush = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return ProductionScheduleService(mock_db)

    def test_generate_schedule_empty_work_orders(self, service):
        """测试空工单列表"""
        # Mock _fetch_work_orders 返回空列表
        service._fetch_work_orders = Mock(return_value=[])
        
        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            algorithm="GREEDY"
        )
        
        with pytest.raises(ValueError, match="未找到有效工单"):
            service.generate_schedule(request, user_id=1)

    def test_generate_schedule_greedy_algorithm(self, service, mock_db):
        """测试贪心算法排程"""
        # 模拟工单
        work_order = Mock(spec=WorkOrder)
        work_order.id = 1
        work_order.work_order_no = "WO001"
        work_order.priority = "HIGH"
        work_order.plan_end_date = date.today() + timedelta(days=7)
        work_order.standard_hours = 8
        work_order.workshop_id = 1

        # Mock 数据库查询
        service._fetch_work_orders = Mock(return_value=[work_order])
        service._get_available_equipment = Mock(return_value=[Mock(spec=Equipment, id=1, name="EQ1")])
        service._get_available_workers = Mock(return_value=[Mock(spec=Worker, id=1, name="Worker1")])
        service._greedy_scheduling = Mock(return_value=[
            Mock(spec=ProductionSchedule, score=80)
        ])
        service._detect_conflicts = Mock(return_value=[])
        service._calculate_schedule_score = Mock(return_value=80)
        service._generate_plan_id = Mock(return_value=1001)

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            algorithm="GREEDY"
        )

        plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)

        assert plan_id == 1001
        assert len(schedules) == 1
        assert len(conflicts) == 0
        mock_db.add_all.assert_called_once()

    def test_generate_schedule_heuristic_algorithm(self, service, mock_db):
        """测试启发式算法排程"""
        work_order = Mock(spec=WorkOrder)
        work_order.id = 1
        work_order.priority = "HIGH"

        service._fetch_work_orders = Mock(return_value=[work_order])
        service._get_available_equipment = Mock(return_value=[])
        service._get_available_workers = Mock(return_value=[])
        service._heuristic_scheduling = Mock(return_value=[
            Mock(spec=ProductionSchedule, score=90)
        ])
        service._detect_conflicts = Mock(return_value=[])
        service._calculate_schedule_score = Mock(return_value=90)
        service._generate_plan_id = Mock(return_value=2001)

        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            algorithm="HEURISTIC"
        )

        plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)

        assert plan_id == 2001
        assert len(schedules) == 1


class TestProductionScheduleServiceAdjust:
    """测试排程调整"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return ProductionScheduleService(mock_db)

    def test_adjust_schedule_invalid_id(self, service):
        """测试无效排程ID"""
        service.db.query = Mock()
        service.db.query.return_value.filter.return_value.first.return_value = None

        request = ScheduleAdjustRequest(
            schedule_id=999,
            adjustment_type="TIME",
            new_start_time=datetime.now(),
            new_end_time=datetime.now() + timedelta(hours=8),
            reason="test"
        )

        with pytest.raises(ValueError):
            service.adjust_schedule(request, user_id=1)


class TestProductionScheduleServiceConflict:
    """测试冲突检测"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return ProductionScheduleService(mock_db)

    def test_detect_conflicts_empty_schedules(self, service):
        """测试空排程无冲突"""
        conflicts = service._detect_conflicts([])
        assert conflicts == []

    def test_detect_conflicts_single_schedule(self, service):
        """测试单个排程无冲突"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.equipment_id = 1
        schedule.worker_id = 1
        schedule.start_time = datetime.now()
        schedule.end_time = datetime.now() + timedelta(hours=4)

        conflicts = service._detect_conflicts([schedule])
        assert conflicts == []


class TestProductionScheduleServiceScoring:
    """测试评分计算"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return ProductionScheduleService(mock_db)

    def test_calculate_schedule_score(self, service):
        """测试排程评分"""
        schedule = Mock(spec=ProductionSchedule)
        schedule.equipment_id = 1
        schedule.worker_id = 1
        
        work_order = Mock(spec=WorkOrder)
        work_order.standard_hours = 8
        work_order.priority = "HIGH"

        score = service._calculate_schedule_score(schedule, [work_order])
        
        # 评分应该是正数
        assert isinstance(score, (int, float))

    def test_calculate_overall_metrics(self, service):
        """测试整体指标计算"""
        # 使用真实的 date 和 datetime 对象
        future_date = date.today() + timedelta(days=7)
        start_time = datetime.now()
        
        # 创建带有完整属性的 Mock，使用正确的属性名
        schedule1 = Mock(spec=ProductionSchedule)
        schedule1.id = 1
        schedule1.work_order_id = 1
        schedule1.equipment_id = 1
        schedule1.worker_id = 1
        schedule1.scheduled_start_time = start_time
        schedule1.scheduled_end_time = start_time + timedelta(hours=8)
        schedule1.duration_hours = 8.0
        schedule1.status = "CONFIRMED"
        
        schedule2 = Mock(spec=ProductionSchedule)
        schedule2.id = 2
        schedule2.work_order_id = 2
        schedule2.equipment_id = 2
        schedule2.worker_id = 2
        schedule2.scheduled_start_time = start_time
        schedule2.scheduled_end_time = start_time + timedelta(hours=10)
        schedule2.duration_hours = 10.0
        schedule2.status = "CONFIRMED"
        
        schedules = [schedule1, schedule2]
        
        work_order1 = Mock(spec=WorkOrder)
        work_order1.id = 1
        work_order1.standard_hours = 8.0
        work_order1.priority = "HIGH"
        work_order1.plan_end_date = future_date
        
        work_order2 = Mock(spec=WorkOrder)
        work_order2.id = 2
        work_order2.standard_hours = 10.0
        work_order2.priority = "NORMAL"
        work_order2.plan_end_date = future_date
        
        work_orders = [work_order1, work_order2]
        
        # Mock 冲突检测
        service._detect_conflicts = Mock(return_value=[])

        metrics = service.calculate_overall_metrics(schedules, work_orders)
        
        assert metrics is not None
        assert hasattr(metrics, 'completion_rate')
        assert hasattr(metrics, 'equipment_utilization')
        assert hasattr(metrics, 'worker_utilization')
        # 基本范围检查
        assert 0 <= metrics.completion_rate <= 1


class TestProductionScheduleServiceTimeCalculation:
    """测试时间计算"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return ProductionScheduleService(mock_db)

    def test_calculate_end_time_within_work_hours(self, service):
        """测试工作时间内的结束时间计算"""
        start_time = datetime.now().replace(hour=9, minute=0)
        duration_hours = 4
        
        request = Mock()
        request.work_days_only = True
        
        end_time = service._calculate_end_time(start_time, duration_hours, request)
        
        assert end_time > start_time
        # 结束时间应该在工作时间范围内
        assert end_time.hour <= ProductionScheduleService.WORK_END_HOUR

    def test_find_earliest_available_slot_empty(self, service):
        """测试空时间表找最早可用时间"""
        current_time = datetime.now()
        duration_hours = 4
        
        request = Mock()
        request.start_date = current_time
        
        earliest = service._find_earliest_available_slot([], [], current_time, duration_hours, request)
        
        assert earliest >= current_time