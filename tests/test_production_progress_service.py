# -*- coding: utf-8 -*-
"""
生产进度跟踪系统 - Service层测试
包含核心算法测试
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.production import (
    ProductionProgressLog,
    WorkstationStatus,
    ProgressAlert,
    WorkOrder,
    Workstation,
    Workshop,
)
from app.models.user import User
from app.schemas.production_progress import ProductionProgressLogCreate
from app.services.production_progress_service import ProductionProgressService


class TestProgressDeviationEngine:
    """测试进度偏差计算引擎"""

    def test_calculate_deviation_on_schedule(self, db: Session, test_work_order_on_schedule):
        """测试按计划进度的偏差计算"""
        service = ProductionProgressService(db)
        
        plan_progress, deviation, is_delayed = service.calculate_progress_deviation(
            test_work_order_on_schedule.id,
            actual_progress=50
        )
        
        # 50%进度，正好按计划
        assert plan_progress == 50
        assert deviation == 0
        assert is_delayed is False

    def test_calculate_deviation_ahead(self, db: Session, test_work_order_on_schedule):
        """测试超前进度的偏差计算"""
        service = ProductionProgressService(db)
        
        plan_progress, deviation, is_delayed = service.calculate_progress_deviation(
            test_work_order_on_schedule.id,
            actual_progress=70
        )
        
        assert plan_progress == 50
        assert deviation == 20  # 超前20%
        assert is_delayed is False

    def test_calculate_deviation_delayed(self, db: Session, test_work_order_on_schedule):
        """测试延期进度的偏差计算"""
        service = ProductionProgressService(db)
        
        plan_progress, deviation, is_delayed = service.calculate_progress_deviation(
            test_work_order_on_schedule.id,
            actual_progress=30
        )
        
        assert plan_progress == 50
        assert deviation == -20  # 落后20%
        assert is_delayed is True  # 落后超过5%认为延期

    def test_calculate_deviation_not_started(self, db: Session):
        """测试未开始工单的偏差计算"""
        # 创建未来的工单
        work_order = WorkOrder(
            work_order_no='WO-FUTURE-001',
            task_name='未来工单',
            task_type='TEST',
            plan_start_date=date.today() + timedelta(days=5),
            plan_end_date=date.today() + timedelta(days=10),
            status='PENDING',
            progress=0
        )
        db.add(work_order)
        db.commit()
        
        service = ProductionProgressService(db)
        plan_progress, deviation, is_delayed = service.calculate_progress_deviation(
            work_order.id,
            actual_progress=0
        )
        
        assert plan_progress == 0  # 还没开始
        assert deviation == 0
        assert is_delayed is False

    def test_calculate_deviation_overdue(self, db: Session):
        """测试逾期工单的偏差计算"""
        # 创建已逾期的工单
        work_order = WorkOrder(
            work_order_no='WO-OVERDUE-001',
            task_name='逾期工单',
            task_type='TEST',
            plan_start_date=date.today() - timedelta(days=10),
            plan_end_date=date.today() - timedelta(days=3),
            status='IN_PROGRESS',
            progress=80
        )
        db.add(work_order)
        db.commit()
        
        service = ProductionProgressService(db)
        plan_progress, deviation, is_delayed = service.calculate_progress_deviation(
            work_order.id,
            actual_progress=80
        )
        
        assert plan_progress == 100  # 应该已经完成
        assert deviation == -20  # 落后20%
        assert is_delayed is True

    def test_deviation_percentage_calculation(self, db: Session):
        """测试偏差百分比计算"""
        service = ProductionProgressService(db)
        
        # 偏差10%，计划进度50%，偏差比例=10/50*100=20%
        percentage = service.calculate_deviation_percentage(
            deviation=10,
            plan_progress=50
        )
        assert percentage == Decimal('20')
        
        # 偏差-15%，计划进度60%，偏差比例=15/60*100=25%
        percentage = service.calculate_deviation_percentage(
            deviation=-15,
            plan_progress=60
        )
        assert percentage == Decimal('25')


class TestBottleneckIdentification:
    """测试瓶颈工位识别算法"""

    def test_identify_light_bottleneck(self, db: Session, test_workstation):
        """测试识别轻度瓶颈"""
        # 创建工位状态：利用率92%
        ws_status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            capacity_utilization=Decimal('92.0'),
            work_hours_today=Decimal('7.36'),
            planned_hours_today=Decimal('8.0'),
            is_bottleneck=1,
            bottleneck_level=1,
            status_updated_at=datetime.now()
        )
        db.add(ws_status)
        db.commit()
        
        service = ProductionProgressService(db)
        bottlenecks = service.identify_bottlenecks(min_level=1)
        
        assert len(bottlenecks) >= 1
        bottleneck = next(b for b in bottlenecks if b['workstation_id'] == test_workstation.id)
        assert bottleneck['bottleneck_level'] == 1
        assert float(bottleneck['capacity_utilization']) >= 90

    def test_identify_medium_bottleneck(self, db: Session, test_workstation, test_work_order):
        """测试识别中度瓶颈"""
        # 创建工位状态：利用率96%，有排队工单
        ws_status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            capacity_utilization=Decimal('96.0'),
            work_hours_today=Decimal('7.68'),
            planned_hours_today=Decimal('8.0'),
            is_bottleneck=1,
            bottleneck_level=2,
            status_updated_at=datetime.now()
        )
        db.add(ws_status)
        
        # 创建排队工单
        pending_wo = WorkOrder(
            work_order_no='WO-PENDING-001',
            task_name='排队工单',
            task_type='TEST',
            workstation_id=test_workstation.id,
            status='PENDING',
            progress=0
        )
        db.add(pending_wo)
        db.commit()
        
        service = ProductionProgressService(db)
        bottlenecks = service.identify_bottlenecks(min_level=2)
        
        assert len(bottlenecks) >= 1
        bottleneck = next(b for b in bottlenecks if b['workstation_id'] == test_workstation.id)
        assert bottleneck['bottleneck_level'] >= 2
        assert bottleneck['pending_work_order_count'] >= 1

    def test_identify_critical_bottleneck(self, db: Session, test_workstation):
        """测试识别严重瓶颈"""
        # 创建工位状态：利用率99%
        ws_status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            capacity_utilization=Decimal('99.0'),
            work_hours_today=Decimal('7.92'),
            planned_hours_today=Decimal('8.0'),
            is_bottleneck=1,
            bottleneck_level=3,
            status_updated_at=datetime.now()
        )
        db.add(ws_status)
        
        # 创建4个排队工单
        for i in range(4):
            wo = WorkOrder(
                work_order_no=f'WO-QUEUE-{i:03d}',
                task_name=f'排队工单{i+1}',
                task_type='TEST',
                workstation_id=test_workstation.id,
                status='PENDING',
                progress=0
            )
            db.add(wo)
        db.commit()
        
        service = ProductionProgressService(db)
        bottlenecks = service.identify_bottlenecks(min_level=3)
        
        assert len(bottlenecks) >= 1
        bottleneck = next(b for b in bottlenecks if b['workstation_id'] == test_workstation.id)
        assert bottleneck['bottleneck_level'] == 3
        assert bottleneck['pending_work_order_count'] >= 4

    def test_bottleneck_filtering(self, db: Session, test_workshop, test_workstation):
        """测试瓶颈筛选"""
        # 创建多个工位
        ws2 = Workstation(
            workstation_code='WK-TEST-02',
            workstation_name='正常工位',
            workshop_id=test_workshop.id,
            status='IDLE',
            is_active=True
        )
        db.add(ws2)
        db.commit()
        
        # 创建瓶颈工位状态
        bottleneck_status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            capacity_utilization=Decimal('95.0'),
            is_bottleneck=1,
            bottleneck_level=2,
            status_updated_at=datetime.now(),
            planned_hours_today=Decimal('8.0')
        )
        
        # 创建正常工位状态
        normal_status = WorkstationStatus(
            workstation_id=ws2.id,
            current_state='IDLE',
            capacity_utilization=Decimal('60.0'),
            is_bottleneck=0,
            bottleneck_level=0,
            status_updated_at=datetime.now(),
            planned_hours_today=Decimal('8.0')
        )
        
        db.add_all([bottleneck_status, normal_status])
        db.commit()
        
        service = ProductionProgressService(db)
        
        # 只查询level≥2的瓶颈
        bottlenecks = service.identify_bottlenecks(min_level=2)
        assert len(bottlenecks) == 1
        assert bottlenecks[0]['workstation_id'] == test_workstation.id


class TestAlertRulesEngine:
    """测试进度预警规则引擎"""

    def test_delay_warning_rule(self, db: Session, test_work_order_delayed, test_user):
        """测试延期预警规则"""
        service = ProductionProgressService(db)
        alerts = service.evaluate_alert_rules(test_work_order_delayed.id, test_user.id)
        
        # 应该触发延期预警
        delay_alerts = [a for a in alerts if a.alert_type == 'DELAY']
        assert len(delay_alerts) > 0
        
        alert = delay_alerts[0]
        assert alert.alert_level in ['WARNING', 'CRITICAL']

    def test_critical_delay_rule(self, db: Session, test_user):
        """测试严重延期预警规则"""
        # 创建严重延期的工单（偏差-25%）
        work_order = WorkOrder(
            work_order_no='WO-CRITICAL-001',
            task_name='严重延期工单',
            task_type='TEST',
            plan_start_date=date.today() - timedelta(days=10),
            plan_end_date=date.today() + timedelta(days=10),
            status='IN_PROGRESS',
            progress=25  # 实际25%，计划应该50%
        )
        db.add(work_order)
        db.commit()
        
        service = ProductionProgressService(db)
        alerts = service.evaluate_alert_rules(work_order.id, test_user.id)
        
        delay_alerts = [a for a in alerts if a.alert_type == 'DELAY']
        assert len(delay_alerts) > 0
        assert delay_alerts[0].alert_level == 'CRITICAL'

    def test_quality_alert_rule(self, db: Session, test_user):
        """测试质量预警规则"""
        # 创建质量问题工单（合格率90%）
        work_order = WorkOrder(
            work_order_no='WO-QUALITY-001',
            task_name='质量问题工单',
            task_type='TEST',
            completed_qty=100,
            qualified_qty=90,  # 合格率90%
            defect_qty=10,
            status='IN_PROGRESS',
            progress=50
        )
        db.add(work_order)
        db.commit()
        
        service = ProductionProgressService(db)
        alerts = service.evaluate_alert_rules(work_order.id, test_user.id)
        
        quality_alerts = [a for a in alerts if a.alert_type == 'QUALITY']
        assert len(quality_alerts) > 0
        assert quality_alerts[0].alert_level == 'CRITICAL'

    def test_efficiency_alert_rule(self, db: Session, test_user):
        """测试效率预警规则"""
        # 创建效率低下工单（效率70%）
        work_order = WorkOrder(
            work_order_no='WO-EFFICIENCY-001',
            task_name='效率问题工单',
            task_type='TEST',
            standard_hours=Decimal('10.0'),
            actual_hours=Decimal('14.3'),  # 效率=10/14.3≈70%
            status='IN_PROGRESS',
            progress=50
        )
        db.add(work_order)
        db.commit()
        
        service = ProductionProgressService(db)
        alerts = service.evaluate_alert_rules(work_order.id, test_user.id)
        
        efficiency_alerts = [a for a in alerts if a.alert_type == 'EFFICIENCY']
        assert len(efficiency_alerts) > 0

    def test_bottleneck_alert_rule(self, db: Session, test_work_order, test_workstation, test_user):
        """测试瓶颈预警规则"""
        # 创建瓶颈工位状态
        ws_status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            capacity_utilization=Decimal('97.0'),
            is_bottleneck=1,
            bottleneck_level=2,
            status_updated_at=datetime.now(),
            planned_hours_today=Decimal('8.0')
        )
        db.add(ws_status)
        
        # 更新工单所在工位
        test_work_order.workstation_id = test_workstation.id
        db.commit()
        
        service = ProductionProgressService(db)
        alerts = service.evaluate_alert_rules(test_work_order.id, test_user.id)
        
        bottleneck_alerts = [a for a in alerts if a.alert_type == 'BOTTLENECK']
        assert len(bottleneck_alerts) > 0


class TestBusinessMethods:
    """测试业务方法"""

    def test_create_progress_log(self, db: Session, test_work_order, test_user):
        """测试创建进度日志"""
        service = ProductionProgressService(db)
        
        log_data = ProductionProgressLogCreate(
            work_order_id=test_work_order.id,
            current_progress=50,
            completed_qty=10,
            qualified_qty=9,
            defect_qty=1,
            work_hours=Decimal('4.0'),
            status='IN_PROGRESS',
            note='完成一半'
        )
        
        log = service.create_progress_log(log_data, test_user.id)
        
        assert log.id is not None
        assert log.current_progress == 50
        assert log.logged_by == test_user.id
        
        # 验证工单更新
        db.refresh(test_work_order)
        assert test_work_order.progress == 50

    def test_get_realtime_overview(self, db: Session, test_work_order):
        """测试获取实时总览"""
        service = ProductionProgressService(db)
        overview = service.get_realtime_overview()
        
        assert overview.total_work_orders >= 1
        assert overview.overall_progress >= Decimal('0')

    def test_get_work_order_timeline(self, db: Session, test_work_order, test_user):
        """测试获取工单时间线"""
        # 先创建一些进度日志
        service = ProductionProgressService(db)
        
        for progress in [20, 40, 60]:
            log_data = ProductionProgressLogCreate(
                work_order_id=test_work_order.id,
                current_progress=progress,
                completed_qty=progress // 5,
                qualified_qty=progress // 5,
                defect_qty=0,
                status='IN_PROGRESS'
            )
            service.create_progress_log(log_data, test_user.id)
        
        timeline = service.get_work_order_timeline(test_work_order.id)
        
        assert timeline is not None
        assert timeline.work_order_id == test_work_order.id
        assert len(timeline.timeline) == 3

    def test_dismiss_alert(self, db: Session, test_work_order, test_user):
        """测试关闭预警"""
        # 创建预警
        alert = ProgressAlert(
            work_order_id=test_work_order.id,
            alert_type='DELAY',
            alert_level='WARNING',
            alert_title='测试预警',
            alert_message='测试',
            status='ACTIVE',
            triggered_at=datetime.now()
        )
        db.add(alert)
        db.commit()
        
        service = ProductionProgressService(db)
        success = service.dismiss_alert(alert.id, test_user.id, '已处理')
        
        assert success is True
        
        db.refresh(alert)
        assert alert.status == 'DISMISSED'
        assert alert.dismissed_by == test_user.id
        assert alert.resolution_note == '已处理'


# ==================== Fixtures ====================

@pytest.fixture
def test_user(db: Session):
    """创建测试用户"""
    user = User(
        username='test_service_user',
        email='service@test.com',
        hashed_password='hashed',
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_workshop(db: Session):
    """创建测试车间"""
    workshop = Workshop(
        workshop_code='WS-SVC-01',
        workshop_name='服务测试车间',
        workshop_type='MACHINING',
        is_active=True
    )
    db.add(workshop)
    db.commit()
    db.refresh(workshop)
    return workshop


@pytest.fixture
def test_workstation(db: Session, test_workshop):
    """创建测试工位"""
    workstation = Workstation(
        workstation_code='WK-SVC-01',
        workstation_name='服务测试工位',
        workshop_id=test_workshop.id,
        status='IDLE',
        is_active=True
    )
    db.add(workstation)
    db.commit()
    db.refresh(workstation)
    return workstation


@pytest.fixture
def test_work_order(db: Session, test_workstation):
    """创建测试工单"""
    work_order = WorkOrder(
        work_order_no='WO-SVC-001',
        task_name='服务测试工单',
        task_type='MACHINING',
        workstation_id=test_workstation.id,
        plan_qty=20,
        completed_qty=0,
        qualified_qty=0,
        defect_qty=0,
        plan_start_date=date.today(),
        plan_end_date=date.today() + timedelta(days=10),
        status='PENDING',
        priority='NORMAL',
        progress=0
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


@pytest.fixture
def test_work_order_on_schedule(db: Session, test_workstation):
    """创建按计划进度的工单（当前应该50%）"""
    work_order = WorkOrder(
        work_order_no='WO-ONTIME-001',
        task_name='按时工单',
        task_type='TEST',
        workstation_id=test_workstation.id,
        plan_start_date=date.today() - timedelta(days=5),
        plan_end_date=date.today() + timedelta(days=5),
        status='IN_PROGRESS',
        progress=50
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


@pytest.fixture
def test_work_order_delayed(db: Session, test_workstation):
    """创建延期工单"""
    work_order = WorkOrder(
        work_order_no='WO-DELAY-001',
        task_name='延期工单',
        task_type='TEST',
        workstation_id=test_workstation.id,
        plan_start_date=date.today() - timedelta(days=10),
        plan_end_date=date.today() + timedelta(days=10),
        status='IN_PROGRESS',
        progress=30  # 计划应该50%，实际30%，偏差-20%
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order
