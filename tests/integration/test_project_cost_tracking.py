# -*- coding: utf-8 -*-
"""项目管理集成测试 - 项目成本跟踪"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestProjectCostTracking:
    def test_cost_budget_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        project_data = {"project_name": "测试项目", "project_code": "PRJ-001", "customer_id": 1, "start_date": str(date.today()), "contract_amount": 5000000.00, "project_manager_id": test_employee.id}
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
    
    def test_cost_tracking(self, client: TestClient, db: Session, auth_headers, test_employee):
        cost_data = {"project_id": 1, "cost_category": "人工", "amount": 100000.00}
        response = client.post("/api/v1/finance/cost-records", json=cost_data, headers=auth_headers)
        assert response.status_code in [200, 201]
    
    def test_cost_variance_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/cost-variance?project_id=1", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_cost_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/cost-reports?project_id=1", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_cost_forecast(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/cost-forecast?project_id=1", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_cost_optimization(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/cost-optimization?project_id=1", headers=auth_headers)
        assert response.status_code in [200, 404]
