# -*- coding: utf-8 -*-
"""PRE-08/PRE-09: sales opportunity AI endpoints must reject mock fallbacks."""

import uuid
from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.api.v1.endpoints.sales.opportunity_workflow import (
    ai_enrich_requirement,
    ai_quote_estimate,
)
from app.models.sales import Customer, Opportunity, OpportunityRequirement
from app.models.user import User


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_opportunity(db_session) -> tuple[Opportunity, User]:
    user = User(
        username=_unique("pre08").lower(),
        password_hash="test",
        real_name="PRE08测试用户",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="PRE08测试客户",
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=_unique("OPP"),
        opp_name="FCT测试工作站商机",
        customer_id=customer.id,
        equipment_type="FCT测试",
        budget_range="100-150万",
        requirement_maturity=3,
    )
    db_session.add(opportunity)
    db_session.flush()

    db_session.execute(
        text(
            """
            INSERT INTO customer_communications(
                communication_no, communication_type, customer_name,
                communication_date, topic, subject, content,
                customer_id, opportunity_id, created_by, created_by_name, created_at, updated_at
            )
            VALUES(:no, 'MEETING', :customer_name, :communication_date,
                   '需求澄清', '需求澄清', :content, :customer_id, :opportunity_id,
                   :created_by, :created_by_name,
                   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "no": _unique("COMM"),
            "customer_name": customer.customer_name,
            "communication_date": date.today().isoformat(),
            "content": "客户需要FCT测试工作站，节拍12秒，MES接口，GRR<10%。",
            "customer_id": customer.id,
            "opportunity_id": opportunity.id,
            "created_by": user.id,
            "created_by_name": user.real_name,
        },
    )
    db_session.commit()
    return opportunity, user


def _ensure_standard_module_table(db_session):
    db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ai_standard_modules(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT,
                category TEXT,
                ref_cost NUMERIC,
                description TEXT,
                source_count INTEGER DEFAULT 1
            )
            """
        )
    )
    db_session.execute(
        text(
            """
            INSERT INTO ai_standard_modules(module_name, category, ref_cost, description, source_count)
            VALUES('FCT测试主机', '检测设备', 120000, 'FCT测试核心模块', 5)
            """
        )
    )
    db_session.commit()


def test_ai_quote_estimate_rejects_mock_response(db_session):
    opportunity, user = _seed_opportunity(db_session)
    _ensure_standard_module_table(db_session)

    with patch(
        "app.services.ai_client_service.AIClientService.generate_solution",
        return_value={
            "content": '{"recommended_modules":[],"suggested_price":999}',
            "model": "qwen3-coder-plus-mock",
            "usage": {},
        },
    ):
        with pytest.raises(HTTPException) as exc:
            ai_quote_estimate(db=db_session, opp_id=opportunity.id, current_user=user)

    assert exc.value.status_code == 502
    assert "AI" in str(exc.value.detail)


def test_ai_enrich_requirement_rejects_mock_and_preserves_existing_requirement(db_session):
    opportunity, user = _seed_opportunity(db_session)
    requirement = OpportunityRequirement(
        opportunity_id=opportunity.id,
        product_object="人工录入产品",
        ct_seconds=12,
        interface_desc="MES/PLC人工接口",
        site_constraints="人工录入现场限制",
        acceptance_criteria="人工录入验收标准",
        safety_requirement="人工录入安全要求",
    )
    db_session.add(requirement)
    db_session.commit()

    with patch(
        "app.services.ai_client_service.AIClientService.generate_solution",
        return_value={
            "content": (
                '{"product_object":"","equipment_type":"","ct_seconds":null,'
                '"interface_desc":"","site_constraints":"","acceptance_criteria":"",'
                '"safety_requirement":"","budget":"","delivery_window":"",'
                '"key_demands":[],"competitors":[],"requirement_maturity":"LOW"}'
            ),
            "model": "qwen3-coder-plus-mock",
            "usage": {},
        },
    ):
        with pytest.raises(HTTPException) as exc:
            ai_enrich_requirement(db=db_session, opp_id=opportunity.id, current_user=user)

    assert exc.value.status_code == 502
    db_session.refresh(requirement)
    db_session.refresh(opportunity)
    assert requirement.product_object == "人工录入产品"
    assert requirement.ct_seconds == 12
    assert requirement.interface_desc == "MES/PLC人工接口"
    assert requirement.site_constraints == "人工录入现场限制"
    assert requirement.acceptance_criteria == "人工录入验收标准"
    assert requirement.safety_requirement == "人工录入安全要求"
    assert opportunity.requirement_maturity == 3


def test_ai_enrich_requirement_merges_only_non_empty_fields(db_session):
    opportunity, user = _seed_opportunity(db_session)
    requirement = OpportunityRequirement(
        opportunity_id=opportunity.id,
        product_object="人工录入产品",
        ct_seconds=12,
        interface_desc="MES/PLC人工接口",
        site_constraints="人工录入现场限制",
        acceptance_criteria="人工录入验收标准",
        safety_requirement="人工录入安全要求",
    )
    db_session.add(requirement)
    db_session.commit()

    with patch(
        "app.services.ai_client_service.AIClientService.generate_solution",
        return_value={
            "content": (
                '{"product_object":"","equipment_type":"视觉检测",'
                '"ct_seconds":null,"interface_desc":"EtherCAT/MES",'
                '"site_constraints":"","acceptance_criteria":"",'
                '"safety_requirement":"","budget":"","delivery_window":"",'
                '"key_demands":["追溯"],"competitors":[],"requirement_maturity":"HIGH"}'
            ),
            "model": "qwen3-coder-plus",
            "usage": {},
        },
    ):
        response = ai_enrich_requirement(
            db=db_session,
            opp_id=opportunity.id,
            current_user=user,
        )

    db_session.refresh(requirement)
    db_session.refresh(opportunity)
    assert response.code == 200
    assert requirement.product_object == "人工录入产品"
    assert requirement.ct_seconds == 12
    assert requirement.interface_desc == "EtherCAT/MES"
    assert requirement.site_constraints == "人工录入现场限制"
    assert requirement.acceptance_criteria == "人工录入验收标准"
    assert requirement.safety_requirement == "人工录入安全要求"
    assert opportunity.equipment_type == "视觉检测"
    assert opportunity.requirement_maturity == 4
