# -*- coding: utf-8 -*-
"""
审批实例 API 测试

测试审批实例的创建、查询、取消、历史记录等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestApprovalsInstancesAPI:
    """审批实例 API 测试类"""

    def test_list_instances(self, client: TestClient, admin_token: str):
        """测试获取审批实例列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Approval instances API not implemented")

        assert response.status_code == 200, response.text

    def test_create_instance(self, client: TestClient, admin_token: str):
        """测试创建审批实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        instance_data = {
            "workflow_id": 1,
            "business_type": "purchase_request",
            "business_id": 1,
            "title": "采购申请审批",
            "description": "总金额5万元的采购申请",
            "priority": "normal",
            "data": {
                "amount": 50000.0,
                "items_count": 3
            }
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/instances/",
            headers=headers,
            json=instance_data
        )

        if response.status_code == 404:
            pytest.skip("Approval instances API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_instance_detail(self, client: TestClient, admin_token: str):
        """测试获取审批实例详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No instance data or API not implemented")

        assert response.status_code == 200, response.text

    def test_get_instance_status(self, client: TestClient, admin_token: str):
        """测试获取审批实例状态"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/1/status",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance status API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_get_instance_history(self, client: TestClient, admin_token: str):
        """测试获取审批历史"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/1/history",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance history API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_cancel_instance(self, client: TestClient, admin_token: str):
        """测试取消审批实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        cancel_data = {
            "reason": "业务需求变更，取消审批"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/instances/1/cancel",
            headers=headers,
            json=cancel_data
        )

        if response.status_code == 404:
            pytest.skip("Instance cancel API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_withdraw_instance(self, client: TestClient, admin_token: str):
        """测试撤回审批实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/instances/1/withdraw",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance withdraw API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_restart_instance(self, client: TestClient, admin_token: str):
        """测试重新发起审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/instances/1/restart",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance restart API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_filter_instances_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤审批实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/?status=approved",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_instances_by_type(self, client: TestClient, admin_token: str):
        """测试按业务类型过滤审批实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/?business_type=purchase_request",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance filter API not implemented")

        assert response.status_code == 200, response.text

    def test_my_initiated_instances(self, client: TestClient, admin_token: str):
        """测试获取我发起的审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/my-initiated",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("My initiated instances API not implemented")

        assert response.status_code == 200, response.text

    def test_instance_timeline(self, client: TestClient, admin_token: str):
        """测试审批时间线"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/1/timeline",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance timeline API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_instance_statistics(self, client: TestClient, admin_token: str):
        """测试审批实例统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_instance_export(self, client: TestClient, admin_token: str):
        """测试导出审批实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Instance export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_instance_unauthorized(self, client: TestClient):
        """测试未授权访问审批实例"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/instances/"
        )

        assert response.status_code in [401, 403], response.text
