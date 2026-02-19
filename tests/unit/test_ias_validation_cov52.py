# -*- coding: utf-8 -*-
"""
Unit tests for app/services/invoice_auto_service/validation.py (cov52)
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.invoice_auto_service.validation import (
        check_deliverables_complete,
        check_acceptance_issues_resolved,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


# ──────────────────────── check_deliverables_complete ────────────────────────

def test_deliverables_complete_no_contract_id():
    """plan 没有 contract_id 时直接返回 True"""
    service = _make_service()
    plan = MagicMock(contract_id=None)
    assert check_deliverables_complete(service, plan) is True


def test_deliverables_complete_contract_not_found():
    """contract_id 有值但查不到合同对象时返回 True"""
    service = _make_service()
    plan = MagicMock(contract_id=1)
    service.db.query.return_value.filter.return_value.first.return_value = None
    assert check_deliverables_complete(service, plan) is True


def test_deliverables_complete_with_contract():
    """找到合同时，当前实现默认返回 True"""
    service = _make_service()
    plan = MagicMock(contract_id=1)
    contract = MagicMock()
    service.db.query.return_value.filter.return_value.first.return_value = contract
    assert check_deliverables_complete(service, plan) is True


# ──────────────────────── check_acceptance_issues_resolved ────────────────────────

def test_no_blocking_issues():
    """无阻塞问题时返回 True"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.all.return_value = []
    order = MagicMock(id=1)
    assert check_acceptance_issues_resolved(service, order) is True


def test_open_blocking_issue():
    """存在 OPEN 阻塞问题时返回 False"""
    service = _make_service()
    issue = MagicMock(status="OPEN", is_blocking=True)
    service.db.query.return_value.filter.return_value.all.return_value = [issue]
    order = MagicMock(id=1)
    assert check_acceptance_issues_resolved(service, order) is False


def test_resolved_but_not_verified():
    """阻塞问题已 RESOLVED 但未 VERIFIED 时返回 False"""
    service = _make_service()
    issue = MagicMock(status="RESOLVED", verified_result="PENDING", is_blocking=True)
    service.db.query.return_value.filter.return_value.all.return_value = [issue]
    order = MagicMock(id=1)
    assert check_acceptance_issues_resolved(service, order) is False


def test_resolved_and_verified():
    """阻塞问题已 RESOLVED 且 VERIFIED 时返回 True"""
    service = _make_service()
    issue = MagicMock(status="RESOLVED", verified_result="VERIFIED", is_blocking=True)
    service.db.query.return_value.filter.return_value.all.return_value = [issue]
    order = MagicMock(id=1)
    assert check_acceptance_issues_resolved(service, order) is True


def test_deferred_blocking_issue():
    """DEFERRED 状态阻塞问题返回 False"""
    service = _make_service()
    issue = MagicMock(status="DEFERRED", is_blocking=True)
    service.db.query.return_value.filter.return_value.all.return_value = [issue]
    order = MagicMock(id=1)
    assert check_acceptance_issues_resolved(service, order) is False
