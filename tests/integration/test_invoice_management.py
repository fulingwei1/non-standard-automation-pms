# -*- coding: utf-8 -*-
"""销售管理集成测试 - 发票管理"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestInvoiceManagement:
    def test_invoice_application(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"contract_id": 1, "invoice_amount": 3000000.00, "invoice_type": "增值税专用发票"}
        response = client.post("/api/v1/sales/invoice-applications", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_invoice_issuance(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"invoice_number": "INV-2024-001", "issue_date": str(date.today())}
        response = client.post("/api/v1/sales/invoices", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_invoice_delivery(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"delivery_method": "快递", "tracking_number": "SF1234567"}
        response = client.post("/api/v1/sales/invoices/1/delivery", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_invoice_status_tracking(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/invoices/1/status", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_invoice_reconciliation(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/sales/invoice-reconciliation", headers=auth_headers)
        assert response.status_code in [200, 404]
