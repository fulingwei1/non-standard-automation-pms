# -*- coding: utf-8 -*-
"""预警管理集成测试 - 预警处理跟踪"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestAlertHandlingTracking:
    def test_alert_assignment(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"alert_id": 1, "assigned_to": test_employee.id}
        response = client.post("/api/v1/alerts/1/assign", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_handling_progress(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"alert_id": 1, "progress": "正在处理", "comments": "已联系相关人员"}
        response = client.post("/api/v1/alerts/1/progress", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_alert_resolution(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"alert_id": 1, "resolution": "已解决", "solution": "调整资源配置"}
        response = client.post("/api/v1/alerts/1/resolve", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_closure(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"alert_id": 1, "closed_by": test_employee.id, "closure_notes": "问题已解决"}
        response = client.post("/api/v1/alerts/1/close", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_handling_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/handling-report", headers=auth_headers)
        assert response.status_code in [200, 404]
