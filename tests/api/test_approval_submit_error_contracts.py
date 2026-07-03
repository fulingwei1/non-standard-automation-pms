from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.acceptance import order_approval as acceptance_approval_api
from app.api.v1.endpoints.outsourcing import workflow as outsourcing_workflow_api
from app.api.v1.endpoints.purchase import workflow as purchase_workflow_api
from app.api.v1.endpoints.sales.contracts import approval as contract_approval_api
from app.schemas.approval_workflow import OrderSubmitRequest


class _NoopDb:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class _PurchaseLikeService:
    def __init__(self, db):
        self.db = db

    def submit_orders_for_approval(self, **kwargs):
        return {"success": [], "errors": [{"order_id": 1, "error": "审批模板不存在"}]}


class _AcceptanceLikeService:
    def __init__(self, db):
        self.db = db

    def submit_orders_for_approval(self, **kwargs):
        return [], [{"order_id": 1, "error": "审批模板不存在"}]


class _ContractLikeService:
    def __init__(self, db):
        self.db = db

    def submit_contracts_for_approval(self, **kwargs):
        return [], [{"contract_id": 1, "error": "审批模板不存在"}]


def _user():
    return SimpleNamespace(id=1, username="admin", real_name="系统管理员")


def test_purchase_submit_all_failed_returns_400(monkeypatch):
    monkeypatch.setattr(purchase_workflow_api, "PurchaseWorkflowService", _PurchaseLikeService)
    db = _NoopDb()

    with pytest.raises(HTTPException) as exc:
        purchase_workflow_api.submit_orders_for_approval(
            db=db,
            request=OrderSubmitRequest(order_ids=[1]),
            current_user=_user(),
        )

    assert exc.value.status_code == 400
    assert "审批模板不存在" in str(exc.value.detail)
    assert db.rolled_back is True
    assert db.committed is False


def test_outsourcing_submit_all_failed_returns_400(monkeypatch):
    monkeypatch.setattr(outsourcing_workflow_api, "OutsourcingWorkflowService", _PurchaseLikeService)
    db = _NoopDb()

    with pytest.raises(HTTPException) as exc:
        outsourcing_workflow_api.submit_orders_for_approval(
            db=db,
            request=OrderSubmitRequest(order_ids=[1]),
            current_user=_user(),
        )

    assert exc.value.status_code == 400
    assert "审批模板不存在" in str(exc.value.detail)
    assert db.rolled_back is True
    assert db.committed is False


def test_acceptance_submit_all_failed_returns_400(monkeypatch):
    monkeypatch.setattr(acceptance_approval_api, "AcceptanceApprovalService", _AcceptanceLikeService)
    db = _NoopDb()

    with pytest.raises(HTTPException) as exc:
        acceptance_approval_api.submit_for_approval(
            db=db,
            request=acceptance_approval_api.AcceptanceSubmitApprovalRequest(order_ids=[1]),
            current_user=_user(),
        )

    assert exc.value.status_code == 400
    assert "审批模板不存在" in str(exc.value.detail)
    assert db.rolled_back is True
    assert db.committed is False


def test_contract_submit_all_failed_returns_400(monkeypatch):
    monkeypatch.setattr(contract_approval_api, "ContractApprovalService", _ContractLikeService)
    db = _NoopDb()

    with pytest.raises(HTTPException) as exc:
        contract_approval_api.submit_for_approval(
            db=db,
            request=contract_approval_api.ContractSubmitApprovalRequest(contract_ids=[1]),
            current_user=_user(),
        )

    assert exc.value.status_code == 400
    assert "审批模板不存在" in str(exc.value.detail)
    assert db.rolled_back is True
    assert db.committed is False
