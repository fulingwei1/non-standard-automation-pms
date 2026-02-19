# -*- coding: utf-8 -*-
"""
Unit tests for QualificationService (第三十一批)
"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.qualification_service import QualificationService


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_chain(mock_db, first_val=None, all_val=None):
    chain = MagicMock()
    mock_db.query.return_value = chain
    chain.filter.return_value = chain
    chain.order_by.return_value = chain
    chain.first.return_value = first_val
    chain.all.return_value = all_val or []
    return chain


# ---------------------------------------------------------------------------
# get_qualification_levels
# ---------------------------------------------------------------------------

class TestGetQualificationLevels:
    def test_returns_all_levels(self, mock_db):
        level = MagicMock()
        chain = _make_chain(mock_db, all_val=[level])
        chain.filter.return_value = chain

        result = QualificationService.get_qualification_levels(mock_db)
        assert result == [level]

    def test_filters_by_role_type(self, mock_db):
        chain = _make_chain(mock_db, all_val=[])
        chain.filter.return_value = chain

        result = QualificationService.get_qualification_levels(mock_db, role_type="ENGINEER")
        assert chain.filter.called


# ---------------------------------------------------------------------------
# get_competency_model
# ---------------------------------------------------------------------------

class TestGetCompetencyModel:
    def test_returns_model_when_found(self, mock_db):
        model = MagicMock()
        chain = _make_chain(mock_db, first_val=model)
        chain.filter.return_value = chain

        result = QualificationService.get_competency_model(
            mock_db, position_type="ENGINEER", level_id=1
        )
        assert result == model

    def test_returns_none_when_not_found(self, mock_db):
        chain = _make_chain(mock_db, first_val=None)
        chain.filter.return_value = chain

        result = QualificationService.get_competency_model(
            mock_db, position_type="MANAGER", level_id=99
        )
        assert result is None


# ---------------------------------------------------------------------------
# certify_employee
# ---------------------------------------------------------------------------

class TestCertifyEmployee:
    def test_raises_when_employee_not_found(self, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None

        with pytest.raises(ValueError, match="员工"):
            QualificationService.certify_employee(
                mock_db,
                employee_id=999,
                position_type="ENGINEER",
                level_id=1,
                assessment_details={},
                certifier_id=1,
            )

    def test_raises_when_level_not_found(self, mock_db):
        employee = MagicMock()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            # First call: employee found; second: level not found
            chain.first.return_value = employee if call_count[0] == 1 else None
            return chain

        mock_db.query.side_effect = query_side_effect

        with pytest.raises(ValueError, match="等级"):
            QualificationService.certify_employee(
                mock_db,
                employee_id=1,
                position_type="ENGINEER",
                level_id=999,
                assessment_details={},
                certifier_id=1,
            )

    def test_creates_new_qualification_when_none_exists(self, mock_db):
        employee = MagicMock()
        level = MagicMock()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            if call_count[0] == 1:
                chain.first.return_value = employee
            elif call_count[0] == 2:
                chain.first.return_value = level
            else:
                chain.first.return_value = None  # no existing qualification
            return chain

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.qualification_service.EmployeeQualification"
        ) as MockQual:
            mock_qual = MagicMock()
            MockQual.return_value = mock_qual
            mock_db.refresh.return_value = None

            result = QualificationService.certify_employee(
                mock_db,
                employee_id=1,
                position_type="ENGINEER",
                level_id=1,
                assessment_details={"score": 90},
                certifier_id=5,
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# assess_employee
# ---------------------------------------------------------------------------

class TestAssessEmployee:
    def test_creates_assessment(self, mock_db):
        with patch(
            "app.services.qualification_service.QualificationAssessment"
        ) as MockAssessment, \
             patch.object(
            QualificationService, "_calculate_total_score", return_value=85.0
        ), patch.object(
            QualificationService, "_determine_result", return_value=MagicMock()
        ):
            mock_assessment = MagicMock()
            MockAssessment.return_value = mock_assessment
            mock_db.refresh.return_value = None

            result = QualificationService.assess_employee(
                mock_db,
                employee_id=1,
                assessment_type="ANNUAL",
                scores={"technical": 90, "communication": 80},
                assessor_id=2,
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
