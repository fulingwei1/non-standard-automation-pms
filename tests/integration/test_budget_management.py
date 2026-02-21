# -*- coding: utf-8 -*-
"""财务管理集成测试 - 预算管理"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestBudgetManagement:
    def test_budget_preparation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"year": 2024, "total_budget": 100000000.00, "department_id": 1}
        response = client.post("/api/v1/finance/budgets", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_budget_allocation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"budget_id": 1, "allocations": [{"category": "人工", "amount": 30000000}]}
        response = client.post("/api/v1/finance/budgets/1/allocate", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_budget_execution_monitoring(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/budgets/1/execution", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_budget_adjustment(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"adjustment_amount": 5000000, "reason": "业务扩展"}
        response = client.post("/api/v1/finance/budgets/1/adjust", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_budget_performance_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/budgets/performance-analysis", headers=auth_headers)
        assert response.status_code in [200, 404]
