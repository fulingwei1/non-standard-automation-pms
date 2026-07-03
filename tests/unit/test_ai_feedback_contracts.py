# -*- coding: utf-8 -*-
"""AI 产出反馈闭环契约（结果反馈环节 0→1）。

所有 AI 产出必须能记录人工采纳/驳回结论并可统计采纳率：
1. record：verdict 只认 ADOPTED/REJECTED/PARTIAL；同一产出多次反馈，统计取最新。
2. stats：按 feature_key 汇总 total/adopted/rejected/partial/adoption_rate。
3. PRE-10 确认动作自动写入 ADOPTED 反馈——确认即采纳，第一处业务接线。
"""
import uuid

import pytest

from app.models.ai_feedback import AIOutputFeedback
from app.services import ai_feedback_service
from tests.conftest import _get_or_create_user


def _user(db):
    return _get_or_create_user(
        db,
        username=f"aifb-{uuid.uuid4().hex[:8]}",
        password="test123",
        real_name="AI反馈用户",
        department="售前部",
    )


def test_record_validates_verdict(db_session):
    user = _user(db_session)
    with pytest.raises(ValueError):
        ai_feedback_service.record(
            db_session,
            feature_key="three_tier_quotation",
            verdict="MAYBE",
            user_id=user.id,
        )


def test_record_and_stats_latest_per_ref(db_session):
    """同一产出先驳回后采纳：统计只按最新一条计，采纳率不被历史双计。"""
    user = _user(db_session)
    ai_feedback_service.record(
        db_session,
        feature_key="three_tier_quotation",
        verdict="REJECTED",
        ref_type="quotation",
        ref_id=101,
        reason="价格档位不合理",
        user_id=user.id,
    )
    ai_feedback_service.record(
        db_session,
        feature_key="three_tier_quotation",
        verdict="ADOPTED",
        ref_type="quotation",
        ref_id=101,
        reason="调整后采纳",
        user_id=user.id,
    )
    ai_feedback_service.record(
        db_session,
        feature_key="three_tier_quotation",
        verdict="REJECTED",
        ref_type="quotation",
        ref_id=102,
        user_id=user.id,
    )

    stats = ai_feedback_service.stats(db_session)
    row = next(s for s in stats if s["feature_key"] == "three_tier_quotation")
    assert row["total"] == 2, "同一产出多次反馈必须按最新去重"
    assert row["adopted"] == 1
    assert row["rejected"] == 1
    assert row["adoption_rate"] == 0.5


def test_confirm_analysis_records_adopted_feedback(db_session):
    """PRE-10 确认动作 = 人工采纳，必须自动落一条 ADOPTED 反馈。"""
    from app.models.presale.core import PresaleSupportTicket
    from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
    from app.services.presale import requirement_analysis_bridge as bridge

    user = _user(db_session)
    ticket = PresaleSupportTicket(
        ticket_no=f"PST-{uuid.uuid4().hex[:8].upper()}",
        title="反馈闭环工单",
        ticket_type="SOLUTION",
        applicant_id=user.id,
    )
    db_session.add(ticket)
    db_session.flush()
    analysis = PresaleAIRequirementAnalysis(
        presale_ticket_id=ticket.id,
        raw_requirement="视觉检测系统需求",
        status="draft",
        created_by=user.id,
    )
    db_session.add(analysis)
    db_session.commit()

    bridge.confirm_and_backfill(db_session, analysis.id, user.id)

    feedback = (
        db_session.query(AIOutputFeedback)
        .filter(
            AIOutputFeedback.feature_key == "presale_requirement_analysis",
            AIOutputFeedback.ref_id == analysis.id,
        )
        .order_by(AIOutputFeedback.id.desc())
        .first()
    )
    assert feedback is not None, "确认分析未自动记录采纳反馈"
    assert feedback.verdict == "ADOPTED"
    assert feedback.created_by == user.id


def test_feedback_router_registered():
    import inspect

    import app.api.v1.api as api_module

    source = inspect.getsource(api_module)
    assert "ai_feedback" in source, "ai_feedback 路由未挂载到 api_router"
