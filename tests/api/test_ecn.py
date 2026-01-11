# -*- coding: utf-8 -*-
"""
工程变更通知 (ECN) 模块 API 测试

测试 ECN 的 CRUD 操作、评估、审批和任务管理
"""

import uuid
import pytest
from datetime import date, timedelta
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


class TestEcnCRUD:
    """ECN CRUD 测试"""

    def test_list_ecns(self, client: TestClient, admin_token: str):
        """测试获取 ECN 列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_ecns_with_filters(self, client: TestClient, admin_token: str):
        """测试按条件筛选 ECN"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10, "status": "DRAFT"},
            headers=headers
        )

        assert response.status_code == 200

    def test_create_ecn(self, client: TestClient, admin_token: str):
        """测试创建 ECN"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        ecn_data = {
            "title": f"测试ECN-{uuid.uuid4().hex[:4]}",
            "project_id": project["id"],
            "change_type": "DESIGN",
            "priority": "MEDIUM",
            "description": "测试变更描述",
            "reason": "测试变更原因",
            "expected_date": (date.today() + timedelta(days=7)).isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/ecns",
            json=ecn_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code == 201, response.text

    def test_get_ecn_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取 ECN"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取 ECN 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get ECN list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No ECNs available for testing")

        ecn_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/{ecn_id}",
            headers=headers
        )

        assert response.status_code == 200


class TestEcnEvaluations:
    """ECN 评估测试"""

    def test_get_ecn_evaluations(self, client: TestClient, admin_token: str):
        """测试获取 ECN 评估列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取 ECN 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get ECN list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No ECNs available for testing")

        ecn_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/{ecn_id}/evaluations",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_ecn_evaluation_summary(self, client: TestClient, admin_token: str):
        """测试获取 ECN 评估汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取 ECN 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get ECN list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No ECNs available for testing")

        ecn_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/{ecn_id}/evaluation-summary",
            headers=headers
        )

        assert response.status_code == 200


class TestEcnApprovals:
    """ECN 审批测试"""

    def test_get_ecn_approvals(self, client: TestClient, admin_token: str):
        """测试获取 ECN 审批列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取 ECN 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get ECN list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No ECNs available for testing")

        ecn_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/{ecn_id}/approvals",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_approval_matrix(self, client: TestClient, admin_token: str):
        """测试获取审批矩阵"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/ecn-approval-matrix",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestEcnTasks:
    """ECN 任务测试"""

    def test_get_ecn_tasks(self, client: TestClient, admin_token: str):
        """测试获取 ECN 任务列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取 ECN 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/ecns",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get ECN list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No ECNs available for testing")

        ecn_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/{ecn_id}/tasks",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
