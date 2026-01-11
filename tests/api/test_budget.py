# -*- coding: utf-8 -*-
"""
预算管理模块 API 测试

测试内容：
- 预算 CRUD 操作
- 预算审批流程
- 预算明细管理
- 成本分摊规则管理
"""

import pytest
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.budget import ProjectBudget, ProjectBudgetItem


class TestBudgetCRUD:
    """预算 CRUD 测试"""

    def test_list_budgets(self, client: TestClient, admin_token: str):
        """测试获取预算列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/?page=1&page_size=10",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_budget_success(self, client: TestClient, admin_token: str, db_session: Session):
        """测试成功创建预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        budget_data = {
            "project_id": project.id,
            "budget_type": "INITIAL",
            "total_amount": 100000.00,
            "budget_year": 2024,
            "remark": "测试预算",
            "items": [
                {
                    "item_no": "01",
                    "item_name": "物料成本",
                    "cost_type": "MATERIAL",
                    "budget_amount": 60000.00,
                },
                {
                    "item_no": "02",
                    "item_name": "人工成本",
                    "cost_type": "LABOR",
                    "budget_amount": 40000.00,
                },
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/",
            json=budget_data,
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project.id
        assert data["budget_type"] == "INITIAL"
        assert "budget_no" in data
        assert "version" in data

    def test_create_budget_invalid_project(self, client: TestClient, admin_token: str):
        """测试创建预算时项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        budget_data = {
            "project_id": 999999,
            "budget_type": "INITIAL",
            "total_amount": 100000.00,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/",
            json=budget_data,
            headers=headers
        )

        assert response.status_code == 404

    def test_get_budget_detail(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取预算详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        budget = db_session.query(ProjectBudget).first()
        if not budget:
            pytest.skip("No budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == budget.id
        assert "items" in data

    def test_get_budget_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/999999",
            headers=headers
        )

        assert response.status_code == 404

    def test_get_project_budgets(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取项目的预算列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/projects/{project.id}/budgets",
            headers=headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestBudgetUpdate:
    """预算更新测试"""

    def test_update_draft_budget(self, client: TestClient, admin_token: str, db_session: Session):
        """测试更新草稿状态的预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status == "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "total_amount": 120000.00,
            "remark": "更新后的备注",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["total_amount"]) == 120000.00

    def test_update_non_draft_budget_fails(self, client: TestClient, admin_token: str, db_session: Session):
        """测试更新非草稿状态的预算失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找非草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status != "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No non-draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "total_amount": 120000.00,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 400
        assert "草稿" in response.json().get("detail", "")


class TestBudgetApproval:
    """预算审批流程测试"""

    def test_submit_budget(self, client: TestClient, admin_token: str, db_session: Session):
        """测试提交预算审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status == "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/submit",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUBMITTED"

    def test_submit_non_draft_fails(self, client: TestClient, admin_token: str, db_session: Session):
        """测试提交非草稿状态的预算失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找非草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status != "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No non-draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/submit",
            headers=headers
        )

        assert response.status_code == 400

    def test_approve_budget(self, client: TestClient, admin_token: str, db_session: Session):
        """测试审批通过预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找已提交状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status == "SUBMITTED"
        ).first()
        if not budget:
            pytest.skip("No submitted budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        approve_data = {
            "approved": True,
            "approval_note": "测试审批通过",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/approve",
            json=approve_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"

    def test_reject_budget(self, client: TestClient, admin_token: str, db_session: Session):
        """测试驳回预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找已提交状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status == "SUBMITTED"
        ).first()
        if not budget:
            pytest.skip("No submitted budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        reject_data = {
            "approved": False,
            "approval_note": "测试驳回",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/approve",
            json=reject_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"


class TestBudgetDelete:
    """预算删除测试"""

    def test_delete_draft_budget(self, client: TestClient, admin_token: str, db_session: Session):
        """测试删除草稿状态的预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个预算
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        budget_data = {
            "project_id": project.id,
            "budget_type": "INITIAL",
            "total_amount": 50000.00,
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/",
            json=budget_data,
            headers=headers
        )

        if create_response.status_code != 201:
            pytest.skip("Failed to create budget for delete test")

        budget_id = create_response.json()["id"]

        # 删除预算
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/budgets/{budget_id}",
            headers=headers
        )

        assert delete_response.status_code == 200

    def test_delete_non_draft_fails(self, client: TestClient, admin_token: str, db_session: Session):
        """测试删除非草稿状态的预算失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找非草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status != "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No non-draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}",
            headers=headers
        )

        assert response.status_code == 400


class TestBudgetItems:
    """预算明细管理测试"""

    def test_get_budget_items(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取预算明细列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        budget = db_session.query(ProjectBudget).first()
        if not budget:
            pytest.skip("No budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/items",
            headers=headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_budget_item(self, client: TestClient, admin_token: str, db_session: Session):
        """测试创建预算明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status == "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        item_data = {
            "item_no": "99",
            "item_name": "测试成本项",
            "cost_type": "OTHER",
            "budget_amount": 10000.00,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/items",
            json=item_data,
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["item_name"] == "测试成本项"

    def test_create_item_non_draft_fails(self, client: TestClient, admin_token: str, db_session: Session):
        """测试为非草稿预算添加明细失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找非草稿状态的预算
        budget = db_session.query(ProjectBudget).filter(
            ProjectBudget.status != "DRAFT"
        ).first()
        if not budget:
            pytest.skip("No non-draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        item_data = {
            "item_no": "99",
            "item_name": "测试成本项",
            "cost_type": "OTHER",
            "budget_amount": 10000.00,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/{budget.id}/items",
            json=item_data,
            headers=headers
        )

        assert response.status_code == 400

    def test_update_budget_item(self, client: TestClient, admin_token: str, db_session: Session):
        """测试更新预算明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找草稿预算的明细
        item = db_session.query(ProjectBudgetItem).join(ProjectBudget).filter(
            ProjectBudget.status == "DRAFT"
        ).first()
        if not item:
            pytest.skip("No budget item in draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "budget_amount": 15000.00,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/budgets/items/{item.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200

    def test_delete_budget_item(self, client: TestClient, admin_token: str, db_session: Session):
        """测试删除预算明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找草稿预算的明细
        item = db_session.query(ProjectBudgetItem).join(ProjectBudget).filter(
            ProjectBudget.status == "DRAFT"
        ).first()
        if not item:
            pytest.skip("No budget item in draft budget available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete(
            f"{settings.API_V1_PREFIX}/budgets/items/{item.id}",
            headers=headers
        )

        assert response.status_code == 200


class TestAllocationRules:
    """成本分摊规则管理测试"""

    def test_list_allocation_rules(self, client: TestClient, admin_token: str):
        """测试获取分摊规则列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/allocation-rules",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_allocation_rule(self, client: TestClient, admin_token: str):
        """测试创建分摊规则"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        rule_data = {
            "rule_name": "测试分摊规则",
            "rule_type": "BY_RATIO",
            "allocation_basis": "MANUAL",
            "is_active": True,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/allocation-rules",
            json=rule_data,
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rule_name"] == "测试分摊规则"

    def test_get_allocation_rule_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的分摊规则"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/budgets/allocation-rules/999999",
            headers=headers
        )

        assert response.status_code == 404

    def test_delete_allocation_rule(self, client: TestClient, admin_token: str):
        """测试删除分摊规则"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 先创建一个规则
        rule_data = {
            "rule_name": "待删除规则",
            "rule_type": "BY_RATIO",
            "allocation_basis": "MANUAL",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/budgets/allocation-rules",
            json=rule_data,
            headers=headers
        )

        if create_response.status_code != 201:
            pytest.skip("Failed to create rule for delete test")

        rule_id = create_response.json()["id"]

        # 删除规则
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/budgets/allocation-rules/{rule_id}",
            headers=headers
        )

        assert delete_response.status_code == 200
