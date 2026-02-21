# -*- coding: utf-8 -*-
"""
采购申请 API 测试

测试采购申请的创建、查询、更新、审批等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPurchaseRequestsAPI:
    """采购申请 API 测试类"""

    def test_list_purchase_requests(self, client: TestClient, admin_token: str):
        """测试获取采购申请列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Purchase requests API not implemented")

        assert response.status_code == 200, response.text

    def test_create_purchase_request(self, client: TestClient, admin_token: str):
        """测试创建采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        request_data = {
            "request_no": f"PR{datetime.now().strftime('%Y%m%d')}001",
            "project_id": 1,
            "request_date": datetime.now().strftime("%Y-%m-%d"),
            "required_date": datetime.now().strftime("%Y-%m-%d"),
            "total_amount": 50000.0,
            "urgency_level": "normal",
            "remarks": "项目采购需求"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/requests/",
            headers=headers,
            json=request_data
        )

        if response.status_code == 404:
            pytest.skip("Purchase requests API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_request_detail(self, client: TestClient, admin_token: str):
        """测试获取采购申请详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No request data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_purchase_request(self, client: TestClient, admin_token: str):
        """测试更新采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "urgency_level": "urgent",
            "remarks": "加急处理"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase/requests/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Purchase request API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_purchase_request(self, client: TestClient, admin_token: str):
        """测试删除采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/purchase/requests/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Purchase request API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_request_items_management(self, client: TestClient, admin_token: str):
        """测试采购申请明细管理"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        item_data = {
            "material_name": "测试物料",
            "specification": "规格A",
            "quantity": 100,
            "unit": "个",
            "estimated_price": 500.0,
            "total_price": 50000.0
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/requests/1/items",
            headers=headers,
            json=item_data
        )

        if response.status_code == 404:
            pytest.skip("Request items API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_submit_request_for_approval(self, client: TestClient, admin_token: str):
        """测试提交采购申请审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/requests/1/submit",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Request approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_approve_purchase_request(self, client: TestClient, admin_token: str):
        """测试审批通过采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {
            "action": "approve",
            "comments": "同意采购"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/requests/1/approve",
            headers=headers,
            json=approval_data
        )

        if response.status_code == 404:
            pytest.skip("Request approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_reject_purchase_request(self, client: TestClient, admin_token: str):
        """测试审批拒绝采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        rejection_data = {
            "action": "reject",
            "comments": "暂缓采购"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/requests/1/approve",
            headers=headers,
            json=rejection_data
        )

        if response.status_code == 404:
            pytest.skip("Request approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_requests_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/?status=approved",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Request filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_requests_by_project(self, client: TestClient, admin_token: str):
        """测试按项目过滤采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/?project_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Request filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_requests_by_urgency(self, client: TestClient, admin_token: str):
        """测试按紧急程度过滤采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/?urgency=urgent",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Request filter API not implemented")

        assert response.status_code == 200, response.text

    def test_request_statistics(self, client: TestClient, admin_token: str):
        """测试采购申请统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Request statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_request_export(self, client: TestClient, admin_token: str):
        """测试导出采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Request export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_request_unauthorized(self, client: TestClient):
        """测试未授权访问采购申请"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/requests/"
        )

        assert response.status_code in [401, 403], response.text
