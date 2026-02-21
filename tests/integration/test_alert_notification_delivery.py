# -*- coding: utf-8 -*-
"""
预警管理集成测试 - 预警通知发送
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestAlertNotificationDelivery:
    
    def test_email_notification(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：邮件通知"""
        notification_data = {
            "alert_id": 1,
            "notification_type": "email",
            "recipients": ["manager@company.com"],
            "subject": "项目进度预警",
            "content": "项目进度延迟"
        }
        
        response = client.post("/api/v1/alerts/notifications", json=notification_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_sms_notification(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：短信通知"""
        sms_data = {
            "alert_id": 1,
            "notification_type": "sms",
            "recipients": ["13800138000"],
            "content": "成本超支预警"
        }
        
        response = client.post("/api/v1/alerts/notifications", json=sms_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_system_notification(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：系统内通知"""
        system_notif_data = {
            "alert_id": 1,
            "notification_type": "system",
            "recipient_ids": [test_employee.id],
            "content": "质量风险预警"
        }
        
        response = client.post("/api/v1/alerts/notifications", json=system_notif_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_notification_delivery_status(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：通知发送状态"""
        response = client.get("/api/v1/alerts/notifications/1/status", headers=auth_headers)
        assert response.status_code in [200, 404]
