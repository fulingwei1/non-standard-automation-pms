# -*- coding: utf-8 -*-
"""
生产进度跟踪系统 - API测试
测试8个核心接口
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.production import (
    ProductionProgressLog,
    WorkstationStatus,
    ProgressAlert,
    WorkOrder,
    Workstation,
    Workshop,
)
from app.models.user import User


client = TestClient(app)


class TestRealtimeProgressAPI:
    """测试实时进度总览API"""

    def test_get_realtime_overview(self, auth_headers, test_work_order):
        """测试 GET /production/progress/realtime"""
        response = client.get(
            "/api/v1/production/progress/realtime",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_work_orders" in data
        assert "in_progress" in data
        assert "overall_progress" in data
        assert data["total_work_orders"] >= 1

    def test_realtime_overview_with_filter(self, auth_headers, test_workshop):
        """测试带筛选的实时总览"""
        response = client.get(
            f"/api/v1/production/progress/realtime?workshop_id={test_workshop.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestWorkOrderTimelineAPI:
    """测试工单进度时间线API"""

    def test_get_work_order_timeline(self, auth_headers, test_work_order_with_logs):
        """测试 GET /production/progress/work-orders/{id}/timeline"""
        response = client.get(
            f"/api/v1/production/progress/work-orders/{test_work_order_with_logs.id}/timeline",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["work_order_id"] == test_work_order_with_logs.id
        assert "timeline" in data
        assert "alerts" in data
        assert len(data["timeline"]) >= 1

    def test_get_nonexistent_work_order(self, auth_headers):
        """测试获取不存在的工单"""
        response = client.get(
            "/api/v1/production/progress/work-orders/99999/timeline",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestWorkstationRealtimeAPI:
    """测试工位实时状态API"""

    def test_get_workstation_realtime(self, auth_headers, test_workstation_with_status):
        """测试 GET /production/progress/workstations/{id}/realtime"""
        response = client.get(
            f"/api/v1/production/progress/workstations/{test_workstation_with_status.id}/realtime",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["workstation_id"] == test_workstation_with_status.id
        assert "current_state" in data
        assert "capacity_utilization" in data

    def test_get_workstation_without_status(self, auth_headers, test_workstation):
        """测试获取无状态的工位"""
        response = client.get(
            f"/api/v1/production/progress/workstations/{test_workstation.id}/realtime",
            headers=auth_headers
        )
        
        # 应该返回404，因为没有状态记录
        assert response.status_code == 404


class TestProgressLogAPI:
    """测试进度日志API"""

    def test_create_progress_log(self, auth_headers, test_work_order, db: Session):
        """测试 POST /production/progress/log"""
        log_data = {
            "work_order_id": test_work_order.id,
            "current_progress": 50,
            "completed_qty": 10,
            "qualified_qty": 9,
            "defect_qty": 1,
            "work_hours": "4.0",
            "status": "IN_PROGRESS",
            "note": "完成一半"
        }
        
        response = client.post(
            "/api/v1/production/progress/log",
            json=log_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["current_progress"] == 50
        assert data["work_order_id"] == test_work_order.id
        
        # 验证工单已更新
        db.refresh(test_work_order)
        assert test_work_order.progress == 50

    def test_create_log_invalid_work_order(self, auth_headers):
        """测试创建无效工单的日志"""
        log_data = {
            "work_order_id": 99999,
            "current_progress": 50,
            "status": "IN_PROGRESS"
        }
        
        response = client.post(
            "/api/v1/production/progress/log",
            json=log_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestBottleneckAPI:
    """测试瓶颈工位识别API"""

    def test_get_bottlenecks(self, auth_headers, test_bottleneck_workstation):
        """测试 GET /production/progress/bottlenecks"""
        response = client.get(
            "/api/v1/production/progress/bottlenecks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        bottleneck = data[0]
        assert "workstation_id" in bottleneck
        assert "bottleneck_level" in bottleneck
        assert "capacity_utilization" in bottleneck

    def test_get_bottlenecks_with_level_filter(self, auth_headers):
        """测试按等级筛选瓶颈"""
        response = client.get(
            "/api/v1/production/progress/bottlenecks?min_level=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for bottleneck in data:
            assert bottleneck["bottleneck_level"] >= 2

    def test_get_bottlenecks_with_limit(self, auth_headers):
        """测试限制返回数量"""
        response = client.get(
            "/api/v1/production/progress/bottlenecks?limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5


class TestAlertAPI:
    """测试进度预警API"""

    def test_get_alerts(self, auth_headers, test_alert):
        """测试 GET /production/progress/alerts"""
        response = client.get(
            "/api/v1/production/progress/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        alert = data[0]
        assert "alert_type" in alert
        assert "alert_level" in alert
        assert "status" in alert

    def test_get_alerts_with_filters(self, auth_headers, test_work_order):
        """测试带筛选条件的预警列表"""
        response = client.get(
            f"/api/v1/production/progress/alerts?work_order_id={test_work_order.id}&alert_level=WARNING",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for alert in data:
            assert alert["work_order_id"] == test_work_order.id

    def test_dismiss_alert(self, auth_headers, test_alert, db: Session):
        """测试 POST /production/progress/alerts/{id}/dismiss"""
        dismiss_data = {
            "resolution_note": "已处理完成"
        }
        
        response = client.post(
            f"/api/v1/production/progress/alerts/{test_alert.id}/dismiss",
            json=dismiss_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["alert_id"] == test_alert.id
        
        # 验证预警已关闭
        db.refresh(test_alert)
        assert test_alert.status == 'DISMISSED'
        assert test_alert.resolution_note == '已处理完成'

    def test_dismiss_nonexistent_alert(self, auth_headers):
        """测试关闭不存在的预警"""
        response = client.post(
            "/api/v1/production/progress/alerts/99999/dismiss",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestDeviationAPI:
    """测试进度偏差分析API"""

    def test_get_deviation_analysis(self, auth_headers, test_delayed_work_order):
        """测试 GET /production/progress/deviation"""
        response = client.get(
            "/api/v1/production/progress/deviation",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            deviation = data[0]
            assert "work_order_id" in deviation
            assert "deviation" in deviation
            assert "risk_level" in deviation

    def test_get_deviation_with_filters(self, auth_headers):
        """测试带筛选条件的偏差分析"""
        response = client.get(
            "/api/v1/production/progress/deviation?min_deviation=15&only_delayed=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for deviation in data:
            assert abs(deviation["deviation"]) >= 15
            assert deviation["is_delayed"] is True


class TestPermissions:
    """测试权限控制"""

    def test_read_permission_required(self, db: Session):
        """测试读取权限要求"""
        # 创建无权限用户
        user = User(
            username='no_perm_user',
            email='noperm@test.com',
            hashed_password='hashed',
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # TODO: 实现无权限用户的认证和测试
        # 这里需要根据实际的权限系统实现
        pass

    def test_write_permission_required(self, db: Session):
        """测试写入权限要求"""
        # TODO: 实现无写入权限用户的测试
        pass


# ==================== Fixtures ====================

@pytest.fixture
def auth_headers(test_user, db: Session):
    """创建认证头"""
    # TODO: 根据实际认证系统生成token
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def test_user(db: Session):
    """创建测试用户"""
    user = User(
        username='test_api_user',
        email='api@test.com',
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
        workshop_code='WS-API-01',
        workshop_name='API测试车间',
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
        workstation_code='WK-API-01',
        workstation_name='API测试工位',
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
        work_order_no='WO-API-001',
        task_name='API测试工单',
        task_type='MACHINING',
        workstation_id=test_workstation.id,
        plan_qty=20,
        plan_start_date=date.today(),
        plan_end_date=date.today() + timedelta(days=10),
        status='PENDING',
        progress=0
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


@pytest.fixture
def test_work_order_with_logs(db: Session, test_work_order, test_user):
    """创建带进度日志的工单"""
    for i, progress in enumerate([20, 40, 60], 1):
        log = ProductionProgressLog(
            work_order_id=test_work_order.id,
            current_progress=progress,
            completed_qty=progress // 5,
            status='IN_PROGRESS',
            logged_at=datetime.now() - timedelta(hours=24-i*8),
            logged_by=test_user.id
        )
        db.add(log)
    db.commit()
    return test_work_order


@pytest.fixture
def test_workstation_with_status(db: Session, test_workstation):
    """创建带状态的工位"""
    status = WorkstationStatus(
        workstation_id=test_workstation.id,
        current_state='BUSY',
        capacity_utilization=Decimal('75.0'),
        work_hours_today=Decimal('6.0'),
        planned_hours_today=Decimal('8.0'),
        status_updated_at=datetime.now()
    )
    db.add(status)
    db.commit()
    return test_workstation


@pytest.fixture
def test_bottleneck_workstation(db: Session, test_workstation):
    """创建瓶颈工位"""
    status = WorkstationStatus(
        workstation_id=test_workstation.id,
        current_state='BUSY',
        capacity_utilization=Decimal('95.0'),
        is_bottleneck=1,
        bottleneck_level=2,
        work_hours_today=Decimal('7.6'),
        planned_hours_today=Decimal('8.0'),
        status_updated_at=datetime.now()
    )
    db.add(status)
    db.commit()
    return test_workstation


@pytest.fixture
def test_alert(db: Session, test_work_order):
    """创建测试预警"""
    alert = ProgressAlert(
        work_order_id=test_work_order.id,
        alert_type='DELAY',
        alert_level='WARNING',
        alert_title='延期预警',
        alert_message='工单进度落后',
        status='ACTIVE',
        triggered_at=datetime.now()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@pytest.fixture
def test_delayed_work_order(db: Session, test_workstation):
    """创建延期工单"""
    work_order = WorkOrder(
        work_order_no='WO-DELAYED-001',
        task_name='延期工单',
        task_type='TEST',
        workstation_id=test_workstation.id,
        plan_start_date=date.today() - timedelta(days=10),
        plan_end_date=date.today() + timedelta(days=10),
        status='IN_PROGRESS',
        progress=30  # 应该50%，实际30%
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order
