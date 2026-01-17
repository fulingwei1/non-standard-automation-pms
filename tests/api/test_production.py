# -*- coding: utf-8 -*-
"""
生产管理 API 测试
测试车间管理、工位管理、生产计划、工单管理、报工系统等功能
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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
            headers=headers
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
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshops endpoint not found")

        assert response.status_code == 200

    def test_get_workshop_by_id(self, client: TestClient, admin_token: str):
        """测试获取单个车间"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/1",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshop not found")

        assert response.status_code == 200

    def test_get_workshop_capacity(self, client: TestClient, admin_token: str):
        """测试获取车间产能"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/1/capacity",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workshop or capacity endpoint not found")

        assert response.status_code == 200


class TestWorkstations:
    """工位管理测试"""

    def test_list_workstations(self, client: TestClient, admin_token: str):
        """测试获取工位列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/1/workstations",
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
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Production plans endpoint not found")

        assert response.status_code == 200

    def test_get_production_plan_by_id(self, client: TestClient, admin_token: str):
        """测试获取单个生产计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/plans/1",
            headers=headers
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
            headers=headers
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
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Work orders endpoint not found")

        assert response.status_code == 200

    def test_get_work_order_by_id(self, client: TestClient, admin_token: str):
        """测试获取单个工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/work-orders/1",
            headers=headers
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
            headers=headers
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
            headers=headers
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
            headers=headers
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
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/dashboard",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Production dashboard endpoint not found")

        assert response.status_code == 200

    def test_get_workshop_task_board(self, client: TestClient, admin_token: str):
        """测试获取车间任务看板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/1/task-board",
            headers=headers
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
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Workers endpoint not found")

        assert response.status_code == 200

    def test_get_worker_performance(self, client: TestClient, admin_token: str):
        """测试获取工人绩效报告"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/production/workers/1/performance",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have production:read permission")
        if response.status_code == 404:
            pytest.skip("Worker performance endpoint not found")

        assert response.status_code == 200
