# -*- coding: utf-8 -*-
"""PROD-23: status changes must go through shared state guards."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.production import work_reports
from app.api.v1.endpoints.purchase import orders_refactored
from app.models.production import WorkOrder, WorkReport, Worker
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.vendor import Vendor
from app.schemas.production import WorkReportCompleteRequest, WorkReportStartRequest


def _user(user_id: int = 1, *, is_superuser: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        is_superuser=is_superuser,
        is_tenant_admin=False,
        role_codes=[],
    )


def _vendor(db_session) -> Vendor:
    vendor = Vendor(
        supplier_code="SUP-PROD23",
        supplier_name="PROD-23 供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


def _purchase_order(db_session, *, status: str) -> PurchaseOrder:
    vendor = _vendor(db_session)
    order = PurchaseOrder(
        order_no=f"PO-PROD23-{status}",
        supplier_id=vendor.id,
        order_type="NORMAL",
        order_title="PROD-23 采购状态治理",
        status=status,
        created_by=10,
        order_date=date.today(),
        total_amount=Decimal("100.00"),
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        PurchaseOrderItem(
            order_id=order.id,
            item_no=1,
            material_code="MAT-PROD23",
            material_name="状态治理物料",
            unit="件",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            amount=Decimal("100.00"),
            status="PENDING",
        )
    )
    db_session.commit()
    db_session.refresh(order)
    return order


def _worker(db_session, *, user_id: int = 1) -> Worker:
    worker = Worker(
        worker_no=f"W-PROD23-{user_id}",
        worker_name="状态治理工人",
        user_id=user_id,
        status="ACTIVE",
    )
    db_session.add(worker)
    db_session.flush()
    return worker


def _work_order(db_session, *, status: str, plan_qty: int = 1) -> WorkOrder:
    worker = _worker(db_session)
    work_order = WorkOrder(
        work_order_no=f"WO-PROD23-{status}",
        task_name="PROD-23 报工状态治理",
        task_type="OTHER",
        plan_qty=plan_qty,
        assigned_to=worker.id,
        status=status,
    )
    db_session.add(work_order)
    db_session.commit()
    db_session.refresh(work_order)
    return work_order


def test_purchase_submit_uses_shared_transition_helper(monkeypatch, db_session):
    order = _purchase_order(db_session, status="DRAFT")
    calls = []

    def fake_transition(order_obj, target_status):
        calls.append((order_obj.id, order_obj.status, target_status))
        order_obj.status = target_status

    monkeypatch.setattr(
        orders_refactored,
        "transition_purchase_order_status",
        fake_transition,
        raising=False,
    )

    orders_refactored.submit_purchase_order(order.id, db=db_session, current_user=_user())

    assert calls == [(order.id, "DRAFT", "SUBMITTED")]


def test_purchase_approve_uses_shared_transition_helper(monkeypatch, db_session):
    order = _purchase_order(db_session, status="SUBMITTED")
    calls = []

    def fake_transition(order_obj, target_status):
        calls.append((order_obj.id, order_obj.status, target_status))
        order_obj.status = target_status

    monkeypatch.setattr(
        orders_refactored,
        "transition_purchase_order_status",
        fake_transition,
        raising=False,
    )

    orders_refactored.approve_purchase_order(
        order.id,
        approved=True,
        approval_note="ok",
        db=db_session,
        current_user=_user(user_id=99),
    )

    assert calls == [(order.id, "SUBMITTED", "APPROVED")]


def test_start_work_report_uses_work_order_state_machine(monkeypatch, db_session):
    work_order = _work_order(db_session, status="ASSIGNED")

    def fake_validate(current_status, new_status):
        assert (current_status, new_status) == ("ASSIGNED", "STARTED")
        raise ValueError("state-machine-blocked")

    monkeypatch.setattr(work_reports, "validate_transition", fake_validate, raising=False)

    with pytest.raises(HTTPException) as exc_info:
        work_reports.start_work_report(
            db=db_session,
            report_in=WorkReportStartRequest(work_order_id=work_order.id),
            current_user=_user(),
        )

    assert exc_info.value.status_code == 400
    assert "state-machine-blocked" in exc_info.value.detail


def test_complete_approval_uses_work_order_state_machine(monkeypatch, db_session):
    work_order = _work_order(db_session, status="STARTED", plan_qty=1)
    report = WorkReport(
        report_no="WR-PROD23-COMPLETE",
        work_order_id=work_order.id,
        worker_id=work_order.assigned_to,
        report_type="COMPLETE",
        completed_qty=1,
        qualified_qty=1,
        defect_qty=0,
        status="PENDING",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    def fake_validate(current_status, new_status):
        assert (current_status, new_status) == ("STARTED", "COMPLETED")
        raise ValueError("state-machine-blocked")

    monkeypatch.setattr(work_reports, "validate_transition", fake_validate, raising=False)

    with pytest.raises(HTTPException) as exc_info:
        work_reports.approve_work_report(
            db=db_session,
            report_id=report.id,
            approved=True,
            approval_note=None,
            current_user=_user(user_id=99),
        )

    assert exc_info.value.status_code == 400
    assert "state-machine-blocked" in exc_info.value.detail
