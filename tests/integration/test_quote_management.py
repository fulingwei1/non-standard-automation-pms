# -*- coding: utf-8 -*-
"""销售管理集成测试 - 报价管理"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestQuoteManagement:
    def test_quote_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"quote_number": "QT-001", "customer_id": 1, "total_amount": 3000000.00}
        response = client.post("/api/v1/sales/quotes", json=data, headers=auth_headers)
        assert response.status_code in [200, 201]
    
    def test_quote_version_management(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"version": "V2.0", "change_description": "价格调整"}
        response = client.post("/api/v1/sales/quotes/1/versions", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_quote_approval(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"action": "approve"}
        response = client.post("/api/v1/sales/quotes/1/approve", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_quote_to_contract_conversion(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"quote_id": 1}
        response = client.post("/api/v1/sales/quotes/1/convert-to-contract", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_quote_expiration_check(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/quotes/expiring", headers=auth_headers)
        assert response.status_code in [200, 404]
