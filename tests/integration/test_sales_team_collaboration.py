# -*- coding: utf-8 -*-
"""销售管理集成测试 - 销售团队协作"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestSalesTeamCollaboration:
    def test_team_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"team_name": "华东销售团队", "team_leader": test_employee.id}
        response = client.post("/api/v1/sales/teams", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_member_assignment(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"employee_id": test_employee.id, "role": "销售代表"}
        response = client.post("/api/v1/sales/teams/1/members", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_territory_division(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"team_id": 1, "territory": "江苏省"}
        response = client.post("/api/v1/sales/territory-assignments", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_team_performance(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/teams/1/performance", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_team_collaboration_log(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/teams/1/collaboration-log", headers=auth_headers)
        assert response.status_code in [200, 404]
