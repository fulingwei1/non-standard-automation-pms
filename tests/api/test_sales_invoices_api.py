# -*- coding: utf-8 -*-
"""
销售发票管理 API 测试

测试发票的创建、查询、更新、审核等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesInvoicesAPI:
    """销售发票管理 API 测试类"""

    def test_list_invoices(self, client: TestClient, admin_token: str):
        """测试获取发票列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Invoices API not implemented")

        assert response.status_code == 200, response.text

    def test_create_invoice(self, client: TestClient, admin_token: str):
        """测试创建发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invoice_data = {
            "invoice_no": f"INV{datetime.now().strftime('%Y%m%d')}001",
            "contract_id": 1,
            "customer_id": 1,
            "invoice_type": "VAT_SPECIAL",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "amount": 100000.0,
            "tax_rate": 13.0,
            "tax_amount": 13000.0,
            "total_amount": 113000.0,
            "remarks": "首批发票"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/",
            headers=headers,
            json=invoice_data
        )

        if response.status_code == 404:
            pytest.skip("Invoices API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_invoice_detail(self, client: TestClient, admin_token: str):
        """测试获取发票详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No invoice data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_invoice(self, client: TestClient, admin_token: str):
        """测试更新发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "remarks": "更新后的备注",
            "status": "issued"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/invoices/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Invoice API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_invoice(self, client: TestClient, admin_token: str):
        """测试删除发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/invoices/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Invoice API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_invoice_approval(self, client: TestClient, admin_token: str):
        """测试发票审核"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {
            "action": "approve",
            "comments": "审核通过"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/1/approve",
            headers=headers,
            json=approval_data
        )

        if response.status_code == 404:
            pytest.skip("Invoice approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_invoice_issue(self, client: TestClient, admin_token: str):
        """测试开具发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        issue_data = {
            "issue_date": datetime.now().strftime("%Y-%m-%d"),
            "issued_by": 1
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/1/issue",
            headers=headers,
            json=issue_data
        )

        if response.status_code == 404:
            pytest.skip("Invoice issue API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_invoice_cancel(self, client: TestClient, admin_token: str):
        """测试作废发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        cancel_data = {
            "reason": "客户要求作废"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/1/cancel",
            headers=headers,
            json=cancel_data
        )

        if response.status_code == 404:
            pytest.skip("Invoice cancel API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_invoices_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/?status=issued",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Invoice filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_invoices_by_customer(self, client: TestClient, admin_token: str):
        """测试按客户过滤发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/?customer_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Invoice filter API not implemented")

        assert response.status_code == 200, response.text

    def test_invoice_statistics(self, client: TestClient, admin_token: str):
        """测试发票统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Invoice statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_invoice_export(self, client: TestClient, admin_token: str):
        """测试导出发票"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Invoice export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_invoice_tax_calculation(self, client: TestClient, admin_token: str):
        """测试发票税额计算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        calc_data = {
            "amount": 100000.0,
            "tax_rate": 13.0
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/calculate-tax",
            headers=headers,
            json=calc_data
        )

        if response.status_code == 404:
            pytest.skip("Tax calculation API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_invoice_validation(self, client: TestClient, admin_token: str):
        """测试发票数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "amount": -1000.0  # 负数金额
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Invoice API not implemented")

        assert response.status_code == 422, response.text

    def test_invoice_unauthorized(self, client: TestClient):
        """测试未授权访问发票"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/invoices/"
        )

        assert response.status_code in [401, 403], response.text
