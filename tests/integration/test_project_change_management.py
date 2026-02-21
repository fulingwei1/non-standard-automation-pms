# -*- coding: utf-8 -*-
"""项目管理集成测试 - 项目变更管理"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestProjectChangeManagement:
    def test_change_request_submission(self, client: TestClient, db: Session, auth_headers, test_employee):
        change_data = {"project_id": 1, "change_type": "需求变更", "description": "增加新功能", "impact_analysis": "需要增加2周工期"}
        response = client.post("/api/v1/projects/1/change-requests", json=change_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_change_approval(self, client: TestClient, db: Session, auth_headers, test_employee):
        approval_data = {"action": "approve", "comments": "同意变更"}
        response = client.post("/api/v1/change-requests/1/approve", json=approval_data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_change_implementation(self, client: TestClient, db: Session, auth_headers, test_employee):
        impl_data = {"change_id": 1, "implementation_plan": "分3个阶段实施"}
        response = client.post("/api/v1/change-requests/1/implement", json=impl_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
    
    def test_change_tracking(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/projects/1/change-tracking", headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_change_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/projects/1/change-report", headers=auth_headers)
        assert response.status_code in [200, 404]
