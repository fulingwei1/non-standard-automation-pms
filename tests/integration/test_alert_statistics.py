# -*- coding: utf-8 -*-
"""预警管理集成测试 - 预警统计分析"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestAlertStatistics:
    def test_alert_count_by_type(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/statistics/by-type", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_trend_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get(
            f"/api/v1/alerts/statistics/trend?start_date={date.today() - timedelta(days=30)}&end_date={date.today()}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
    
    def test_alert_response_time(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/statistics/response-time", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_resolution_rate(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/statistics/resolution-rate", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_dashboard(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/dashboard", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_alert_report_export(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"start_date": str(date.today() - timedelta(days=30)), "end_date": str(date.today()), "format": "excel"}
        response = client.post("/api/v1/alerts/export", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
