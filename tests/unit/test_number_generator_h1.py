# -*- coding: utf-8 -*-
"""
Additional unit tests for app/utils/number_generator.py (H1 group supplement)
Covers: generate_monthly_no, generate_employee_code, generate_customer_code
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.utils.number_generator import (
    generate_sequential_no,
    generate_monthly_no,
    generate_employee_code,
    generate_customer_code,
)


def _make_mock_db_no_record():
    """DB mock with no existing records."""
    db = MagicMock()
    db.query.return_value.order_by.return_value.first.return_value = None
    return db


class TestGenerateMonthlyNo:
    """Tests for generate_monthly_no function."""

    def _mock_db(self, existing_no=None):
        db = MagicMock()
        if existing_no:
            record = MagicMock()
            setattr(record, "lead_code", existing_no)
            db.query.return_value.order_by.return_value.first.return_value = record
        else:
            db.query.return_value.order_by.return_value.first.return_value = None
        return db

    @patch("app.utils.number_generator.apply_like_filter")
    def test_monthly_no_starts_at_001(self, mock_filter):
        """First record of month starts at 001."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        with patch("app.utils.number_generator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 15)
            result = generate_monthly_no(db, MagicMock(), "lead_code", "L")

        assert result.startswith("L2607-")
        assert result.endswith("-001")

    @patch("app.utils.number_generator.apply_like_filter")
    def test_monthly_no_increments_from_existing(self, mock_filter):
        """Increments from the last existing monthly number."""
        db = MagicMock()
        existing = MagicMock()
        existing.lead_code = "L2607-005"
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = existing

        with patch("app.utils.number_generator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 15)
            result = generate_monthly_no(db, MagicMock(), "lead_code", "L")

        assert result == "L2607--006"  # sep + 006

    @patch("app.utils.number_generator.apply_like_filter")
    def test_monthly_no_handles_invalid_format(self, mock_filter):
        """Falls back to 001 when existing record has invalid format."""
        db = MagicMock()
        existing = MagicMock()
        existing.lead_code = "L2607-invalid"
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = existing

        with patch("app.utils.number_generator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 1)
            result = generate_monthly_no(db, MagicMock(), "lead_code", "L")

        assert result.endswith("-001")

    @patch("app.utils.number_generator.apply_like_filter")
    def test_monthly_no_custom_separator(self, mock_filter):
        """Custom separator is used in the generated number."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        with patch("app.utils.number_generator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 3, 10)
            result = generate_monthly_no(db, MagicMock(), "order_no", "O", separator="")

        assert result.startswith("O2603")
        assert "001" in result


class TestGenerateEmployeeCode:
    """Tests for generate_employee_code function."""

    @patch("app.utils.number_generator.apply_like_filter")
    def test_first_employee_gets_00001(self, mock_filter):
        """First employee code is EMP-00001."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        result = generate_employee_code(db)
        assert result.startswith("EMP-")
        assert result.endswith("00001")

    @patch("app.utils.number_generator.apply_like_filter")
    def test_employee_code_increments(self, mock_filter):
        """Employee code increments from last existing code."""
        db = MagicMock()
        existing = MagicMock()
        existing.employee_code = "EMP-00042"
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = existing

        result = generate_employee_code(db)
        assert result == "EMP-00043"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_employee_code_invalid_format_fallback(self, mock_filter):
        """Falls back to 00001 on invalid existing code format."""
        db = MagicMock()
        existing = MagicMock()
        existing.employee_code = "EMP"  # missing seq part
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = existing

        result = generate_employee_code(db)
        assert result.endswith("00001")


class TestGenerateCustomerCode:
    """Tests for generate_customer_code function."""

    @patch("app.utils.number_generator.apply_like_filter")
    def test_first_customer_code(self, mock_filter):
        """First customer gets CUS-0000001."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        result = generate_customer_code(db)
        assert result.startswith("CUS-")
        # Should be CUS-0000001 (7 digits)
        assert result == "CUS-0000001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_customer_code_increments(self, mock_filter):
        """Customer code increments from existing max."""
        db = MagicMock()
        existing = MagicMock()
        existing.customer_code = "CUS-0000099"
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = existing

        result = generate_customer_code(db)
        assert result == "CUS-0000100"


class TestGenerateSequentialNoEdgeCases:
    """Edge case tests for generate_sequential_no."""

    @patch("app.utils.number_generator.apply_like_filter")
    def test_without_date_with_separator(self, mock_filter):
        """use_date=False with separator generates PREFIX-SEQ."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db, MagicMock(), "code", "ORD",
            use_date=False, separator="-", seq_length=4
        )
        assert result == "ORD-0001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_without_date_without_separator(self, mock_filter):
        """use_date=False without separator generates PREFIXSEQ."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db, MagicMock(), "code", "PJ",
            use_date=False, separator="", seq_length=3
        )
        assert result == "PJ001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_with_date_and_no_separator(self, mock_filter):
        """use_date=True without separator generates PREFIXDATESEQ."""
        db = MagicMock()
        mock_filter.return_value = db.query.return_value
        db.query.return_value.order_by.return_value.first.return_value = None

        with patch("app.utils.number_generator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)
            result = generate_sequential_no(
                db, MagicMock(), "proj_code", "PJ",
                date_format="%y%m%d", separator="", seq_length=3
            )

        assert result == "PJ260115001"
