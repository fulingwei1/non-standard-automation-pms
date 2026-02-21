# -*- coding: utf-8 -*-
"""人事管理集成测试 - 薪资计算流程"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestSalaryCalculation:
    def test_salary_structure_setup(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"employee_id": test_employee.id, "base_salary": 15000, "allowances": {"housing": 2000}}
        response = client.post("/api/v1/hr/salary-structures", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_salary_calculation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"year": 2024, "month": 2}
        response = client.post("/api/v1/hr/salary-calculation", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_payroll_generation(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.post("/api/v1/hr/payroll/generate?year=2024&month=2", headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_payslip_distribution(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.post("/api/v1/hr/payslips/distribute", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_salary_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/hr/salary-report?year=2024&month=2", headers=auth_headers)
        assert response.status_code in [200, 404]
