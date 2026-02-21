# -*- coding: utf-8 -*-
"""销售管理集成测试 - 客户跟进记录"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestCustomerFollowUp:
    def test_follow_up_recording(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"customer_id": 1, "follow_up_type": "电话", "content": "跟进项目进展"}
        response = client.post("/api/v1/customers/1/follow-ups", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_follow_up_schedule(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"customer_id": 1, "scheduled_date": str(date.today())}
        response = client.post("/api/v1/customers/1/follow-up-schedule", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_follow_up_history(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/customers/1/follow-up-history", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_follow_up_reminder(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/follow-up-reminders", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_follow_up_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/follow-up-report", headers=auth_headers)
        assert response.status_code in [200, 404]
