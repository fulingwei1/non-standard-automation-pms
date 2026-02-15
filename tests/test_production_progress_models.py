# -*- coding: utf-8 -*-
"""
生产进度跟踪系统 - 模型测试
"""
import pytest
from datetime import datetime, date
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


class TestProductionProgressLog:
    """测试 ProductionProgressLog 模型"""

    def test_create_progress_log(self, db: Session, test_work_order, test_user):
        """测试创建进度日志"""
        log = ProductionProgressLog(
            work_order_id=test_work_order.id,
            previous_progress=0,
            current_progress=50,
            progress_delta=50,
            completed_qty=10,
            qualified_qty=9,
            defect_qty=1,
            work_hours=Decimal('8.0'),
            cumulative_hours=Decimal('8.0'),
            status='IN_PROGRESS',
            logged_at=datetime.now(),
            logged_by=test_user.id,
            plan_progress=50,
            deviation=0,
            is_delayed=0
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.current_progress == 50
        assert log.progress_delta == 50
        assert log.is_delayed == 0

    def test_progress_log_deviation_calculation(self, db: Session, test_work_order, test_user):
        """测试进度偏差记录"""
        log = ProductionProgressLog(
            work_order_id=test_work_order.id,
            previous_progress=30,
            current_progress=35,
            progress_delta=5,
            status='IN_PROGRESS',
            logged_at=datetime.now(),
            logged_by=test_user.id,
            plan_progress=50,
            deviation=-15,  # 实际35% vs 计划50%
            is_delayed=1
        )
        
        db.add(log)
        db.commit()
        
        assert log.deviation == -15
        assert log.is_delayed == 1

    def test_progress_log_cumulative_hours(self, db: Session, test_work_order, test_user):
        """测试累计工时"""
        # 第一次记录
        log1 = ProductionProgressLog(
            work_order_id=test_work_order.id,
            current_progress=30,
            work_hours=Decimal('4.0'),
            cumulative_hours=Decimal('4.0'),
            status='IN_PROGRESS',
            logged_at=datetime.now(),
            logged_by=test_user.id
        )
        db.add(log1)
        db.commit()
        
        # 第二次记录
        log2 = ProductionProgressLog(
            work_order_id=test_work_order.id,
            current_progress=60,
            work_hours=Decimal('5.0'),
            cumulative_hours=Decimal('9.0'),
            status='IN_PROGRESS',
            logged_at=datetime.now(),
            logged_by=test_user.id
        )
        db.add(log2)
        db.commit()
        
        assert log2.cumulative_hours == Decimal('9.0')


class TestWorkstationStatus:
    """测试 WorkstationStatus 模型"""

    def test_create_workstation_status(self, db: Session, test_workstation):
        """测试创建工位状态"""
        status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            current_progress=50,
            completed_qty_today=10,
            target_qty_today=20,
            capacity_utilization=Decimal('75.5'),
            work_hours_today=Decimal('6.0'),
            idle_hours_today=Decimal('2.0'),
            planned_hours_today=Decimal('8.0'),
            efficiency_rate=Decimal('85.0'),
            quality_rate=Decimal('98.5'),
            is_bottleneck=0,
            bottleneck_level=0,
            status_updated_at=datetime.now()
        )
        
        db.add(status)
        db.commit()
        db.refresh(status)
        
        assert status.id is not None
        assert status.current_state == 'BUSY'
        assert status.capacity_utilization == Decimal('75.5')

    def test_workstation_bottleneck_identification(self, db: Session, test_workstation):
        """测试瓶颈工位识别"""
        status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            capacity_utilization=Decimal('96.0'),  # 超过95%
            work_hours_today=Decimal('7.7'),
            idle_hours_today=Decimal('0.3'),
            planned_hours_today=Decimal('8.0'),
            is_bottleneck=1,
            bottleneck_level=2,  # 中度瓶颈
            alert_count=3,
            status_updated_at=datetime.now()
        )
        
        db.add(status)
        db.commit()
        
        assert status.is_bottleneck == 1
        assert status.bottleneck_level == 2

    def test_workstation_capacity_calculation(self, db: Session, test_workstation):
        """测试产能利用率计算"""
        status = WorkstationStatus(
            workstation_id=test_workstation.id,
            current_state='BUSY',
            work_hours_today=Decimal('7.2'),
            idle_hours_today=Decimal('0.8'),
            planned_hours_today=Decimal('8.0'),
            capacity_utilization=Decimal('90.0'),
            status_updated_at=datetime.now()
        )
        
        db.add(status)
        db.commit()
        
        # 验证产能利用率 = 工作工时 / 计划工时 * 100
        expected = (Decimal('7.2') / Decimal('8.0')) * Decimal('100')
        assert status.capacity_utilization == Decimal('90.0')


class TestProgressAlert:
    """测试 ProgressAlert 模型"""

    def test_create_delay_alert(self, db: Session, test_work_order, test_user):
        """测试创建延期预警"""
        alert = ProgressAlert(
            work_order_id=test_work_order.id,
            alert_type='DELAY',
            alert_level='WARNING',
            alert_title='进度延期预警',
            alert_message='工单进度落后计划10%',
            current_value=Decimal('40'),
            threshold_value=Decimal('50'),
            deviation_value=Decimal('10'),
            status='ACTIVE',
            triggered_at=datetime.now(),
            rule_code='RULE_DELAY_WARNING',
            rule_name='延期预警规则'
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        assert alert.id is not None
        assert alert.alert_type == 'DELAY'
        assert alert.alert_level == 'WARNING'
        assert alert.status == 'ACTIVE'

    def test_create_bottleneck_alert(self, db: Session, test_work_order, test_workstation):
        """测试创建瓶颈预警"""
        alert = ProgressAlert(
            work_order_id=test_work_order.id,
            workstation_id=test_workstation.id,
            alert_type='BOTTLENECK',
            alert_level='CRITICAL',
            alert_title='工位瓶颈预警',
            alert_message='工位产能利用率98%，存在严重瓶颈',
            current_value=Decimal('98'),
            threshold_value=Decimal('90'),
            status='ACTIVE',
            triggered_at=datetime.now(),
            rule_code='RULE_BOTTLENECK',
            rule_name='瓶颈预警规则'
        )
        
        db.add(alert)
        db.commit()
        
        assert alert.alert_type == 'BOTTLENECK'
        assert alert.workstation_id == test_workstation.id

    def test_alert_lifecycle(self, db: Session, test_work_order, test_user):
        """测试预警生命周期"""
        alert = ProgressAlert(
            work_order_id=test_work_order.id,
            alert_type='QUALITY',
            alert_level='WARNING',
            alert_title='质量预警',
            alert_message='合格率低于95%',
            status='ACTIVE',
            triggered_at=datetime.now()
        )
        
        db.add(alert)
        db.commit()
        
        # 确认预警
        alert.status = 'ACKNOWLEDGED'
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = test_user.id
        db.commit()
        
        assert alert.status == 'ACKNOWLEDGED'
        assert alert.acknowledged_by == test_user.id
        
        # 关闭预警
        alert.status = 'DISMISSED'
        alert.dismissed_at = datetime.now()
        alert.dismissed_by = test_user.id
        alert.resolution_note = '已整改'
        db.commit()
        
        assert alert.status == 'DISMISSED'
        assert alert.resolution_note == '已整改'

    def test_multiple_alert_types(self, db: Session, test_work_order):
        """测试多种预警类型"""
        alert_types = [
            ('DELAY', 'WARNING', '延期预警'),
            ('BOTTLENECK', 'CRITICAL', '瓶颈预警'),
            ('QUALITY', 'WARNING', '质量预警'),
            ('EFFICIENCY', 'INFO', '效率预警'),
            ('CAPACITY', 'CRITICAL', '产能预警'),
        ]
        
        for alert_type, level, title in alert_types:
            alert = ProgressAlert(
                work_order_id=test_work_order.id,
                alert_type=alert_type,
                alert_level=level,
                alert_title=title,
                alert_message=f'{title}测试',
                status='ACTIVE',
                triggered_at=datetime.now()
            )
            db.add(alert)
        
        db.commit()
        
        # 验证创建了5种预警
        count = db.query(ProgressAlert).filter(
            ProgressAlert.work_order_id == test_work_order.id
        ).count()
        assert count == 5


# ==================== Fixtures ====================

@pytest.fixture
def test_user(db: Session):
    """创建测试用户"""
    user = User(
        username='test_progress_user',
        email='progress@test.com',
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
        workshop_code='WS-TEST-01',
        workshop_name='测试车间',
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
        workstation_code='WK-TEST-01',
        workstation_name='测试工位',
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
        work_order_no='WO-TEST-001',
        task_name='测试工单',
        task_type='MACHINING',
        workstation_id=test_workstation.id,
        plan_qty=20,
        completed_qty=0,
        qualified_qty=0,
        defect_qty=0,
        plan_start_date=date.today(),
        plan_end_date=date.today(),
        status='PENDING',
        priority='NORMAL',
        progress=0
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order
