# -*- coding: utf-8 -*-
"""
生产排程模块测试
"""
import time
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.production import (
    Equipment,
    ProductionSchedule,
    ResourceConflict,
    ScheduleAdjustmentLog,
    Worker,
    WorkerSkill,
    WorkOrder,
    Workshop,
)
from app.models.production.process import ProcessDict
from app.schemas.production_schedule import (
    ScheduleGenerateRequest,
    UrgentInsertRequest,
)
from app.services.production_schedule_service import ProductionScheduleService


class TestProductionScheduleModels:
    """测试数据模型"""
    
    def test_production_schedule_model(self, db: Session):
        """测试排程模型创建"""
        schedule = ProductionSchedule(
            work_order_id=1,
            schedule_plan_id=1001,
            equipment_id=1,
            worker_id=1,
            workshop_id=1,
            scheduled_start_time=datetime.now(),
            scheduled_end_time=datetime.now() + timedelta(hours=8),
            duration_hours=8.0,
            priority_score=3.0,
            status='PENDING',
            algorithm_version='v1.0.0'
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        assert schedule.id is not None
        assert schedule.status == 'PENDING'
        assert schedule.duration_hours == 8.0
    
    def test_resource_conflict_model(self, db: Session):
        """测试资源冲突模型"""
        conflict = ResourceConflict(
            schedule_id=1,
            conflicting_schedule_id=2,
            conflict_type='EQUIPMENT',
            resource_type='equipment',
            resource_id=1,
            conflict_description='设备时间冲突',
            severity='HIGH',
            status='UNRESOLVED',
            detected_at=datetime.now(),
            detected_by='AUTO'
        )
        
        db.add(conflict)
        db.commit()
        db.refresh(conflict)
        
        assert conflict.id is not None
        assert conflict.conflict_type == 'EQUIPMENT'
        assert conflict.severity == 'HIGH'
    
    def test_schedule_adjustment_log_model(self, db: Session):
        """测试排程调整日志模型"""
        log = ScheduleAdjustmentLog(
            schedule_id=1,
            adjustment_type='TIME_CHANGE',
            trigger_source='MANUAL',
            reason='手动调整时间',
            adjusted_by=1,
            adjusted_at=datetime.now()
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.adjustment_type == 'TIME_CHANGE'


class TestProductionScheduleService:
    """测试排程服务"""
    
    @pytest.fixture
    def setup_test_data(self, db: Session):
        """准备测试数据"""
        # 创建车间
        workshop = Workshop(
            workshop_code='WS001',
            workshop_name='测试车间',
            workshop_type='MACHINING'
        )
        db.add(workshop)
        db.flush()
        
        # 创建设备
        equipment_list = []
        for i in range(5):
            eq = Equipment(
                equipment_code=f'EQ{i+1:03d}',
                equipment_name=f'测试设备{i+1}',
                workshop_id=workshop.id,
                status='IDLE',
                is_active=True
            )
            equipment_list.append(eq)
            db.add(eq)
        db.flush()
        
        # 创建工人
        worker_list = []
        for i in range(10):
            worker = Worker(
                worker_no=f'W{i+1:03d}',
                worker_name=f'测试工人{i+1}',
                workshop_id=workshop.id,
                status='ACTIVE',
                skill_level='INTERMEDIATE',
                is_active=True
            )
            worker_list.append(worker)
            db.add(worker)
        db.flush()
        
        # 创建工序
        process = ProcessDict(
            process_code='P001',
            process_name='组装',
            process_type='ASSEMBLY'
        )
        db.add(process)
        db.flush()
        
        # 创建工单
        work_order_list = []
        for i in range(20):
            wo = WorkOrder(
                work_order_no=f'WO2026{i+1:04d}',
                task_name=f'测试任务{i+1}',
                task_type='ASSEMBLY',
                workshop_id=workshop.id,
                process_id=process.id,
                plan_qty=10,
                standard_hours=8.0,
                plan_start_date=(datetime.now() + timedelta(days=1)).date(),
                plan_end_date=(datetime.now() + timedelta(days=10)).date(),
                priority='NORMAL' if i % 2 == 0 else 'HIGH',
                status='PENDING'
            )
            work_order_list.append(wo)
            db.add(wo)
        
        db.commit()
        
        return {
            'workshop': workshop,
            'equipment': equipment_list,
            'workers': worker_list,
            'work_orders': work_order_list,
            'process': process
        }
    
    def test_greedy_scheduling(self, db: Session, setup_test_data):
        """测试贪心排程算法"""
        data = setup_test_data
        service = ProductionScheduleService(db)
        
        # 准备请求
        work_order_ids = [wo.id for wo in data['work_orders'][:10]]
        request = ScheduleGenerateRequest(
            work_orders=work_order_ids,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=15),
            algorithm='GREEDY',
            optimize_target='BALANCED',
            consider_worker_skills=True,
            consider_equipment_capacity=True
        )
        
        # 生成排程
        plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
        
        assert plan_id > 0
        assert len(schedules) == 10
        assert all(s.algorithm_version == service.ALGORITHM_VERSION for s in schedules)
        assert all(s.status == 'PENDING' for s in schedules)
    
    def test_heuristic_scheduling(self, db: Session, setup_test_data):
        """测试启发式排程算法"""
        data = setup_test_data
        service = ProductionScheduleService(db)
        
        work_order_ids = [wo.id for wo in data['work_orders'][:15]]
        request = ScheduleGenerateRequest(
            work_orders=work_order_ids,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=20),
            algorithm='HEURISTIC',
            optimize_target='TIME',
            consider_worker_skills=True,
            consider_equipment_capacity=True
        )
        
        plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
        
        assert len(schedules) == 15
        # 启发式算法应该有优化过程
        assert all(s.schedule_plan_id == plan_id for s in schedules)
    
    def test_conflict_detection(self, db: Session, setup_test_data):
        """测试冲突检测"""
        data = setup_test_data
        service = ProductionScheduleService(db)
        
        # 创建两个时间重叠的排程
        now = datetime.now()
        schedule1 = ProductionSchedule(
            work_order_id=data['work_orders'][0].id,
            equipment_id=data['equipment'][0].id,
            worker_id=data['workers'][0].id,
            workshop_id=data['workshop'].id,
            scheduled_start_time=now,
            scheduled_end_time=now + timedelta(hours=8),
            duration_hours=8.0,
            status='PENDING'
        )
        
        schedule2 = ProductionSchedule(
            work_order_id=data['work_orders'][1].id,
            equipment_id=data['equipment'][0].id,  # 同一设备
            worker_id=data['workers'][1].id,
            workshop_id=data['workshop'].id,
            scheduled_start_time=now + timedelta(hours=4),  # 时间重叠
            scheduled_end_time=now + timedelta(hours=12),
            duration_hours=8.0,
            status='PENDING'
        )
        
        schedules = [schedule1, schedule2]
        conflicts = service._detect_conflicts(schedules)
        
        # 应该检测到设备冲突
        assert len(conflicts) > 0
        assert any(c.conflict_type == 'EQUIPMENT' for c in conflicts)
    
    def test_urgent_insert(self, db: Session, setup_test_data):
        """测试紧急插单"""
        data = setup_test_data
        service = ProductionScheduleService(db)
        
        # 先创建一些排程
        work_order_ids = [wo.id for wo in data['work_orders'][:5]]
        request = ScheduleGenerateRequest(
            work_orders=work_order_ids,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=10),
            algorithm='GREEDY'
        )
        
        plan_id, schedules, _ = service.generate_schedule(request, user_id=1)
        db.add_all(schedules)
        db.commit()
        
        # 紧急插单
        urgent_wo = data['work_orders'][10]
        insert_time = datetime.now() + timedelta(days=2)
        
        new_schedule, adjusted, conflicts = service.urgent_insert(
            work_order_id=urgent_wo.id,
            insert_time=insert_time,
            max_delay_hours=8,
            auto_adjust=True,
            user_id=1
        )
        
        assert new_schedule is not None
        assert new_schedule.is_urgent is True
        assert new_schedule.priority_score == 5.0
    
    def test_schedule_scoring(self, db: Session, setup_test_data):
        """测试排程评分"""
        data = setup_test_data
        service = ProductionScheduleService(db)
        
        work_order_ids = [wo.id for wo in data['work_orders'][:10]]
        request = ScheduleGenerateRequest(
            work_orders=work_order_ids,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=15),
            algorithm='GREEDY'
        )
        
        plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
        
        # 计算整体指标
        work_orders = data['work_orders'][:10]
        metrics = service.calculate_overall_metrics(schedules, work_orders)
        
        assert 0 <= metrics.completion_rate <= 1
        assert 0 <= metrics.equipment_utilization <= 1
        assert 0 <= metrics.worker_utilization <= 1
        assert metrics.total_duration_hours > 0
        
        overall_score = metrics.calculate_overall_score()
        assert 0 <= overall_score <= 100


class TestProductionSchedulePerformance:
    """性能测试"""
    
    @pytest.fixture
    def setup_large_dataset(self, db: Session):
        """准备大数据集"""
        # 创建车间
        workshop = Workshop(
            workshop_code='WS001',
            workshop_name='测试车间',
            workshop_type='MACHINING'
        )
        db.add(workshop)
        db.flush()
        
        # 创建20个设备
        for i in range(20):
            eq = Equipment(
                equipment_code=f'EQ{i+1:03d}',
                equipment_name=f'设备{i+1}',
                workshop_id=workshop.id,
                status='IDLE',
                is_active=True
            )
            db.add(eq)
        
        # 创建50个工人
        for i in range(50):
            worker = Worker(
                worker_no=f'W{i+1:04d}',
                worker_name=f'工人{i+1}',
                workshop_id=workshop.id,
                status='ACTIVE',
                is_active=True
            )
            db.add(worker)
        
        # 创建工序
        process = ProcessDict(
            process_code='P001',
            process_name='加工',
            process_type='MACHINING'
        )
        db.add(process)
        db.flush()
        
        # 创建100个工单
        work_order_list = []
        for i in range(100):
            wo = WorkOrder(
                work_order_no=f'WO2026{i+1:05d}',
                task_name=f'任务{i+1}',
                task_type='MACHINING',
                workshop_id=workshop.id,
                process_id=process.id,
                plan_qty=10,
                standard_hours=8.0,
                plan_start_date=(datetime.now() + timedelta(days=1)).date(),
                plan_end_date=(datetime.now() + timedelta(days=30)).date(),
                priority=['LOW', 'NORMAL', 'HIGH', 'URGENT'][i % 4],
                status='PENDING'
            )
            work_order_list.append(wo)
            db.add(wo)
        
        db.commit()
        
        return {
            'workshop': workshop,
            'work_orders': work_order_list,
            'process': process
        }
    
    def test_100_work_orders_performance(self, db: Session, setup_large_dataset):
        """测试100个工单排程性能(要求<5秒)"""
        data = setup_large_dataset
        service = ProductionScheduleService(db)
        
        work_order_ids = [wo.id for wo in data['work_orders']]
        request = ScheduleGenerateRequest(
            work_orders=work_order_ids,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=30),
            algorithm='GREEDY',
            optimize_target='BALANCED',
            consider_worker_skills=True,
            consider_equipment_capacity=True
        )
        
        # 计时
        start_time = time.time()
        plan_id, schedules, conflicts = service.generate_schedule(request, user_id=1)
        elapsed_time = time.time() - start_time
        
        # 验证
        assert len(schedules) == 100
        assert elapsed_time < 5.0, f"排程耗时 {elapsed_time:.2f}秒，超过5秒限制"
        
        print(f"\n✅ 100个工单排程耗时: {elapsed_time:.2f}秒")


class TestProductionScheduleAPI:
    """API集成测试"""
    
    def test_generate_schedule_api(self, client, db: Session, auth_headers):
        """测试生成排程API"""
        # 准备数据
        workshop = Workshop(
            workshop_code='WS001',
            workshop_name='测试车间',
            workshop_type='ASSEMBLY'
        )
        db.add(workshop)
        db.flush()
        
        equipment = Equipment(
            equipment_code='EQ001',
            equipment_name='测试设备',
            workshop_id=workshop.id,
            status='IDLE',
            is_active=True
        )
        db.add(equipment)
        
        worker = Worker(
            worker_no='W001',
            worker_name='测试工人',
            workshop_id=workshop.id,
            status='ACTIVE',
            is_active=True
        )
        db.add(worker)
        
        process = ProcessDict(
            process_code='P001',
            process_name='组装',
            process_type='ASSEMBLY'
        )
        db.add(process)
        db.flush()
        
        work_orders = []
        for i in range(5):
            wo = WorkOrder(
                work_order_no=f'WO{i+1:04d}',
                task_name=f'测试任务{i+1}',
                task_type='ASSEMBLY',
                workshop_id=workshop.id,
                process_id=process.id,
                plan_qty=10,
                standard_hours=8.0,
                plan_end_date=(datetime.now() + timedelta(days=10)).date(),
                priority='NORMAL',
                status='PENDING'
            )
            work_orders.append(wo)
            db.add(wo)
        
        db.commit()
        
        # 调用API
        response = client.post(
            "/api/v1/production/schedule/generate",
            json={
                "work_orders": [wo.id for wo in work_orders],
                "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "end_date": (datetime.now() + timedelta(days=15)).isoformat(),
                "algorithm": "GREEDY",
                "optimize_target": "BALANCED",
                "consider_worker_skills": True,
                "consider_equipment_capacity": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success_count'] == 5
        assert 'plan_id' in data
        assert 'schedules' in data
        assert 'metrics' in data
    
    def test_preview_schedule_api(self, client, db: Session, auth_headers):
        """测试排程预览API"""
        # 创建测试排程
        schedule = ProductionSchedule(
            work_order_id=1,
            schedule_plan_id=1001,
            equipment_id=1,
            scheduled_start_time=datetime.now(),
            scheduled_end_time=datetime.now() + timedelta(hours=8),
            duration_hours=8.0,
            status='PENDING'
        )
        db.add(schedule)
        db.commit()
        
        response = client.get(
            f"/api/v1/production/schedule/preview?plan_id=1001",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['plan_id'] == 1001
        assert 'schedules' in data
        assert 'statistics' in data
    
    def test_conflicts_api(self, client, db: Session, auth_headers):
        """测试冲突检测API"""
        response = client.get(
            "/api/v1/production/schedule/conflicts?plan_id=1001",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'has_conflicts' in data
        assert 'total_conflicts' in data
        assert 'conflicts' in data
    
    def test_urgent_insert_api(self, client, db: Session, auth_headers):
        """测试紧急插单API"""
        # 准备数据
        workshop = Workshop(
            workshop_code='WS001',
            workshop_name='测试车间',
            workshop_type='ASSEMBLY'
        )
        db.add(workshop)
        db.flush()
        
        work_order = WorkOrder(
            work_order_no='WO9999',
            task_name='紧急任务',
            task_type='ASSEMBLY',
            workshop_id=workshop.id,
            plan_qty=5,
            standard_hours=4.0,
            priority='URGENT',
            status='PENDING'
        )
        db.add(work_order)
        db.commit()
        
        response = client.post(
            "/api/v1/production/schedule/urgent-insert",
            json={
                "work_order_id": work_order.id,
                "insert_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "max_delay_hours": 4.0,
                "auto_adjust": True,
                "priority_override": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'schedule' in data
    
    def test_gantt_data_api(self, client, db: Session, auth_headers):
        """测试甘特图数据API"""
        response = client.get(
            "/api/v1/production/schedule/gantt?plan_id=1001",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]  # 可能没有数据


# 测试用例统计
def test_count():
    """统计测试用例数量"""
    test_classes = [
        TestProductionScheduleModels,
        TestProductionScheduleService,
        TestProductionSchedulePerformance,
        TestProductionScheduleAPI
    ]
    
    total = 0
    for cls in test_classes:
        test_methods = [m for m in dir(cls) if m.startswith('test_')]
        total += len(test_methods)
        print(f"{cls.__name__}: {len(test_methods)} 个测试")
    
    print(f"\n总计: {total} 个测试用例")
    assert total >= 25, f"测试用例数量不足，需要至少25个，当前{total}个"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
