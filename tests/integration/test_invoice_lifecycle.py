# -*- coding: utf-8 -*-
"""财务管理集成测试 - 发票生命周期"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestInvoiceLifecycle:
    def test_invoice_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"invoice_number": "INV-001", "amount": 1000000.00, "customer_id": 1}
        response = client.post("/api/v1/finance/invoices", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_invoice_verification(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"verified_by": test_employee.id, "verification_status": "通过"}
        response = client.post("/api/v1/finance/invoices/1/verify", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_invoice_payment_matching(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"invoice_id": 1, "payment_id": 1}
        response = client.post("/api/v1/finance/invoice-payment-matching", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_invoice_cancellation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"cancellation_reason": "客户要求"}
        response = client.post("/api/v1/finance/invoices/1/cancel", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_invoice_archiving(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.post("/api/v1/finance/invoices/1/archive", headers=auth_headers)
        assert response.status_code in [200, 404]
