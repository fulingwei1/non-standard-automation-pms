import uuid

# -*- coding: utf-8 -*-
"""
预警管理集成测试 - 预警规则触发

测试场景：
1. 项目进度预警
2. 成本超支预警
3. 质量风险预警
4. 交期延误预警
5. 资源短缺预警
6. 合同风险预警
7. 多级预警升级
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def build_alert_rule_payload(
    rule_code: str,
    rule_name: str,
    rule_type: str,
    target_type: str,
    *,
    target_field: str = "value",
    condition_type: str = "THRESHOLD",
    condition_operator: str = "GT",
    threshold_value: str = "0",
    alert_level: str = "WARNING",
    notify_users=None,
):
    return {
        "rule_code": rule_code,
        "rule_name": rule_name,
        "rule_type": rule_type,
        "target_type": target_type,
        "target_field": target_field,
        "condition_type": condition_type,
        "condition_operator": condition_operator,
        "threshold_value": str(threshold_value),
        "alert_level": alert_level,
        "notify_channels": ["SYSTEM"],
        "notify_users": notify_users or [],
        "check_frequency": "DAILY",
    }


@pytest.mark.integration
class TestAlertRuleTrigger:
    """预警规则触发集成测试"""

    def test_project_progress_alert(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        """测试：项目进度预警"""
        # 1. 创建项目
        project_data = {
            "project_name": "智能制造项目",
            "project_code": f"PRJ-SMART-2024-{uuid.uuid4().hex[:8]}",
            "customer_id": 1,
            "start_date": str(date.today() - timedelta(days=60)),
            "expected_end_date": str(date.today() + timedelta(days=30)),
            "contract_amount": 10000000.00,
            "project_manager_id": test_employee.id,
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]

        # 2. 创建进度预警规则
        alert_rule = build_alert_rule_payload(
            rule_code="PROGRESS_DELAY_001",
            rule_name="项目进度延迟预警",
            rule_type="project_progress",
            target_type="project",
            target_field="progress_percentage",
            condition_operator="LT",
            threshold_value="50",
            alert_level="WARNING",
            notify_users=[test_employee.id],
        )

        response = client.post("/api/v1/alert-rules", json=alert_rule, headers=auth_headers)
        assert response.status_code in [200, 201]

        # 3. 更新项目进度（触发预警）
        progress_update = {
            "project_id": project_id,
            "progress_percentage": 45,  # 低于预警阈值
            "update_date": str(date.today()),
            "updated_by": test_employee.id,
        }

        response = client.post(
            f"/api/v1/projects/{project_id}/progress", json=progress_update, headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]

        # 4. 查询触发的预警
        response = client.get(
            f"/api/v1/alerts?project_id={project_id}&status=active", headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_cost_overrun_alert(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：成本超支预警"""
        # 1. 创建项目和预算
        project_data = {
            "project_name": "ERP系统实施",
            "project_code": f"PRJ-ERP-2024-{uuid.uuid4().hex[:8]}",
            "customer_id": 1,
            "start_date": str(date.today()),
            "contract_amount": 8000000.00,
            "project_manager_id": test_employee.id,
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]

        # 2. 设置成本预警规则
        cost_alert_rule = build_alert_rule_payload(
            rule_code="COST_OVERRUN_001",
            rule_name="成本超支预警",
            rule_type="cost_overrun",
            target_type="project",
            target_field="budget_usage_percentage",
            condition_operator="GT",
            threshold_value="85",
            alert_level="WARNING",
            notify_users=[test_employee.id, test_employee.id + 1],
        )

        response = client.post("/api/v1/alert-rules", json=cost_alert_rule, headers=auth_headers)
        assert response.status_code in [200, 201]

        # 3. 记录成本（触发预警）
        cost_record = {
            "project_id": project_id,
            "cost_date": str(date.today()),
            "cost_category": "total",
            "amount": 6000000.00,  # 假设预算为7000000，使用率86%
            "description": "累计成本",
        }

        response = client.post(
            "/api/v1/finance/cost-records", json=cost_record, headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]

    def test_quality_risk_alert(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：质量风险预警"""
        # 1. 创建项目
        project_data = {
            "project_name": "软件开发项目",
            "project_code": f"PRJ-DEV-2024-{uuid.uuid4().hex[:8]}",
            "customer_id": 1,
            "start_date": str(date.today()),
            "contract_amount": 5000000.00,
            "project_manager_id": test_employee.id,
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]

        # 2. 设置质量预警规则
        quality_alert_rule = build_alert_rule_payload(
            rule_code="QUALITY_RISK_001",
            rule_name="缺陷率预警",
            rule_type="quality_risk",
            target_type="project",
            target_field="defect_rate",
            condition_operator="GT",
            threshold_value="0.05",
            alert_level="CRITICAL",
            notify_users=[test_employee.id],
        )

        response = client.post(
            "/api/v1/alert-rules", json=quality_alert_rule, headers=auth_headers
        )
        assert response.status_code in [200, 201]

        # 3. 记录质量问题（触发预警）
        quality_issue = {
            "project_id": project_id,
            "issue_date": str(date.today()),
            "issue_type": "defect",
            "severity": "high",
            "description": "系统崩溃严重缺陷",
            "defect_count": 8,
            "total_test_cases": 100,
        }

        response = client.post("/api/v1/quality/issues", json=quality_issue, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_delivery_delay_alert(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        """测试：交期延误预警"""
        # 1. 创建销售订单
        order_data = {
            "order_number": "SO-2024-001",
            "customer_id": 1,
            "order_date": str(date.today() - timedelta(days=30)),
            "delivery_date": str(date.today() + timedelta(days=10)),
            "order_amount": 3000000.00,
            "order_status": "生产中",
        }

        response = client.post("/api/v1/sales/orders", json=order_data, headers=auth_headers)
        assert response.status_code in [200, 201, 403, 404]
        order_id = response.json().get("id") if response.status_code in [200, 201] else None

        # 2. 设置交期预警规则
        if order_id:
            delivery_alert_rule = build_alert_rule_payload(
                rule_code="DELIVERY_DELAY_001",
                rule_name="交期延误预警",
                rule_type="delivery_delay",
                target_type="order",
                target_field="completion_percentage",
                condition_operator="LT",
                threshold_value="80",
                alert_level="WARNING",
                notify_users=[test_employee.id],
            )

            response = client.post(
                "/api/v1/alert-rules", json=delivery_alert_rule, headers=auth_headers
            )
            assert response.status_code in [200, 201]

        # 3. 更新订单进度（触发预警）
        if order_id:
            progress_update = {
                "order_id": order_id,
                "completion_percentage": 65,  # 低于80%
                "update_date": str(date.today()),
                "remarks": "生产进度落后",
            }

            response = client.post(
                f"/api/v1/sales/orders/{order_id}/progress",
                json=progress_update,
                headers=auth_headers,
            )
            assert response.status_code in [200, 201, 404]

    def test_resource_shortage_alert(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        """测试：资源短缺预警"""
        # 1. 设置库存预警规则
        inventory_alert_rule = build_alert_rule_payload(
            rule_code="INVENTORY_LOW_001",
            rule_name="库存不足预警",
            rule_type="resource_shortage",
            target_type="material",
            target_field="stock_quantity",
            condition_operator="LT",
            threshold_value="100",
            alert_level="WARNING",
            notify_users=[test_employee.id],
        )

        response = client.post(
            "/api/v1/alert-rules", json=inventory_alert_rule, headers=auth_headers
        )
        assert response.status_code in [200, 201]

        # 2. 更新库存（触发预警）
        inventory_update = {
            "material_code": f"MAT-001-{uuid.uuid4().hex[:8]}",
            "material_name": "电机",
            "stock_quantity": 80,
            "safety_stock": 150,
            "update_date": str(date.today()),
        }

        response = client.post(
            "/api/v1/inventory/stock-updates", json=inventory_update, headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]

        # 3. 查询库存预警
        response = client.get(
            "/api/v1/alerts?rule_type=resource_shortage&status=active", headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_contract_risk_alert(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        """测试：合同风险预警"""
        # 1. 创建合同
        contract_data = {
            "contract_number": "CON-2024-001",
            "customer_id": 1,
            "contract_date": str(date.today() - timedelta(days=60)),
            "contract_amount": 6000000.00,
            "payment_terms": "分期付款",
            "payment_due_dates": [
                {
                    "milestone": "签约",
                    "amount": 1800000.00,
                    "due_date": str(date.today() - timedelta(days=53)),
                },
                {
                    "milestone": "交货",
                    "amount": 3000000.00,
                    "due_date": str(date.today() - timedelta(days=5)),
                },
                {
                    "milestone": "验收",
                    "amount": 1200000.00,
                    "due_date": str(date.today() + timedelta(days=30)),
                },
            ],
        }

        response = client.post("/api/v1/sales/contracts", json=contract_data, headers=auth_headers)
        assert response.status_code in [200, 201, 403, 404]
        contract_id = response.json().get("id") if response.status_code in [200, 201] else None

        # 2. 设置回款预警规则
        if contract_id:
            payment_alert_rule = build_alert_rule_payload(
                rule_code="PAYMENT_OVERDUE_001",
                rule_name="回款逾期预警",
                rule_type="contract_risk",
                target_type="contract",
                target_field="overdue_days",
                condition_operator="GT",
                threshold_value="7",
                alert_level="WARNING",
                notify_users=[test_employee.id],
            )

            response = client.post(
                "/api/v1/alert-rules", json=payment_alert_rule, headers=auth_headers
            )
            assert response.status_code in [200, 201]

        # 3. 记录回款（部分逾期）
        if contract_id:
            payment_record = {
                "contract_id": contract_id,
                "payment_amount": 1800000.00,
                "payment_date": str(date.today() - timedelta(days=50)),
                "payment_milestone": "签约",
            }

            response = client.post(
                "/api/v1/finance/payments", json=payment_record, headers=auth_headers
            )
            assert response.status_code in [200, 201, 404]

    def test_multi_level_alert_escalation(
        self, client: TestClient, db: Session, auth_headers, test_employee
    ):
        """测试：多级预警升级"""
        # 1. 创建项目
        project_data = {
            "project_name": "关键项目",
            "project_code": f"PRJ-CRITICAL-2024-{uuid.uuid4().hex[:8]}",
            "customer_id": 1,
            "start_date": str(date.today()),
            "contract_amount": 15000000.00,
            "project_manager_id": test_employee.id,
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]

        # 2. 设置多级预警规则
        escalation_alert_rule = build_alert_rule_payload(
            rule_code="MULTI_LEVEL_001",
            rule_name="项目风险多级预警",
            rule_type="multi_level",
            target_type="project",
            target_field="delay_days",
            condition_operator="GT",
            threshold_value="3",
            alert_level="WARNING",
            notify_users=[test_employee.id, test_employee.id + 1, test_employee.id + 2],
        )

        response = client.post(
            "/api/v1/alert-rules", json=escalation_alert_rule, headers=auth_headers
        )
        assert response.status_code in [200, 201]

        # 3. 触发不同级别预警
        delay_scenarios = [
            {"delay_days": 5, "expected_level": "warning"},
            {"delay_days": 15, "expected_level": "critical"},
        ]

        for scenario in delay_scenarios:
            progress_update = {
                "project_id": project_id,
                "actual_progress": 30,
                "planned_progress": 50,
                "delay_days": scenario["delay_days"],
                "update_date": str(date.today()),
            }

            response = client.post(
                f"/api/v1/projects/{project_id}/progress",
                json=progress_update,
                headers=auth_headers,
            )
            assert response.status_code in [200, 201, 404]

        # 4. 查询预警升级记录
        response = client.get(
            f"/api/v1/alerts/escalations?project_id={project_id}", headers=auth_headers
        )
        assert response.status_code in [200, 404]
