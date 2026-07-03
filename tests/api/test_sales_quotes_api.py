# -*- coding: utf-8 -*-
"""
销售报价管理 API 测试

测试报价单的创建、查询、更新、审批等功能
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval import ApprovalFlowDefinition, ApprovalNodeDefinition, ApprovalTemplate
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Project
from app.models.sales import (
    Customer,
    Lead,
    Opportunity,
    Quote,
    QuoteTemplate,
    QuoteTemplateVersion,
)
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:6].upper()}"


def _create_customer(client: TestClient, token: str) -> int:
    headers = _auth_headers(token)
    response = client.post(
        f"{settings.API_V1_PREFIX}/customers",
        headers=headers,
        json={
            "customer_code": _unique_code("CUST"),
            "customer_name": f"报价测试客户-{uuid4().hex[:4]}",
            "industry": "电子制造",
            "contact_person": "客户联系人",
            "contact_phone": "021-88888888",
        },
    )
    assert response.status_code in (200, 201), response.text
    data = response.json()
    customer = data.get("data", data)
    return customer["id"]


def _create_opportunity(client: TestClient, token: str) -> dict:
    headers = _auth_headers(token)
    customer_id = _create_customer(client, token)
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/opportunities",
        headers=headers,
        json={
            "customer_id": customer_id,
            "opportunity_name": f"报价测试商机-{uuid4().hex[:4]}",
            "stage": "QUALIFICATION",
            "expected_amount": 200000.0,
            "expected_close_date": (date.today() + timedelta(days=30)).isoformat(),
            "probability": 80,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_quote(client: TestClient, token: str) -> dict:
    """通过 API 创建一张带 V1 版本的报价，返回创建响应体。"""
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
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _ensure_quote_approval_template(db_session: Session, approver_id: int) -> None:
    template = (
        db_session.query(ApprovalTemplate)
        .filter(ApprovalTemplate.template_code == "SALES_QUOTE_APPROVAL")
        .first()
    )
    if not template:
        template = ApprovalTemplate(
            template_code="SALES_QUOTE_APPROVAL",
            template_name="销售报价审批",
            category="BUSINESS",
            entity_type="QUOTE",
            is_active=True,
            is_published=True,
            created_by=approver_id,
        )
        db_session.add(template)
        db_session.flush()
    else:
        template.is_active = True
        template.is_published = True

    flow = (
        db_session.query(ApprovalFlowDefinition)
        .filter(
            ApprovalFlowDefinition.template_id == template.id,
            ApprovalFlowDefinition.is_default,
            ApprovalFlowDefinition.is_active,
        )
        .first()
    )
    if not flow:
        flow = ApprovalFlowDefinition(
            template_id=template.id,
            flow_name="默认销售报价审批",
            is_default=True,
            is_active=True,
            created_by=approver_id,
        )
        db_session.add(flow)
        db_session.flush()

    node = (
        db_session.query(ApprovalNodeDefinition)
        .filter(
            ApprovalNodeDefinition.flow_id == flow.id,
            ApprovalNodeDefinition.node_code == "QUOTE_APPROVER",
        )
        .first()
    )
    if not node:
        node = ApprovalNodeDefinition(
            flow_id=flow.id,
            node_code="QUOTE_APPROVER",
            node_name="报价审批",
            node_order=1,
            node_type="APPROVAL",
            approver_type="FIXED_USER",
            approver_config={"user_ids": [approver_id]},
            is_active=True,
        )
        db_session.add(node)
    else:
        node.approver_config = {"user_ids": [approver_id]}
        node.is_active = True

    db_session.commit()


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

    def test_create_quote_presale_context_round_trips(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """从售前方案创建报价后，响应、详情和列表都应带回售前上下文。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-QCTX-{unique}",
            customer_name=f"报价上下文客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADQCTX{unique[:6]}",
            source="官网",
            customer_name=customer.customer_name,
            demand_summary="需要自动化测试线报价",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPQCTX{unique[:6]}",
            lead_id=lead.id,
            customer_id=customer.id,
            opp_name=f"报价上下文商机-{unique}",
            stage="QUOTE",
            probability=80,
            est_amount=Decimal("350000"),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(opportunity)
        db_session.flush()

        project = Project(
            project_code=f"PRJ-QCTX-{unique}",
            project_name=f"报价上下文项目-{unique}",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            lead_id=lead.id,
            opportunity_id=opportunity.id,
            is_active=True,
        )
        db_session.add(project)
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-QCTX-{unique}",
            title=f"报价上下文工单-{unique}",
            ticket_type="QUOTATION",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            lead_id=lead.id,
            opportunity_id=opportunity.id,
            project_id=project.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        solution = PresaleSolution(
            solution_no=f"SOL-QCTX-{unique}",
            name=f"报价上下文方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            technical_spec="双工位测试、扫码、MES 对接",
            estimated_cost=Decimal("210000"),
            suggested_price=Decimal("350000"),
            estimated_duration=45,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()

        quote_code = f"QCTX{unique[:8]}"
        created = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes",
            headers=headers,
            json={
                "quote_code": quote_code,
                "opportunity_id": opportunity.id,
                "customer_id": customer.id,
                "solution_id": solution.id,
                "presale_ticket_id": ticket.id,
                "valid_until": (date.today() + timedelta(days=30)).isoformat(),
                "version": {"version_no": "V1", "items": []},
            },
        )

        assert created.status_code == 201, created.text
        created_payload = created.json()
        assert created_payload["solution_id"] == solution.id
        assert created_payload["presale_solution_id"] == solution.id
        assert created_payload["presale_ticket_id"] == ticket.id
        assert created_payload["current_version"]["solution_id"] == solution.id
        assert created_payload["current_version"]["presale_ticket_id"] == ticket.id

        detail = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/{created_payload['id']}",
            headers=headers,
        )
        assert detail.status_code == 200, detail.text
        detail_payload = detail.json()["data"]
        assert detail_payload["lead_id"] == lead.id
        assert detail_payload["project_id"] == project.id
        assert detail_payload["solution_id"] == solution.id
        assert detail_payload["presale_solution_id"] == solution.id
        assert detail_payload["presale_ticket_id"] == ticket.id
        assert detail_payload["current_version"]["solution_id"] == solution.id
        assert detail_payload["current_version"]["presale_ticket_id"] == ticket.id

        listed = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes",
            headers=headers,
            params={"keyword": quote_code},
        )
        assert listed.status_code == 200, listed.text
        items = listed.json()["items"]
        assert len(items) == 1
        assert items[0]["lead_id"] == lead.id
        assert items[0]["project_id"] == project.id
        assert items[0]["solution_id"] == solution.id
        assert items[0]["presale_ticket_id"] == ticket.id
        assert items[0]["version"]["solution_id"] == solution.id
        assert items[0]["version"]["presale_ticket_id"] == ticket.id

    # ------------------------------------------------------------------
    # 回归测试：报价链路三处缺陷修复
    # ------------------------------------------------------------------
    def test_approve_does_not_bypass_approval_workflow(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """回归 #1：POST /quotes/{id}/approve 不应绕过权限/审批流。

        此前 quotes.py 里有一个无权限校验的“极简审批”实现，因 router 注册
        顺序在前会遮蔽 quote_per_id_approval.py 中带 quote:approve 权限的正式
        实现，使任意登录用户都能把未提交审批的报价直接改成 APPROVED。

        修复后该路径交由正式实现处理：没有待审批任务时返回 404，且报价状态
        保持不变（不会被静默改写为 APPROVED）。
        """
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        quote = _create_quote(client, admin_token)
        quote_id = quote["id"]

        before = db_session.query(Quote).filter(Quote.id == quote_id).one()
        assert before.status == "DRAFT"

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/approve",
            headers=headers,
            json={"comment": "尝试直接审批"},
        )

        # 未提交审批 -> 没有待办任务 -> 正式实现返回 404（旧的极简实现会返回 200）
        assert response.status_code == 404, response.text

        db_session.expire_all()
        after = db_session.query(Quote).filter(Quote.id == quote_id).one()
        assert after.status == "DRAFT", "报价状态不应被未经审批流的请求改写"

    def test_versions_compare_route_is_reachable(
        self, client: TestClient, admin_token: str
    ):
        """回归 #2：/quotes/{id}/versions/compare 应可达。

        此前 /versions/{version_id}（int）声明在 /versions/compare 之前，
        "compare" 会被当作 version_id 解析为 int 而返回 422，使对比接口不可达。
        修复后（version_id 使用整数路径转换器）compare 应正常返回 200，
        且数字版本详情路由仍然可用。
        """
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        quote = _create_quote(client, admin_token)
        quote_id = quote["id"]

        # 追加 V2 版本
        v2 = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/versions",
            headers=headers,
            json={
                "version_no": "V2",
                "items": [
                    {
                        "item_type": "SYSTEM",
                        "item_name": "自动化测试平台",
                        "qty": 1,
                        "unit_price": 160000.0,
                        "cost": 95000.0,
                        "lead_time_days": 50,
                    }
                ],
            },
        )
        assert v2.status_code == 200, v2.text

        versions = (
            client.get(
                f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/versions",
                headers=headers,
            )
            .json()["data"]["versions"]
        )
        version_ids = sorted(v["id"] for v in versions)
        assert len(version_ids) >= 2

        # 数字版本详情路由仍可用（确认 {version_id:int} 未破坏既有详情接口）
        detail = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/versions/{version_ids[0]}",
            headers=headers,
        )
        assert detail.status_code == 200, detail.text

        # 对比接口可达
        compare = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}/versions/compare",
            headers=headers,
            params={"version_id_1": version_ids[0], "version_id_2": version_ids[1]},
        )
        assert compare.status_code == 200, compare.text
        data = compare.json()["data"]
        assert "summary_diff" in data
        assert "item_diff" in data

    def test_delete_quote_blocked_for_committed_status(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """回归 #3：已成交（CONVERTED/ACCEPTED 等）报价不可删除。

        此前删除守卫误用了不存在的状态 "CONTRACTED"，导致 ACCEPTED/CONVERTED
        等已成交报价仍会被硬删除（级联删除版本与明细）。修复后这些状态应被拦截。
        """
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        quote = _create_quote(client, admin_token)
        quote_id = quote["id"]

        committed = db_session.query(Quote).filter(Quote.id == quote_id).one()
        committed.status = "CONVERTED"
        db_session.commit()

        response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}", headers=headers
        )
        assert response.status_code == 400, response.text

        # 报价仍然存在
        assert db_session.query(Quote).filter(Quote.id == quote_id).count() == 1

    def test_delete_quote_allowed_for_draft(
        self, client: TestClient, admin_token: str
    ):
        """草稿报价仍可正常删除（确认守卫未误伤可删除状态）。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        quote = _create_quote(client, admin_token)
        quote_id = quote["id"]

        response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote_id}", headers=headers
        )
        assert response.status_code in (200, 204), response.text

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

    def test_quote_approval_submit(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试提交报价单审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None
        _ensure_quote_approval_template(db_session, admin_user.id)
        quote = _create_quote(client, admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote['id']}/submit",
            headers=headers,
        )

        assert response.status_code in [200, 201], response.text

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
