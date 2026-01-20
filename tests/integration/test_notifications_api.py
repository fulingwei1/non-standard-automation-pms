# -*- coding: utf-8 -*-
"""
Integration tests for Notifications API
Covers: app/api/v1/endpoints/notifications.py
"""

from datetime import datetime


class TestNotificationsAPI:
    """通知管理API集成测试"""

    def test_list_notifications(self, client, admin_token):
        """测试获取通知列表"""
        response = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_notifications_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/notifications/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_notifications_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/notifications/?is_read=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_notifications_by_type(self, client, admin_token):
        """测试按类型筛选"""
        response = client.get(
            "/api/v1/notifications/?notification_type=SYSTEM",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_notification_detail(self, client, admin_token, db_session):
        """测试获取通知详情"""
        from app.models.notification import Notification

        notification = Notification(
            title="测试通知",
            content="测试通知内容",
            notification_type="SYSTEM",
            recipient_id=1,
            is_read=False,
            created_at=datetime.now(),
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        response = client.get(
            f"/api/v1/notifications/{notification.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notification.id
        assert data["title"] == notification.title

    def test_get_notification_not_found(self, client, admin_token):
        """测试获取不存在的通知"""
        response = client.get(
            "/api/v1/notifications/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_mark_notification_read(self, client, admin_token, db_session):
        """测试标记通知已读"""
        from app.models.notification import Notification

        notification = Notification(
            title="未读通知",
            content="测试内容",
            notification_type="SYSTEM",
            recipient_id=1,
            is_read=False,
            created_at=datetime.now(),
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        response = client.put(
            f"/api/v1/notifications/{notification.id}/read",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_mark_all_notifications_read(self, client, admin_token):
        """测试标记所有通知已读"""
        response = client.put(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_delete_notification(self, client, admin_token, db_session):
        """测试删除通知"""
        from app.models.notification import Notification

        notification = Notification(
            title="待删除通知",
            content="测试内容",
            notification_type="SYSTEM",
            recipient_id=1,
            is_read=True,
            created_at=datetime.now(),
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        response = client.delete(
            f"/api/v1/notifications/{notification.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_delete_notification_not_found(self, client, admin_token):
        """测试删除不存在的通知"""
        response = client.delete(
            "/api/v1/notifications/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestNotificationsAPIAuth:
    """通知API认证测试"""

    def test_list_notifications_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 401

    def test_get_notification_without_token(self, client):
        """测试无token获取详情"""
        response = client.get("/api/v1/notifications/1")
        assert response.status_code == 401

    def test_mark_read_without_token(self, client):
        """测试无token标记已读"""
        response = client.put("/api/v1/notifications/1/read")
        assert response.status_code == 401

    def test_delete_without_token(self, client):
        """测试无token删除"""
        response = client.delete("/api/v1/notifications/1")
        assert response.status_code == 401


class TestNotificationsAPIValidation:
    """通知API验证测试"""

    def test_invalid_notification_type(self, client, admin_token):
        """测试无效通知类型"""
        response = client.get(
            "/api/v1/notifications/?notification_type=INVALID",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Should return 200 or 422 depending on implementation
        assert response.status_code in [200, 422]

    def test_unread_filter_with_invalid_value(self, client, admin_token):
        """测试无效的已读状态过滤"""
        response = client.get(
            "/api/v1/notifications/?is_read=invalid",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 422]

    def test_get_notification_invalid_id(self, client, admin_token):
        """测试无效的通知ID"""
        response = client.get(
            "/api/v1/notifications/-1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [404, 422]


class TestNotificationsAPIUnreadCount:
    """通知未读计数测试"""

    def test_get_unread_count(self, client, admin_token):
        """测试获取未读通知数量"""
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data or "unread_count" in data
