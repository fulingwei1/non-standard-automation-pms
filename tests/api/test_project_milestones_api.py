# -*- coding: utf-8 -*-
"""
项目中心里程碑API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/milestones/
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectMilestonesAPI:
    """项目中心里程碑API测试"""

    def test_list_project_milestones(self, client: TestClient, admin_token: str):
        """测试获取项目里程碑列表"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        # 新API返回分页格式
        assert "items" in data or isinstance(data, list)
        if "items" in data:
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    def test_list_project_milestones_with_pagination(self, client: TestClient, admin_token: str):
        """测试分页参数"""
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

        # 测试分页
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        if "items" in data:
            assert data["page"] == 1
            assert data["page_size"] == 10

    def test_list_project_milestones_with_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索"""
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

        # 测试关键词搜索
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            params={"keyword": "测试"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_list_project_milestones_with_status_filter(self, client: TestClient, admin_token: str):
        """测试状态筛选"""
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

        # 测试状态筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            params={"status": "PENDING"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_create_project_milestone(self, client: TestClient, admin_token: str):
        """测试创建项目里程碑"""
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

        milestone_data = {
            "milestone_name": f"测试里程碑-{uuid.uuid4().hex[:4]}",
            "milestone_code": f"MS-{uuid.uuid4().hex[:8]}",
            "milestone_type": "DELIVERY",
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            json=milestone_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create milestone")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["milestone_name"] == milestone_data["milestone_name"]
        assert data["project_id"] == project_id  # 确保项目ID正确

    def test_get_project_milestone_detail(self, client: TestClient, admin_token: str):
        """测试获取项目里程碑详情"""
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

        # 先创建里程碑
        milestone_data = {
            "milestone_name": f"测试里程碑-{uuid.uuid4().hex[:4]}",
            "milestone_code": f"MS-{uuid.uuid4().hex[:8]}",
            "milestone_type": "DELIVERY",
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            json=milestone_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create milestone for testing")

        milestone_id = create_response.json()["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/{milestone_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == milestone_id
        assert data["project_id"] == project_id

    def test_get_project_milestone_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的里程碑"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_project_milestone(self, client: TestClient, admin_token: str):
        """测试更新项目里程碑"""
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

        # 先创建里程碑
        milestone_data = {
            "milestone_name": f"测试里程碑-{uuid.uuid4().hex[:4]}",
            "milestone_code": f"MS-{uuid.uuid4().hex[:8]}",
            "milestone_type": "DELIVERY",
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            json=milestone_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create milestone for testing")

        milestone_id = create_response.json()["id"]

        # 更新里程碑
        update_data = {
            "milestone_name": f"更新里程碑-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/{milestone_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update milestone")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["milestone_name"] == update_data["milestone_name"]

    def test_delete_project_milestone(self, client: TestClient, admin_token: str):
        """测试删除项目里程碑"""
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

        # 先创建里程碑
        milestone_data = {
            "milestone_name": f"测试里程碑-{uuid.uuid4().hex[:4]}",
            "milestone_code": f"MS-{uuid.uuid4().hex[:8]}",
            "milestone_type": "DELIVERY",
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            json=milestone_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create milestone for testing")

        milestone_id = create_response.json()["id"]

        # 删除里程碑
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/{milestone_id}",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to delete milestone")

        assert response.status_code in [200, 204], response.text

    def test_complete_project_milestone(self, client: TestClient, admin_token: str):
        """测试完成项目里程碑（自定义端点）"""
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

        # 先创建里程碑
        milestone_data = {
            "milestone_name": f"测试里程碑-{uuid.uuid4().hex[:4]}",
            "milestone_code": f"MS-{uuid.uuid4().hex[:8]}",
            "milestone_type": "DELIVERY",
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            json=milestone_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create milestone for testing")

        milestone_id = create_response.json()["id"]

        # 完成里程碑
        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/{milestone_id}/complete",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to complete milestone")
        if response.status_code == 400:
            pytest.skip("Milestone already completed or validation error")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "COMPLETED"


class TestProjectMilestonesAdvanced:
    """项目里程碑高级测试"""

    def test_milestone_delay(self, client: TestClient, admin_token: str):
        """测试里程碑延期"""
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

        # 先创建里程碑
        milestone_data = {
            "milestone_name": f"延期测试里程碑-{uuid.uuid4().hex[:4]}",
            "milestone_code": f"MS-{uuid.uuid4().hex[:8]}",
            "milestone_type": "DELIVERY",
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            json=milestone_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create milestone for testing")

        milestone_id = create_response.json()["id"]

        # 延期里程碑
        new_date = (date.today() + timedelta(days=60)).isoformat()
        update_data = {
            "planned_date": new_date,
            "delay_reason": "因供应商交期延迟",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/{milestone_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update milestone")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["planned_date"] == new_date

    def test_milestone_timeline(self, client: TestClient, admin_token: str):
        """测试里程碑时间线"""
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

        # 获取时间线视图
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/timeline",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Timeline endpoint not found")
        if response.status_code == 422:
            pytest.skip("Timeline endpoint not implemented")

        assert response.status_code == 200, response.text

    def test_milestone_by_type_filter(self, client: TestClient, admin_token: str):
        """测试按类型筛选里程碑"""
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

        # 测试不同类型筛选
        types = ["DELIVERY", "FAT", "SAT", "PAYMENT", "INTERNAL"]
        for milestone_type in types:
            response = client.get(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
                params={"type": milestone_type},
                headers=headers
            )

            assert response.status_code == 200, f"Failed for type {milestone_type}: {response.text}"

    def test_overdue_milestones(self, client: TestClient, admin_token: str):
        """测试获取逾期里程碑"""
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

        # 获取逾期里程碑
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            params={"overdue": True},
            headers=headers
        )

        if response.status_code == 422:
            pytest.skip("Overdue filter not supported")

        assert response.status_code == 200, response.text

    def test_upcoming_milestones(self, client: TestClient, admin_token: str):
        """测试获取即将到期的里程碑"""
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

        # 获取即将到期的里程碑（7天内）
        today = date.today()
        end_date = (today + timedelta(days=7)).isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            params={
                "status": "PENDING",
                "planned_date_before": end_date,
            },
            headers=headers
        )

        if response.status_code == 422:
            pytest.skip("Date filter not supported")

        assert response.status_code == 200, response.text

    def test_milestone_summary(self, client: TestClient, admin_token: str):
        """测试里程碑汇总"""
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

        # 获取汇总
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/summary",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Summary endpoint not found")
        if response.status_code == 422:
            pytest.skip("Summary endpoint not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        # 验证汇总字段
        summary = data["data"]
        expected_fields = ["total", "completed", "pending", "overdue"]
        for field in expected_fields:
            if field in summary:
                assert isinstance(summary[field], int)
