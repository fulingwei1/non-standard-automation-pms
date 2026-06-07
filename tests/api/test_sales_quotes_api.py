# -*- coding: utf-8 -*-
"""
销售报价管理 API 测试

测试报价单的创建、查询、更新、审批等功能
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sales import Customer, Opportunity, Quote, QuoteTemplate, QuoteTemplateVersion


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesQuotesAPI:
    """销售报价管理 API 测试类"""

    def test_list_quotes(self, client: TestClient, admin_token: str):
        """测试获取报价单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/quotes/", headers=headers)

        if response.status_code == 404:
            pytest.skip("Quotes API not implemented")

        assert response.status_code == 200, response.text

    def test_create_quote(self, client: TestClient, admin_token: str):
        """测试创建报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        quote_data = {
            "quote_no": f"Q{datetime.now().strftime('%Y%m%d')}001",
            "customer_id": 1,
            "opportunity_id": 1,
            "quote_date": datetime.now().strftime("%Y-%m-%d"),
            "valid_until": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "total_amount": 500000.0,
            "discount_rate": 5.0,
            "final_amount": 475000.0,
            "payment_terms": "分期付款",
            "delivery_terms": "3个月内交付",
            "remarks": "优惠价格，含税",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/", headers=headers, json=quote_data
        )

        if response.status_code == 404:
            pytest.skip("Quotes API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_quote_detail(self, client: TestClient, admin_token: str):
        """测试获取报价单详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/quotes/1", headers=headers)

        if response.status_code in [404, 422]:
            pytest.skip("No quote data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_quote(self, client: TestClient, admin_token: str):
        """测试更新报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {"discount_rate": 8.0, "final_amount": 460000.0, "remarks": "增加折扣"}

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/quotes/1", headers=headers, json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Quote API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_quote(self, client: TestClient, admin_token: str):
        """测试删除报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(f"{settings.API_V1_PREFIX}/sales/quotes/999", headers=headers)

        if response.status_code == 404:
            pytest.skip("Quote API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_quote_items_management(self, client: TestClient, admin_token: str):
        """测试报价单明细管理"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        item_data = {
            "product_name": "测试设备",
            "specification": "型号X1",
            "quantity": 10,
            "unit_price": 50000.0,
            "total_price": 500000.0,
            "delivery_period": "60天",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/1/items", headers=headers, json=item_data
        )

        if response.status_code == 404:
            pytest.skip("Quote items API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_quote_approval_submit(self, client: TestClient, admin_token: str):
        """测试提交报价单审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(f"{settings.API_V1_PREFIX}/sales/quotes/1/submit", headers=headers)

        if response.status_code == 404:
            pytest.skip("Quote approval API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_submit_missing_quote_returns_404(self, client: TestClient, admin_token: str):
        """不存在的报价提交审批应返回 404，而不是业务 400"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/999999/submit", headers=headers
        )

        assert response.status_code == 404, response.text

    def test_quote_approval_approve(self, client: TestClient, admin_token: str):
        """测试审批通过报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {"action": "approve", "comments": "同意报价"}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/1/approve", headers=headers, json=approval_data
        )

        if response.status_code == 404:
            pytest.skip("Quote approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_quote_approval_reject(self, client: TestClient, admin_token: str):
        """测试审批拒绝报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        rejection_data = {"action": "reject", "comments": "价格过低"}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/1/approve", headers=headers, json=rejection_data
        )

        if response.status_code == 404:
            pytest.skip("Quote approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_quotes_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/?status=approved", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Quote filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_quotes_by_customer(self, client: TestClient, admin_token: str):
        """测试按客户过滤报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/?customer_id=1", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Quote filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_quotes_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围过滤报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        start_date = "2024-01-01"
        end_date = "2024-12-31"

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/"
            f"?start_date={start_date}&end_date={end_date}",
            headers=headers,
        )

        if response.status_code == 404:
            pytest.skip("Quote filter API not implemented")

        assert response.status_code == 200, response.text

    def test_quote_statistics(self, client: TestClient, admin_token: str):
        """测试报价单统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/quotes/statistics", headers=headers)

        if response.status_code == 404:
            pytest.skip("Quote statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_quote_export(self, client: TestClient, admin_token: str):
        """测试导出报价单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/quotes/1/export", headers=headers)

        if response.status_code == 404:
            pytest.skip("Quote export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_quote_template_usage(self, client: TestClient, admin_token: str):
        """测试使用报价模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        template_data = {"template_id": 1, "customer_id": 1}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/from-template",
            headers=headers,
            json=template_data,
        )

        if response.status_code == 404:
            pytest.skip("Quote template API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_create_quote_from_template_static_route(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """旧入口 /quotes/from-template 应按当前模板模型创建报价，不应被动态路由遮住"""
        if not admin_token:
            pytest.skip("Admin token not available")

        suffix = uuid4().hex[:8]
        customer = Customer(
            customer_code=f"CUST-QT-{suffix}",
            customer_name=f"模板客户-{suffix}",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPP-QT-{suffix}",
            customer_id=customer.id,
            opp_name=f"模板商机-{suffix}",
            stage="QUOTE",
            est_amount=Decimal("200000"),
            owner_id=1,
        )
        db_session.add(opportunity)
        db_session.flush()

        template = QuoteTemplate(
            template_code=f"TPL-QT-{suffix}",
            template_name=f"模板报价-{suffix}",
            status="ACTIVE",
            visibility_scope="TEAM",
            owner_id=1,
        )
        db_session.add(template)
        db_session.flush()

        version = QuoteTemplateVersion(
            template_id=template.id,
            version_no="V1",
            status="PUBLISHED",
            sections={
                "items": [
                    {
                        "item_type": "equipment",
                        "item_name": "ICT测试工站",
                        "specification": "双工位",
                        "unit": "套",
                        "qty": 2,
                        "unit_price": 100000,
                        "cost": 65000,
                        "lead_time_days": 45,
                    }
                ]
            },
            pricing_rules={"total_price": 200000, "cost_total": 130000, "lead_time_days": 45},
            created_by=1,
            published_by=1,
        )
        db_session.add(version)
        db_session.flush()
        template.current_version_id = version.id
        db_session.commit()

        headers = _auth_headers(admin_token)
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/from-template",
            headers=headers,
            json={
                "template_id": template.id,
                "customer_id": customer.id,
                "opportunity_id": opportunity.id,
                "valid_until": "2026-07-08",
            },
        )

        assert response.status_code == 201, response.text
        data = response.json()["data"]
        assert data["template_id"] == template.id
        assert data["customer_id"] == customer.id
        assert data["opportunity_id"] == opportunity.id
        assert data["current_version_id"]

        quote = db_session.query(Quote).filter(Quote.id == data["quote_id"]).one()
        assert quote.current_version.total_price == Decimal("200000.00")
        assert quote.current_version.items[0].item_name == "ICT测试工站"
