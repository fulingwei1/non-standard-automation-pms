# -*- coding: utf-8 -*-
"""
销售合同管理 API 测试

测试合同的创建、查询、更新、审批、归档等功能
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Customer, Project
from app.models.sales import Contract, Lead, Opportunity, Quote, QuoteVersion
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesContractsAPI:
    """销售合同管理 API 测试类"""

    def test_list_contracts(self, client: TestClient, admin_token: str):
        """测试获取合同列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/", headers=headers)

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
            "remarks": "重要合同",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/", headers=headers, json=contract_data
        )

        if response.status_code == 404:
            pytest.skip("Contracts API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_create_contract_accepts_legacy_quote_payload_and_infers_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """旧前端合同 payload 也应能从报价反推出商机、客户和报价版本。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-CONTRACT-{unique}",
            customer_name=f"合同兼容客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPCON{unique[:6]}",
            customer=customer,
            opp_name=f"合同兼容商机-{unique}",
            stage="QUOTATION",
            probability=80,
            est_amount=Decimal("500000"),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QCON{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, opportunity, quote])
        db_session.flush()
        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("500000"),
            cost_total=Decimal("300000"),
            gross_margin=Decimal("40.00"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id
        db_session.commit()

        contract_code = f"CTCON{unique[:6]}"
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts?skip_g3_validation=true",
            headers=headers,
            json={
                "contract_no": contract_code,
                "quote_id": quote.id,
                "contract_name": f"合同兼容测试-{unique}",
                "total_amount": 500000,
                "sign_date": "2026-06-08",
                "payment_terms": "30-60-10",
            },
        )

        try:
            assert response.status_code == 201, response.text
            payload = response.json()
            assert payload["contract_code"] == contract_code
            assert payload["opportunity_id"] == opportunity.id
            assert payload["customer_id"] == customer.id
            assert payload["quote_version_id"] == quote_version.id
            assert float(payload["contract_amount"]) == 500000.0
            assert payload["signed_date"] == "2026-06-08"
            assert payload["payment_terms_summary"] == "30-60-10"
        finally:
            db_session.query(Contract).filter(Contract.contract_code == contract_code).delete(
                synchronize_session=False
            )
            quote.current_version_id = None
            db_session.flush()
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(
                synchronize_session=False
            )
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_sign_contract_auto_creates_project_with_quote_cost_and_opportunity_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """合同签署自动建项时，应把报价成本基线和商机上下文带入项目。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-SIGN-{unique}",
            customer_name=f"签约建项客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADSIGN{unique[:6]}",
            customer_name=customer.customer_name,
            industry="电子制造",
            demand_summary="签约前已冻结FCT/EOL测试线需求",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPSIGN{unique[:6]}",
            lead_id=lead.id,
            customer=customer,
            opp_name=f"签约建项商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("580000"),
            est_margin=Decimal("37.93"),
            acceptance_basis="按冻结需求和终验清单验收",
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QSIGN{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([opportunity, quote])
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("580000"),
            cost_total=Decimal("360000"),
            gross_margin=Decimal("37.93"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        contract = Contract(
            contract_code=f"CTSIGN{unique[:6]}",
            contract_name=f"签约建项合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_version.id,
            total_amount=Decimal("580000"),
            payment_terms="30-60-10",
            status="approved",
            sales_owner_id=admin_user.id,
        )
        db_session.add(contract)
        db_session.commit()

        response = client.post(
            (
                f"{settings.API_V1_PREFIX}/sales/contracts/{contract.id}/sign"
                "?auto_generate_payment_plans=false"
            ),
            headers=headers,
            json={
                "sign_date": "2026-06-08",
                "signed_by": "张总",
                "customer_signed_by": "李经理",
                "auto_create_project": True,
            },
        )

        try:
            assert response.status_code == 200, response.text
            data = response.json()["data"]
            project = db_session.get(Project, data["project_id"])
            assert project is not None
            assert project.contract_id == contract.id
            assert project.customer_id == customer.id
            assert project.lead_id == lead.id
            assert project.opportunity_id == opportunity.id
            assert project.contract_no == contract.contract_code
            assert float(project.contract_amount) == 580000.0
            assert float(project.budget_amount) == 360000.0
            assert project.project_type == "FCT"
            assert project.product_category == "EOL"
            assert project.industry == "电子制造"
        finally:
            db_session.query(Project).filter(Project.contract_id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(Contract).filter(Contract.id == contract.id).delete(
                synchronize_session=False
            )
            quote.current_version_id = None
            db_session.flush()
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(
                synchronize_session=False
            )
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Lead).filter(Lead.id == lead.id).delete(synchronize_session=False)
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_get_contract_detail(self, client: TestClient, admin_token: str):
        """测试获取合同详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/1", headers=headers)

        if response.status_code in [404, 422]:
            pytest.skip("No contract data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_contract(self, client: TestClient, admin_token: str):
        """测试更新合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {"remarks": "更新后的备注", "warranty_period": "24个月"}

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/contracts/1", headers=headers, json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Contract API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_contract(self, client: TestClient, admin_token: str):
        """测试删除合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(f"{settings.API_V1_PREFIX}/sales/contracts/999", headers=headers)

        if response.status_code == 404:
            pytest.skip("Contract API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_contract_approval_submit(self, client: TestClient, admin_token: str):
        """测试提交合同审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/submit", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_approval_approve(self, client: TestClient, admin_token: str):
        """测试审批通过合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {"action": "approve", "comments": "审批通过"}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/approve",
            headers=headers,
            json=approval_data,
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
            "customer_signed_by": "李经理",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/sign", headers=headers, json=signing_data
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
            f"{settings.API_V1_PREFIX}/sales/contracts/1/archive", headers=headers
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
            f"{settings.API_V1_PREFIX}/sales/contracts/?status=signed", headers=headers
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
            f"{settings.API_V1_PREFIX}/sales/contracts/?customer_id=1", headers=headers
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
            f"{settings.API_V1_PREFIX}/sales/contracts/expiring?days=30", headers=headers
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
            f"{settings.API_V1_PREFIX}/sales/contracts/statistics", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_contract_export(self, client: TestClient, admin_token: str):
        """测试导出合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/1/export", headers=headers)

        if response.status_code == 404:
            pytest.skip("Contract export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_unauthorized(self, client: TestClient):
        """测试未授权访问合同"""
        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/")

        assert response.status_code in [401, 403], response.text
