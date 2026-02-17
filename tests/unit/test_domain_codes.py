# -*- coding: utf-8 -*-
"""
Unit tests for domain_codes.py
Covers: app/utils/domain_codes.py
"""

import pytest
from unittest.mock import MagicMock, patch
import re

# We'll import domain code classes lazily inside tests to avoid model import errors


def make_mock_db():
    """Return a mock DB session where query returns no existing record."""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    # Also satisfy apply_like_filter chain
    q = MagicMock()
    q.order_by.return_value.first.return_value = None
    db.query.return_value = q
    return db


# Helper: patch generate_sequential_no to return a predictable value
def _patch_gen(return_value="TEST-250101-001"):
    return patch(
        "app.utils.domain_codes.generate_sequential_no",
        return_value=return_value,
    )


class TestOutsourcingCodes:
    """Tests for OutsourcingCodes class."""

    def test_generate_order_no_format(self):
        """generate_order_no calls generate_sequential_no and returns its result."""
        from app.utils.domain_codes import OutsourcingCodes
        with _patch_gen("OS-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.utils.domain_codes.OutsourcingCodes.generate_order_no.__func__", create=True):
                pass
            # Patch the lazy import inside the method
            with patch("app.models.outsourcing.OutsourcingOrder", MagicMock()):
                result = OutsourcingCodes.generate_order_no(db)
        assert result == "OS-250101-001"
        mock_gen.assert_called_once()

    def test_generate_delivery_no_format(self):
        """generate_delivery_no calls generate_sequential_no."""
        from app.utils.domain_codes import OutsourcingCodes
        with _patch_gen("DL-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.outsourcing.OutsourcingDelivery", MagicMock()):
                result = OutsourcingCodes.generate_delivery_no(db)
        assert result == "DL-250101-001"

    def test_generate_inspection_no_format(self):
        """generate_inspection_no calls generate_sequential_no."""
        from app.utils.domain_codes import OutsourcingCodes
        with _patch_gen("IQ-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.outsourcing.OutsourcingInspection", MagicMock()):
                result = OutsourcingCodes.generate_inspection_no(db)
        assert result == "IQ-250101-001"


class TestPresaleCodes:
    """Tests for PresaleCodes class."""

    def test_generate_ticket_no(self):
        """generate_ticket_no returns TICKET prefixed number."""
        from app.utils.domain_codes import PresaleCodes
        with _patch_gen("TICKET-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.presale.PresaleSupportTicket", MagicMock()):
                result = PresaleCodes.generate_ticket_no(db)
        assert result == "TICKET-250101-001"

    def test_generate_solution_no(self):
        """generate_solution_no returns SOL prefixed number."""
        from app.utils.domain_codes import PresaleCodes
        with _patch_gen("SOL-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.presale.PresaleSolution", MagicMock()):
                result = PresaleCodes.generate_solution_no(db)
        assert result == "SOL-250101-001"

    def test_generate_tender_no(self):
        """generate_tender_no returns TENDER prefixed number."""
        from app.utils.domain_codes import PresaleCodes
        with _patch_gen("TENDER-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.presale.PresaleTenderRecord", MagicMock()):
                result = PresaleCodes.generate_tender_no(db)
        assert result == "TENDER-250101-001"


class TestPmoCodes:
    """Tests for PmoCodes class."""

    def test_generate_risk_no(self):
        """generate_risk_no returns RISK prefixed number."""
        from app.utils.domain_codes import PmoCodes
        with _patch_gen("RISK-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.pmo.PmoProjectRisk", MagicMock()):
                result = PmoCodes.generate_risk_no(db)
        assert result == "RISK-250101-001"
        mock_gen.assert_called_once()

    def test_generate_meeting_no(self):
        """generate_meeting_no returns MTG prefixed number."""
        from app.utils.domain_codes import PmoCodes
        with _patch_gen("MTG-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.pmo.PmoMeeting", MagicMock()):
                result = PmoCodes.generate_meeting_no(db)
        assert result == "MTG-250101-001"

    def test_generate_initiation_no(self):
        """generate_initiation_no returns INIT prefixed number."""
        from app.utils.domain_codes import PmoCodes
        with _patch_gen("INIT-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.pmo.PmoProjectInitiation", MagicMock()):
                result = PmoCodes.generate_initiation_no(db)
        assert result == "INIT-250101-001"


class TestTaskCenterCodes:
    """Tests for TaskCenterCodes class."""

    def test_generate_task_code(self):
        """generate_task_code returns TASK prefixed number."""
        from app.utils.domain_codes import TaskCenterCodes
        with _patch_gen("TASK-250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.task_center.TaskUnified", MagicMock()):
                result = TaskCenterCodes.generate_task_code(db)
        assert result == "TASK-250101-001"
        mock_gen.assert_called_once()


class TestPurchaseCodes:
    """Tests for PurchaseCodes class."""

    def test_generate_order_no(self):
        """generate_order_no returns PO prefixed number."""
        from app.utils.domain_codes import PurchaseCodes
        with _patch_gen("PO-20250101-001") as mock_gen:
            db = MagicMock()
            with patch("app.models.purchase.PurchaseOrder", MagicMock()):
                result = PurchaseCodes.generate_order_no(db)
        assert result == "PO-20250101-001"


class TestDomainCodeModuleExports:
    """Tests that module-level singleton instances exist."""

    def test_outsourcing_instance_exists(self):
        """Module exports an outsourcing instance."""
        from app.utils.domain_codes import OutsourcingCodes
        assert OutsourcingCodes is not None

    def test_presale_instance_exists(self):
        """Module exports a presale instance."""
        from app.utils.domain_codes import PresaleCodes
        assert PresaleCodes is not None

    def test_pmo_instance_exists(self):
        """Module exports a pmo instance."""
        from app.utils.domain_codes import PmoCodes
        assert PmoCodes is not None

    def test_task_center_instance_exists(self):
        """Module exports a task_center instance."""
        from app.utils.domain_codes import TaskCenterCodes
        assert TaskCenterCodes is not None

    def test_generate_sequential_no_is_called_with_correct_prefix(self):
        """Ensure prefix param is correctly passed for each code type."""
        from app.utils.domain_codes import OutsourcingCodes
        call_kwargs = {}
        def capture_gen(*args, **kwargs):
            call_kwargs['prefix'] = args[3] if len(args) > 3 else kwargs.get('prefix')
            return "OS-250101-001"

        with patch("app.utils.domain_codes.generate_sequential_no", side_effect=capture_gen):
            db = MagicMock()
            with patch("app.models.outsourcing.OutsourcingOrder", MagicMock()):
                OutsourcingCodes.generate_order_no(db)

        assert call_kwargs.get('prefix') == 'OS'
