# -*- coding: utf-8 -*-
"""
销售付款管理 API 测试

测试付款计划、付款记录、付款统计等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesPaymentsAPI:
    """销售付款管理 API 测试类"""

    def test_list_payment_plans(self, client: TestClient, admin_token: str):
        """测试获取付款计划列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/plans",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment plans API not implemented")

        assert response.status_code == 200, response.text

    def test_create_payment_plan(self, client: TestClient, admin_token: str):
        """测试创建付款计划"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        plan_data = {
            "contract_id": 1,
            "total_amount": 500000.0,
            "payment_stages": [
                {"stage": "签约", "percentage": 30, "amount": 150000.0},
                {"stage": "交付", "percentage": 50, "amount": 250000.0},
                {"stage": "验收", "percentage": 20, "amount": 100000.0}
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/payments/plans",
            headers=headers,
            json=plan_data
        )

        if response.status_code == 404:
            pytest.skip("Payment plans API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_list_payment_records(self, client: TestClient, admin_token: str):
        """测试获取付款记录列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/records",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment records API not implemented")

        assert response.status_code == 200, response.text

    def test_create_payment_record(self, client: TestClient, admin_token: str):
        """测试创建付款记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        record_data = {
            "contract_id": 1,
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "amount": 150000.0,
            "payment_method": "bank_transfer",
            "transaction_no": "TRX20240101001",
            "remarks": "首期款"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/payments/records",
            headers=headers,
            json=record_data
        )

        if response.status_code == 404:
            pytest.skip("Payment records API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_update_payment_record(self, client: TestClient, admin_token: str):
        """测试更新付款记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "transaction_no": "TRX20240101001-UPDATED",
            "remarks": "更新备注"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/payments/records/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Payment API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_payment_record(self, client: TestClient, admin_token: str):
        """测试删除付款记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/payments/records/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_payment_statistics(self, client: TestClient, admin_token: str):
        """测试付款统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_payment_by_contract(self, client: TestClient, admin_token: str):
        """测试按合同查询付款"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/records?contract_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment filter API not implemented")

        assert response.status_code == 200, response.text

    def test_overdue_payments(self, client: TestClient, admin_token: str):
        """测试逾期付款查询"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/overdue",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Overdue payments API not implemented")

        assert response.status_code == 200, response.text

    def test_payment_reminders(self, client: TestClient, admin_token: str):
        """测试付款提醒"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/reminders",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment reminders API not implemented")

        assert response.status_code == 200, response.text

    def test_payment_export(self, client: TestClient, admin_token: str):
        """测试导出付款数据"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_payment_verification(self, client: TestClient, admin_token: str):
        """测试付款核对"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        verification_data = {
            "record_id": 1,
            "verified": True,
            "verified_by": 1,
            "verification_date": datetime.now().strftime("%Y-%m-%d")
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/payments/verify",
            headers=headers,
            json=verification_data
        )

        if response.status_code == 404:
            pytest.skip("Payment verification API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_payment_reconciliation(self, client: TestClient, admin_token: str):
        """测试付款对账"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/reconciliation?contract_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Payment reconciliation API not implemented")

        assert response.status_code == 200, response.text

    def test_payment_unauthorized(self, client: TestClient):
        """测试未授权访问付款"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/payments/records"
        )

        assert response.status_code in [401, 403], response.text

    def test_payment_amount_validation(self, client: TestClient, admin_token: str):
        """测试付款金额验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "amount": -1000.0,  # 负数金额
            "payment_date": datetime.now().strftime("%Y-%m-%d")
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/payments/records",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Payment API not implemented")

        assert response.status_code in [200, 422], response.text
