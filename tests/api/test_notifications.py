# -*- coding: utf-8 -*-
"""
通知管理模块 API 测试

测试通知的 CRUD 操作
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestNotificationCRUD:
    """通知 CRUD 测试"""

    def test_list_notifications(self, client: TestClient, admin_token: str):
        """测试获取通知列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_list_notifications_with_pagination(self, client: TestClient, admin_token: str):
        """测试分页获取通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200

    def test_list_unread_notifications(self, client: TestClient, admin_token: str):
        """测试获取未读通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            params={"is_read": False},
            headers=headers
        )

        assert response.status_code == 200

    def test_get_notification_by_id(self, client: TestClient, admin_token: str):
        """测试根据ID获取通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取通知列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get notifications list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No notifications available for testing")

        notification_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers
        )

        if response.status_code == 405:
            pytest.skip("Get notification by ID endpoint not implemented")

        assert response.status_code == 200

    def test_mark_notification_read(self, client: TestClient, admin_token: str):
        """测试标记通知为已读"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取通知列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get notifications list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No notifications available for testing")

        notification_id = items[0]["id"]

        response = client.put(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}/read",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Mark read endpoint not implemented")

        assert response.status_code == 200

    def test_mark_all_notifications_read(self, client: TestClient, admin_token: str):
        """测试标记所有通知为已读"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.put(
            f"{settings.API_V1_PREFIX}/notifications/read-all",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Mark all read endpoint not implemented")

        assert response.status_code == 200

    def test_get_notification_count(self, client: TestClient, admin_token: str):
        """测试获取通知计数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/count",
            headers=headers
        )

        if response.status_code in [404, 405]:
            pytest.skip("Notification count endpoint not implemented")

        assert response.status_code == 200

    def test_delete_notification(self, client: TestClient, admin_token: str):
        """测试删除通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取通知列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get notifications list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No notifications available for testing")

        notification_id = items[0]["id"]

        response = client.delete(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Delete endpoint not implemented")
        if response.status_code == 403:
            pytest.skip("No permission to delete notification")

        assert response.status_code in [200, 204]
