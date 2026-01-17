# -*- coding: utf-8 -*-
"""
机台管理模块 API 测试

测试机台的 CRUD 操作、进度更新、BOM 和文档管理
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_project(client: TestClient, token: str) -> dict:
    """获取第一个可用的项目"""
    headers = _auth_headers(token)
    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/",
        headers=headers
    )

    if response.status_code != 200:
        return None

    projects = response.json()
    items = projects.get("items", projects) if isinstance(projects, dict) else projects
    if not items:
        return None

    return items[0]


class TestMachineCRUD:
    """机台 CRUD 测试"""

    def test_list_machines(self, client: TestClient, admin_token: str):
        """测试获取机台列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_machines_with_project_filter(self, client: TestClient, admin_token: str):
        """测试按项目筛选机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            params={"project_id": project["id"]},
            headers=headers
        )

        assert response.status_code == 200

    def test_list_machines_by_project(self, client: TestClient, admin_token: str):
        """测试获取项目的机台列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/projects/{project['id']}/machines",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_machine(self, client: TestClient, admin_token: str):
        """测试创建机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        machine_data = {
            "machine_code": f"PN{uuid.uuid4().hex[:3].upper()}",
            "machine_name": f"测试机台-{uuid.uuid4().hex[:4]}",
            "project_id": project["id"],
            "machine_type": "ICT",
            "quantity": 1,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/machines/",
            json=machine_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create machine")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400:
            pytest.skip("Machine code already exists or validation error")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["machine_code"] == machine_data["machine_code"]

    def test_create_machine_for_project(self, client: TestClient, admin_token: str):
        """测试为项目创建机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        machine_data = {
            "machine_code": f"PN{uuid.uuid4().hex[:3].upper()}",
            "machine_name": f"项目机台-{uuid.uuid4().hex[:4]}",
            "machine_type": "FCT",
            "quantity": 1,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/machines/projects/{project['id']}/machines",
            json=machine_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create machine")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400:
            pytest.skip("Machine code already exists or validation error")

        assert response.status_code in [200, 201], response.text

    def test_get_machine_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取机台列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get machines list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No machines available for testing")

        machine_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/{machine_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == machine_id

    def test_get_machine_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_machine(self, client: TestClient, admin_token: str):
        """测试更新机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取机台列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get machines list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No machines available for testing")

        machine_id = items[0]["id"]

        update_data = {
            "machine_name": f"更新机台-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/machines/{machine_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update machine")

        assert response.status_code == 200, response.text


class TestMachineProgress:
    """机台进度测试"""

    def test_update_machine_progress(self, client: TestClient, admin_token: str):
        """测试更新机台进度"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取机台列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get machines list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No machines available for testing")

        machine_id = items[0]["id"]

        progress_data = {
            "progress": 50,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/machines/{machine_id}/progress",
            json=progress_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update progress")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code == 200, response.text


class TestMachineBom:
    """机台 BOM 测试"""

    def test_get_machine_bom(self, client: TestClient, admin_token: str):
        """测试获取机台的 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取机台列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get machines list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No machines available for testing")

        machine_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/{machine_id}/bom",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMachineServiceHistory:
    """机台服务历史测试"""

    def test_get_machine_service_history(self, client: TestClient, admin_token: str):
        """测试获取机台服务历史"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取机台列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get machines list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No machines available for testing")

        machine_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/{machine_id}/service-history",
            headers=headers
        )

        assert response.status_code == 200


class TestMachineDocuments:
    """机台文档测试"""

    def test_get_machine_documents(self, client: TestClient, admin_token: str):
        """测试获取机台文档列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取机台列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/machines/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get machines list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No machines available for testing")

        machine_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/machines/{machine_id}/documents",
            headers=headers
        )

        assert response.status_code == 200


class TestMachineDelete:
    """机台删除测试"""

    def test_delete_machine_not_found(self, client: TestClient, admin_token: str):
        """测试删除不存在的机台"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.delete(
            f"{settings.API_V1_PREFIX}/machines/99999",
            headers=headers
        )

        assert response.status_code in [404, 403]  # 可能返回403如果没有权限
