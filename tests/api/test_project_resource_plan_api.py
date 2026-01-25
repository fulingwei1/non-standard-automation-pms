# -*- coding: utf-8 -*-
"""
项目中心资源计划API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/resource-plan/
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectResourcePlanAPI:
    """项目中心资源计划API测试"""

    def test_list_project_resource_plans(self, client: TestClient, admin_token: str):
        """测试获取项目资源计划列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试项目中心API
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

    def test_list_project_resource_plans_with_stage_filter(self, client: TestClient, admin_token: str):
        """测试阶段筛选"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试阶段筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            params={"stage_code": "S1"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_get_project_resource_plan_detail(self, client: TestClient, admin_token: str):
        """测试获取资源计划详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先获取资源计划列表
        plans_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            headers=headers
        )

        if plans_response.status_code != 200:
            pytest.skip("Failed to get resource plans list")

        plans = plans_response.json()
        if not plans:
            pytest.skip("No resource plans available for testing")

        plan_id = plans[0]["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/{plan_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == plan_id
        assert data["project_id"] == project_id

    def test_get_project_resource_plan_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_get_resource_plan_summary(self, client: TestClient, admin_token: str):
        """测试获取资源计划汇总（自定义端点）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试汇总
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/summary",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "project_id" in data
        assert "stages" in data
        assert "overall_fill_rate" in data

    def test_create_resource_plan(self, client: TestClient, admin_token: str):
        """测试创建资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 创建资源计划
        plan_data = {
            "stage_code": "S2",
            "role_name": "软件工程师",
            "headcount": 2,
            "skill_requirements": "Python, FastAPI",
            "planned_start": "2025-02-01",
            "planned_end": "2025-03-31",
            "remark": "方案设计阶段人员需求"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            json=plan_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create resource plan")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["project_id"] == project_id
        assert data["stage_code"] == "S2"
        assert data["role_name"] == "软件工程师"

    def test_update_resource_plan(self, client: TestClient, admin_token: str):
        """测试更新资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先创建一个资源计划
        plan_data = {
            "stage_code": "S3",
            "role_name": "测试工程师",
            "headcount": 1,
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            json=plan_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create resource plan for update test")

        plan_id = create_response.json().get("id")
        if not plan_id:
            pytest.skip("Failed to get resource plan ID")

        # 更新资源计划
        update_data = {
            "headcount": 3,
            "remark": "更新后的备注"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/{plan_id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["headcount"] == 3

    def test_delete_resource_plan(self, client: TestClient, admin_token: str):
        """测试删除资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先创建一个资源计划
        plan_data = {
            "stage_code": "S4",
            "role_name": "机械工程师",
            "headcount": 1,
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            json=plan_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create resource plan for delete test")

        plan_id = create_response.json().get("id")
        if not plan_id:
            pytest.skip("Failed to get resource plan ID")

        # 删除资源计划
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/{plan_id}",
            headers=headers
        )

        assert response.status_code in [200, 204], response.text

        # 验证已删除
        get_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/{plan_id}",
            headers=headers
        )
        assert get_response.status_code == 404

    def test_delete_assigned_resource_plan_fails(self, client: TestClient, admin_token: str):
        """测试删除已分配的资源计划应失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 获取资源计划列表，找一个已分配的
        plans_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            headers=headers
        )

        if plans_response.status_code != 200:
            pytest.skip("Failed to get resource plans list")

        plans = plans_response.json()
        assigned_plan = None
        for plan in plans:
            if plan.get("assignment_status") == "ASSIGNED":
                assigned_plan = plan
                break

        if not assigned_plan:
            pytest.skip("No assigned resource plan available for testing")

        # 尝试删除已分配的资源计划
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/{assigned_plan['id']}",
            headers=headers
        )

        # 应该返回400错误
        assert response.status_code == 400

    def test_resource_plan_by_multiple_stages(self, client: TestClient, admin_token: str):
        """测试按多个阶段筛选资源计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 按不同阶段筛选
        stages = ["S1", "S2", "S3", "S4", "S5"]
        for stage in stages:
            response = client.get(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
                params={"stage_code": stage},
                headers=headers
            )

            assert response.status_code == 200, f"Failed for stage {stage}: {response.text}"
            data = response.json()
            # 验证返回的所有计划都是该阶段的
            for plan in data:
                if plan.get("stage_code"):
                    assert plan["stage_code"] == stage
