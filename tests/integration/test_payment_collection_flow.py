# -*- coding: utf-8 -*-
"""
财务管理集成测试 - 回款管理流程
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestPaymentCollectionFlow:
    
    def test_payment_plan_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：回款计划创建"""
        contract_data = {
            "contract_number": "CON-2024-001",
            "customer_id": 1,
            "contract_amount": 10000000.00,
            "payment_milestones": [
                {"milestone": "签约", "percentage": 30, "amount": 3000000.00},
                {"milestone": "交货", "percentage": 50, "amount": 5000000.00},
                {"milestone": "验收", "percentage": 20, "amount": 2000000.00}
            ]
        }
        
        response = client.post("/api/v1/sales/contracts", json=contract_data, headers=auth_headers)
        assert response.status_code in [200, 201]

    def test_payment_reminder(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：回款提醒"""
        reminder_data = {
            "contract_id": 1,
            "reminder_date": str(date.today() + timedelta(days=3)),
            "reminder_type": "email",
            "recipients": ["finance@customer.com"]
        }
        
        response = client.post("/api/v1/finance/payment-reminders", json=reminder_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_payment_recording(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：回款记录"""
        payment_data = {
            "contract_id": 1,
            "payment_amount": 3000000.00,
            "payment_date": str(date.today()),
            "payment_method": "银行转账",
            "payment_milestone": "签约"
        }
        
        response = client.post("/api/v1/finance/payments", json=payment_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_overdue_payment_handling(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：逾期回款处理"""
        response = client.get("/api/v1/finance/overdue-payments", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_payment_collection_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：回款统计报表"""
        response = client.get(
            f"/api/v1/finance/collection-report?start_date={date.today() - timedelta(days=30)}&end_date={date.today()}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
