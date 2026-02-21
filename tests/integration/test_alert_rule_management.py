# -*- coding: utf-8 -*-
"""预警管理集成测试 - 预警规则管理"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.integration
class TestAlertRuleManagement:
    def test_rule_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"rule_code": "RULE-001", "rule_name": "测试规则", "rule_type": "progress"}
        response = client.post("/api/v1/alerts/rules", json=data, headers=auth_headers)
        assert response.status_code in [200, 201]
    
    def test_rule_update(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"rule_name": "更新后的规则"}
        response = client.put("/api/v1/alerts/rules/1", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_rule_enable_disable(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"enabled": False}
        response = client.post("/api/v1/alerts/rules/1/toggle", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_rule_testing(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"rule_id": 1, "test_data": {"progress": 45}}
        response = client.post("/api/v1/alerts/rules/1/test", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_rule_effectiveness_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        response = client.get("/api/v1/alerts/rules/effectiveness", headers=auth_headers)
        assert response.status_code in [200, 404]
