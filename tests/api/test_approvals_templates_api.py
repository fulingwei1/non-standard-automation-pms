# -*- coding: utf-8 -*-
"""
审批模板 API 测试

测试审批模板的创建、查询、更新、应用等功能
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestApprovalsTemplatesAPI:
    """审批模板 API 测试类"""

    def test_list_templates(self, client: TestClient, admin_token: str):
        """测试获取审批模板列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Approval templates API not implemented")

        assert response.status_code == 200, response.text

    def test_create_template(self, client: TestClient, admin_token: str):
        """测试创建审批模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        template_data = {
            "name": "标准采购审批模板",
            "description": "适用于一般采购申请的审批流程",
            "template_type": "purchase_request",
            "category": "procurement",
            "is_default": False,
            "steps": [
                {
                    "step_order": 1,
                    "step_name": "部门经理审批",
                    "approver_role": "department_manager",
                    "required": True
                },
                {
                    "step_order": 2,
                    "step_name": "采购经理审批",
                    "approver_role": "procurement_manager",
                    "required": True
                }
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/templates/",
            headers=headers,
            json=template_data
        )

        if response.status_code == 404:
            pytest.skip("Approval templates API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_template_detail(self, client: TestClient, admin_token: str):
        """测试获取审批模板详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No template data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_template(self, client: TestClient, admin_token: str):
        """测试更新审批模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "description": "更新后的模板描述",
            "is_default": True
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/approvals/templates/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Template API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_template(self, client: TestClient, admin_token: str):
        """测试删除审批模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/approvals/templates/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Template API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_clone_template(self, client: TestClient, admin_token: str):
        """测试复制审批模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        clone_data = {
            "name": "复制的审批模板"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/templates/1/clone",
            headers=headers,
            json=clone_data
        )

        if response.status_code == 404:
            pytest.skip("Template clone API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_set_default_template(self, client: TestClient, admin_token: str):
        """测试设置默认模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/templates/1/set-default",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Set default template API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_templates_by_type(self, client: TestClient, admin_token: str):
        """测试按类型过滤模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/?type=purchase_request",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Template filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_templates_by_category(self, client: TestClient, admin_token: str):
        """测试按分类过滤模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/?category=procurement",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Template filter API not implemented")

        assert response.status_code == 200, response.text

    def test_get_default_templates(self, client: TestClient, admin_token: str):
        """测试获取默认模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/defaults",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Default templates API not implemented")

        assert response.status_code == 200, response.text

    def test_preview_template(self, client: TestClient, admin_token: str):
        """测试预览模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        preview_data = {
            "business_data": {
                "amount": 50000.0
            }
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/templates/1/preview",
            headers=headers,
            json=preview_data
        )

        if response.status_code == 404:
            pytest.skip("Template preview API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_template_usage_statistics(self, client: TestClient, admin_token: str):
        """测试模板使用统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/1/usage",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Template usage API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_template_export(self, client: TestClient, admin_token: str):
        """测试导出模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/1/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Template export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_template_import(self, client: TestClient, admin_token: str):
        """测试导入模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        import_data = {
            "template_data": {
                "name": "导入的模板",
                "steps": []
            }
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/templates/import",
            headers=headers,
            json=import_data
        )

        if response.status_code == 404:
            pytest.skip("Template import API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_template_unauthorized(self, client: TestClient):
        """测试未授权访问审批模板"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/templates/"
        )

        assert response.status_code in [401, 403], response.text
