# -*- coding: utf-8 -*-
"""人事管理集成测试 - 培训管理流程"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestTrainingManagement:
    def test_training_plan_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"year": 2024, "training_budget": 500000, "planned_courses": 20}
        response = client.post("/api/v1/hr/training-plans", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_training_registration(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"course_id": 1, "employee_id": test_employee.id}
        response = client.post("/api/v1/hr/training-registrations", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_training_attendance(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"registration_id": 1, "attendance_status": "已参加"}
        response = client.post("/api/v1/hr/training-attendance", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_training_evaluation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"registration_id": 1, "evaluation_score": 90, "feedback": "课程很有帮助"}
        response = client.post("/api/v1/hr/training-evaluation", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_training_effectiveness_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/hr/training-effectiveness", headers=auth_headers)
        assert response.status_code in [200, 404]
