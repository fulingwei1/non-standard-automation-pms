# -*- coding: utf-8 -*-
"""Tests for AcceptanceService."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.acceptance.acceptance_service import AcceptanceService


pytestmark = pytest.mark.unit


class _FakeQuery:
    def join(self, *args, **kwargs):
        return self

    def where(self, *args, **kwargs):
        return self


@pytest.mark.asyncio
async def test_complete_acceptance_order_not_found():
    db = AsyncMock()
    db.add = MagicMock()
    result = MagicMock()
    result.first.return_value = None
    db.execute.return_value = result

    with pytest.raises(ValueError, match="验收单不存在"):
        await AcceptanceService.complete_acceptance_order(db, order_id=999, completed_by=1)


@pytest.mark.asyncio
async def test_complete_acceptance_order_wrong_status(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.acceptance.acceptance_service.select", lambda *args, **kwargs: _FakeQuery())

    db = AsyncMock()
    db.add = MagicMock()
    order = SimpleNamespace(status="PENDING")
    project = SimpleNamespace(project_code="P-001")

    first_result = MagicMock()
    first_result.first.return_value = (order, project, None)
    db.execute.return_value = first_result

    with pytest.raises(ValueError, match="验收单状态不是PASSED"):
        await AcceptanceService.complete_acceptance_order(db, order_id=1, completed_by=1)


@pytest.mark.asyncio
async def test_complete_acceptance_order_returns_open_issue_summary(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.acceptance.acceptance_service.select", lambda *args, **kwargs: _FakeQuery())

    db = AsyncMock()
    db.add = MagicMock()
    order = SimpleNamespace(
        id=1,
        status="PASSED",
        project_id=7,
        acceptance_type="FAT",
    )
    project = SimpleNamespace(project_code="P-001")

    first_result = MagicMock()
    first_result.first.return_value = (order, project, None)

    issues_result = MagicMock()
    issues_result.scalars.return_value.all.return_value = [SimpleNamespace(id=10)]

    db.execute.side_effect = [first_result, issues_result]

    result = await AcceptanceService.complete_acceptance_order(db, order_id=1, completed_by=2)

    assert result["success"] is False
    assert result["open_issues_count"] == 1
    assert "未解决的验收问题" in result["message"]


@pytest.mark.asyncio
async def test_complete_acceptance_order_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.acceptance.acceptance_service.select", lambda *args, **kwargs: _FakeQuery())

    generated_codes = []

    async def fake_generate_code():
        generated_codes.append("INV-001")
        return "INV-001"

    monkeypatch.setattr(
        "app.services.acceptance.acceptance_service.InvoiceService.generate_code",
        fake_generate_code,
    )

    created_invoices = []

    class FakeInvoice:
        _id_counter = 99

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.id = FakeInvoice._id_counter
            created_invoices.append(self)

    monkeypatch.setattr("app.services.acceptance.acceptance_service.Invoice", FakeInvoice)

    async def fake_update_project_to_warranty(db, project_id, completed_by):
        db.warranty_called = (project_id, completed_by)

    monkeypatch.setattr(
        AcceptanceService,
        "_update_project_to_warranty",
        fake_update_project_to_warranty,
    )

    db = AsyncMock()
    db.add = MagicMock()
    order = SimpleNamespace(
        id=1,
        status="PASSED",
        project_id=7,
        contract_id=None,
        customer_id=None,
        total_amount=None,
        acceptance_type="SAT",
    )
    project = SimpleNamespace(project_code="P-001", contract_id=88, customer_id=66, contract_amount=1234)

    first_result = MagicMock()
    first_result.first.return_value = (order, project, None)

    issues_result = MagicMock()
    issues_result.scalars.return_value.all.return_value = []

    db.execute.side_effect = [first_result, issues_result]

    result = await AcceptanceService.complete_acceptance_order(
        db,
        order_id=1,
        completed_by=5,
        completion_notes="done",
    )

    assert result == {
        "success": True,
        "message": "验收完成，已自动创建发票",
        "order_id": 1,
        "invoice_id": 99,
        "invoice_code": "INV-001",
        "project_id": 7,
        "project_code": "P-001",
    }
    assert generated_codes == ["INV-001"]
    assert created_invoices[0].invoice_code == "INV-001"
    assert created_invoices[0].contract_id == 88
    assert created_invoices[0].amount == 1234
    assert created_invoices[0].total_amount == 1234
    assert order.status == "COMPLETED"
    assert order.completed_by == 5
    assert order.completion_notes == "done"
    assert db.warranty_called == (7, 5)
    assert db.commit.await_count == 2


@pytest.mark.asyncio
async def test_update_project_not_found():
    db = AsyncMock()
    db.add = MagicMock()
    db.get.return_value = None

    with pytest.raises(ValueError, match="项目不存在"):
        await AcceptanceService._update_project_to_warranty(db, 999, 1)


@pytest.mark.asyncio
async def test_update_project_s8_to_s9_updates_health_and_status():
    db = AsyncMock()
    db.add = MagicMock()
    project = MagicMock(stage="S8", status="ST08")
    db.get.return_value = project

    await AcceptanceService._update_project_to_warranty(db, 1, 1)

    assert project.stage == "S9"
    assert project.status == "ST30"
    assert project.end_date == date.today()
    assert project.health_status == "H4"
    db.add.assert_called_with(project)
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_update_project_uses_health_field_when_health_status_missing():
    db = AsyncMock()
    db.add = MagicMock()
    project = SimpleNamespace(stage="S8", status="ST08", health="H2")
    db.get.return_value = project

    await AcceptanceService._update_project_to_warranty(db, 1, 1)

    assert project.stage == "S9"
    assert project.status == "ST30"
    assert project.health == "H4"


@pytest.mark.asyncio
async def test_update_project_not_s8_no_change():
    db = AsyncMock()
    db.add = MagicMock()
    project = MagicMock(stage="S5", status="ST12")
    db.get.return_value = project

    await AcceptanceService._update_project_to_warranty(db, 1, 1)

    assert project.stage == "S5"


@pytest.mark.asyncio
async def test_send_invoice_notification_is_noop():
    db = AsyncMock()
    db.add = MagicMock()
    await AcceptanceService._send_invoice_notification(db, MagicMock(id=1), MagicMock(id=2))
