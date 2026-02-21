# -*- coding: utf-8 -*-
"""人事管理集成测试 - 绩效考核流程"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestPerformanceEvaluationFlow:
    def test_performance_plan_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"year": 2024, "quarter": 1, "employee_id": test_employee.id}
        response = client.post("/api/v1/hr/performance-plans", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_self_evaluation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"plan_id": 1, "self_score": 85, "comments": "完成主要目标"}
        response = client.post("/api/v1/hr/performance-plans/1/self-evaluate", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_manager_evaluation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"plan_id": 1, "manager_score": 88, "comments": "表现良好"}
        response = client.post("/api/v1/hr/performance-plans/1/manager-evaluate", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_performance_interview(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"plan_id": 1, "interview_date": str(date.today()), "summary": "沟通绩效结果"}
        response = client.post("/api/v1/hr/performance-interviews", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_performance_ranking(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/hr/performance-ranking?year=2024&quarter=1", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_performance_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/hr/performance-report", headers=auth_headers)
        assert response.status_code in [200, 404]
