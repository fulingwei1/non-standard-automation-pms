# -*- coding: utf-8 -*-
"""
P0-5 / APPR-03: 会签驳回后，REJECTED 实例不能被剩余待办翻回 APPROVED。
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base

pytestmark = pytest.mark.audit_p0


def _create_test_engine():
    """创建只服务本用例的 SQLite 内存库，避免触碰 data/app.db。"""
    import app.models  # noqa: F401

    for stub in ["production_work_orders", "suppliers"]:
        if stub not in Base.metadata.tables:
            Table(stub, Base.metadata, Column("id", Integer, primary_key=True))

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=engine, checkfirst=True)
        except Exception:
            pass
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            try:
                index.create(bind=engine, checkfirst=True)
            except Exception:
                pass
    return engine


@pytest.fixture()
def db():
    engine = _create_test_engine()
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class _NoopNotify:
    def notify_pending(self, *args, **kwargs):
        return None

    def notify_approved(self, *args, **kwargs):
        return None

    def notify_rejected(self, *args, **kwargs):
        return None


def _make_user(db, username: str, real_name: str):
    from app.models.user import User

    user = User(
        username=username,
        password_hash="test",
        real_name=real_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _make_instance_with_node(db, *, approval_mode: str, approver_ids: list[int]):
    from app.models.approval import (
        ApprovalFlowDefinition,
        ApprovalInstance,
        ApprovalNodeDefinition,
        ApprovalTemplate,
    )

    initiator = _make_user(db, f"initiator_{uuid4().hex[:8]}", "发起人")
    template = ApprovalTemplate(
        template_code=f"APPR03_{uuid4().hex[:8]}",
        template_name="APPR-03 测试模板",
        category="TEST",
        entity_type="TEST",
        version=1,
        is_published=True,
        published_at=datetime.now(),
        published_by=initiator.id,
        is_active=True,
        created_by=initiator.id,
    )
    db.add(template)
    db.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name="APPR-03 测试流程",
        is_default=True,
        version=1,
        is_active=True,
        created_by=initiator.id,
    )
    db.add(flow)
    db.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code="COSIGN",
        node_name="会签节点",
        node_type="APPROVAL",
        node_order=1,
        approval_mode=approval_mode,
        approver_type="FIXED_USER",
        approver_config={"user_ids": approver_ids, "pass_rule": "ALL"},
        is_active=True,
        can_reject_to="START",
    )
    db.add(node)
    db.flush()

    instance = ApprovalInstance(
        instance_no=f"AP{uuid4().hex[:12].upper()}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="TEST",
        entity_id=1,
        initiator_id=initiator.id,
        initiator_name=initiator.real_name,
        form_data={"title": "APPR-03"},
        status="PENDING",
        current_node_id=node.id,
        current_node_order=node.node_order,
        urgency="NORMAL",
        title="APPR-03",
        summary="终态防复活",
        submitted_at=datetime.now(),
    )
    db.add(instance)
    db.flush()
    return instance, node


def _make_engine(db):
    from app.services.approval_engine.engine import ApprovalEngineService

    engine = ApprovalEngineService(db)
    engine.notify = _NoopNotify()
    return engine


def test_cosign_reject_uses_aggregate_result_and_cannot_flip_to_approved(db):
    approver_a = _make_user(db, "appr03_a", "会签人A")
    approver_b = _make_user(db, "appr03_b", "会签人B")
    instance, node = _make_instance_with_node(
        db,
        approval_mode="AND_SIGN",
        approver_ids=[approver_a.id, approver_b.id],
    )
    engine = _make_engine(db)
    tasks = engine.executor.create_tasks_for_node(instance, node, [approver_a.id, approver_b.id])
    db.commit()

    task_a, task_b = tasks
    engine.reject(task_a.id, approver_a.id, comment="不同意", reject_to="START")

    db.refresh(instance)
    db.refresh(task_b)
    assert instance.status == "PENDING"
    assert task_b.status == "PENDING"

    engine.approve(task_b.id, approver_b.id, comment="同意")

    db.refresh(instance)
    assert instance.status == "REJECTED"


def test_or_sign_reject_waits_for_other_approvers(db):
    approver_a = _make_user(db, "appr03_or_a", "或签人A")
    approver_b = _make_user(db, "appr03_or_b", "或签人B")
    instance, node = _make_instance_with_node(
        db,
        approval_mode="OR_SIGN",
        approver_ids=[approver_a.id, approver_b.id],
    )
    engine = _make_engine(db)
    tasks = engine.executor.create_tasks_for_node(instance, node, [approver_a.id, approver_b.id])
    db.commit()

    task_a, task_b = tasks
    engine.reject(task_a.id, approver_a.id, comment="不同意", reject_to="START")

    db.refresh(instance)
    db.refresh(task_b)
    assert instance.status == "PENDING"
    assert task_b.status == "PENDING"

    engine.approve(task_b.id, approver_b.id, comment="另一位同意")

    db.refresh(instance)
    assert instance.status == "APPROVED"


def test_terminal_rejected_instance_cannot_be_reapproved_by_pending_task(db):
    approver = _make_user(db, "appr03_terminal", "终态审批人")
    instance, node = _make_instance_with_node(
        db,
        approval_mode="SINGLE",
        approver_ids=[approver.id],
    )
    engine = _make_engine(db)
    [task] = engine.executor.create_tasks_for_node(instance, node, [approver.id])
    instance.status = "REJECTED"
    instance.completed_at = datetime.now()
    db.commit()

    with pytest.raises(ValueError, match="审批实例已结束|任务状态不正确"):
        engine.approve(task.id, approver.id, comment="迟到的同意")

    db.refresh(instance)
    db.refresh(task)
    assert instance.status == "REJECTED"
    assert task.status == "PENDING"
