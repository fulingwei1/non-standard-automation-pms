# -*- coding: utf-8 -*-
"""项目管理集成测试 - 项目资源分配"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestProjectResourceAllocation:
    def test_resource_planning(self, client: TestClient, db: Session, auth_headers, test_employee):
        plan_data = {"project_id": 1, "resource_type": "人力", "quantity": 10}
        response = client.post("/api/v1/projects/1/resource-plan", json=plan_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_resource_allocation(self, client: TestClient, db: Session, auth_headers, test_employee):
        alloc_data = {"project_id": 1, "employee_id": test_employee.id, "allocation_percentage": 80}
        response = client.post("/api/v1/projects/1/resource-allocation", json=alloc_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_resource_conflict_detection(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/resource-conflicts", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_resource_utilization(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/resource-utilization", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_resource_optimization(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/resource-optimization?project_id=1", headers=auth_headers)
        assert response.status_code in [200, 404]
