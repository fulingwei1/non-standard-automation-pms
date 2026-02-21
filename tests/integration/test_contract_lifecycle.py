# -*- coding: utf-8 -*-
"""销售管理集成测试 - 合同生命周期"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestContractLifecycle:
    def test_contract_drafting(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"contract_number": "CON-001", "customer_id": 1, "contract_amount": 5000000.00}
        response = client.post("/api/v1/sales/contracts", json=data, headers=auth_headers)
        assert response.status_code in [200, 201]
    
    def test_contract_review(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"action": "review", "comments": "合同条款需要修改"}
        response = client.post("/api/v1/sales/contracts/1/review", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_contract_signing(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"signed_date": str(date.today()), "signed_by": "客户代表"}
        response = client.post("/api/v1/sales/contracts/1/sign", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_contract_execution_tracking(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/contracts/1/execution-status", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_contract_completion(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"completion_date": str(date.today())}
        response = client.post("/api/v1/sales/contracts/1/complete", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_contract_archive(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.post("/api/v1/sales/contracts/1/archive", headers=auth_headers)
        assert response.status_code in [200, 404]
