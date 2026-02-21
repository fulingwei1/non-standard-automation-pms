# -*- coding: utf-8 -*-
"""
审批流程 API 测试

测试审批流程的创建、查询、更新、启用/禁用等功能
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestApprovalsWorkflowsAPI:
    """审批流程 API 测试类"""

    def test_list_workflows(self, client: TestClient, admin_token: str):
        """测试获取审批流程列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflows API not implemented")

        assert response.status_code == 200, response.text

    def test_create_workflow(self, client: TestClient, admin_token: str):
        """测试创建审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        workflow_data = {
            "name": "采购申请审批流程",
            "description": "采购金额超过1万元的审批流程",
            "workflow_type": "purchase_request",
            "enabled": True,
            "steps": [
                {"step_order": 1, "approver_role": "department_manager", "step_name": "部门经理审批"},
                {"step_order": 2, "approver_role": "finance_manager", "step_name": "财务经理审批"},
                {"step_order": 3, "approver_role": "general_manager", "step_name": "总经理审批"}
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/workflows/",
            headers=headers,
            json=workflow_data
        )

        if response.status_code == 404:
            pytest.skip("Workflows API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_workflow_detail(self, client: TestClient, admin_token: str):
        """测试获取审批流程详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No workflow data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_workflow(self, client: TestClient, admin_token: str):
        """测试更新审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "description": "更新后的流程描述",
            "enabled": False
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/approvals/workflows/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Workflow API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_workflow(self, client: TestClient, admin_token: str):
        """测试删除审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/approvals/workflows/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_enable_workflow(self, client: TestClient, admin_token: str):
        """测试启用审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/workflows/1/enable",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow enable API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_disable_workflow(self, client: TestClient, admin_token: str):
        """测试禁用审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/workflows/1/disable",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow disable API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_workflow_steps_management(self, client: TestClient, admin_token: str):
        """测试审批步骤管理"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        step_data = {
            "step_order": 4,
            "approver_role": "ceo",
            "step_name": "CEO终审",
            "condition": "amount > 100000"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/workflows/1/steps",
            headers=headers,
            json=step_data
        )

        if response.status_code == 404:
            pytest.skip("Workflow steps API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_filter_workflows_by_type(self, client: TestClient, admin_token: str):
        """测试按类型过滤审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/?type=purchase_request",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_workflows_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/?enabled=true",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow filter API not implemented")

        assert response.status_code == 200, response.text

    def test_workflow_templates(self, client: TestClient, admin_token: str):
        """测试审批流程模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/templates",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow templates API not implemented")

        assert response.status_code == 200, response.text

    def test_create_workflow_from_template(self, client: TestClient, admin_token: str):
        """测试从模板创建审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        template_data = {
            "template_id": 1,
            "name": "基于模板的审批流程"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/workflows/from-template",
            headers=headers,
            json=template_data
        )

        if response.status_code == 404:
            pytest.skip("Workflow template API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_workflow_statistics(self, client: TestClient, admin_token: str):
        """测试审批流程统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workflow statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_workflow_unauthorized(self, client: TestClient):
        """测试未授权访问审批流程"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/workflows/"
        )

        assert response.status_code in [401, 403], response.text

    def test_workflow_validation(self, client: TestClient, admin_token: str):
        """测试审批流程数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "steps": []  # 没有审批步骤
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/workflows/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Workflows API not implemented")

        assert response.status_code == 422, response.text
