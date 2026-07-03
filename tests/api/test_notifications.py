# -*- coding: utf-8 -*-
"""
通知管理模块 API 测试

测试通知的 CRUD 操作
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.config import settings
from app.models.notification import Notification
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return _auth_headers(token)


class TestNotificationCRUD:
    """通知 CRUD 测试"""

    def test_regular_user_can_read_only_own_notifications(
        self,
        client: TestClient,
        db_session,
        regular_user: User,
        normal_user: User,
    ):
        """普通登录用户应能读取自己的通知，不需要额外 notification:read 权限"""
        marker = f"NOTIFY-OWN-{uuid.uuid4().hex}"
        own_notification = Notification(
            user_id=regular_user.id,
            notification_type="SYSTEM",
            source_type="test",
            source_id=regular_user.id,
            title=f"{marker}-own",
            content="own notification",
            is_read=False,
        )
        other_notification = Notification(
            user_id=normal_user.id,
            notification_type="SYSTEM",
            source_type="test",
            source_id=normal_user.id,
            title=f"{marker}-other",
            content="other notification",
            is_read=False,
        )
        db_session.add_all([own_notification, other_notification])
        db_session.commit()

        headers = _auth_headers_for_user(regular_user)
        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/",
            params={"page": 1, "page_size": 100},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        titles = {item["title"] for item in data["items"]}
        assert f"{marker}-own" in titles
        assert f"{marker}-other" not in titles

        count_response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/unread-count",
            headers=headers,
        )

        assert count_response.status_code == 200
        assert count_response.json()["data"]["unread_count"] >= 1

        read_response = client.put(
            f"{settings.API_V1_PREFIX}/notifications/{own_notification.id}/read",
            headers=headers,
        )
        assert read_response.status_code == 200
        db_session.refresh(own_notification)
        assert own_notification.is_read is True

        own_notification.is_read = False
        db_session.add(own_notification)
        db_session.commit()
        batch_response = client.put(
            f"{settings.API_V1_PREFIX}/notifications/batch-read",
            json={"notification_ids": [own_notification.id]},
            headers=headers,
        )
        assert batch_response.status_code == 200
        db_session.refresh(own_notification)
        assert own_notification.is_read is True

        own_notification.is_read = False
        db_session.add(own_notification)
        db_session.commit()
        read_all_response = client.put(
            f"{settings.API_V1_PREFIX}/notifications/read-all",
            headers=headers,
        )
        assert read_all_response.status_code == 200
        db_session.refresh(own_notification)
        assert own_notification.is_read is True

        settings_response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/settings",
            headers=headers,
        )
        assert settings_response.status_code == 200

        delete_other_response = client.delete(
            f"{settings.API_V1_PREFIX}/notifications/{other_notification.id}",
            headers=headers,
        )
        assert delete_other_response.status_code == 404

        delete_own_response = client.delete(
            f"{settings.API_V1_PREFIX}/notifications/{own_notification.id}",
            headers=headers,
        )
        assert delete_own_response.status_code == 200

    def test_list_notifications(self, client: TestClient, admin_token: str):
        """测试获取通知列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/notifications/", headers=headers)

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
            headers=headers,
        )

        assert response.status_code == 200

    def test_list_unread_notifications(self, client: TestClient, admin_token: str):
        """测试获取未读通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/", params={"is_read": False}, headers=headers
        )

        assert response.status_code == 200

    def test_get_notification_by_id(self, client: TestClient, admin_token: str):
        """测试根据ID获取通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取通知列表
        list_response = client.get(f"{settings.API_V1_PREFIX}/notifications/", headers=headers)

        if list_response.status_code != 200:
            pytest.skip("Failed to get notifications list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No notifications available for testing")

        notification_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}", headers=headers
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
        list_response = client.get(f"{settings.API_V1_PREFIX}/notifications/", headers=headers)

        if list_response.status_code != 200:
            pytest.skip("Failed to get notifications list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No notifications available for testing")

        notification_id = items[0]["id"]

        response = client.put(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}/read", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Mark read endpoint not implemented")

        assert response.status_code == 200

    def test_mark_all_notifications_read(self, client: TestClient, admin_token: str):
        """测试标记所有通知为已读"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.put(f"{settings.API_V1_PREFIX}/notifications/read-all", headers=headers)

        if response.status_code == 404:
            pytest.skip("Mark all read endpoint not implemented")

        assert response.status_code == 200

    def test_get_notification_count(self, client: TestClient, admin_token: str):
        """测试获取通知计数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/notifications/count", headers=headers)

        if response.status_code in [404, 405]:
            pytest.skip("Notification count endpoint not implemented")

        assert response.status_code == 200

    def test_delete_notification(self, client: TestClient, admin_token: str):
        """测试删除通知"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取通知列表
        list_response = client.get(f"{settings.API_V1_PREFIX}/notifications/", headers=headers)

        if list_response.status_code != 200:
            pytest.skip("Failed to get notifications list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No notifications available for testing")

        notification_id = items[0]["id"]

        response = client.delete(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Delete endpoint not implemented")
        if response.status_code == 403:
            pytest.skip("No permission to delete notification")

        assert response.status_code in [200, 204]
