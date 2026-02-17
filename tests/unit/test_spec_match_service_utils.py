# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/spec_match_service.py
Covers: SpecMatchService class
"""

import pytest
from unittest.mock import MagicMock, patch, call
from decimal import Decimal

from app.utils.spec_match_service import SpecMatchService
from app.utils.spec_matcher import SpecMatchResult


def make_requirement(id=1, project_id=1, material_code="MAT001",
                     material_name="电阻", specification="100Ω 1%"):
    req = MagicMock()
    req.id = id
    req.project_id = project_id
    req.material_code = material_code
    req.material_name = material_name
    req.specification = specification
    req.brand = None
    req.model = None
    req.key_parameters = None
    req.requirement_level = "MANDATORY"
    return req


class TestSpecMatchServiceInit:
    """Test SpecMatchService initialization."""

    def test_init_creates_matcher(self):
        """SpecMatchService creates a SpecMatcher on init."""
        from app.utils.spec_matcher import SpecMatcher
        service = SpecMatchService()
        assert isinstance(service.matcher, SpecMatcher)


class TestCheckPoItemSpecMatch:
    """Tests for check_po_item_spec_match."""

    def test_returns_none_when_no_requirements(self):
        """Returns None when no TechnicalSpecRequirements found."""
        service = SpecMatchService()
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.check_po_item_spec_match(
            db=db,
            project_id=1,
            po_item_id=10,
            material_code="MAT001",
            specification="100Ω",
        )
        assert result is None

    def test_returns_match_record_when_requirements_found(self):
        """Returns a SpecMatchRecord when requirements are found and matched."""
        service = SpecMatchService()
        db = MagicMock()

        req = make_requirement()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        # Patch the matcher to return a MATCHED result
        match_result = SpecMatchResult(
            match_status="MATCHED",
            match_score=Decimal("95.0"),
            differences={}
        )
        service.matcher.match_specification = MagicMock(return_value=match_result)

        # Mock SpecMatchRecord creation
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.match_status = "MATCHED"
        db.flush = MagicMock()

        with patch("app.utils.spec_match_service.SpecMatchRecord", return_value=mock_record):
            result = service.check_po_item_spec_match(
                db=db,
                project_id=1,
                po_item_id=10,
                material_code="MAT001",
                specification="100Ω",
            )

        assert result is not None
        db.add.assert_called()

    def test_creates_alert_when_mismatched(self):
        """Creates alert when match_status is MISMATCHED."""
        service = SpecMatchService()
        db = MagicMock()

        req = make_requirement()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        # Patch matcher to return MISMATCHED
        match_result = SpecMatchResult(
            match_status="MISMATCHED",
            match_score=Decimal("50.0"),
            differences={"specification": {"required": "100Ω", "actual": "200Ω"}}
        )
        service.matcher.match_specification = MagicMock(return_value=match_result)
        service._create_alert = MagicMock()

        mock_record = MagicMock()
        mock_record.id = 2
        mock_record.match_status = "MISMATCHED"

        with patch("app.utils.spec_match_service.SpecMatchRecord", return_value=mock_record):
            result = service.check_po_item_spec_match(
                db=db,
                project_id=1,
                po_item_id=10,
                material_code="MAT001",
                specification="200Ω",
            )

        service._create_alert.assert_called_once()

    def test_skips_requirement_with_different_material_code(self):
        """Skips requirements whose material_code doesn't match."""
        service = SpecMatchService()
        db = MagicMock()

        req = make_requirement(material_code="OTHER")
        req.material_code = "OTHER"
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        result = service.check_po_item_spec_match(
            db=db,
            project_id=1,
            po_item_id=10,
            material_code="MAT001",
            specification="100Ω",
        )
        # material codes don't match, so skipped → returns None
        assert result is None


class TestCheckBomItemSpecMatch:
    """Tests for check_bom_item_spec_match."""

    def test_returns_none_when_no_requirements(self):
        """Returns None when no requirements found for BOM item."""
        service = SpecMatchService()
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.check_bom_item_spec_match(
            db=db,
            project_id=1,
            bom_item_id=20,
            material_code="MAT002",
            specification="220V",
        )
        assert result is None

    def test_returns_match_record_for_bom(self):
        """Returns SpecMatchRecord for BOM item match."""
        service = SpecMatchService()
        db = MagicMock()

        req = make_requirement(material_code=None)  # None = match all
        req.material_code = None
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        match_result = SpecMatchResult(
            match_status="MATCHED",
            match_score=Decimal("90.0"),
            differences={}
        )
        service.matcher.match_specification = MagicMock(return_value=match_result)

        mock_record = MagicMock()
        mock_record.id = 3
        mock_record.match_status = "MATCHED"

        with patch("app.utils.spec_match_service.SpecMatchRecord", return_value=mock_record):
            result = service.check_bom_item_spec_match(
                db=db,
                project_id=1,
                bom_item_id=20,
                material_code="MAT002",
                specification="220V",
            )

        assert result is not None


class TestCreateAlert:
    """Tests for SpecMatchService._create_alert."""

    def test_creates_new_rule_when_none_exists(self):
        """Creates a default AlertRule when none exists in DB."""
        service = SpecMatchService()
        db = MagicMock()

        # No existing rule
        db.query.return_value.filter.return_value.first.return_value = None
        # alert count query
        count_mock = MagicMock()
        count_mock.count.return_value = 0
        db.query.return_value.filter.return_value.filter.return_value = count_mock

        req = make_requirement()
        match_result = SpecMatchResult(
            match_status="MISMATCHED",
            match_score=Decimal("40.0"),
            differences={}
        )

        with patch("app.utils.spec_match_service.AlertRule") as MockRule, \
             patch("app.utils.spec_match_service.AlertRecord") as MockAlert, \
             patch("app.utils.spec_match_service.apply_like_filter") as mock_filter:

            mock_rule_instance = MagicMock()
            mock_rule_instance.id = 1
            MockRule.return_value = mock_rule_instance
            mock_filter.return_value = count_mock

            mock_alert = MagicMock()
            mock_alert.id = 10
            MockAlert.return_value = mock_alert

            # Patch match_record lookup
            mock_match_record = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [None, mock_match_record]

            service._create_alert(
                db=db,
                project_id=1,
                match_record_id=5,
                requirement=req,
                match_result=match_result
            )

        db.add.assert_called()

    def test_reuses_existing_rule(self):
        """Reuses existing AlertRule when one already exists."""
        service = SpecMatchService()
        db = MagicMock()

        existing_rule = MagicMock()
        existing_rule.id = 99

        count_mock = MagicMock()
        count_mock.count.return_value = 5

        db.query.return_value.filter.return_value.first.return_value = existing_rule

        req = make_requirement()
        match_result = SpecMatchResult(
            match_status="MISMATCHED",
            match_score=Decimal("30.0"),
            differences={}
        )

        with patch("app.utils.spec_match_service.AlertRecord") as MockAlert, \
             patch("app.utils.spec_match_service.apply_like_filter") as mock_filter:

            mock_filter.return_value = count_mock
            mock_alert = MagicMock()
            MockAlert.return_value = mock_alert

            match_record = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [existing_rule, match_record]

            service._create_alert(
                db=db,
                project_id=1,
                match_record_id=5,
                requirement=req,
                match_result=match_result
            )

        # Should not create a new rule
        db.add.assert_called()
