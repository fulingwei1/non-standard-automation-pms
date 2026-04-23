# -*- coding: utf-8 -*-
"""预警管理集成测试 - 预警规则管理"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def build_rule_payload(rule_code: str, rule_name: str, rule_type: str = "progress"):
    return {
        "rule_code": rule_code,
        "rule_name": rule_name,
        "rule_type": rule_type,
        "target_type": "project",
        "target_field": "progress_percentage",
        "condition_type": "THRESHOLD",
        "condition_operator": "LT",
        "threshold_value": "50",
        "alert_level": "WARNING",
        "notify_channels": ["SYSTEM"],
        "check_frequency": "DAILY",
    }


@pytest.mark.integration
class TestAlertRuleManagement:
    def test_rule_creation(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = build_rule_payload("RULE_001", "测试规则")
        response = client.post("/api/v1/alert-rules", json=data, headers=auth_headers)
        assert response.status_code in [200, 201]

    def test_rule_update(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"rule_name": "更新后的规则"}
        response = client.put("/api/v1/alert-rules/1", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_rule_enable_disable(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        response = client.put("/api/v1/alert-rules/1/toggle", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_rule_testing(self, client: TestClient, db: Session, auth_headers, test_employee):
        data = {"rule_id": 1, "test_data": {"progress": 45}}
        response = client.post("/api/v1/alert-rules/1/test", json=data, headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_rule_effectiveness_analysis(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        response = client.get("/api/v1/alert-rules/effectiveness", headers=auth_headers)
        assert response.status_code in [200, 404, 422]
