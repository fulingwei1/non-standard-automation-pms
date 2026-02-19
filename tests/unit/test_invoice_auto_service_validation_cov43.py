# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/invoice_auto_service/validation.py
"""
import pytest

pytest.importorskip("app.services.invoice_auto_service.validation")

from unittest.mock import MagicMock
from app.services.invoice_auto_service.validation import (
    check_deliverables_complete,
    check_acceptance_issues_resolved,
)


def make_service():
    svc = MagicMock()
    svc.db = MagicMock()
    return svc


# ── 1. check_deliverables_complete: 无合同时返回 True ──────────────────────────
def test_deliverables_no_contract():
    svc = make_service()
    plan = MagicMock()
    plan.contract_id = None
    assert check_deliverables_complete(svc, plan) is True


# ── 2. check_deliverables_complete: 合同不存在时返回 True ───────────────────────
def test_deliverables_contract_not_found():
    svc = make_service()
    plan = MagicMock()
    plan.contract_id = 1
    svc.db.query.return_value.filter.return_value.first.return_value = None
    assert check_deliverables_complete(svc, plan) is True


# ── 3. check_deliverables_complete: 合同存在时返回 True（简化实现） ──────────────
def test_deliverables_contract_exists():
    svc = make_service()
    plan = MagicMock()
    plan.contract_id = 2
    contract = MagicMock()
    svc.db.query.return_value.filter.return_value.first.return_value = contract
    assert check_deliverables_complete(svc, plan) is True


# ── 4. check_acceptance_issues_resolved: 无阻塞问题时返回 True ──────────────────
def test_no_blocking_issues():
    svc = make_service()
    order = MagicMock()
    order.id = 1
    svc.db.query.return_value.filter.return_value.all.return_value = []
    assert check_acceptance_issues_resolved(svc, order) is True


# ── 5. check_acceptance_issues_resolved: 有未解决的阻塞问题 ─────────────────────
def test_open_blocking_issue():
    svc = make_service()
    order = MagicMock()
    order.id = 2
    issue = MagicMock()
    issue.status = "OPEN"
    issue.is_blocking = True
    svc.db.query.return_value.filter.return_value.all.return_value = [issue]
    assert check_acceptance_issues_resolved(svc, order) is False


# ── 6. check_acceptance_issues_resolved: 已解决但未验证 ─────────────────────────
def test_resolved_but_not_verified():
    svc = make_service()
    order = MagicMock()
    order.id = 3
    issue = MagicMock()
    issue.status = "RESOLVED"
    issue.verified_result = "PENDING"
    issue.is_blocking = True
    svc.db.query.return_value.filter.return_value.all.return_value = [issue]
    assert check_acceptance_issues_resolved(svc, order) is False


# ── 7. check_acceptance_issues_resolved: 已解决且已验证 ─────────────────────────
def test_resolved_and_verified():
    svc = make_service()
    order = MagicMock()
    order.id = 4
    issue = MagicMock()
    issue.status = "RESOLVED"
    issue.verified_result = "VERIFIED"
    issue.is_blocking = True
    svc.db.query.return_value.filter.return_value.all.return_value = [issue]
    assert check_acceptance_issues_resolved(svc, order) is True


# ── 8. check_acceptance_issues_resolved: DEFERRED 状态阻止开票 ──────────────────
def test_deferred_blocking_issue():
    svc = make_service()
    order = MagicMock()
    order.id = 5
    issue = MagicMock()
    issue.status = "DEFERRED"
    issue.is_blocking = True
    svc.db.query.return_value.filter.return_value.all.return_value = [issue]
    assert check_acceptance_issues_resolved(svc, order) is False
