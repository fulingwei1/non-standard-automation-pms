# -*- coding: utf-8 -*-
"""SALES-11 契约：线索转商机不得丢字段。

线索侧已录的需求详情（LeadRequirementDetail，G1 模板的数据源）在转商机时
必须承接到商机与商机需求表：被测对象/节拍/接口协议/验收依据/安全要求/需求成熟度。
显式传入的 requirement_data 优先，承接只补空位。
"""
import uuid
from decimal import Decimal

from app.models.sales import Customer, Lead
from app.models.sales.leads import Opportunity, OpportunityRequirement
from app.models.sales.technical_assessment import LeadRequirementDetail
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_lead_with_detail(db):
    user = _get_or_create_user(
        db,
        username=_unique("lcv").lower(),
        password="test123",
        real_name="转化用户",
        department="销售部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="承接客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db.add(customer)
    db.flush()
    lead = Lead(
        lead_code=_unique("LD"),
        customer_name="承接客户",
        contact_name="张工",
        contact_phone="13800000000",
        demand_summary="整机FCT功能测试线",
        owner_id=user.id,
        status="FOLLOWING",
    )
    db.add(lead)
    db.flush()
    detail = LeadRequirementDetail(
        lead_id=lead.id,
        target_object_type="家电整机FCT",
        cycle_time_seconds=Decimal("15"),
        communication_protocols='["MES", "RS232"]',
        acceptance_basis="GRR<10%；节拍15秒",
        acceptance_method="现场验收",
        safety_requirements='{"level": "PL-d"}',
        requirement_maturity=4,
        environment='{"温度": "常温"}',
    )
    db.add(detail)
    db.flush()
    lead.requirement_detail_id = detail.id
    db.commit()
    return user, customer, lead


def test_convert_carries_over_requirement_detail(db_session):
    from app.api.v1.endpoints.sales.leads.actions import convert_lead_to_opportunity

    user, customer, lead = _seed_lead_with_detail(db_session)

    result = convert_lead_to_opportunity(
        db=db_session,
        lead_id=lead.id,
        customer_id=customer.id,
        requirement_data=None,
        skip_validation=True,
        current_user=user,
    )
    opp_id = result["id"] if isinstance(result, dict) else result.id

    opp = db_session.get(Opportunity, opp_id)
    assert opp.requirement_maturity == 4, "需求成熟度未承接"
    assert "GRR" in (opp.acceptance_basis or ""), "验收依据未承接到商机"

    req = (
        db_session.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opp_id)
        .first()
    )
    assert req is not None, "转商机未创建需求行（线索需求详情被丢弃）"
    assert req.product_object == "家电整机FCT"
    assert req.ct_seconds == 15
    assert "MES" in (req.interface_desc or ""), "接口协议未承接"
    assert "GRR" in (req.acceptance_criteria or "")
    assert "PL-d" in (req.safety_requirement or "")


def test_convert_explicit_requirement_wins_over_carryover(db_session):
    from app.api.v1.endpoints.sales.leads.actions import convert_lead_to_opportunity

    user, customer, lead = _seed_lead_with_detail(db_session)

    result = convert_lead_to_opportunity(
        db=db_session,
        lead_id=lead.id,
        customer_id=customer.id,
        requirement_data={"product_object": "人工指定对象", "ct_seconds": 20},
        skip_validation=True,
        current_user=user,
    )
    opp_id = result["id"] if isinstance(result, dict) else result.id

    req = (
        db_session.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opp_id)
        .first()
    )
    assert req.product_object == "人工指定对象", "显式传入必须优先于承接"
    assert req.ct_seconds == 20
    assert "MES" in (req.interface_desc or ""), "空位仍应由承接补齐"
