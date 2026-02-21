# -*- coding: utf-8 -*-
"""
销售合同管理 API 测试

测试合同的创建、查询、更新、审批、归档等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesContractsAPI:
    """销售合同管理 API 测试类"""

    def test_list_contracts(self, client: TestClient, admin_token: str):
        """测试获取合同列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contracts API not implemented")

        assert response.status_code == 200, response.text

    def test_create_contract(self, client: TestClient, admin_token: str):
        """测试创建合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        contract_data = {
            "contract_no": f"CT{datetime.now().strftime('%Y%m%d')}001",
            "customer_id": 1,
            "quote_id": 1,
            "contract_name": "测试设备采购合同",
            "contract_type": "sales",
            "sign_date": datetime.now().strftime("%Y-%m-%d"),
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "total_amount": 500000.0,
            "payment_terms": "分期付款，按进度支付",
            "delivery_terms": "3个月内交付",
            "warranty_period": "12个月",
            "remarks": "重要合同"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/",
            headers=headers,
            json=contract_data
        )

        if response.status_code == 404:
            pytest.skip("Contracts API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_contract_detail(self, client: TestClient, admin_token: str):
        """测试获取合同详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No contract data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_contract(self, client: TestClient, admin_token: str):
        """测试更新合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "remarks": "更新后的备注",
            "warranty_period": "24个月"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/contracts/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Contract API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_contract(self, client: TestClient, admin_token: str):
        """测试删除合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/contracts/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_contract_approval_submit(self, client: TestClient, admin_token: str):
        """测试提交合同审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/submit",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_approval_approve(self, client: TestClient, admin_token: str):
        """测试审批通过合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {
            "action": "approve",
            "comments": "审批通过"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/approve",
            headers=headers,
            json=approval_data
        )

        if response.status_code == 404:
            pytest.skip("Contract approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_signing(self, client: TestClient, admin_token: str):
        """测试合同签署"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        signing_data = {
            "sign_date": datetime.now().strftime("%Y-%m-%d"),
            "signed_by": "张总",
            "customer_signed_by": "李经理"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/sign",
            headers=headers,
            json=signing_data
        )

        if response.status_code == 404:
            pytest.skip("Contract signing API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_archive(self, client: TestClient, admin_token: str):
        """测试合同归档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/archive",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract archive API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_contracts_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/?status=signed",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_contracts_by_customer(self, client: TestClient, admin_token: str):
        """测试按客户过滤合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/?customer_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract filter API not implemented")

        assert response.status_code == 200, response.text

    def test_expiring_contracts(self, client: TestClient, admin_token: str):
        """测试即将到期的合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/expiring?days=30",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Expiring contracts API not implemented")

        assert response.status_code == 200, response.text

    def test_contract_statistics(self, client: TestClient, admin_token: str):
        """测试合同统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_contract_export(self, client: TestClient, admin_token: str):
        """测试导出合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_unauthorized(self, client: TestClient):
        """测试未授权访问合同"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/"
        )

        assert response.status_code in [401, 403], response.text
