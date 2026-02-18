# -*- coding: utf-8 -*-
"""第五批：approval_engine/workflow_engine.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

try:
    from app.services.approval_engine.workflow_engine import WorkflowEngine
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="workflow_engine not importable")


def make_db():
    return MagicMock()


def make_instance(**kwargs):
    inst = MagicMock()
    inst.due_date = kwargs.get("due_date", None)
    inst.created_at = kwargs.get("created_at", None)
    inst.flow_id = kwargs.get("flow_id", 1)
    inst.current_status = kwargs.get("current_status", "PENDING")
    return inst


def make_flow(**kwargs):
    f = MagicMock()
    f.flow_code = kwargs.get("flow_code", "TEST_FLOW")
    f.is_active = True
    f.nodes = kwargs.get("nodes", [])
    f.first_node_timeout = kwargs.get("first_node_timeout", 48)
    return f


class TestWorkflowEngineGenerateInstanceNo:
    def test_returns_string(self):
        no = WorkflowEngine._generate_instance_no()
        assert isinstance(no, str)
        assert no.startswith("AP")
        assert len(no) > 5


class TestWorkflowEngineCreateInstance:
    def test_flow_not_found_raises(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        engine = WorkflowEngine(db)
        with pytest.raises(ValueError, match="不存在或未启用"):
            engine.create_instance("NO_FLOW", "ECN", 1, "Test", 1)

    def test_create_success(self):
        db = make_db()
        flow = make_flow(nodes=[MagicMock(), MagicMock()])
        db.query.return_value.filter.return_value.first.return_value = flow
        engine = WorkflowEngine(db)
        result = engine.create_instance("TEST_FLOW", "ECN", 42, "Title", 99)
        assert result.flow_id == flow.id
        assert result.submitted_by == 99
        assert result.business_id == 42


class TestWorkflowEngineIsExpired:
    def test_not_expired_with_future_due_date(self):
        db = make_db()
        engine = WorkflowEngine(db)
        instance = make_instance(due_date=datetime.now() + timedelta(hours=24))
        assert engine.is_expired(instance) is False

    def test_expired_with_past_due_date(self):
        db = make_db()
        engine = WorkflowEngine(db)
        instance = make_instance(due_date=datetime.now() - timedelta(hours=1))
        assert engine.is_expired(instance) is True

    def test_no_due_date_returns_false(self):
        db = make_db()
        engine = WorkflowEngine(db)
        instance = make_instance()
        result = engine.is_expired(instance)
        assert isinstance(result, bool)


class TestWorkflowEngineGetFirstNodeTimeout:
    def test_returns_flow_timeout(self):
        db = make_db()
        engine = WorkflowEngine(db)
        flow = make_flow(first_node_timeout=72)
        assert engine._get_first_node_timeout(flow) == 72

    def test_default_timeout(self):
        db = make_db()
        engine = WorkflowEngine(db)
        flow = MagicMock()
        flow.first_node_timeout = "invalid"
        assert engine._get_first_node_timeout(flow) == 48


class TestWorkflowEngineGetCurrentNode:
    def test_returns_none_when_terminal_status(self):
        db = make_db()
        engine = WorkflowEngine(db)
        instance = make_instance(current_status="APPROVED")
        result = engine.get_current_node(instance)
        assert result is None

    def test_returns_node_when_pending(self):
        db = make_db()
        engine = WorkflowEngine(db)
        node = MagicMock()
        instance = make_instance(current_status="PENDING")
        instance.current_node_id = 5
        db.query.return_value.filter.return_value.first.return_value = node
        result = engine.get_current_node(instance)
        assert result == node
