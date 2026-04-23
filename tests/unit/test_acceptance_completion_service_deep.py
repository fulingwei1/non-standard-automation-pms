# -*- coding: utf-8 -*-
"""Deep branch tests for acceptance_completion_service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import acceptance_completion_service as service


pytestmark = pytest.mark.unit


def test_trigger_invoice_on_acceptance_logs_created_requests(monkeypatch: pytest.MonkeyPatch):
    class FakeInvoiceAutoService:
        def __init__(self, db):
            self.db = db

        def check_and_create_invoice_request(self, acceptance_order_id, auto_create):
            assert acceptance_order_id == 12
            assert auto_create is True
            return {"success": True, "invoice_requests": [{"id": 1}, {"id": 2}]}

    logger = MagicMock()
    monkeypatch.setattr(service, "logger", logger)
    monkeypatch.setenv("AUTO_CREATE_INVOICE_ON_ACCEPTANCE", "true")
    monkeypatch.setattr("app.services.invoice_auto_service.InvoiceAutoService", FakeInvoiceAutoService)

    result = service.trigger_invoice_on_acceptance(MagicMock(), 12, auto_trigger=True)

    assert result["success"] is True
    logger.info.assert_called_once()


@pytest.mark.parametrize(
    ("overall_result", "expected"),
    [
        ("FAILED", {"blocked_milestones": [1, 2]}),
        ("PASSED", {"unblocked_milestones": [3]}),
        ("PENDING", {}),
    ],
)
def test_handle_progress_integration_branches(
    monkeypatch: pytest.MonkeyPatch, overall_result: str, expected: dict
):
    class FakeProgressIntegrationService:
        def __init__(self, db):
            self.db = db

        def handle_acceptance_failed(self, order):
            return [1, 2]

        def handle_acceptance_passed(self, order):
            return [3]

    monkeypatch.setattr(
        "app.services.progress_integration_service.ProgressIntegrationService",
        FakeProgressIntegrationService,
    )

    result = service.handle_progress_integration(MagicMock(), MagicMock(), overall_result)

    assert result == expected


def test_handle_progress_integration_exception(monkeypatch: pytest.MonkeyPatch):
    logger = MagicMock()
    monkeypatch.setattr(service, "logger", logger)

    class BrokenProgressIntegrationService:
        def __init__(self, db):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.services.progress_integration_service.ProgressIntegrationService",
        BrokenProgressIntegrationService,
    )

    result = service.handle_progress_integration(MagicMock(), MagicMock(), "PASSED")

    assert result == {"error": "boom"}
    logger.error.assert_called_once()


def test_check_auto_stage_transition_after_acceptance_fat_success(
    monkeypatch: pytest.MonkeyPatch,
):
    transition_service = MagicMock()
    transition_service.check_auto_stage_transition.return_value = {"auto_advanced": True, "to": "S8"}
    monkeypatch.setattr(
        "app.services.status_transition_service.StatusTransitionService",
        lambda db: transition_service,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(stage="S7")
    order = SimpleNamespace(project_id=9, acceptance_type="FAT")

    result = service.check_auto_stage_transition_after_acceptance(db, order, "PASSED")

    assert result == {"auto_advanced": True, "to": "S8"}


def test_check_auto_stage_transition_after_acceptance_sat_success(
    monkeypatch: pytest.MonkeyPatch,
):
    transition_service = MagicMock()
    transition_service.check_auto_stage_transition.return_value = {"auto_advanced": True, "to": "S9"}
    monkeypatch.setattr(
        "app.services.status_transition_service.StatusTransitionService",
        lambda db: transition_service,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(stage="S8")
    order = SimpleNamespace(project_id=9, acceptance_type="SAT")

    result = service.check_auto_stage_transition_after_acceptance(db, order, "PASSED")

    assert result == {"auto_advanced": True, "to": "S9"}


def test_check_auto_stage_transition_after_acceptance_not_advanced(
    monkeypatch: pytest.MonkeyPatch,
):
    transition_service = MagicMock()
    transition_service.check_auto_stage_transition.return_value = {"auto_advanced": False}
    monkeypatch.setattr(
        "app.services.status_transition_service.StatusTransitionService",
        lambda db: transition_service,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(stage="S7")
    order = SimpleNamespace(project_id=9, acceptance_type="FAT")

    assert service.check_auto_stage_transition_after_acceptance(db, order, "PASSED") == {}


def test_check_auto_stage_transition_after_acceptance_no_project(
    monkeypatch: pytest.MonkeyPatch,
):
    transition_service = MagicMock()
    monkeypatch.setattr(
        "app.services.status_transition_service.StatusTransitionService",
        lambda db: transition_service,
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    order = SimpleNamespace(project_id=9, acceptance_type="FAT")

    assert service.check_auto_stage_transition_after_acceptance(db, order, "PASSED") == {}


def test_trigger_warranty_period_no_project():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    order = SimpleNamespace(project_id=1, acceptance_type="FINAL")

    service.trigger_warranty_period(db, order, "PASSED")

    db.add.assert_not_called()


def test_trigger_warranty_period_exception_logs(monkeypatch: pytest.MonkeyPatch):
    logger = MagicMock()
    monkeypatch.setattr(service, "logger", logger)

    query = MagicMock()
    query.filter.side_effect = RuntimeError("warranty boom")
    db = MagicMock()
    db.query.return_value = query
    order = SimpleNamespace(project_id=1, acceptance_type="FINAL")

    service.trigger_warranty_period(db, order, "PASSED")

    logger.error.assert_called_once()


def test_trigger_bonus_calculation_exception_logs(monkeypatch: pytest.MonkeyPatch):
    logger = MagicMock()
    monkeypatch.setattr(service, "logger", logger)

    class BrokenBonusCalculator:
        def __init__(self, db):
            raise RuntimeError("bonus boom")

    monkeypatch.setattr("app.services.bonus.BonusCalculator", BrokenBonusCalculator)

    service.trigger_bonus_calculation(MagicMock(), SimpleNamespace(project_id=1), "PASSED")

    logger.error.assert_called_once()
