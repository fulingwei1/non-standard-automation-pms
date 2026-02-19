# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/models.py - batch 41"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.approval_engine.models")

from app.services.approval_engine.models import (
    ApprovalFlowType,
    ApprovalNodeRole,
    ApprovalStatus,
    ApprovalDecision,
    LegacyApprovalFlow,
    LegacyApprovalNode,
    LegacyApprovalInstance,
    LegacyApprovalRecord,
)


def test_approval_flow_type_values():
    assert ApprovalFlowType.SINGLE_LEVEL == "SINGLE_LEVEL"
    assert ApprovalFlowType.MULTI_LEVEL == "MULTI_LEVEL"
    assert ApprovalFlowType.CONDITIONAL_ROUTE == "CONDITIONAL_ROUTE"
    assert ApprovalFlowType.AMOUNT_BASED == "AMOUNT_BASED"
    assert ApprovalFlowType.PARALLEL == "PARALLEL"


def test_approval_node_role_values():
    assert ApprovalNodeRole.USER == "USER"
    assert ApprovalNodeRole.ROLE == "ROLE"
    assert ApprovalNodeRole.DEPARTMENT == "DEPARTMENT"
    assert ApprovalNodeRole.SUPERVISOR == "SUPERVISOR"


def test_approval_status_values():
    assert ApprovalStatus.PENDING == "PENDING"
    assert ApprovalStatus.APPROVED == "APPROVED"
    assert ApprovalStatus.REJECTED == "REJECTED"
    assert ApprovalStatus.CANCELLED == "CANCELLED"


def test_approval_decision_aliases():
    assert ApprovalDecision.APPROVE == "APPROVED"
    assert ApprovalDecision.REJECT == "REJECTED"


def test_legacy_instance_status_property():
    # Test via the property descriptor directly on a plain object
    status_prop = LegacyApprovalInstance.__dict__["status"]
    obj = MagicMock()
    obj.current_status = "PENDING"
    result = status_prop.fget(obj)
    assert result == "PENDING"


def test_legacy_instance_status_setter():
    status_prop = LegacyApprovalInstance.__dict__["status"]
    obj = MagicMock()
    obj.current_status = None
    status_prop.fset(obj, "APPROVED")
    assert obj.current_status == "APPROVED"


def test_legacy_instance_status_setter_with_enum():
    status_prop = LegacyApprovalInstance.__dict__["status"]
    obj = MagicMock()
    obj.current_status = None
    status_prop.fset(obj, ApprovalStatus.REJECTED)
    assert obj.current_status == "REJECTED"


def test_legacy_flow_tablename():
    assert LegacyApprovalFlow.__tablename__ == "legacy_approval_flows"


def test_legacy_node_tablename():
    assert LegacyApprovalNode.__tablename__ == "legacy_approval_nodes"


def test_legacy_record_tablename():
    assert LegacyApprovalRecord.__tablename__ == "legacy_approval_records"
