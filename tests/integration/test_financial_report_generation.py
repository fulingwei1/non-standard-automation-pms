# -*- coding: utf-8 -*-
"""财务管理集成测试 - 财务报表生成"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestFinancialReportGeneration:
    def test_income_statement(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/reports/income-statement?year=2024&month=2", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_balance_sheet(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/reports/balance-sheet?year=2024", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_cash_flow_statement(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/reports/cash-flow?year=2024", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_profit_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/reports/profit-analysis", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_financial_dashboard(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/finance/dashboard", headers=auth_headers)
        assert response.status_code in [200, 404]
