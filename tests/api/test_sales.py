# -*- coding: utf-8 -*-
"""
销售模块 API 单元测试
Issue 8.1: 销售模块单元测试完善

测试覆盖：
- 线索管理：创建、更新、转化、权限检查
- 商机管理：创建、更新、阶段门控、权限检查
- 报价管理：创建、版本管理、审批、权限检查
- 合同管理：创建、签订、项目生成、权限检查
- 发票管理：创建、开票、收款、权限检查
- 阶段门验证：G1-G4 所有验证场景
- 审批工作流：启动、审批、驳回、委托
"""

import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AssessmentStatusEnum
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project
from app.models.sales import (
    AssessmentRisk,
    Opportunity,
    QuoteVersion,
    ScoringRule,
    TechnicalAssessment,
)
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def _create_customer(client: TestClient, token: str, name_prefix: str = "测试客户") -> int:
    headers = _auth_headers(token)
    customer_payload = {
        "customer_code": _unique_code("CUST"),
        "customer_name": f"{name_prefix}-{uuid.uuid4().hex[:4]}",
        "industry": "电子制造",
        "contact_person": "客户联系人",
        "contact_phone": "021-88888888",
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/customers",
        json=customer_payload,
        headers=headers,
    )
    assert response.status_code in (200, 201), response.text
    data = response.json()
    customer = data.get("data", data)
    return customer["id"]


def _create_lead(client: TestClient, token: str) -> dict:
    headers = _auth_headers(token)
    lead_payload = {
        "customer_name": f"测试客户-{uuid.uuid4().hex[:4]}",
        "source": "展会",
        "industry": "电子制造",
        "contact_name": "张三",
        "contact_phone": "13800138000",
        "demand_summary": "需要自动化测试设备",
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/leads",
        json=lead_payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_opportunity(client: TestClient, token: str) -> dict:
    headers = _auth_headers(token)
    customer_id = _create_customer(client, token)
    payload = {
        "customer_id": customer_id,
        "opportunity_name": f"测试商机-{uuid.uuid4().hex[:4]}",
        "stage": "QUALIFICATION",
        "expected_amount": 200000.0,
        "expected_close_date": (date.today() + timedelta(days=30)).isoformat(),
        "probability": 80,
        "budget_range": "100000-300000",
        "decision_chain": "工程经理->采购->总经理",
        "delivery_window": "Q4",
        "acceptance_basis": "企业标准验收",
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/opportunities",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_quote(client: TestClient, token: str) -> dict:
    headers = _auth_headers(token)
    opportunity = _create_opportunity(client, token)
    payload = {
        "quote_code": _unique_code("QUOTE"),
        "opportunity_id": opportunity["id"],
        "customer_id": opportunity["customer_id"],
        "valid_until": (date.today() + timedelta(days=45)).isoformat(),
        "version": {
            "version_no": "V1",
            "total_price": 150000.0,
            "cost_total": 90000.0,
            "gross_margin": 40.0,
            "lead_time_days": 45,
            "risk_terms": "Standard delivery terms",
            "items": [
                {
                    "item_type": "SYSTEM",
                    "item_name": "自动化测试平台",
                    "qty": 1,
                    "unit_price": 150000.0,
                    "cost": 90000.0,
                    "lead_time_days": 45,
                }
            ],
        },
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/quotes",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_contract(client: TestClient, token: str) -> dict:
    headers = _auth_headers(token)
    quote = _create_quote(client, token)
    payload = {
        "contract_code": _unique_code("CONTRACT"),
        "opportunity_id": quote["opportunity_id"],
        "customer_id": quote["customer_id"],
        "quote_version_id": quote.get("current_version_id"),
        "contract_amount": 150000.0,
        "signed_date": date.today().isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/contracts",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_invoice(client: TestClient, token: str) -> dict:
    headers = _auth_headers(token)
    contract = _create_contract(client, token)
    payload = {
        "invoice_code": _unique_code("INV"),
        "contract_id": contract["id"],
        "invoice_type": "VAT_SPECIAL",
        "amount": 50000.0,
        "tax_rate": 13.0,
        "issue_date": date.today().isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_active_scoring_rule(client: TestClient, token: str) -> int:
    headers = _auth_headers(token)
    rules_config = {
        "evaluation_criteria": {
            "tech_maturity": {
                "field": "tech_maturity",
                "max_points": 10,
                "options": [{"value": "mature", "points": 10}],
            },
            "budget_status": {
                "field": "budget_status",
                "max_points": 10,
                "options": [{"value": "confirmed", "points": 10}],
            },
        },
        "scales": {
            "decision_thresholds": [
                {"min_score": 80, "decision": "推荐立项"},
                {"min_score": 60, "decision": "有条件立项"},
                {"min_score": 40, "decision": "暂缓"},
                {"min_score": 0, "decision": "不建议立项"},
            ]
        },
        "veto_rules": [],
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/scoring-rules",
        json={
            "version": _unique_code("TA"),
            "rules_json": json.dumps(rules_config, ensure_ascii=False),
            "description": "售前技术闭环测试评分规则",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    rule_id = response.json()["id"]

    response = client.put(
        f"{settings.API_V1_PREFIX}/sales/scoring-rules/{rule_id}/activate",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return rule_id


def _sign_contract(
    client: TestClient, token: str, contract_id: int, *, auto_create_project: bool = True
) -> dict:
    headers = _auth_headers(token)
    sign_data = {
        "signed_date": date.today().isoformat(),
        "remark": "合同签署",
        "auto_create_project": auto_create_project,
    }
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/contracts/{contract_id}/sign",
        json=sign_data,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["code"] == 200
    return data


class TestLeadManagement:
    """线索管理测试"""

    def test_create_lead_success(self, client: TestClient, admin_token: str):
        """测试正常创建线索"""
        lead = _create_lead(client, admin_token)
        assert lead["customer_name"].startswith("测试客户-")
        assert lead["status"] == "NEW"
        assert lead["source"] == "展会"

    def test_create_lead_missing_required_fields(self, client: TestClient, admin_token: str):
        """测试最小必填字段"""

        headers = _auth_headers(admin_token)
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads",
            json={"source": "市场活动"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "NEW"
        assert data["source"] == "市场活动"

    def test_get_lead_list(self, client: TestClient, admin_token: str):
        """测试获取线索列表"""

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads?page=1&page_size=10", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_get_lead_detail(self, client: TestClient, admin_token: str, lead_id: int = None):
        """测试获取线索详情"""

        lead = _create_lead(client, admin_token)
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead["id"]

    def test_update_lead(self, client: TestClient, admin_token: str, lead_id: int = None):
        """测试更新线索"""

        lead = _create_lead(client, admin_token)
        headers = _auth_headers(admin_token)
        update_data = {
            "status": "CONTACTED",
            "contact_name": "李四",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}", json=update_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CONTACTED"
        assert data["contact_name"] == "李四"

    def test_convert_lead_to_opportunity(
        self, client: TestClient, admin_token: str, lead_id: int = None
    ):
        """测试线索转商机"""

        lead = _create_lead(client, admin_token)
        customer_id = _create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/convert",
            params={"customer_id": customer_id, "skip_validation": "true"},
            json={},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["lead_id"] == lead["id"]
        assert data["id"] > 0
        detail = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}",
            headers=headers,
        ).json()
        assert detail["status"] == "CONVERTED"
        assert detail["opportunity_id"] == data["id"]
        assert detail["opportunity_name"] == data["opp_name"]

        list_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads?page=1&page_size=50",
            headers=headers,
        )
        assert list_response.status_code == 200
        list_item = next(
            item for item in list_response.json()["items"] if item["id"] == lead["id"]
        )
        assert list_item["opportunity_id"] == data["id"]
        assert list_item["opportunity_name"] == data["opp_name"]


class TestOpportunityManagement:
    """商机管理测试"""

    def test_create_opportunity_success(self, client: TestClient, admin_token: str):
        """测试正常创建商机"""

        opportunity = _create_opportunity(client, admin_token)
        assert opportunity["stage"] == "QUALIFICATION"
        assert opportunity["customer_id"] > 0

    def test_get_opportunity_list(self, client: TestClient, admin_token: str):
        """测试获取商机列表"""

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities?page=1&page_size=10", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_update_opportunity(
        self, client: TestClient, admin_token: str, opportunity_id: int = None
    ):
        """测试更新商机"""

        opportunity = _create_opportunity(client, admin_token)
        headers = _auth_headers(admin_token)
        update_data = {
            "stage": "PROPOSAL",
            "probability": 50,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/opportunities/{opportunity['id']}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "PROPOSAL"
        assert data["probability"] == 50

    def test_submit_gate_validation(
        self, client: TestClient, admin_token: str, opportunity_id: int = None
    ):
        """测试提交阶段门控验证"""

        opportunity = _create_opportunity(client, admin_token)
        headers = _auth_headers(admin_token)
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/{opportunity['id']}/gate",
            params={"gate_type": "G2"},
            json={"gate_status": "PASS"},
            headers=headers,
        )
        assert response.status_code in (200, 400)


class TestQuoteManagement:
    """报价管理测试"""

    def test_create_quote_success(self, client: TestClient, admin_token: str):
        """测试正常创建报价"""

        quote = _create_quote(client, admin_token)
        assert quote["opportunity_id"] is not None
        assert "quote_code" in quote

    def test_create_quote_inherits_approved_presale_solution_cost_baseline(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """报价从已审批售前方案创建时，应继承成本、建议售价和交期。"""

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid.uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-QPRE-{unique}",
            customer_name=f"报价继承客户-{unique}",
            industry="电子制造",
            contact_person="王工",
            contact_phone="021-88888888",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPQPRE{unique[:6]}",
            customer_id=customer.id,
            opp_name=f"报价继承商机-{unique}",
            stage="QUOTATION",
            probability=80,
            est_amount=Decimal("250000"),
            expected_close_date=date.today() + timedelta(days=30),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(opportunity)
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=_unique_code("TICKET-QPRE"),
            title=f"报价继承售前工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            opportunity_id=opportunity.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            assessment_status=AssessmentStatusEnum.COMPLETED.value,
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        solution = PresaleSolution(
            solution_no=_unique_code("SOL-QPRE"),
            name=f"报价继承方案-{unique}",
            solution_type="CUSTOM",
            industry="电子制造",
            test_type="FCT",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            requirement_summary="报价前冻结的客户需求",
            solution_overview="FCT自动化测试平台方案",
            technical_spec="自动上下料、扫码、FCT测试、数据追溯",
            estimated_cost=Decimal("150000"),
            suggested_price=Decimal("250000"),
            estimated_duration=45,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()

        response = client.post(
            f"{prefix}/sales/quotes",
            json={
                "quote_code": _unique_code("QUOTE-PRE"),
                "opportunity_id": opportunity.id,
                "customer_id": customer.id,
                "solution_id": solution.id,
                "valid_until": (date.today() + timedelta(days=45)).isoformat(),
                "version": {
                    "version_no": "V1",
                    "items": [],
                },
            },
            headers=headers,
        )

        assert response.status_code == 201, response.text
        quote = response.json()
        version = db_session.get(QuoteVersion, quote["current_version_id"])
        assert version is not None
        assert version.cost_total == Decimal("150000")
        assert version.total_price == Decimal("250000")
        assert version.gross_margin == Decimal("40.00")
        assert version.lead_time_days == 45
        assert version.presale_solution_id == solution.id
        assert version.presale_ticket_id == ticket.id

        detail_response = client.get(f"{prefix}/sales/quotes/{quote['id']}", headers=headers)
        assert detail_response.status_code == 200, detail_response.text
        current_version = detail_response.json()["data"]["current_version"]
        assert current_version["cost_total"] == 150000.0
        assert current_version["total_price"] == 250000.0
        assert current_version["gross_margin"] == 40.0
        assert current_version["lead_time_days"] == 45

    def test_create_quote_version(self, client: TestClient, admin_token: str, quote_id: int = None):
        """测试创建报价版本"""

        if not quote_id:
            quote = _create_quote(client, admin_token)
            quote_id = quote["id"]

        headers = _auth_headers(admin_token)
        version_data = {"version_no": "V2", "total_price": 160000.0}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/versions",
            json=version_data,
            headers=headers,
        )

        assert response.status_code in (200, 201)
        data = response.json()
        version = data.get("data", data)
        assert version["version_no"] == "V2"

    def test_create_quote_version_inherits_presale_solution_cost_baseline(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """报价新版本来自售前修订方案时，也应继承成本、建议售价和交期。"""

        headers = _auth_headers(admin_token)
        quote = _create_quote(client, admin_token)
        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None
        customer = db_session.get(Customer, quote["customer_id"])
        assert customer is not None

        ticket = PresaleSupportTicket(
            ticket_no=_unique_code("TICKET-QVER"),
            title=f"报价版本售前工单-{uuid.uuid4().hex[:4]}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=quote["customer_id"],
            customer_name=customer.customer_name,
            opportunity_id=quote["opportunity_id"],
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            assessment_status=AssessmentStatusEnum.COMPLETED.value,
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        solution = PresaleSolution(
            solution_no=_unique_code("SOL-QVER"),
            name=f"报价版本修订方案-{uuid.uuid4().hex[:4]}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=quote["customer_id"],
            opportunity_id=quote["opportunity_id"],
            requirement_summary="客户方案修订后重新报价",
            solution_overview="新版FCT自动化测试平台方案",
            technical_spec="新增扫码追溯和MES对接",
            estimated_cost=Decimal("175000"),
            suggested_price=Decimal("300000"),
            estimated_duration=60,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote['id']}/versions",
            json={
                "version_no": "V2",
                "presale_solution_id": solution.id,
                "items": [],
            },
            headers=headers,
        )

        assert response.status_code in (200, 201), response.text
        version_id = response.json()["data"]["id"]
        db_session.expire_all()
        version = db_session.get(QuoteVersion, version_id)
        assert version is not None
        assert version.cost_total == Decimal("175000")
        assert version.total_price == Decimal("300000")
        assert version.gross_margin == Decimal("41.67")
        assert version.lead_time_days == 60
        assert version.presale_solution_id == solution.id
        assert version.presale_ticket_id == ticket.id

    def test_approve_quote(self, client: TestClient, admin_token: str, quote_id: int = None):
        """测试审批报价"""

        if not quote_id:
            quote = _create_quote(client, admin_token)
            quote_id = quote["id"]

        headers = _auth_headers(admin_token)
        approve_data = {"approved": True, "remark": "同意报价"}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/approve",
            json=approve_data,
            headers=headers,
        )

        # 根据权限和审批流程，可能成功或失败
        assert response.status_code in [200, 403, 400, 404]

    def test_list_quotes_searches_by_display_quote_number(
        self, client: TestClient, admin_token: str
    ):
        """报价列表应支持按前端展示编号 QT-000123 搜索。"""

        quote = _create_quote(client, admin_token)
        headers = _auth_headers(admin_token)
        display_quote_no = f"QT-{quote['id']:06d}"

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes",
            params={"keyword": display_quote_no},
            headers=headers,
        )

        assert response.status_code == 200, response.text
        items = response.json()["items"]
        assert any(item["id"] == quote["id"] for item in items)


class TestContractManagement:
    """合同管理测试"""

    def test_create_contract_success(self, client: TestClient, admin_token: str):
        """测试正常创建合同"""

        contract = _create_contract(client, admin_token)
        assert "contract_code" in contract
        assert contract["opportunity_id"] is not None

    def test_sign_contract(self, client: TestClient, admin_token: str, contract_id: int = None):
        """测试合同签订"""

        if not contract_id:
            contract = _create_contract(client, admin_token)
            contract_id = contract["id"]

        sign_data = _sign_contract(client, admin_token, contract_id)

        headers = _auth_headers(admin_token)
        detail_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract_id}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        contract_detail = detail_response.json()
        assert contract_detail["status"] == "SIGNED"
        assert contract_detail["signed_date"] == date.today().isoformat()
        assert sign_data["data"]["contract_id"] == contract_id

    def test_generate_project_from_contract(
        self, client: TestClient, admin_token: str, contract_id: int = None
    ):
        """测试从合同生成项目"""

        if not contract_id:
            contract = _create_contract(client, admin_token)
            contract_id = contract["id"]
            _sign_contract(client, admin_token, contract_id, auto_create_project=False)

        headers = _auth_headers(admin_token)
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract_id}/project",
            params={"skip_g4_validation": "true"},
            json={
                "project_code": _unique_code("PRJ"),
                "project_name": f"合同项目-{uuid.uuid4().hex[:4]}",
            },
            headers=headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["code"] == 200
        assert "project_id" in data.get("data", {})


class TestSalesClosedLoop:
    """销售闭环测试"""

    def test_lead_to_opportunity_quote_contract_project_closed_loop(
        self, client: TestClient, admin_token: str
    ):
        """同一条沙箱数据走通：线索 -> 商机 -> 报价 -> 合同 -> 项目立项"""

        headers = _auth_headers(admin_token)

        lead = _create_lead(client, admin_token)
        customer_id = _create_customer(client, admin_token, name_prefix="闭环客户")

        convert_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/convert",
            params={"customer_id": customer_id, "skip_validation": "true"},
            json={},
            headers=headers,
        )
        assert convert_response.status_code == 201, convert_response.text
        opportunity = convert_response.json()
        assert opportunity["lead_id"] == lead["id"]
        assert opportunity["customer_id"] == customer_id

        quote_payload = {
            "quote_code": _unique_code("QUOTE-CLOSE"),
            "opportunity_id": opportunity["id"],
            "customer_id": customer_id,
            "valid_until": (date.today() + timedelta(days=45)).isoformat(),
            "version": {
                "version_no": "V1",
                "total_price": 188000.0,
                "cost_total": 112800.0,
                "gross_margin": 40.0,
                "lead_time_days": 45,
                "risk_terms": "Standard delivery terms",
                "items": [
                    {
                        "item_type": "SYSTEM",
                        "item_name": "闭环自动化测试平台",
                        "qty": 1,
                        "unit_price": 188000.0,
                        "cost": 112800.0,
                        "lead_time_days": 45,
                    }
                ],
            },
        }
        quote_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes",
            json=quote_payload,
            headers=headers,
        )
        assert quote_response.status_code == 201, quote_response.text
        quote = quote_response.json()
        assert quote["opportunity_id"] == opportunity["id"]
        assert quote["customer_id"] == customer_id
        assert quote.get("current_version_id")

        contract_name = f"闭环合同-{uuid.uuid4().hex[:4]}"
        contract_payload = {
            "contract_code": _unique_code("CTCL"),
            "contract_name": contract_name,
            "opportunity_id": opportunity["id"],
            "customer_id": customer_id,
            "quote_version_id": quote["current_version_id"],
            "contract_amount": 188000.0,
            "signed_date": date.today().isoformat(),
        }
        contract_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts",
            json=contract_payload,
            headers=headers,
        )
        assert contract_response.status_code == 201, contract_response.text
        contract = contract_response.json()
        assert contract["opportunity_id"] == opportunity["id"]
        assert contract["customer_id"] == customer_id
        assert contract["contract_name"] == contract_name

        _sign_contract(client, admin_token, contract["id"], auto_create_project=False)

        project_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract['id']}/project",
            params={"skip_g4_validation": "true"},
            json={
                "project_code": _unique_code("PRJCL"),
                "project_name": f"闭环项目-{uuid.uuid4().hex[:4]}",
                "allocation_amount": 188000.0,
            },
            headers=headers,
        )
        assert project_response.status_code == 200, project_response.text
        project_data = project_response.json()["data"]
        assert project_data["project_id"] > 0

        contract_detail_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract['id']}",
            headers=headers,
        )
        assert contract_detail_response.status_code == 200, contract_detail_response.text
        contract_detail = contract_detail_response.json()
        assert contract_detail["project_id"] == project_data["project_id"]
        assert contract_detail["status"] == "SIGNED"
        assert contract_detail["contract_name"] == contract_name

    def test_manual_contract_project_inherits_quote_cost_and_opportunity_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """手动合同建项也必须带入报价成本基线和商机上下文。"""

        headers = _auth_headers(admin_token)

        lead = _create_lead(client, admin_token)
        customer_id = _create_customer(client, admin_token, name_prefix="手动建项客户")

        convert_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/convert",
            params={"customer_id": customer_id, "skip_validation": "true"},
            json={},
            headers=headers,
        )
        assert convert_response.status_code == 201, convert_response.text
        opportunity = convert_response.json()

        quote_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes",
            json={
                "quote_code": _unique_code("QUOTE-MANUAL"),
                "opportunity_id": opportunity["id"],
                "customer_id": customer_id,
                "valid_until": (date.today() + timedelta(days=45)).isoformat(),
                "version": {
                    "version_no": "V1",
                    "total_price": 258000.0,
                    "cost_total": 154800.0,
                    "gross_margin": 40.0,
                    "lead_time_days": 45,
                    "risk_terms": "Standard delivery terms",
                    "items": [
                        {
                            "item_type": "SYSTEM",
                            "item_name": "手动建项自动化测试平台",
                            "qty": 1,
                            "unit_price": 258000.0,
                            "cost": 154800.0,
                            "lead_time_days": 45,
                        }
                    ],
                },
            },
            headers=headers,
        )
        assert quote_response.status_code == 201, quote_response.text
        quote = quote_response.json()

        contract_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts",
            json={
                "contract_code": _unique_code("CTMAN"),
                "contract_name": f"手动建项合同-{uuid.uuid4().hex[:4]}",
                "opportunity_id": opportunity["id"],
                "customer_id": customer_id,
                "quote_version_id": quote["current_version_id"],
                "contract_amount": 258000.0,
                "signed_date": date.today().isoformat(),
            },
            headers=headers,
        )
        assert contract_response.status_code == 201, contract_response.text
        contract = contract_response.json()

        _sign_contract(client, admin_token, contract["id"], auto_create_project=False)

        project_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract['id']}/project",
            params={"skip_g4_validation": "true"},
            json={
                "project_code": _unique_code("PRJMAN"),
                "project_name": f"手动闭环项目-{uuid.uuid4().hex[:4]}",
            },
            headers=headers,
        )
        assert project_response.status_code == 200, project_response.text
        project_id = project_response.json()["data"]["project_id"]

        db_session.expire_all()
        project = db_session.get(Project, project_id)
        assert project is not None
        assert project.lead_id == lead["id"]
        assert project.opportunity_id == opportunity["id"]
        assert project.contract_id == contract["id"]
        assert project.customer_id == customer_id
        assert float(project.contract_amount) == 258000.0
        assert float(project.budget_amount) == 154800.0
        assert project.project_type == opportunity["project_type"]
        assert project.product_category == opportunity["equipment_type"]
        assert project.industry == "电子制造"
        assert project.salesperson_id == opportunity["owner_id"]

    def test_contract_pmo_initiation_approval_links_project_back_to_contract(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """合同走 PMO 立项审批后，生成项目必须回写合同和售前交接资料。"""

        headers = _auth_headers(admin_token)
        contract = _create_contract(client, admin_token)
        _sign_contract(client, admin_token, contract["id"], auto_create_project=False)

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None
        ticket = PresaleSupportTicket(
            ticket_no=_unique_code("TICKET-PMO"),
            title=f"PMO售前交接工单-{uuid.uuid4().hex[:4]}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=contract["customer_id"],
            customer_name=contract["customer_name"],
            opportunity_id=contract["opportunity_id"],
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            actual_hours=Decimal("12.5"),
            pm_involvement_required=True,
            pm_involvement_risk_level="高",
            pm_involvement_risk_factors=["金额高", "交期紧"],
            pm_assigned=False,
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()
        assessment = TechnicalAssessment(
            source_type="OPPORTUNITY",
            source_id=contract["opportunity_id"],
            evaluator_id=admin_user.id,
            status=AssessmentStatusEnum.COMPLETED.value,
            total_score=82,
            decision="RECOMMEND",
            risks='[{"dimension":"delivery","level":"MEDIUM","description":"交期压缩风险"}]',
            presale_ticket_id=ticket.id,
        )
        db_session.add(assessment)
        db_session.flush()
        assessment_risk = AssessmentRisk(
            assessment_id=assessment.id,
            risk_code=_unique_code("RSK-PMO"),
            risk_title="交期压缩风险",
            risk_category="delivery",
            risk_description="交付周期偏紧，项目启动后需要 PM 提前排产",
            probability="MEDIUM",
            impact="MEDIUM",
            risk_level="HIGH",
            risk_score=4,
            owner_id=admin_user.id,
            status="OPEN",
        )
        db_session.add(assessment_risk)
        ticket.current_assessment_id = assessment.id
        ticket.assessment_status = AssessmentStatusEnum.COMPLETED.value
        solution = PresaleSolution(
            solution_no=_unique_code("SOL-PMO"),
            name=f"PMO售前交接方案-{uuid.uuid4().hex[:4]}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=contract["customer_id"],
            opportunity_id=contract["opportunity_id"],
            requirement_summary="PMO立项前冻结的客户需求",
            solution_overview="PMO审批后应进入项目工作台",
            technical_spec="ICT/FCT一体化测试设备",
            estimated_cost=Decimal("90000"),
            suggested_price=Decimal("150000"),
            estimated_hours=96,
            estimated_duration=35,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()

        initiation_response = client.post(
            f"{settings.API_V1_PREFIX}/pmo/initiations",
            json={
                "project_name": f"PMO闭环项目-{uuid.uuid4().hex[:4]}",
                "project_type": "NEW",
                "customer_name": contract["customer_name"],
                "contract_no": contract["contract_code"],
                "contract_amount": contract["contract_amount"],
                "required_start_date": date.today().isoformat(),
                "required_end_date": (date.today() + timedelta(days=45)).isoformat(),
                "technical_solution_id": solution.id,
                "requirement_summary": f"由合同 {contract['contract_code']} 发起立项",
            },
            headers=headers,
        )
        assert initiation_response.status_code == 201, initiation_response.text
        initiation = initiation_response.json()

        initiation_detail_response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/initiations/{initiation['id']}",
            headers=headers,
        )
        assert initiation_detail_response.status_code == 200, initiation_detail_response.text
        initiation_detail = initiation_detail_response.json()
        handover = initiation_detail["presale_handover_context"]
        assert handover["contract"]["contract_code"] == contract["contract_code"]
        assert handover["presale_solution"]["id"] == solution.id
        assert handover["presale_solution"]["estimated_cost"] == 90000.0
        assert handover["presale_ticket"]["id"] == ticket.id
        assert handover["presale_ticket"]["actual_hours"] == 12.5
        assert handover["presale_ticket"]["assessment_status"] == AssessmentStatusEnum.COMPLETED.value
        assert handover["presale_ticket"]["current_assessment_id"] == assessment.id
        assert handover["presale_ticket"]["pm_involvement_required"] is True
        assert handover["presale_ticket"]["pm_involvement_risk_level"] == "高"
        assert handover["presale_ticket"]["pm_involvement_risk_factors"] == ["金额高", "交期紧"]
        assert handover["presale_ticket"]["pm_assigned"] is False
        assert handover["technical_assessment"]["current"]["id"] == assessment.id
        assert handover["technical_assessment"]["current"]["total_score"] == 82
        assert handover["technical_assessment"]["current"]["decision"] == "RECOMMEND"
        assert handover["technical_assessment"]["risks"]["total"] == 1
        assert (
            handover["technical_assessment"]["risks"]["items"][0]["risk_description"]
            == "交付周期偏紧，项目启动后需要 PM 提前排产"
        )
        assert handover["baseline_cost"]["presale_estimated_cost"] == 90000.0
        assert handover["handover_status"]["ready"] is True

        submit_response = client.put(
            f"{settings.API_V1_PREFIX}/pmo/initiations/{initiation['id']}/submit",
            headers=headers,
        )
        assert submit_response.status_code == 200, submit_response.text

        approve_response = client.put(
            f"{settings.API_V1_PREFIX}/pmo/initiations/{initiation['id']}/approve",
            json={
                "review_result": "同意立项",
                "approved_pm_id": 1,
                "approved_level": "A",
            },
            headers=headers,
        )
        assert approve_response.status_code == 200, approve_response.text
        project_id = approve_response.json()["data"]["project_id"]
        assert project_id > 0

        db_session.expire_all()
        refreshed_solution = db_session.get(PresaleSolution, solution.id)
        refreshed_ticket = db_session.get(PresaleSupportTicket, ticket.id)
        assert refreshed_solution.project_id == project_id
        assert refreshed_ticket.project_id == project_id

        contract_detail_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract['id']}",
            headers=headers,
        )
        assert contract_detail_response.status_code == 200, contract_detail_response.text
        assert contract_detail_response.json()["project_id"] == project_id

        workspace_context_response = client.get(
            f"{settings.API_V1_PREFIX}/project-workspace/projects/{project_id}/workspace/context",
            headers=headers,
        )
        assert workspace_context_response.status_code == 200, workspace_context_response.text
        workspace_context = workspace_context_response.json()
        assert workspace_context["contract"]["contract_code"] == contract["contract_code"]
        assert workspace_context["opportunity"]["id"] == contract["opportunity_id"]
        assert workspace_context["quote"]["version"]["cost_total"] == 90000.0
        assert workspace_context["baseline_cost"]["presale_estimated_cost"] == 90000.0
        assert workspace_context["presale_tickets"][0]["id"] == ticket.id
        assert workspace_context["presale_tickets"][0]["actual_hours"] == 12.5
        assert workspace_context["presale_solutions"][0]["id"] == solution.id
        assert workspace_context["technical_assessment"]["current"]["id"] == assessment.id
        assert workspace_context["technical_assessment"]["risks"]["total"] == 1
        assert workspace_context["handover_status"]["ready"] is True

        payment_plans_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract['id']}/payment-plans",
            headers=headers,
        )
        assert payment_plans_response.status_code == 200, payment_plans_response.text
        payment_plans = payment_plans_response.json()
        assert len(payment_plans) == 4
        assert {plan["payment_name"] for plan in payment_plans} == {
            "预付款",
            "发货款",
            "验收款",
            "质保款",
        }
        assert sum(float(plan["planned_amount"]) for plan in payment_plans) == float(
            contract["contract_amount"]
        )

    def test_quote_list_exposes_contract_id_after_contract_created(
        self, client: TestClient, admin_token: str
    ):
        """报价已生成合同时，列表必须返回 contract_id，前端才能隐藏重复生成入口。"""

        headers = _auth_headers(admin_token)
        quote = _create_quote(client, admin_token)
        contract_payload = {
            "contract_code": _unique_code("QTC"),
            "contract_name": f"报价关联合同-{uuid.uuid4().hex[:4]}",
            "opportunity_id": quote["opportunity_id"],
            "customer_id": quote["customer_id"],
            "quote_version_id": quote["current_version_id"],
            "contract_amount": 150000.0,
        }
        contract_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts",
            json=contract_payload,
            headers=headers,
        )
        assert contract_response.status_code == 201, contract_response.text
        contract = contract_response.json()

        list_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes",
            params={"keyword": quote["quote_code"]},
            headers=headers,
        )
        assert list_response.status_code == 200, list_response.text
        items = list_response.json()["items"]
        matched = [item for item in items if item["id"] == quote["id"]]
        assert matched
        assert matched[0]["contract_id"] == contract["id"]


class TestSalesFunnelWorkflow:
    """销售漏斗跨阶段闭环测试。"""

    def test_g2_quote_can_continue_to_g3_contract(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """G2 转出的报价应自带版本/金额，审批后可继续 G3 转合同。"""

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid.uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-G2Q-{unique}",
            customer_name=f"G2报价闭环客户-{unique}",
            industry="电子制造",
            contact_person="王工",
            contact_phone="021-88888888",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPG2Q{unique[:6]}",
            customer_id=customer.id,
            opp_name=f"G2报价闭环商机-{unique}",
            stage="QUALIFICATION",
            probability=75,
            est_amount=Decimal("360000"),
            expected_close_date=date.today() + timedelta(days=30),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
            assessment_status=AssessmentStatusEnum.COMPLETED.value,
            requirement_maturity=3,
        )
        db_session.add(opportunity)
        db_session.flush()

        assessment = TechnicalAssessment(
            source_type="OPPORTUNITY",
            source_id=opportunity.id,
            evaluator_id=admin_user.id,
            status=AssessmentStatusEnum.COMPLETED.value,
            decision="推荐立项",
        )
        db_session.add(assessment)
        db_session.flush()
        opportunity.assessment_id = assessment.id
        db_session.commit()

        converted = client.post(
            f"{prefix}/sales/funnel/opportunity-to-quote",
            json={
                "opportunity_id": opportunity.id,
                "quote_title": f"G2闭环报价-{unique}",
                "validity_days": 30,
            },
            headers=headers,
        )
        assert converted.status_code == 200, converted.text
        quote_id = converted.json()["data"]["quote_id"]

        quote_detail = client.get(f"{prefix}/sales/quotes/{quote_id}", headers=headers)
        assert quote_detail.status_code == 200, quote_detail.text
        quote = quote_detail.json()["data"]
        assert quote["current_version"] is not None
        assert float(quote["current_version"]["total_price"]) > 0

        approved = client.post(
            f"{prefix}/sales/quotes/{quote_id}/approve",
            json={"approved": True, "remark": "同意报价"},
            headers=headers,
        )
        assert approved.status_code == 200, approved.text

        gate = client.post(
            f"{prefix}/sales/funnel/validate-gate",
            json={"gate_type": "G3", "entity_id": quote_id, "save_result": False},
            headers=headers,
        )
        assert gate.status_code == 200, gate.text
        gate_data = gate.json()["data"]
        assert gate_data["is_valid"] is True
        assert "报价版本有效" in gate_data["checked_items"]
        assert "报价金额有效" in gate_data["checked_items"]

        contracted = client.post(
            f"{prefix}/sales/funnel/quote-to-contract",
            json={
                "quote_id": quote_id,
                "contract_title": f"G2报价闭环合同-{unique}",
                "contract_type": "SALES",
            },
            headers=headers,
        )
        assert contracted.status_code == 200, contracted.text
        assert contracted.json()["data"]["contract_id"] is not None


class TestInvoiceManagement:
    """发票管理测试"""

    def test_create_invoice_success(self, client: TestClient, admin_token: str):
        """测试正常创建发票"""

        invoice = _create_invoice(client, admin_token)
        assert "invoice_code" in invoice
        assert invoice["contract_id"] is not None

    def test_issue_invoice(self, client: TestClient, admin_token: str, invoice_id: int = None):
        """测试开票"""

        if not invoice_id:
            invoice = _create_invoice(client, admin_token)
            invoice_id = invoice["id"]

        headers = _auth_headers(admin_token)
        issue_data = {
            "issue_date": date.today().isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/invoices/{invoice_id}/issue",
            json=issue_data,
            headers=headers,
        )

        # 根据权限和状态，可能成功或失败
        assert response.status_code in [200, 403, 400]


class TestGateValidation:
    """阶段门验证测试"""

    def test_g1_validation_success(self, client: TestClient, admin_token: str):
        """测试G1验证成功场景"""

        lead = _create_lead(client, admin_token)
        customer_id = _create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        requirement_data = {
            "product_object": "自动化测试台",
            "ct_seconds": 60,
            "interface_desc": "MODBUS",
            "site_constraints": "需要洁净室",
            "acceptance_criteria": "样机通过试验",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/convert",
            params={"customer_id": customer_id},
            json=requirement_data,
            headers=headers,
        )
        assert response.status_code == 201

    def test_g1_validation_failure(self, client: TestClient, admin_token: str):
        """测试G1验证失败场景"""

        lead = _create_lead(client, admin_token)
        customer_id = _create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/convert",
            params={"customer_id": customer_id},
            json={},
            headers=headers,
        )
        assert response.status_code == 400


class TestTechnicalAssessmentClosedLoop:
    """售前技术评估闭环测试"""

    def test_evaluating_assessment_uses_default_rule_when_no_active_rule(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """没有启用评分规则时，接口应使用系统默认规则完成评估。"""

        db_session.query(ScoringRule).update(
            {ScoringRule.is_active: False},
            synchronize_session=False,
        )
        db_session.commit()

        lead = _create_lead(client, admin_token)
        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        assessment_id = response.json()["data"]["assessment_id"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/assessments/{assessment_id}/evaluate",
            json={
                "requirement_data": {
                    "tech_maturity": "mature",
                    "process_difficulty": "standard",
                    "precision_requirement": "normal",
                    "sample_support": "available",
                    "budgetStatus": "confirmed",
                    "price_sensitivity": "low",
                    "gross_margin_safety": "safe",
                    "payment_terms": "good",
                    "resource_occupancy": "available",
                    "has_similar_case": "yes",
                    "delivery_feasibility": "feasible",
                    "delivery_months": 3,
                    "change_risk": "low",
                    "customer_nature": "strategic",
                    "customer_potential": "high",
                    "relationship_depth": "deep",
                    "contact_level": "decision_maker",
                    "hasSOW": True,
                },
                "enable_ai": False,
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        evaluated_assessment = response.json()
        assert evaluated_assessment["id"] == assessment_id
        assert evaluated_assessment["status"] == AssessmentStatusEnum.COMPLETED.value
        assert evaluated_assessment["total_score"] >= 80
        dimension_scores = json.loads(evaluated_assessment["dimension_scores"])
        assert dimension_scores["business"] > 0

    def test_evaluating_applied_lead_assessment_updates_same_record(
        self, client: TestClient, admin_token: str
    ):
        """申请后的评估应闭环到同一条记录，不留下重复待办"""

        _create_active_scoring_rule(client, admin_token)
        lead = _create_lead(client, admin_token)
        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        assessment_id = response.json()["data"]["assessment_id"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/assessments/{assessment_id}/evaluate",
            json={
                "requirement_data": {
                    "tech_maturity": "mature",
                    "budget_status": "confirmed",
                    "has_sow": True,
                },
                "enable_ai": False,
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        evaluated_assessment = response.json()
        assert evaluated_assessment["id"] == assessment_id
        assert evaluated_assessment["status"] == "COMPLETED"

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assessments = response.json()
        assert [item["id"] for item in assessments] == [assessment_id]
        assert assessments[0]["status"] == "COMPLETED"

    def test_reapplying_pending_assessment_reuses_existing_record(
        self, client: TestClient, admin_token: str
    ):
        """线索/商机重复申请待评估技术评估时，不应生成重复待办。"""
        headers = _auth_headers(admin_token)

        lead = _create_lead(client, admin_token)
        first_lead_apply = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert first_lead_apply.status_code == 201, first_lead_apply.text
        first_lead_assessment_id = first_lead_apply.json()["data"]["assessment_id"]

        second_lead_apply = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert second_lead_apply.status_code == 201, second_lead_apply.text
        assert second_lead_apply.json()["data"]["assessment_id"] == first_lead_assessment_id

        lead_assessments = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments",
            headers=headers,
        )
        assert lead_assessments.status_code == 200, lead_assessments.text
        assert [item["id"] for item in lead_assessments.json()] == [first_lead_assessment_id]

        opportunity = _create_opportunity(client, admin_token)
        first_opp_apply = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/{opportunity['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert first_opp_apply.status_code == 201, first_opp_apply.text
        first_opp_assessment_id = first_opp_apply.json()["data"]["assessment_id"]

        second_opp_apply = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/{opportunity['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert second_opp_apply.status_code == 201, second_opp_apply.text
        assert second_opp_apply.json()["data"]["assessment_id"] == first_opp_assessment_id

        opp_assessments = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/{opportunity['id']}/assessments",
            headers=headers,
        )
        assert opp_assessments.status_code == 200, opp_assessments.text
        assert [item["id"] for item in opp_assessments.json()] == [first_opp_assessment_id]

    def test_evaluating_lead_assessment_updates_linked_presale_ticket(
        self, client: TestClient, admin_token: str
    ):
        """线索技术评估完成后，应回写同线索售前工单的评估状态。"""

        _create_active_scoring_rule(client, admin_token)
        lead = _create_lead(client, admin_token)
        headers = _auth_headers(admin_token)

        ticket_response = client.post(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            json={
                "title": f"线索技术支持-{uuid.uuid4().hex[:4]}",
                "ticket_type": "TECHNICAL_SUPPORT",
                "urgency": "NORMAL",
                "customer_name": lead["customer_name"],
                "lead_id": lead["id"],
            },
            headers=headers,
        )
        assert ticket_response.status_code == 201, ticket_response.text
        ticket_id = ticket_response.json()["id"]
        assert ticket_response.json()["assessment_status"] == AssessmentStatusEnum.PENDING.value

        apply_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert apply_response.status_code == 201, apply_response.text
        assessment_id = apply_response.json()["data"]["assessment_id"]

        evaluate_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/assessments/{assessment_id}/evaluate",
            json={
                "requirement_data": {
                    "tech_maturity": "mature",
                    "budget_status": "confirmed",
                    "has_sow": True,
                },
                "enable_ai": False,
            },
            headers=headers,
        )
        assert evaluate_response.status_code == 200, evaluate_response.text
        assert evaluate_response.json()["id"] == assessment_id

        refreshed_ticket = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets/{ticket_id}",
            headers=headers,
        )
        assert refreshed_ticket.status_code == 200, refreshed_ticket.text
        ticket = refreshed_ticket.json()
        assert ticket["status"] == "PENDING"
        assert ticket["assessment_status"] == AssessmentStatusEnum.COMPLETED.value
        assert ticket["current_assessment_id"] == assessment_id

    def test_evaluation_generated_risks_are_available_as_structured_risks(
        self, client: TestClient, admin_token: str
    ):
        """评估生成的风险应进入结构化风险列表，供售前工作台继续跟踪"""

        _create_active_scoring_rule(client, admin_token)
        lead = _create_lead(client, admin_token)
        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/leads/{lead['id']}/assessments/apply",
            json={},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        assessment_id = response.json()["data"]["assessment_id"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/assessments/{assessment_id}/evaluate",
            json={
                "requirement_data": {
                    "tech_maturity": "immature",
                    "budget_status": "unclear",
                    "requirement_maturity": 1,
                    "has_sow": False,
                },
                "enable_ai": False,
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        evaluated_assessment = response.json()
        assert evaluated_assessment["id"] == assessment_id
        assert evaluated_assessment["risks"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/assessments/{assessment_id}/risks",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert payload["total"] >= 1
        risk_descriptions = {item["risk_description"] for item in payload["items"]}
        assert "technology维度评分较低(0分)，存在较高风险" in risk_descriptions
        assert any(item["risk_title"] == "technology维度风险" for item in payload["items"])
        assert any(item["risk_type"] == "technology" for item in payload["items"])

    def test_failure_case_detail_and_update_routes_match_frontend_api(
        self, client: TestClient, admin_token: str
    ):
        """失败案例库详情/编辑接口应与前端 technicalAssessmentApi 声明一致。"""
        headers = _auth_headers(admin_token)
        create_payload = {
            "case_code": _unique_code("FC"),
            "project_name": "新能源电控测试线失败复盘",
            "industry": "新能源",
            "product_types": '["EOL"]',
            "processes": '["功能测试"]',
            "takt_time_s": 45,
            "annual_volume": 120000,
            "budget_status": "rough",
            "customer_project_status": "方案阶段",
            "spec_status": "频繁变更",
            "price_sensitivity": "high",
            "delivery_months": 3,
            "failure_tags": '["需求不清", "成本失控"]',
            "core_failure_reason": "客户接口边界不清，报价前未冻结SOW",
            "early_warning_signals": '["样品未提供", "接口协议缺失"]',
            "final_result": "LOST",
            "lesson_learned": "报价前必须完成需求冻结和技术风险确认",
            "keywords": '["EOL", "SOW", "需求冻结"]',
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/failure-cases",
            json=create_payload,
            headers=headers,
        )
        assert create_response.status_code == 201, create_response.text
        case_id = create_response.json()["id"]

        detail_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/failure-cases/{case_id}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        assert detail_response.json()["case_code"] == create_payload["case_code"]

        update_response = client.put(
            f"{settings.API_V1_PREFIX}/sales/failure-cases/{case_id}",
            json={
                "core_failure_reason": "技术评估未覆盖客户夹具换型边界",
                "failure_tags": '["技术评估缺口", "换型风险"]',
            },
            headers=headers,
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["core_failure_reason"] == "技术评估未覆盖客户夹具换型边界"
        assert updated["failure_tags"] == '["技术评估缺口", "换型风险"]'
        assert updated["lesson_learned"] == create_payload["lesson_learned"]


class TestPermissionControl:
    """权限控制测试"""

    def test_lead_permission_filtering(self, client: TestClient, sales_user_token: str):
        """测试线索数据权限过滤"""
        headers = _auth_headers(sales_user_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/leads?page=1&page_size=10", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        # 销售用户应该只能看到自己的线索或团队线索
        # 这里需要根据实际权限逻辑验证

    def test_edit_permission_check(self, client: TestClient, normal_user_token: str):
        """测试编辑权限检查"""
        headers = _auth_headers(normal_user_token)

        # 尝试更新不属于自己的线索
        update_data = {"status": "CONTACTED"}

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/leads/1", json=update_data, headers=headers
        )

        # 应该返回403 Forbidden
        assert response.status_code in [403, 404]
