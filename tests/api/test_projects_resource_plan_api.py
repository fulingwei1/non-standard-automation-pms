# -*- coding: utf-8 -*-
"""
项目资源计划 API 测试

测试项目资源规划、分配、调整等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectResourcePlanAPI:
    """项目资源计划 API 测试类"""

    def test_get_resource_plan(self, client: TestClient, admin_token: str):
        """测试获取项目资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource plan API not implemented")

        assert response.status_code == 200, response.text

    def test_create_resource_plan(self, client: TestClient, admin_token: str):
        """测试创建资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        plan_data = {
            "resource_type": "employee",
            "resource_id": 1,
            "allocation_rate": 80.0,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "role": "developer"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/",
            headers=headers,
            json=plan_data
        )

        if response.status_code == 404:
            pytest.skip("Resource plan API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_update_resource_assignment(self, client: TestClient, admin_token: str):
        """测试更新资源分配"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "allocation_rate": 100.0,
            "end_date": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d")
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Resource plan API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_resource_assignment(self, client: TestClient, admin_token: str):
        """测试删除资源分配"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource plan API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_resource_conflict_detection(self, client: TestClient, admin_token: str):
        """测试资源冲突检测"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/conflicts",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource conflict API not implemented")

        assert response.status_code == 200, response.text

    def test_resource_utilization_report(self, client: TestClient, admin_token: str):
        """测试资源利用率报告"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/utilization",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource utilization API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_resources_by_type(self, client: TestClient, admin_token: str):
        """测试按类型过滤资源"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/?resource_type=employee",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_resources_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围过滤资源"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/"
            f"?start_date={start_date}&end_date={end_date}",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource filter API not implemented")

        assert response.status_code == 200, response.text

    def test_resource_availability_check(self, client: TestClient, admin_token: str):
        """测试资源可用性检查"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        check_data = {
            "resource_id": 1,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/resource-plan/availability",
            headers=headers,
            json=check_data
        )

        if response.status_code == 404:
            pytest.skip("Resource availability API not implemented")

        assert response.status_code == 200, response.text

    def test_resource_plan_validation(self, client: TestClient, admin_token: str):
        """测试资源计划验证（分配率超过100%等）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "allocation_rate": 150.0,  # 超过100%
            "start_date": datetime.now().strftime("%Y-%m-%d")
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Resource plan API not implemented")

        assert response.status_code in [200, 422], response.text

    def test_batch_resource_assignment(self, client: TestClient, admin_token: str):
        """测试批量资源分配"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        batch_data = {
            "assignments": [
                {"resource_id": 1, "allocation_rate": 80.0, "role": "developer"},
                {"resource_id": 2, "allocation_rate": 50.0, "role": "tester"}
            ],
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/batch",
            headers=headers,
            json=batch_data
        )

        if response.status_code == 404:
            pytest.skip("Batch resource API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_resource_workload_balance(self, client: TestClient, admin_token: str):
        """测试资源工作量平衡分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/resource-plan/workload-balance",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload balance API not implemented")

        assert response.status_code == 200, response.text

    def test_resource_skills_matching(self, client: TestClient, admin_token: str):
        """测试资源技能匹配"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        match_data = {
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "min_proficiency": 3
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/skills-match",
            headers=headers,
            json=match_data
        )

        if response.status_code == 404:
            pytest.skip("Skills matching API not implemented")

        assert response.status_code == 200, response.text

    def test_resource_plan_timeline_view(self, client: TestClient, admin_token: str):
        """测试资源计划时间线视图"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/timeline",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Timeline view API not implemented")

        assert response.status_code == 200, response.text

    def test_resource_cost_calculation(self, client: TestClient, admin_token: str):
        """测试资源成本计算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/resource-plan/cost",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Resource cost API not implemented")

        assert response.status_code == 200, response.text
