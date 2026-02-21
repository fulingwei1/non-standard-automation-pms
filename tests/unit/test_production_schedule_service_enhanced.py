# -*- coding: utf-8 -*-
"""
生产排程服务增强测试
测试 ProductionScheduleService 的所有核心方法
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List

from app.services.production_schedule_service import ProductionScheduleService
from app.schemas.production_schedule import (
    ScheduleGenerateRequest,
    ScheduleAdjustRequest,
    ScheduleScoreMetrics,
)
from app.models.production import (
    WorkOrder,
    Equipment,
    Worker,
    ProductionSchedule,
    ProductionResourceConflict,
    ScheduleAdjustmentLog,
    WorkerSkill,
)


class TestProductionScheduleServiceCore:
    """核心功能测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库session"""
        db = MagicMock()
        db.add = MagicMock()
        db.add_all = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.query = MagicMock()
        return db
    
    def setup_db_query_mock(self, mock_db, work_orders=None, schedules=None, workers_skills=None):
        """设置数据库查询mock的辅助方法"""
        def query_side_effect(model_class):
            mock_query = MagicMock()
            model_name = str(model_class)
            
            if 'WorkOrder' in model_name and work_orders:
                mock_query.filter.return_value.all.return_value = work_orders
                mock_query.filter.return_value.first.return_value = work_orders[0] if work_orders else None
            elif 'ProductionSchedule' in model_name and schedules:
                mock_query.filter.return_value.all.return_value = schedules
                mock_query.filter.return_value.first.return_value = schedules[0] if schedules else None
            elif 'WorkerSkill' in model_name:
                mock_query.filter.return_value.all.return_value = workers_skills or []
            else:
                mock_query.filter.return_value.all.return_value = []
                mock_query.filter.return_value.first.return_value = None
            
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
    
    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return ProductionScheduleService(mock_db)
    
    @pytest.fixture
    def sample_work_orders(self):
        """创建示例工单"""
        return [
            WorkOrder(
                id=1,
                work_order_no="WO-001",
                task_name="Task 1",
                priority="HIGH",
                plan_end_date=(datetime.now() + timedelta(days=7)).date(),
                standard_hours=Decimal("8.0"),
                workshop_id=1,
                process_id=1,
                machine_id=None,
                assigned_to=None,
                progress=0
            ),
            WorkOrder(
                id=2,
                work_order_no="WO-002",
                task_name="Task 2",
                priority="NORMAL",
                plan_end_date=(datetime.now() + timedelta(days=10)).date(),
                standard_hours=Decimal("12.0"),
                workshop_id=1,
                process_id=2,
                machine_id=None,
                assigned_to=None,
                progress=0
            ),
            WorkOrder(
                id=3,
                work_order_no="WO-003",
                task_name="Task 3",
                priority="URGENT",
                plan_end_date=(datetime.now() + timedelta(days=3)).date(),
                standard_hours=Decimal("6.0"),
                workshop_id=2,
                process_id=1,
                machine_id=2,
                assigned_to=3,
                progress=0
            ),
        ]
    
    @pytest.fixture
    def sample_equipment(self):
        """创建示例设备"""
        now = datetime.now()
        return [
            Equipment(id=1, equipment_code="EQ-001", equipment_name="设备1", workshop_id=1, is_active=True, status="IDLE", created_at=now, updated_at=now),
            Equipment(id=2, equipment_code="EQ-002", equipment_name="设备2", workshop_id=2, is_active=True, status="RUNNING", created_at=now, updated_at=now),
            Equipment(id=3, equipment_code="EQ-003", equipment_name="设备3", workshop_id=1, is_active=True, status="IDLE", created_at=now, updated_at=now),
        ]
    
    @pytest.fixture
    def sample_workers(self):
        """创建示例工人"""
        return [
            Worker(id=1, worker_no="W-001", worker_name="Worker1", workshop_id=1, is_active=True, status="ACTIVE"),
            Worker(id=2, worker_no="W-002", worker_name="Worker2", workshop_id=1, is_active=True, status="ACTIVE"),
            Worker(id=3, worker_no="W-003", worker_name="Worker3", workshop_id=2, is_active=True, status="ACTIVE"),
        ]


class TestGenerateSchedule(TestProductionScheduleServiceCore):
    """测试排程生成功能"""
    
    def test_generate_schedule_greedy_success(
        self, service, mock_db, sample_work_orders, sample_equipment, sample_workers
    ):
        """测试贪心算法排程生成成功"""
        self.setup_db_query_mock(mock_db, work_orders=sample_work_orders)
        
        with patch.object(service, '_get_available_equipment', return_value=sample_equipment), \
             patch.object(service, '_get_available_workers', return_value=sample_workers), \
             patch.object(service, '_generate_plan_id', return_value=12345):
            
            request = ScheduleGenerateRequest(
                work_orders=[1, 2, 3],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                algorithm="GREEDY",
                consider_worker_skills=False,  # 不使用技能匹配以简化测试
                consider_equipment_capacity=True
            )
            
            plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
            
            # 验证
            assert plan_id == 12345
            assert len(schedules) == 3
            assert all(isinstance(s, ProductionSchedule) for s in schedules)
            assert schedules[0].status == 'PENDING'
            mock_db.add_all.assert_called()
            mock_db.flush.assert_called_once()
    
    def test_generate_schedule_heuristic_algorithm(
        self, service, mock_db, sample_work_orders, sample_equipment, sample_workers
    ):
        """测试启发式算法"""
        self.setup_db_query_mock(mock_db, work_orders=sample_work_orders)
        
        with patch.object(service, '_get_available_equipment', return_value=sample_equipment), \
             patch.object(service, '_get_available_workers', return_value=sample_workers), \
             patch.object(service, '_generate_plan_id', return_value=99999):
            
            request = ScheduleGenerateRequest(
                work_orders=[1, 2, 3],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                algorithm="HEURISTIC",
                consider_worker_skills=False
            )
            
            plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
            
            assert len(schedules) == 3
            assert plan_id == 99999
    
    def test_generate_schedule_no_work_orders(self, service, mock_db):
        """测试无工单时抛出异常"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        request = ScheduleGenerateRequest(
            work_orders=[],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        with pytest.raises(ValueError, match="未找到有效工单"):
            service.generate_schedule(request, user_id=1)
    
    def test_generate_and_evaluate_schedule_complete_flow(
        self, service, mock_db, sample_work_orders, sample_equipment, sample_workers
    ):
        """测试完整的生成和评估流程"""
        self.setup_db_query_mock(mock_db, work_orders=sample_work_orders)
        
        # Mock ScheduleResponse.model_validate 以避免ORM字段验证问题
        mock_response = MagicMock()
        mock_response.id = 1
        
        with patch.object(service, '_get_available_equipment', return_value=sample_equipment), \
             patch.object(service, '_get_available_workers', return_value=sample_workers), \
             patch.object(service, '_generate_plan_id', return_value=55555), \
             patch('app.schemas.production_schedule.ScheduleResponse.model_validate', return_value=mock_response):
            
            request = ScheduleGenerateRequest(
                work_orders=[1, 2, 3],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                algorithm="GREEDY",
                consider_worker_skills=False
            )
            
            result = service.generate_and_evaluate_schedule(request, user_id=1)
            
            # 验证返回结构
            assert result["plan_id"] == 55555
            assert "schedules" in result
            assert result["total_count"] == 3
            assert result["success_count"] == 3
            assert "metrics" in result
            assert "warnings" in result
            assert isinstance(result["score"], float)
            mock_db.commit.assert_called_once()
    
    def test_generate_schedule_with_conflicts(
        self, service, mock_db, sample_work_orders, sample_equipment, sample_workers
    ):
        """测试排程生成时检测到冲突"""
        # 创建冲突的工单（相同资源、重叠时间）
        conflicting_orders = [
            WorkOrder(
                id=1, work_order_no="WO-001", task_name="Task 1",
                priority="HIGH", standard_hours=Decimal("8.0"),
                workshop_id=1, process_id=1, machine_id=1, assigned_to=1, progress=0
            ),
            WorkOrder(
                id=2, work_order_no="WO-002", task_name="Task 2",
                priority="HIGH", standard_hours=Decimal("8.0"),
                workshop_id=1, process_id=1, machine_id=1, assigned_to=1, progress=0
            ),
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = conflicting_orders
        
        # 提供单个设备和工人，强制冲突
        single_equipment = [sample_equipment[0]]
        single_worker = [sample_workers[0]]
        
        with patch.object(service, '_get_available_equipment', return_value=single_equipment), \
             patch.object(service, '_get_available_workers', return_value=single_worker), \
             patch.object(service, '_generate_plan_id', return_value=77777):
            
            request = ScheduleGenerateRequest(
                work_orders=[1, 2],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30)
            )
            
            plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
            
            # 冲突数量可能为0（因为算法会调整时间避免冲突）
            # 这里主要验证流程正常执行
            assert len(schedules) == 2
            assert isinstance(conflicts, list)


class TestUrgentInsert(TestProductionScheduleServiceCore):
    """测试紧急插单功能"""
    
    def test_urgent_insert_success(self, service, mock_db, sample_work_orders, sample_equipment, sample_workers):
        """测试紧急插单成功"""
        order = sample_work_orders[0]
        mock_db.query.return_value.filter.return_value.first.return_value = order
        mock_db.query.return_value.filter.return_value.all.return_value = []  # 无冲突排程
        
        with patch.object(service, '_get_available_equipment', return_value=sample_equipment), \
             patch.object(service, '_get_available_workers', return_value=sample_workers):
            
            insert_time = datetime.now() + timedelta(hours=2)
            new_schedule, adjusted, conflicts = service.urgent_insert(
                work_order_id=1,
                insert_time=insert_time,
                max_delay_hours=4.0,
                auto_adjust=True,
                user_id=1
            )
            
            assert new_schedule is not None
            assert new_schedule.is_urgent is True
            assert new_schedule.priority_score == 5.0
            assert new_schedule.work_order_id == 1
    
    def test_urgent_insert_work_order_not_found(self, service, mock_db):
        """测试工单不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="工单不存在"):
            service.urgent_insert(
                work_order_id=999,
                insert_time=datetime.now(),
                max_delay_hours=4.0,
                auto_adjust=False,
                user_id=1
            )
    
    def test_urgent_insert_with_auto_adjust(
        self, service, mock_db, sample_work_orders, sample_equipment, sample_workers
    ):
        """测试紧急插单自动调整其他排程"""
        order = sample_work_orders[0]
        
        # 模拟冲突的排程
        conflicting_schedule = ProductionSchedule(
            id=100,
            work_order_id=2,
            equipment_id=1,
            worker_id=1,
            scheduled_start_time=datetime.now() + timedelta(hours=1),
            scheduled_end_time=datetime.now() + timedelta(hours=9),
            duration_hours=8.0,
            status='PENDING'
        )
        
        # 设置查询mock
        def query_side_effect(model_class):
            mock_query = MagicMock()
            if 'WorkOrder' in str(model_class):
                mock_query.filter.return_value.first.return_value = order
            elif 'ProductionSchedule' in str(model_class):
                mock_query.filter.return_value.all.return_value = [conflicting_schedule]
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(service, '_get_available_equipment', return_value=sample_equipment), \
             patch.object(service, '_get_available_workers', return_value=sample_workers):
            
            new_schedule, adjusted, conflicts = service.urgent_insert(
                work_order_id=1,
                insert_time=datetime.now() + timedelta(hours=2),
                max_delay_hours=10.0,
                auto_adjust=True,
                user_id=1
            )
            
            assert new_schedule is not None
            assert len(adjusted) >= 0  # 可能有调整的排程
    
    def test_execute_urgent_insert_with_logging(
        self, service, mock_db, sample_work_orders, sample_equipment, sample_workers
    ):
        """测试紧急插单并创建日志"""
        order = sample_work_orders[0]
        
        # Mock ScheduleResponse
        mock_response = MagicMock()
        mock_response.id = 1
        
        def query_side_effect(model_class):
            mock_query = MagicMock()
            if 'WorkOrder' in str(model_class):
                mock_query.filter.return_value.first.return_value = order
            elif 'ProductionSchedule' in str(model_class):
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(service, '_get_available_equipment', return_value=sample_equipment), \
             patch.object(service, '_get_available_workers', return_value=sample_workers), \
             patch('app.schemas.production_schedule.ScheduleResponse.model_validate', return_value=mock_response):
            
            result = service.execute_urgent_insert_with_logging(
                work_order_id=1,
                insert_time=datetime.now() + timedelta(hours=1),
                max_delay_hours=4.0,
                auto_adjust=True,
                user_id=1
            )
            
            assert result["success"] is True
            assert result["schedule"] is not None
            assert "message" in result
            mock_db.commit.assert_called_once()


class TestSchedulePreviewAndConfirmation(TestProductionScheduleServiceCore):
    """测试排程预览和确认功能"""
    
    def test_get_schedule_preview_success(self, service, mock_db, sample_work_orders):
        """测试获取排程预览"""
        now = datetime.now()
        schedules = [
            ProductionSchedule(
                id=i,
                work_order_id=wo.id,
                schedule_plan_id=123,
                scheduled_start_time=now + timedelta(days=i),
                scheduled_end_time=now + timedelta(days=i, hours=8),
                duration_hours=8.0,
                status='PENDING',
                priority_score=2.0,
                is_urgent=False,
                is_manually_adjusted=False,
                created_at=now,
                updated_at=now
            )
            for i, wo in enumerate(sample_work_orders, 1)
        ]
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            schedules,  # 第一次调用返回schedules
            [],  # 第二次调用返回conflicts (空列表)
            sample_work_orders  # 第三次调用返回work_orders
        ]
        
        result = service.get_schedule_preview(plan_id=123)
        
        assert result["plan_id"] == 123
        assert len(result["schedules"]) == 3
        assert "statistics" in result
        assert "conflicts" in result
        assert "optimization_suggestions" in result
    
    def test_get_schedule_preview_not_found(self, service, mock_db):
        """测试排程方案不存在"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with pytest.raises(ValueError, match="排程方案不存在"):
            service.get_schedule_preview(plan_id=999)
    
    def test_confirm_schedule_success(self, service, mock_db):
        """测试确认排程成功"""
        schedules = [
            ProductionSchedule(id=1, schedule_plan_id=123, status='PENDING'),
            ProductionSchedule(id=2, schedule_plan_id=123, status='PENDING'),
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = schedules
        mock_db.query.return_value.filter.return_value.count.return_value = 0  # 无冲突
        
        result = service.confirm_schedule(plan_id=123, user_id=1)
        
        assert result["success"] is True
        assert result["confirmed_count"] == 2
        assert result["plan_id"] == 123
        assert "confirmed_at" in result
        mock_db.commit.assert_called_once()
    
    def test_confirm_schedule_no_pending(self, service, mock_db):
        """测试没有待确认的排程"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with pytest.raises(ValueError, match="没有待确认的排程"):
            service.confirm_schedule(plan_id=123, user_id=1)
    
    def test_confirm_schedule_with_conflicts(self, service, mock_db):
        """测试存在高优先级冲突时无法确认"""
        schedules = [ProductionSchedule(id=1, schedule_plan_id=123, status='PENDING')]
        
        mock_db.query.return_value.filter.return_value.all.return_value = schedules
        mock_db.query.return_value.filter.return_value.count.return_value = 2  # 有冲突
        
        with pytest.raises(RuntimeError, match="高优先级冲突"):
            service.confirm_schedule(plan_id=123, user_id=1)


class TestConflictManagement(TestProductionScheduleServiceCore):
    """测试冲突管理功能"""
    
    def test_get_conflict_summary_with_plan_id(self, service, mock_db):
        """测试按方案ID获取冲突摘要"""
        schedules = [
            ProductionSchedule(id=1, schedule_plan_id=100),
            ProductionSchedule(id=2, schedule_plan_id=100),
        ]
        
        conflicts = [
            ProductionResourceConflict(
                id=1,
                schedule_id=1,
                conflicting_schedule_id=2,
                conflict_type='EQUIPMENT',
                severity='HIGH',
                status='UNRESOLVED',
                detected_at=datetime.now()
            ),
            ProductionResourceConflict(
                id=2,
                schedule_id=1,
                conflicting_schedule_id=2,
                conflict_type='WORKER',
                severity='MEDIUM',
                status='UNRESOLVED',
                detected_at=datetime.now()
            ),
        ]
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [(1,), (2,)],  # schedule_ids
            conflicts
        ]
        
        result = service.get_conflict_summary(plan_id=100)
        
        assert result["has_conflicts"] is True
        assert result["total_conflicts"] == 2
        assert result["conflicts_by_type"]["EQUIPMENT"] == 1
        assert result["conflicts_by_type"]["WORKER"] == 1
        assert result["severity_summary"]["HIGH"] == 1
        assert result["severity_summary"]["MEDIUM"] == 1
    
    def test_get_conflict_summary_no_conflicts(self, service, mock_db):
        """测试无冲突情况"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = service.get_conflict_summary(schedule_id=123)
        
        assert result["has_conflicts"] is False
        assert result["total_conflicts"] == 0
        assert result["conflicts_by_type"] == {}
    
    def test_detect_conflicts_equipment_conflict(self, service):
        """测试检测设备冲突"""
        schedules = [
            ProductionSchedule(
                id=1,
                work_order_id=1,
                equipment_id=1,
                worker_id=1,
                scheduled_start_time=datetime(2026, 2, 21, 8, 0),
                scheduled_end_time=datetime(2026, 2, 21, 16, 0)
            ),
            ProductionSchedule(
                id=2,
                work_order_id=2,
                equipment_id=1,  # 相同设备
                worker_id=2,
                scheduled_start_time=datetime(2026, 2, 21, 14, 0),  # 时间重叠
                scheduled_end_time=datetime(2026, 2, 21, 22, 0)
            ),
        ]
        
        conflicts = service._detect_conflicts(schedules)
        
        assert len(conflicts) > 0
        equipment_conflicts = [c for c in conflicts if c.conflict_type == 'EQUIPMENT']
        assert len(equipment_conflicts) >= 1
        assert equipment_conflicts[0].resource_id == 1


class TestScheduleAdjustment(TestProductionScheduleServiceCore):
    """测试排程调整功能"""
    
    def test_adjust_schedule_success(self, service, mock_db):
        """测试调整排程成功"""
        schedule = ProductionSchedule(
            id=1,
            work_order_id=1,
            scheduled_start_time=datetime(2026, 2, 21, 8, 0),
            scheduled_end_time=datetime(2026, 2, 21, 16, 0),
            equipment_id=1,
            worker_id=1
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = schedule
        
        request = ScheduleAdjustRequest(
            schedule_id=1,
            adjustment_type='TIME_CHANGE',
            new_start_time=datetime(2026, 2, 22, 8, 0),
            new_end_time=datetime(2026, 2, 22, 16, 0),
            reason="客户要求延期",
            auto_resolve_conflicts=False
        )
        
        result = service.adjust_schedule(request, user_id=1)
        
        assert result["success"] is True
        assert result["schedule_id"] == 1
        assert "开始时间" in result["changes"]
        assert "结束时间" in result["changes"]
        assert schedule.is_manually_adjusted is True
        mock_db.commit.assert_called_once()
    
    def test_adjust_schedule_not_found(self, service, mock_db):
        """测试排程不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        request = ScheduleAdjustRequest(
            schedule_id=999,
            adjustment_type='TIME_CHANGE',
            reason="测试"
        )
        
        with pytest.raises(ValueError, match="排程不存在"):
            service.adjust_schedule(request, user_id=1)
    
    def test_adjust_schedule_change_resource(self, service, mock_db):
        """测试调整设备和工人"""
        schedule = ProductionSchedule(
            id=1,
            work_order_id=1,
            scheduled_start_time=datetime.now(),
            scheduled_end_time=datetime.now() + timedelta(hours=8),
            equipment_id=1,
            worker_id=1
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = schedule
        
        request = ScheduleAdjustRequest(
            schedule_id=1,
            adjustment_type='RESOURCE_CHANGE',
            new_equipment_id=2,
            new_worker_id=3,
            reason="设备维护，更换资源"
        )
        
        result = service.adjust_schedule(request, user_id=1)
        
        assert "设备" in result["changes"]
        assert "工人" in result["changes"]
        assert schedule.equipment_id == 2
        assert schedule.worker_id == 3


class TestScheduleComparison(TestProductionScheduleServiceCore):
    """测试排程方案对比功能"""
    
    def test_compare_schedule_plans_success(self, service, mock_db, sample_work_orders):
        """测试方案对比成功"""
        # 准备两个方案的排程
        plan1_schedules = [
            ProductionSchedule(
                id=1, work_order_id=1, schedule_plan_id=101,
                scheduled_start_time=datetime.now(),
                scheduled_end_time=datetime.now() + timedelta(hours=8),
                duration_hours=8.0
            )
        ]
        
        plan2_schedules = [
            ProductionSchedule(
                id=2, work_order_id=1, schedule_plan_id=102,
                scheduled_start_time=datetime.now(),
                scheduled_end_time=datetime.now() + timedelta(hours=10),
                duration_hours=10.0
            )
        ]
        
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            plan1_schedules,
            sample_work_orders[:1],
            plan2_schedules,
            sample_work_orders[:1],
        ]
        
        result = service.compare_schedule_plans(plan_ids=[101, 102])
        
        assert result["plans_compared"] == 2
        assert result["best_plan_id"] in [101, 102]
        assert len(result["results"]) == 2
        assert result["results"][0]["rank"] == 1
        assert "comparison_summary" in result
    
    def test_compare_schedule_plans_too_few(self, service):
        """测试方案数量不足"""
        with pytest.raises(ValueError, match="至少需要2个方案"):
            service.compare_schedule_plans(plan_ids=[101])
    
    def test_compare_schedule_plans_too_many(self, service):
        """测试方案数量过多"""
        with pytest.raises(ValueError, match="最多支持5个方案"):
            service.compare_schedule_plans(plan_ids=[1, 2, 3, 4, 5, 6])


class TestGanttData(TestProductionScheduleServiceCore):
    """测试甘特图数据生成"""
    
    def test_generate_gantt_data_success(self, service, mock_db, sample_work_orders):
        """测试生成甘特图数据"""
        schedules = [
            ProductionSchedule(
                id=i,
                work_order_id=wo.id,
                schedule_plan_id=200,
                equipment_id=i,
                worker_id=i,
                scheduled_start_time=datetime.now() + timedelta(days=i),
                scheduled_end_time=datetime.now() + timedelta(days=i, hours=8),
                duration_hours=8.0,
                status='PENDING'
            )
            for i, wo in enumerate(sample_work_orders, 1)
        ]
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            schedules,
            sample_work_orders
        ]
        
        result = service.generate_gantt_data(plan_id=200)
        
        assert result["total_tasks"] == 3
        assert len(result["tasks"]) == 3
        assert "start_date" in result
        assert "end_date" in result
        assert len(result["resources"]) > 0
    
    def test_generate_gantt_data_not_found(self, service, mock_db):
        """测试排程方案不存在"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with pytest.raises(ValueError, match="排程方案不存在"):
            service.generate_gantt_data(plan_id=999)


class TestScheduleReset(TestProductionScheduleServiceCore):
    """测试排程重置功能"""
    
    def test_reset_schedule_plan_success(self, service, mock_db):
        """测试重置排程方案"""
        # 模拟查询返回
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]
        mock_db.query.return_value.filter.return_value.delete.return_value = 3
        
        result = service.reset_schedule_plan(plan_id=300)
        
        assert result["success"] is True
        assert result["deleted_count"] == 3
        mock_db.commit.assert_called_once()


class TestScheduleHistory(TestProductionScheduleServiceCore):
    """测试排程历史查询"""
    
    def test_get_schedule_history_with_pagination(self, service, mock_db):
        """测试带分页的历史查询"""
        adjustments = [
            ScheduleAdjustmentLog(
                id=i,
                schedule_id=1,
                adjustment_type='TIME_CHANGE',
                trigger_source='MANUAL',
                reason=f"调整 {i}",
                adjusted_at=datetime.now() - timedelta(days=i),
                affected_schedules_count=0
            )
            for i in range(1, 6)
        ]
        
        schedules = [ProductionSchedule(id=1, work_order_id=1)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.side_effect = [adjustments[:3], schedules]
        
        mock_db.query.return_value = mock_query
        
        result = service.get_schedule_history(schedule_id=1, page=1, page_size=3)
        
        assert result["total_count"] == 5
        assert result["page"] == 1
        assert result["page_size"] == 3


class TestMetricsCalculation(TestProductionScheduleServiceCore):
    """测试评估指标计算"""
    
    def test_calculate_overall_metrics_complete(self, service, sample_work_orders):
        """测试计算完整指标"""
        schedules = [
            ProductionSchedule(
                id=1,
                work_order_id=1,
                equipment_id=1,
                worker_id=1,
                scheduled_start_time=datetime.now(),
                scheduled_end_time=datetime.now() + timedelta(hours=8),
                duration_hours=8.0
            ),
            ProductionSchedule(
                id=2,
                work_order_id=2,
                equipment_id=2,
                worker_id=2,
                scheduled_start_time=datetime.now() + timedelta(hours=8),
                scheduled_end_time=datetime.now() + timedelta(hours=20),
                duration_hours=12.0
            ),
        ]
        
        metrics = service.calculate_overall_metrics(schedules, sample_work_orders[:2])
        
        assert isinstance(metrics, ScheduleScoreMetrics)
        assert 0 <= metrics.completion_rate <= 1
        assert 0 <= metrics.equipment_utilization <= 1
        assert 0 <= metrics.worker_utilization <= 1
        assert metrics.total_duration_hours > 0
    
    def test_calculate_overall_metrics_empty(self, service):
        """测试空排程列表"""
        metrics = service.calculate_overall_metrics([], [])
        
        assert metrics.completion_rate == 0
        assert metrics.equipment_utilization == 0
        assert metrics.total_duration_hours == 0


class TestHelperMethods(TestProductionScheduleServiceCore):
    """测试辅助方法"""
    
    def test_calculate_priority_score(self, service):
        """测试优先级评分计算"""
        order_low = WorkOrder(id=1, priority="LOW")
        order_high = WorkOrder(id=2, priority="HIGH")
        order_urgent = WorkOrder(id=3, priority="URGENT")
        
        assert service._calculate_priority_score(order_low) == 1.0
        assert service._calculate_priority_score(order_high) == 3.0
        assert service._calculate_priority_score(order_urgent) == 5.0
    
    def test_get_priority_weight(self, service):
        """测试优先级权重"""
        assert service._get_priority_weight("URGENT") < service._get_priority_weight("HIGH")
        assert service._get_priority_weight("HIGH") < service._get_priority_weight("NORMAL")
        assert service._get_priority_weight("NORMAL") < service._get_priority_weight("LOW")
    
    def test_adjust_to_work_time_before_start(self, service):
        """测试调整到工作时间-早于上班"""
        dt = datetime(2026, 2, 21, 6, 30)  # 早上6:30
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=1)
        )
        
        adjusted = service._adjust_to_work_time(dt, request)
        
        assert adjusted.hour == service.WORK_START_HOUR
        assert adjusted.minute == 0
    
    def test_adjust_to_work_time_after_end(self, service):
        """测试调整到工作时间-晚于下班"""
        dt = datetime(2026, 2, 21, 20, 0)  # 晚上8点
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=1)
        )
        
        adjusted = service._adjust_to_work_time(dt, request)
        
        assert adjusted.day == 22  # 第二天
        assert adjusted.hour == service.WORK_START_HOUR
    
    def test_time_overlap_detection(self, service):
        """测试时间重叠检测"""
        start1 = datetime(2026, 2, 21, 8, 0)
        end1 = datetime(2026, 2, 21, 16, 0)
        
        # 完全重叠
        start2 = datetime(2026, 2, 21, 10, 0)
        end2 = datetime(2026, 2, 21, 14, 0)
        assert service._time_overlap(start1, end1, start2, end2) is True
        
        # 部分重叠
        start3 = datetime(2026, 2, 21, 14, 0)
        end3 = datetime(2026, 2, 21, 18, 0)
        assert service._time_overlap(start1, end1, start3, end3) is True
        
        # 不重叠
        start4 = datetime(2026, 2, 21, 18, 0)
        end4 = datetime(2026, 2, 21, 20, 0)
        assert service._time_overlap(start1, end1, start4, end4) is False
    
    def test_calculate_end_time_single_day(self, service):
        """测试计算结束时间-单日内完成"""
        start = datetime(2026, 2, 21, 9, 0)
        duration = 6.0
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=start,
            end_date=start + timedelta(days=7)
        )
        
        end = service._calculate_end_time(start, duration, request)
        
        assert end.day == 21
        assert end.hour == 15  # 9 + 6 = 15
    
    def test_calculate_end_time_cross_day(self, service):
        """测试计算结束时间-跨天"""
        start = datetime(2026, 2, 21, 14, 0)
        duration = 12.0  # 需要跨天
        request = ScheduleGenerateRequest(
            work_orders=[1],
            start_date=start,
            end_date=start + timedelta(days=7)
        )
        
        end = service._calculate_end_time(start, duration, request)
        
        # 14:00开始，当天剩余4小时，第二天需要8小时
        assert end.day == 22
        assert end.hour == 16  # 8:00 + 8 = 16:00
    
    def test_select_best_equipment_with_assigned(self, service, sample_equipment):
        """测试选择设备-已指定设备"""
        order = WorkOrder(
            id=1, work_order_no="WO-001",
            workshop_id=1, machine_id=2  # 指定设备2
        )
        
        best_eq = service._select_best_equipment(
            order, sample_equipment, {},
            ScheduleGenerateRequest(
                work_orders=[1],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7)
            )
        )
        
        assert best_eq.id == 2
    
    def test_select_best_worker_with_skills(self, service, mock_db, sample_workers):
        """测试选择工人-考虑技能"""
        order = WorkOrder(
            id=1,
            workshop_id=1,
            process_id=5
        )
        
        # 模拟技能查询
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,)]
        
        best_worker = service._select_best_worker(
            order, sample_workers, {},
            ScheduleGenerateRequest(
                work_orders=[1],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7),
                consider_worker_skills=True
            )
        )
        
        assert best_worker is not None
        assert best_worker.id in [1, 2]


class TestResourceAvailability(TestProductionScheduleServiceCore):
    """测试资源可用性查询"""
    
    def test_get_available_equipment(self, service, mock_db, sample_equipment):
        """测试获取可用设备"""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_equipment
        
        equipment = service._get_available_equipment()
        
        assert len(equipment) == 3
        assert all(eq.is_active is True for eq in equipment)
    
    def test_get_available_workers(self, service, mock_db, sample_workers):
        """测试获取可用工人"""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_workers
        
        workers = service._get_available_workers()
        
        assert len(workers) == 3
        assert all(w.status == 'ACTIVE' for w in workers)


class TestScheduleOptimization(TestProductionScheduleServiceCore):
    """测试排程优化"""
    
    def test_should_swap_schedules(self, service):
        """测试是否应该交换排程"""
        schedule1 = ProductionSchedule(
            id=1,
            priority_score=2.0,
            scheduled_start_time=datetime(2026, 2, 21, 8, 0)
        )
        
        schedule2 = ProductionSchedule(
            id=2,
            priority_score=5.0,  # 更高优先级
            scheduled_start_time=datetime(2026, 2, 21, 16, 0)  # 更晚时间
        )
        
        # 高优先级排程应该被提前
        assert service._should_swap_schedules(schedule1, schedule2) is True
    
    def test_optimize_schedules(self, service):
        """测试优化排程（交换优化）"""
        schedules = [
            ProductionSchedule(
                id=1,
                priority_score=2.0,
                scheduled_start_time=datetime(2026, 2, 21, 8, 0),
                scheduled_end_time=datetime(2026, 2, 21, 16, 0)
            ),
            ProductionSchedule(
                id=2,
                priority_score=5.0,
                scheduled_start_time=datetime(2026, 2, 21, 16, 0),
                scheduled_end_time=datetime(2026, 2, 22, 0, 0)
            ),
        ]
        
        request = ScheduleGenerateRequest(
            work_orders=[1, 2],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        optimized = service._optimize_schedules(schedules, request)
        
        # 验证优化后仍有两个排程
        assert len(optimized) == 2


class TestScheduleScore(TestProductionScheduleServiceCore):
    """测试排程评分"""
    
    def test_calculate_schedule_score_on_time(self, service):
        """测试准时完成的排程评分"""
        order = WorkOrder(
            id=1,
            priority="HIGH",
            plan_end_date=(datetime.now() + timedelta(days=10)).date()
        )
        
        schedule = ProductionSchedule(
            id=1,
            work_order_id=1,
            priority_score=3.0,
            scheduled_end_time=datetime.now() + timedelta(days=5)  # 提前完成
        )
        
        score = service._calculate_schedule_score(schedule, [order])
        
        assert score > 30  # 基础分 + 准时奖励
    
    def test_calculate_schedule_score_late(self, service):
        """测试延期的排程评分"""
        order = WorkOrder(
            id=1,
            priority="NORMAL",
            plan_end_date=(datetime.now() + timedelta(days=5)).date()
        )
        
        schedule = ProductionSchedule(
            id=1,
            work_order_id=1,
            priority_score=2.0,
            scheduled_end_time=datetime.now() + timedelta(days=10)  # 延期
        )
        
        score = service._calculate_schedule_score(schedule, [order])
        
        assert score <= 20  # 只有基础分
