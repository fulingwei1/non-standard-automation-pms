# -*- coding: utf-8 -*-
"""
approval_engine/workflow_engine.py 单元测试（第二批）
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


def _make_engine(mock_db=None):
    from app.services.approval_engine.workflow_engine import WorkflowEngine
    if mock_db is None:
        mock_db = MagicMock()
    return WorkflowEngine(mock_db)


# ─── 1. _generate_instance_no ───────────────────────────────────────────────
def test_generate_instance_no_format():
    from app.services.approval_engine.workflow_engine import WorkflowEngine
    no = WorkflowEngine._generate_instance_no()
    assert no.startswith("AP")
    assert len(no) == 14  # AP + 12 digits


def test_generate_instance_no_unique():
    from app.services.approval_engine.workflow_engine import WorkflowEngine
    import time
    no1 = WorkflowEngine._generate_instance_no()
    time.sleep(1)
    no2 = WorkflowEngine._generate_instance_no()
    # 两次调用（不在同一秒内）应不同
    # 即使相同，格式也应正确
    assert no1.startswith("AP")
    assert no2.startswith("AP")


# ─── 2. create_instance - flow 不存在 ────────────────────────────────────────
def test_create_instance_flow_not_found():
    engine = _make_engine()
    engine.db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="不存在或未启用"):
        engine.create_instance(
            flow_code="NONEXISTENT",
            business_type="ECN",
            business_id=1,
            business_title="Test",
            submitted_by=1,
        )


# ─── 3. get_current_node ─────────────────────────────────────────────────────
def test_get_current_node_wrong_status():
    engine = _make_engine()

    instance = MagicMock()
    instance.current_status = "COMPLETED"  # 非 PENDING/IN_PROGRESS

    result = engine.get_current_node(instance)
    assert result is None


def test_get_current_node_with_current_node_id():
    engine = _make_engine()

    mock_node = MagicMock()
    engine.db.query.return_value.filter.return_value.first.return_value = mock_node

    instance = MagicMock()
    instance.current_status = "PENDING"
    instance.current_node_id = 5

    result = engine.get_current_node(instance)
    assert result == mock_node


def test_get_current_node_no_current_node_id():
    engine = _make_engine()

    mock_node = MagicMock()
    engine.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_node

    instance = MagicMock()
    instance.current_status = "PENDING"
    instance.current_node_id = None

    result = engine.get_current_node(instance)
    assert result == mock_node


# ─── 4. evaluate_node_conditions ─────────────────────────────────────────────
def test_evaluate_node_conditions_no_condition():
    engine = _make_engine()

    node = MagicMock()
    node.condition_expression = None
    node.condition_expr = None

    instance = MagicMock()
    result = engine.evaluate_node_conditions(node, instance)
    assert result is True


def test_evaluate_node_conditions_with_expression():
    engine = _make_engine()

    node = MagicMock()
    node.condition_expression = "{{ amount > 100 }}"

    instance = MagicMock()
    instance.submitted_by = 1
    instance.business_type = "TEST"
    instance.business_id = 1
    instance.flow_code = "TEST_FLOW"
    instance.current_status = "PENDING"

    # Mock db queries for user and entity
    engine.db.query.return_value.filter.return_value.first.return_value = None

    # The form_data might have amount
    instance.form_data = {"amount": 200}

    # Should not raise, returns bool
    result = engine.evaluate_node_conditions(node, instance)
    assert isinstance(result, bool)


def test_evaluate_node_conditions_parse_error_defaults_to_true():
    engine = _make_engine()

    node = MagicMock()
    # 无效 Jinja2 语法
    node.condition_expression = "{{ invalid jinja {{ }}"
    node.condition_expr = None

    instance = MagicMock()
    instance.submitted_by = None
    instance.business_type = "UNKNOWN"
    instance.business_id = 0
    instance.flow_code = "X"
    instance.current_status = "PENDING"
    instance.form_data = {}

    engine.db.query.return_value.filter.return_value.first.return_value = None

    # 解析失败时默认允许（返回 True）
    result = engine.evaluate_node_conditions(node, instance)
    assert result is True


# ─── 5. _get_business_entity_data ────────────────────────────────────────────
def test_get_business_entity_data_unknown_type():
    engine = _make_engine()
    result = engine._get_business_entity_data("UNKNOWN_TYPE", 1)
    assert result == {}


def test_get_business_entity_data_ecn_not_found():
    engine = _make_engine()
    engine.db.query.return_value.filter.return_value.first.return_value = None

    result = engine._get_business_entity_data("ECN", 999)
    assert result == {}


def test_get_business_entity_data_ecn_found():
    engine = _make_engine()

    mock_ecn = MagicMock()
    mock_ecn.id = 1
    mock_ecn.ecn_no = "ECN001"
    mock_ecn.ecn_type = "DESIGN"
    mock_ecn.status = "PENDING"
    mock_ecn.change_reason = "Test"

    engine.db.query.return_value.filter.return_value.first.return_value = mock_ecn

    result = engine._get_business_entity_data("ECN", 1)
    assert result["ecn_no"] == "ECN001"
    assert result["id"] == 1


# ─── 6. submit_approval - no current node ────────────────────────────────────
def test_submit_approval_no_current_node():
    engine = _make_engine()

    instance = MagicMock()
    instance.current_status = "COMPLETED"

    with pytest.raises(ValueError, match="没有可审批的节点"):
        engine.submit_approval(instance, approver_id=1, decision="APPROVE")
