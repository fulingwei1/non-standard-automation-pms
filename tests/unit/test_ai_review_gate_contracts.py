# -*- coding: utf-8 -*-
"""AI 方案评审嵌入 G2 闸门契约（决策流改造第一处）。

此前 ai-solution-review 结果不落库、看完即丢，闸门无从消费。契约：
1. 评审结果持久化到 opportunity_requirements.extra_json（无需求行则创建）。
2. G2 校验：存在未处置的 HIGH 风险评审 → 拦截；人工处置（关键判断留痕）后放行；
   未做过评审不新增拦截（评审目前非强制，不破坏存量流程）。
3. 人工处置动作自动落 AI 反馈（评审被消费 = 采纳）。
"""
import uuid

from app.models.ai_feedback import AIOutputFeedback
from app.models.sales import Customer
from app.models.sales.leads import Opportunity, OpportunityRequirement
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


REVIEWS = [
    {"aspect": "节拍可达性", "risk_level": "HIGH", "finding": "15秒节拍下测试项超时", "suggestion": "并行测试工位"},
    {"aspect": "接口兼容", "risk_level": "MEDIUM", "finding": "MES 协议版本未确认", "suggestion": "向客户确认"},
]


def _seed_g2_ready_opportunity(db):
    user = _get_or_create_user(
        db,
        username=_unique("aigate").lower(),
        password="test123",
        real_name="闸门用户",
        department="销售部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="闸门客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db.add(customer)
    db.flush()
    opp = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="闸门商机",
        stage="REQUIREMENT",
        owner_id=user.id,
        budget_range="100-200万",
        decision_chain="采购部->总经理",
        delivery_window="2026Q4",
        acceptance_basis="GRR<10%",
        score=80,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return user, opp


def test_persist_solution_review_creates_requirement_row(db_session):
    from app.api.v1.endpoints.sales.utils.solution_review import (
        get_solution_review,
        persist_solution_review,
    )

    _, opp = _seed_g2_ready_opportunity(db_session)
    persist_solution_review(db_session, opp.id, REVIEWS)

    stored = get_solution_review(db_session, opp.id)
    assert stored is not None
    assert stored["high_risk"] == 1
    assert stored["resolved"] is False
    assert len(stored["reviews"]) == 2

    row = (
        db_session.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opp.id)
        .one()
    )
    assert "ai_solution_review" in (row.extra_json or "")


def test_g2_blocks_on_unresolved_high_risk_review(db_session):
    from app.api.v1.endpoints.sales.utils.gate_validation import (
        validate_g2_opportunity_to_quote,
    )
    from app.api.v1.endpoints.sales.utils.solution_review import persist_solution_review

    _, opp = _seed_g2_ready_opportunity(db_session)

    # 没做过评审：不新增拦截
    ok, errors = validate_g2_opportunity_to_quote(opp, db=db_session)
    assert ok, errors

    # 有未处置 HIGH 风险：拦截
    persist_solution_review(db_session, opp.id, REVIEWS)
    ok, errors = validate_g2_opportunity_to_quote(opp, db=db_session)
    assert not ok
    assert any("高风险" in e for e in errors)


def test_g2_passes_after_resolution_and_records_feedback(db_session):
    from app.api.v1.endpoints.sales.utils.gate_validation import (
        validate_g2_opportunity_to_quote,
    )
    from app.api.v1.endpoints.sales.utils.solution_review import (
        persist_solution_review,
        resolve_solution_review,
    )

    user, opp = _seed_g2_ready_opportunity(db_session)
    persist_solution_review(db_session, opp.id, REVIEWS)

    resolve_solution_review(
        db_session, opp.id, action="ACCEPT_RISK", note="客户接受并行工位方案，带险推进", user_id=user.id
    )

    ok, errors = validate_g2_opportunity_to_quote(opp, db=db_session)
    assert ok, errors

    feedback = (
        db_session.query(AIOutputFeedback)
        .filter(
            AIOutputFeedback.feature_key == "opportunity_solution_review",
            AIOutputFeedback.ref_id == opp.id,
        )
        .first()
    )
    assert feedback is not None, "评审处置未落 AI 反馈"


def test_resolve_requires_note(db_session):
    import pytest

    from app.api.v1.endpoints.sales.utils.solution_review import (
        persist_solution_review,
        resolve_solution_review,
    )

    user, opp = _seed_g2_ready_opportunity(db_session)
    persist_solution_review(db_session, opp.id, REVIEWS)

    with pytest.raises(ValueError):
        resolve_solution_review(db_session, opp.id, action="ACCEPT_RISK", note="", user_id=user.id)
    with pytest.raises(ValueError):
        resolve_solution_review(db_session, opp.id, action="WHATEVER", note="x", user_id=user.id)
