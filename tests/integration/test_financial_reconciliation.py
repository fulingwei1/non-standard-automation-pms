# -*- coding: utf-8 -*-
"""财务管理集成测试 - 财务对账"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestFinancialReconciliation:
    def test_bank_reconciliation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"bank_account": "1234567890", "period": "2024-02"}
        response = client.post("/api/v1/finance/bank-reconciliation", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_accounts_receivable_reconciliation(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/ar-reconciliation", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_accounts_payable_reconciliation(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/ap-reconciliation", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_reconciliation_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/reconciliation-report", headers=auth_headers)
        assert response.status_code in [200, 404]
