# -*- coding: utf-8 -*-
"""
Unit tests for QualificationService (第三十批)
"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.qualification_service import QualificationService


@pytest.fixture
def mock_db():
    return MagicMock()


# ---------------------------------------------------------------------------
# get_qualification_levels
# ---------------------------------------------------------------------------

class TestGetQualificationLevels:
    def test_returns_all_levels_when_no_filters(self, mock_db):
        levels = [MagicMock(), MagicMock()]
        # is_active=True by default -> filter() is called once, then order_by()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = levels

        result = QualificationService.get_qualification_levels(mock_db, is_active=None)
        # With is_active=None, no filter called
        mock_db.query.return_value.order_by.return_value.all.return_value = levels
        result = QualificationService.get_qualification_levels(mock_db, is_active=None)
        assert result == levels

    def test_filters_by_role_type(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = QualificationService.get_qualification_levels(mock_db, role_type="ENGINEER", is_active=True)
        assert result == []


# ---------------------------------------------------------------------------
# get_competency_model
# ---------------------------------------------------------------------------

class TestGetCompetencyModel:
    def test_returns_model_for_position(self, mock_db):
        model = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = model

        result = QualificationService.get_competency_model(mock_db, "ENGINEER", level_id=2)
        assert result is model

    def test_returns_none_when_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = QualificationService.get_competency_model(mock_db, "UNKNOWN", level_id=99)
        assert result is None


# ---------------------------------------------------------------------------
# get_employee_qualification
# ---------------------------------------------------------------------------

class TestGetEmployeeQualification:
    def test_returns_latest_qualification(self, mock_db):
        qual = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = qual

        result = QualificationService.get_employee_qualification(mock_db, employee_id=1)
        assert result is qual

    def test_filters_by_position_type(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = QualificationService.get_employee_qualification(mock_db, employee_id=1, position_type="ENGINEER")
        assert result is None


# ---------------------------------------------------------------------------
# certify_employee
# ---------------------------------------------------------------------------

class TestCertifyEmployee:
    def test_raises_when_employee_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="员工"):
            QualificationService.certify_employee(
                mock_db, employee_id=999, position_type="ENGINEER",
                level_id=1, assessment_details={}, certifier_id=1
            )

    def test_raises_when_level_not_found(self, mock_db):
        employee = MagicMock()
        call_count = [0]

        def first_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return employee  # employee found
            return None  # level not found

        mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

        with pytest.raises(ValueError, match="等级"):
            QualificationService.certify_employee(
                mock_db, employee_id=1, position_type="ENGINEER",
                level_id=999, assessment_details={}, certifier_id=1
            )

    def test_updates_existing_qualification(self, mock_db):
        employee = MagicMock()
        level = MagicMock()
        existing_qual = MagicMock()

        call_count = [0]

        def first_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return employee
            elif call_count[0] == 2:
                return level
            else:
                return existing_qual

        mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

        result = QualificationService.certify_employee(
            mock_db, employee_id=1, position_type="ENGINEER",
            level_id=2, assessment_details={"score": 90}, certifier_id=5
        )

        mock_db.commit.assert_called()
        assert result is existing_qual

    def test_creates_new_qualification_when_none_exists(self, mock_db):
        employee = MagicMock()
        level = MagicMock()

        call_count = [0]

        def first_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return employee
            elif call_count[0] == 2:
                return level
            else:
                return None  # no existing qualification

        mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

        result = QualificationService.certify_employee(
            mock_db, employee_id=1, position_type="ENGINEER",
            level_id=2, assessment_details={}, certifier_id=5
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()


# ---------------------------------------------------------------------------
# assess_employee
# ---------------------------------------------------------------------------

class TestAssessEmployee:
    @patch("app.services.qualification_service.save_obj")
    def test_creates_assessment_record(self, mock_save, mock_db):
        scores = {"technical": 85, "communication": 78}

        with patch.object(QualificationService, "_calculate_total_score", return_value=Decimal("82")):
            with patch.object(QualificationService, "_determine_result", return_value="PASS"):
                result = QualificationService.assess_employee(
                    mock_db, employee_id=1, assessment_type="ANNUAL",
                    scores=scores, assessor_id=10
                )

        mock_save.assert_called_once()
        assert result is not None


# ---------------------------------------------------------------------------
# check_promotion_eligibility
# ---------------------------------------------------------------------------

class TestCheckPromotionEligibility:
    def test_returns_not_eligible_when_no_qualification(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = QualificationService.check_promotion_eligibility(mock_db, employee_id=1, target_level_id=3)
        assert result["eligible"] is False
        assert "尚未" in result["reason"]

    def test_returns_not_eligible_when_target_level_lower(self, mock_db):
        qualification = MagicMock()
        qualification.current_level_id = 3
        qualification.id = 1

        current_level = MagicMock()
        current_level.level_order = 3

        target_level = MagicMock()
        target_level.level_order = 2  # lower than current (int comparison)

        # get_employee_qualification -> order_by().first() returns qualification
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = qualification

        # current_level and target_level queries via filter().first()
        call_count = [0]

        def first_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return current_level
            else:
                return target_level

        mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

        result = QualificationService.check_promotion_eligibility(mock_db, employee_id=1, target_level_id=2)
        assert result["eligible"] is False
