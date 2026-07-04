# -*- coding: utf-8 -*-
"""APPR-19: quote approval routing must keep large quotes on the GM path."""

from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.user import User
from app.services.approval_engine import ApprovalEngineService
from app.services.approval_engine.adapters import quote as quote_adapter_module
from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
from app.services.approval_engine.router import ApprovalRouterService
from app.utils.init_approval_data import init_approval_workflow_seeds


def _user(db: Session, username: str) -> User:
    user = User(
        username=username,
        password_hash="x",
        real_name=username,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_quote_seed_routes_500k_quote_to_gm_flow(db_session: Session):
    admin = _user(db_session, "admin")
    db_session.commit()

    init_approval_workflow_seeds(db_session)

    template = (
        db_session.query(ApprovalTemplate)
        .filter(ApprovalTemplate.template_code == "SALES_QUOTE_APPROVAL")
        .one()
    )
    router = ApprovalRouterService(db_session)

    flow = router.select_flow(
        template.id,
        {
            "form_data": {"total_price": 500000, "gross_margin": 0.2},
            "initiator": {"id": admin.id},
        },
    )

    assert flow.flow_name == "低毛利报价审批"
    assert any("总经理" in node.node_name for node in flow.nodes)


def test_quote_adapter_uses_unified_quote_template_and_quote_id(monkeypatch):
    db = MagicMock()
    adapter = QuoteApprovalAdapter(db)
    quote_version = MagicMock()
    quote_version.id = 7
    quote_version.quote_id = 42
    quote_version.quote_code = "Q-APPR19"
    quote_version.quote_total = Decimal("600000")
    quote_version.margin_percent = Decimal("18")
    quote_version.status = "DRAFT"
    quote_version.approval_instance_id = None

    instance = MagicMock()
    instance.id = 99
    instance.status = "PENDING"
    engine = MagicMock()
    engine.submit.return_value = instance
    engine_cls = MagicMock(return_value=engine)
    monkeypatch.setattr(quote_adapter_module, "ApprovalEngineService", engine_cls)

    result = adapter.submit_for_approval(quote_version, initiator_id=5)

    assert result is instance
    call = engine.submit.call_args.kwargs
    assert call["template_code"] == "SALES_QUOTE_APPROVAL"
    assert call["entity_type"] == "QUOTE"
    assert call["entity_id"] == quote_version.quote_id
    assert call["form_data"]["total_price"] == 600000.0
    assert call["form_data"]["gross_margin"] == 18.0


def test_advancing_condition_branch_uses_adapter_entity_data(db_session: Session, monkeypatch):
    approver = _user(db_session, "appr19_approver")
    template = ApprovalTemplate(
        template_code="APPR19_CONDITION",
        template_name="APPR19 条件流程",
        category="BUSINESS",
        entity_type="QUOTE",
        is_active=True,
        is_published=True,
    )
    db_session.add(template)
    db_session.flush()
    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name="APPR19 条件分支",
        is_default=True,
        is_active=True,
    )
    db_session.add(flow)
    db_session.flush()
    first = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code="FIRST",
        node_name="初审",
        node_order=1,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [approver.id]},
        is_active=True,
    )
    condition = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code="ROUTE",
        node_name="金额分支",
        node_order=2,
        node_type="CONDITION",
        is_active=True,
    )
    high = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code="GM",
        node_name="总经理审批",
        node_order=3,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [approver.id]},
        is_active=True,
    )
    low = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code="SALES",
        node_name="销售经理审批",
        node_order=4,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [approver.id]},
        is_active=True,
    )
    db_session.add_all([first, condition, high, low])
    db_session.flush()
    condition.approver_config = {
        "branches": [
            {
                "conditions": {
                    "operator": "AND",
                    "items": [{"field": "entity.total_price", "op": ">=", "value": 500000}],
                },
                "target_node_id": high.id,
            }
        ],
        "default_node_id": low.id,
    }

    instance = ApprovalInstance(
        instance_no="APPR19-1",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="QUOTE",
        entity_id=123,
        initiator_id=approver.id,
        form_data={},
        status="PENDING",
        current_node_id=first.id,
        title="APPR19 大额报价",
    )
    db_session.add(instance)
    db_session.flush()
    task = ApprovalTask(
        instance_id=instance.id,
        node_id=first.id,
        assignee_id=approver.id,
        status="COMPLETED",
        task_type="APPROVAL",
    )
    db_session.add(task)
    db_session.commit()

    fake_adapter = MagicMock()
    fake_adapter.get_entity_data.return_value = {"total_price": 600000}
    monkeypatch.setattr(
        "app.services.approval_engine.adapters.get_adapter",
        lambda entity_type, db: fake_adapter,
    )

    engine = ApprovalEngineService(db_session)
    monkeypatch.setattr(engine, "_create_node_tasks", lambda *_args, **_kwargs: None)

    engine._advance_to_next_node(instance, task)

    assert instance.current_node_id == high.id
