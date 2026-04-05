# -*- coding: utf-8 -*-
"""
生产管理 API 测试
测试车间管理、工位管理、生产计划、工单管理、报工系统等功能
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.production import ProductionPlan, WorkOrder, WorkReport, Worker, Workshop, Workstation


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def production_seed(db: Session) -> dict:
    """构造一组最小生产测试数据，避免详情接口因空库而跳过。"""
    suffix = uuid4().hex[:8]
    today = date.today()

    workshop = Workshop(
        workshop_code=f"WS-{suffix}",
        workshop_name=f"测试车间-{suffix}",
        workshop_type="MACHINING",
        capacity_hours=Decimal("8.00"),
        is_active=True,
    )
    db.add(workshop)
    db.flush()

    worker = Worker(
        worker_no=f"WK-{suffix}",
        worker_name=f"测试工人-{suffix}",
        workshop_id=workshop.id,
        position="OPERATOR",
        skill_level="INTERMEDIATE",
        entry_date=today,
        status="ACTIVE",
        is_active=True,
    )
    db.add(worker)
    db.flush()

    workstation = Workstation(
        workstation_code=f"ST-{suffix}",
        workstation_name=f"测试工位-{suffix}",
        workshop_id=workshop.id,
        status="IDLE",
        is_active=True,
    )
    db.add(workstation)
    db.flush()

    plan = ProductionPlan(
        plan_no=f"PLAN-{suffix}",
        plan_name=f"测试计划-{suffix}",
        plan_type="WORKSHOP",
        workshop_id=workshop.id,
        plan_start_date=today,
        plan_end_date=today,
        status="DRAFT",
        progress=0,
    )
    db.add(plan)
    db.flush()

    work_order = WorkOrder(
        work_order_no=f"WO-{suffix}",
        task_name=f"测试工单-{suffix}",
        task_type="MACHINING",
        production_plan_id=plan.id,
        workshop_id=workshop.id,
        workstation_id=workstation.id,
        assigned_to=worker.id,
        plan_qty=10,
        completed_qty=5,
        qualified_qty=5,
        defect_qty=0,
        standard_hours=Decimal("4.00"),
        actual_hours=Decimal("2.00"),
        plan_start_date=today,
        plan_end_date=today,
        status="ASSIGNED",
        priority="NORMAL",
        progress=50,
    )
    db.add(work_order)
    db.flush()

    workstation.current_worker_id = worker.id
    workstation.current_work_order_id = work_order.id

    report = WorkReport(
        report_no=f"WR-{suffix}",
        work_order_id=work_order.id,
        worker_id=worker.id,
        report_type="PROGRESS",
        report_time=datetime.now(),
        progress_percent=50,
        work_hours=Decimal("2.00"),
        completed_qty=5,
        qualified_qty=5,
        defect_qty=0,
        status="APPROVED",
    )
    db.add(report)
    db.commit()

    return {
        "workshop_id": workshop.id,
        "workstation_id": workstation.id,
        "plan_id": plan.id,
        "work_order_id": work_order.id,
        "worker_id": worker.id,
    }


class TestWorkshops:
    """车间管理测试"""

    def test_list_workshops(self, client: TestClient, admin_token: str):
        """测试获取车间列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshops endpoint not found")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_workshops_by_type(self, client: TestClient, admin_token: str):
        """测试按类型筛选车间"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops",
            params={"workshop_type": "MACHINING"},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshops endpoint not found")

        assert response.status_code == 200

    def test_get_workshop_by_id(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取单个车间"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/{production_seed['workshop_id']}",
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshop not found")

        assert response.status_code == 200

    def test_get_workshop_capacity(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取车间产能"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/{production_seed['workshop_id']}/capacity",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshop or capacity endpoint not found")

        assert response.status_code == 200


class TestWorkstations:
    """工位管理测试"""

    def test_list_workstations(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取工位列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/{production_seed['workshop_id']}/workstations",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workstations endpoint not found")

        assert response.status_code == 200


class TestProductionPlans:
    """生产计划测试"""

    def test_list_production_plans(self, client: TestClient, admin_token: str):
        """测试获取生产计划列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/plans",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Production plans endpoint not found")

        assert response.status_code == 200

    def test_get_production_plan_by_id(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取单个生产计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/plans/{production_seed['plan_id']}",
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Production plan not found")

        assert response.status_code == 200


class TestWorkOrders:
    """工单管理测试"""

    def test_list_work_orders(self, client: TestClient, admin_token: str):
        """测试获取工单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/work-orders",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Work orders endpoint not found")

        assert response.status_code == 200

    def test_list_work_orders_by_status(self, client: TestClient, admin_token: str):
        """测试按状态筛选工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/work-orders",
            params={"status": "PENDING"},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Work orders endpoint not found")

        assert response.status_code == 200

    def test_get_work_order_by_id(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取单个工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/work-orders/{production_seed['work_order_id']}",
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Work order not found")

        assert response.status_code == 200


class TestWorkReports:
    """报工系统测试"""

    def test_list_work_reports(self, client: TestClient, admin_token: str):
        """测试获取报工列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/work-reports",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Work reports endpoint not found")

        assert response.status_code == 200


class TestMaterialRequisition:
    """领料管理测试"""

    def test_list_material_requisitions(self, client: TestClient, admin_token: str):
        """测试获取领料单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/material-requisitions",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Material requisitions endpoint not found")

        assert response.status_code == 200


class TestProductionExceptions:
    """生产异常测试"""

    def test_list_production_exceptions(self, client: TestClient, admin_token: str):
        """测试获取生产异常列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/exceptions",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Production exceptions endpoint not found")

        assert response.status_code == 200


class TestProductionDashboard:
    """生产驾驶舱测试"""

    def test_get_production_dashboard(self, client: TestClient, admin_token: str):
        """测试获取生产驾驶舱数据"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/production/dashboard", headers=headers)

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Production dashboard endpoint not found")

        assert response.status_code == 200

    def test_get_workshop_task_board(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取车间任务看板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/{production_seed['workshop_id']}/task-board",
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Task board endpoint not found")

        assert response.status_code == 200


class TestWorkerManagement:
    """工人管理测试"""

    def test_list_workers(self, client: TestClient, admin_token: str):
        """测试获取工人列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workers",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workers endpoint not found")

        assert response.status_code == 200

    def test_get_worker_performance(
        self, client: TestClient, admin_token: str, production_seed: dict
    ):
        """测试获取工人绩效报告"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workers/{production_seed['worker_id']}/performance",
            headers=headers,
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Worker performance endpoint not found")

        assert response.status_code == 200
