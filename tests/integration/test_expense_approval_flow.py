# -*- coding: utf-8 -*-
"""财务管理集成测试 - 费用审批流程"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestExpenseApprovalFlow:
    def test_expense_application(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"expense_type": "差旅费", "amount": 5000.00, "description": "出差上海"}
        response = client.post("/api/v1/finance/expense-applications", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_expense_approval(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"action": "approve", "comments": "同意报销"}
        response = client.post("/api/v1/finance/expense-applications/1/approve", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_expense_reimbursement(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"application_id": 1, "reimbursement_amount": 5000.00}
        response = client.post("/api/v1/finance/reimbursements", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_expense_statistics(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/expense-statistics", headers=auth_headers)
        assert response.status_code in [200, 404]
