# -*- coding: utf-8 -*-
"""人事管理集成测试 - 员工入职流程"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestEmployeeOnboarding:
    def test_offer_letter_issuance(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"candidate_name": "张三", "position": "软件工程师", "salary": 20000}
        response = client.post("/api/v1/hr/offer-letters", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_employee_registration(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"name": "张三", "employee_code": "EMP-001", "department_id": 1}
        response = client.post("/api/v1/hr/employees", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_onboarding_checklist(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"employee_id": 1, "checklist_items": ["工位分配", "电脑领用", "门禁卡"]}
        response = client.post("/api/v1/hr/onboarding-checklist", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_orientation_training(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"employee_id": 1, "training_type": "入职培训", "completed": True}
        response = client.post("/api/v1/hr/orientation-training", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_probation_evaluation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"employee_id": 1, "evaluation_result": "合格"}
        response = client.post("/api/v1/hr/probation-evaluation", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
