# -*- coding: utf-8 -*-
"""AS-22: fault diagnosis AI must use service history and label degradation."""

from datetime import datetime

from app.api.v1.endpoints import ai_engineering
from app.models.project import Customer, Project
from app.models.service import KnowledgeBase, ServiceTicket
from app.models.service.enums import KnowledgeBaseStatusEnum, ServiceTicketStatusEnum
from app.models.user import User


def _seed_user_project(db_session):
    user = User(
        username="as22-admin",
        password_hash="x",
        real_name="AS22 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS22-CUST", customer_name="AS22 客户")
    db_session.add_all([user, customer])
    db_session.flush()
    project = Project(
        project_code="AS22-PROJ",
        project_name="AS22 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.flush()
    return user, customer, project


def test_fault_diagnosis_prompt_includes_service_history_and_knowledge(
    db_session,
    monkeypatch,
):
    user, customer, project = _seed_user_project(db_session)
    db_session.add(
        ServiceTicket(
            ticket_no="AS22-TICKET",
            project_id=project.id,
            customer_id=customer.id,
            problem_type="ELECTRICAL",
            problem_desc="伺服报警 E01，回零失败",
            urgency="HIGH",
            reported_by=str(user.id),
            reported_time=datetime(2026, 7, 1, 10, 0),
            status=ServiceTicketStatusEnum.CLOSED.value,
            solution="更换编码器线后恢复",
            root_cause="编码器线接触不良",
        )
    )
    db_session.add(
        KnowledgeBase(
            article_no="AS22-KB",
            title="伺服报警 E01 排查",
            category="故障诊断",
            content="先查编码器线，再查驱动器报警码。",
            status=KnowledgeBaseStatusEnum.PUBLISHED.value,
            author_id=user.id,
            author_name=user.real_name,
        )
    )
    db_session.commit()

    captured = {}

    def fake_ai(prompt: str, max_tokens: int = 1600):
        captured["prompt"] = prompt
        return {
            "possible_causes": [{"cause": "编码器线松动", "likelihood": "高", "check": "检查线缆"}],
            "steps": ["断电检查编码器线"],
            "safety": "断电后操作",
        }

    monkeypatch.setattr(ai_engineering, "_ai", fake_ai)

    result = ai_engineering.fault_diagnosis(
        ai_engineering.FaultReq(symptom="伺服报警 E01", equipment_type="FCT"),
        db=db_session,
        current_user=user,
    )

    assert "历史服务工单" in captured["prompt"]
    assert "AS22-TICKET" in captured["prompt"]
    assert "更换编码器线后恢复" in captured["prompt"]
    assert "服务知识库" in captured["prompt"]
    assert "伺服报警 E01 排查" in captured["prompt"]
    assert result.data["context_sources"]["service_tickets"] == 1
    assert result.data["context_sources"]["knowledge_base"] == 1
    assert result.data["ai_generated"] is True
    assert result.data["degraded"] is False


def test_fault_diagnosis_labels_rule_fallback_when_ai_fails(
    db_session,
    monkeypatch,
):
    user, _customer, _project = _seed_user_project(db_session)
    db_session.commit()
    monkeypatch.setattr(ai_engineering, "_ai", lambda *args, **kwargs: {})

    result = ai_engineering.fault_diagnosis(
        ai_engineering.FaultReq(symptom="PLC 无输出", equipment_type="ICT"),
        db=db_session,
        current_user=user,
    )

    assert result.code == 200
    assert result.data["ai_generated"] is False
    assert result.data["degraded"] is True
    assert result.data["degraded_reason"] == "AI_DIAGNOSIS_UNAVAILABLE"
    assert result.data["possible_causes"]
    assert result.data["steps"]
