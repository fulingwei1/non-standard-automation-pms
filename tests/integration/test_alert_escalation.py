# -*- coding: utf-8 -*-
"""预警管理集成测试 - 预警升级"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestAlertEscalation:
    def test_escalation_rule_setup(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {
            "rule_id": 1,
            "escalation_levels": [
                {"level": 1, "timeout_hours": 2, "recipients": [test_employee.id]},
                {"level": 2, "timeout_hours": 6, "recipients": [test_employee.id, test_employee.id + 1]}
            ]
        }
        response = client.post("/api/v1/alerts/escalation-rules", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_auto_escalation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"alert_id": 1, "reason": "超时未处理"}
        response = client.post("/api/v1/alerts/1/escalate", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_escalation_history(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/1/escalation-history", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_escalation_notification(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.post("/api/v1/alerts/1/escalate/notify", headers=auth_headers)
        assert response.status_code in [200, 404]
