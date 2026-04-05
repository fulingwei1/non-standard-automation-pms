# -*- coding: utf-8 -*-
"""Sales AI assistant service tests."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.sales_ai_assistant_service import SalesAIAssistantService


def _make_service():
    db = MagicMock()
    return SalesAIAssistantService(db), db


def test_recommend_scripts_fallback_when_ai_unavailable():
    service, db = _make_service()
    db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(service, "_generate_json", return_value=None):
        result = service.recommend_scripts(customer_id=1, opportunity_id=None, scenario_type="初次接触")

    assert result["customer_id"] == 1
    assert result["scenario"] == "初次接触"
    assert len(result["recommended_scripts"]) >= 1


def test_generate_proposal_prefers_ai_payload():
    service, db = _make_service()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    ai_payload = {
        "title": "AI技术方案",
        "generated_content": {
            "sections": [
                {"title": "1. 项目概述", "content": "AI生成内容"},
                {"title": "2. 技术方案", "content": "详细设计"},
            ]
        },
        "reference_projects": [{"name": "历史项目", "similarity": "88%"}],
    }

    with patch.object(service, "_generate_json", return_value=ai_payload):
        result = service.generate_proposal(opportunity_id=9, proposal_type="technical")

    assert result["title"] == "AI技术方案"
    assert result["generated_content"]["sections"][0]["content"] == "AI生成内容"
    assert result["reference_projects"][0]["name"] == "历史项目"


def test_predict_churn_risk_fallback_uses_customer_signals():
    service, db = _make_service()

    customer = SimpleNamespace(
        id=2,
        customer_name="测试客户",
        annual_revenue=0,
        last_follow_up_at=(datetime.now() - timedelta(days=50)).isoformat(),
        updated_at=datetime.now(),
    )
    opportunities = [
        SimpleNamespace(updated_at=datetime.now() - timedelta(days=40)),
    ]

    customer_query = MagicMock()
    customer_query.filter.return_value.first.return_value = customer

    opportunity_query = MagicMock()
    opportunity_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
        opportunities
    )

    db.query.side_effect = [customer_query, opportunity_query]

    with patch.object(service, "_generate_json", return_value=None):
        result = service.predict_churn_risk(customer_id=2)

    assert result["customer_id"] == 2
    assert result["customer_name"] == "测试客户"
    assert result["risk_level"] in {"MEDIUM", "HIGH"}
    assert len(result["risk_factors"]) >= 1


def test_get_churn_risk_list_contains_customer_name():
    service, db = _make_service()
    customers = [
        SimpleNamespace(
            id=1,
            customer_name="客户A",
            last_follow_up_at=None,
            updated_at=datetime.now(),
        ),
        SimpleNamespace(
            id=2,
            customer_name="客户B",
            last_follow_up_at=None,
            updated_at=datetime.now(),
        ),
    ]
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = customers

    result = service.get_churn_risk_list()

    assert result["total_count"] == 2
    assert result["risk_list"][0]["customer_name"] == "客户A"
