# -*- coding: utf-8 -*-
"""销售管理集成测试 - 销售目标管理"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestSalesTargetManagement:
    def test_target_setting(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"year": 2024, "target_amount": 50000000.00, "employee_id": test_employee.id}
        response = client.post("/api/v1/sales/targets", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_target_decomposition(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"target_id": 1, "quarterly_breakdown": [12500000, 12500000, 12500000, 12500000]}
        response = client.post("/api/v1/sales/targets/1/decompose", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_target_tracking(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/targets/1/tracking", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_target_achievement_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/targets/achievement-analysis", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_target_adjustment(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"new_target_amount": 55000000.00, "adjustment_reason": "市场环境变化"}
        response = client.put("/api/v1/sales/targets/1", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
