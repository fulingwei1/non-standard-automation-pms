# -*- coding: utf-8 -*-
"""SALES-16 契约：AI 销售助手降级必须显式标注，不得冒充 AI 输出。

1. AI 不可用时的罐头/规则内容必须带 ai_generated=False + degraded=True + 原因。
2. 真 AI 输出标 ai_generated=True。
3. 流失清单是规则批量扫描（设计如此），必须标 scoring_method 与每项 analysis_source，
   不得让规则分静默冒充 AI 分析。
"""
import uuid
from unittest.mock import patch

from app.models.sales import Customer
from app.services.sales_ai_assistant_service import SalesAIAssistantService
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_customer(db):
    user = _get_or_create_user(
        db,
        username=_unique("s16").lower(),
        password="test123",
        real_name="降级标注用户",
        department="销售部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="降级标注客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def test_churn_fallback_is_marked_degraded(db_session):
    customer = _seed_customer(db_session)
    service = SalesAIAssistantService(db_session)

    with patch.object(service, "_generate_json", return_value=None):
        result = service.predict_churn_risk(customer.id)

    assert result["ai_generated"] is False, "降级结果不得冒充 AI 输出"
    assert result["degraded"] is True
    assert result.get("degraded_reason"), "必须说明降级原因"


def test_churn_live_ai_is_marked_generated(db_session):
    customer = _seed_customer(db_session)
    service = SalesAIAssistantService(db_session)

    payload = {
        "risk_score": 66,
        "risk_level": "MEDIUM",
        "risk_factors": [],
        "recommended_actions": ["安排回访"],
        "analysis_summary": "近期互动下降",
    }
    with patch.object(service, "_generate_json", return_value=payload):
        result = service.predict_churn_risk(customer.id)

    assert result["ai_generated"] is True
    assert not result.get("degraded")


def test_scripts_fallback_is_marked_degraded(db_session):
    customer = _seed_customer(db_session)
    service = SalesAIAssistantService(db_session)

    with patch.object(service, "_generate_json", return_value=None):
        result = service.recommend_scripts(
            customer_id=customer.id, opportunity_id=None, scenario_type="first_visit"
        )

    assert result["ai_generated"] is False
    assert result["degraded"] is True


def test_churn_list_is_honest_rule_scan(db_session):
    _seed_customer(db_session)
    service = SalesAIAssistantService(db_session)

    result = service.get_churn_risk_list()

    assert result["scoring_method"] == "rule_scan", "清单必须声明是规则扫描"
    assert result.get("ai_generated") is False
    assert result["risk_list"], "清单不应为空"
    assert all(item.get("analysis_source") == "rule" for item in result["risk_list"])
