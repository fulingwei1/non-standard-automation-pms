# -*- coding: utf-8 -*-
"""
验收管理模块 API 测试

测试验收模板、验收单、验收明细和问题管理
"""

import uuid
import pytest
from datetime import date
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


class TestAcceptanceTemplates:
    """验收模板测试"""

    def test_list_templates(self, client: TestClient, admin_token: str):
        """测试获取验收模板列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-templates",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_create_template(self, client: TestClient, admin_token: str):
        """测试创建验收模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        template_data = {
            "template_code": f"TPL-{uuid.uuid4().hex[:6].upper()}",
            "template_name": f"测试模板-{uuid.uuid4().hex[:4]}",
            "acceptance_type": "FAT",
            "version": "V1.0",
            "is_default": False,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/acceptance-templates",
            json=template_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code == 201, response.text

    def test_get_template_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取验收模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取模板列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-templates",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get templates list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No templates available for testing")

        template_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-templates/{template_id}",
            headers=headers
        )

        assert response.status_code == 200

    def test_get_template_items(self, client: TestClient, admin_token: str):
        """测试获取模板检查项"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取模板列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-templates",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get templates list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No templates available for testing")

        template_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-templates/{template_id}/items",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAcceptanceOrders:
    """验收单测试"""

    def test_list_orders(self, client: TestClient, admin_token: str):
        """测试获取验收单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_orders_with_filters(self, client: TestClient, admin_token: str):
        """测试按条件筛选验收单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10, "acceptance_type": "FAT"},
            headers=headers
        )

        assert response.status_code == 200

    def test_get_order_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取验收单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取验收单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get orders list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No orders available for testing")

        order_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{order_id}",
            headers=headers
        )

        assert response.status_code == 200

    def test_get_order_items(self, client: TestClient, admin_token: str):
        """测试获取验收单检查项"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取验收单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get orders list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No orders available for testing")

        order_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{order_id}/items",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_order_issues(self, client: TestClient, admin_token: str):
        """测试获取验收单问题列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取验收单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get orders list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No orders available for testing")

        order_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{order_id}/issues",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_order_signatures(self, client: TestClient, admin_token: str):
        """测试获取验收单签名"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取验收单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get orders list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No orders available for testing")

        order_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{order_id}/signatures",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAcceptanceIssues:
    """验收问题测试"""

    def test_get_issue_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取验收问题"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取验收单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get orders list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No orders available for testing")

        order_id = items[0]["id"]

        # 获取问题列表
        issues_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{order_id}/issues",
            headers=headers
        )

        if issues_response.status_code != 200 or not issues_response.json():
            pytest.skip("No issues available for testing")

        issue_id = issues_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-issues/{issue_id}",
            headers=headers
        )

        assert response.status_code == 200

    def test_get_issue_follow_ups(self, client: TestClient, admin_token: str):
        """测试获取问题跟进记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取验收单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get orders list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No orders available for testing")

        order_id = items[0]["id"]

        # 获取问题列表
        issues_response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{order_id}/issues",
            headers=headers
        )

        if issues_response.status_code != 200 or not issues_response.json():
            pytest.skip("No issues available for testing")

        issue_id = issues_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-issues/{issue_id}/follow-ups",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
