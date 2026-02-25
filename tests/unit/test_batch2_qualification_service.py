# -*- coding: utf-8 -*-
"""Qualification Service 测试 - Batch 2"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.services.qualification_service import QualificationService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    return db


class TestGetQualificationLevels:
    def test_all_levels(self, mock_db):
        levels = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = levels
        result = QualificationService.get_qualification_levels(mock_db)
        assert len(result) == 2

    def test_filter_by_role_type(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = QualificationService.get_qualification_levels(mock_db, role_type="ENGINEER")
        assert result == []

    def test_active_filter_none(self, mock_db):
        mock_db.query.return_value.order_by.return_value.all.return_value = [MagicMock()]
        result = QualificationService.get_qualification_levels(mock_db, is_active=None)
        assert len(result) == 1


class TestGetCompetencyModel:
    def test_found(self, mock_db):
        model = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = model
        result = QualificationService.get_competency_model(mock_db, "ENGINEER", 1)
        assert result == model

    def test_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = QualificationService.get_competency_model(mock_db, "UNKNOWN", 999)
        assert result is None

    def test_with_subtype(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = MagicMock()
        result = QualificationService.get_competency_model(mock_db, "ENGINEER", 1, "SOFTWARE")
        assert result is not None


class TestGetEmployeeQualification:
    def test_found(self, mock_db):
        qual = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = qual
        result = QualificationService.get_employee_qualification(mock_db, 1)
        assert result == qual

    def test_with_position_type(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = QualificationService.get_employee_qualification(mock_db, 1, "ENGINEER")
        assert result is None


class TestCertifyEmployee:
    def test_employee_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="员工.*不存在"):
            QualificationService.certify_employee(mock_db, 999, "ENG", 1, {}, 1)

    def test_level_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.side_effect = [MagicMock(), None]
        with pytest.raises(ValueError, match="等级.*不存在"):
            QualificationService.certify_employee(mock_db, 1, "ENG", 999, {}, 1)

    def test_create_new_qualification(self, mock_db):
        employee = MagicMock()
        level = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [employee, level, None]
        result = QualificationService.certify_employee(
            mock_db, 1, "ENGINEER", 1, {"skill": 90}, 2
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_existing_qualification(self, mock_db):
        employee = MagicMock()
        level = MagicMock()
        existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [employee, level, existing]
        result = QualificationService.certify_employee(
            mock_db, 1, "ENGINEER", 2, {"skill": 95}, 3, certified_date=date(2024, 6, 1)
        )
        assert existing.current_level_id == 2
        mock_db.commit.assert_called_once()

    def test_with_valid_until(self, mock_db):
        employee = MagicMock()
        level = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [employee, level, None]
        result = QualificationService.certify_employee(
            mock_db, 1, "ENG", 1, {}, 1, valid_until=date(2025, 12, 31)
        )
        mock_db.add.assert_called_once()


class TestAssessEmployee:
    @patch('app.services.qualification_service.save_obj')
    def test_assess(self, mock_save, mock_db):
        scores = {"technical": 85, "communication": 70}
        result = QualificationService.assess_employee(
            mock_db, 1, "ANNUAL", scores, assessor_id=2
        )
        mock_save.assert_called_once()
        assert result.total_score == Decimal("77.50")

    @patch('app.services.qualification_service.save_obj')
    def test_assess_pass(self, mock_save, mock_db):
        scores = {"a": 90, "b": 85}
        result = QualificationService.assess_employee(mock_db, 1, "ANNUAL", scores)
        assert result.result  # Should be PASS enum

    @patch('app.services.qualification_service.save_obj')
    def test_assess_with_comments(self, mock_save, mock_db):
        result = QualificationService.assess_employee(
            mock_db, 1, "QUARTERLY", {"skill": 70}, comments="需要提升"
        )
        assert result.comments == "需要提升"


class TestCalculateTotalScore:
    def test_normal_scores(self):
        result = QualificationService._calculate_total_score({"a": 80, "b": 90})
        assert result == Decimal("85.00")

    def test_empty_scores(self):
        result = QualificationService._calculate_total_score({})
        assert result == Decimal("0.00")

    def test_single_score(self):
        result = QualificationService._calculate_total_score({"skill": 75})
        assert result == Decimal("75.00")

    def test_non_numeric_values(self):
        result = QualificationService._calculate_total_score({"a": "not_number", "b": 80})
        assert result == Decimal("40.00")  # 0 + 80 / 2


class TestDetermineResult:
    def test_pass(self):
        result = QualificationService._determine_result(Decimal("85"))
        # Should return PASS enum
        assert result is not None

    def test_partial(self):
        result = QualificationService._determine_result(Decimal("70"))
        assert result is not None

    def test_fail(self):
        result = QualificationService._determine_result(Decimal("50"))
        assert result is not None

    def test_boundary_80(self):
        result_80 = QualificationService._determine_result(Decimal("80"))
        result_79 = QualificationService._determine_result(Decimal("79"))
        assert result_80 != result_79

    def test_boundary_60(self):
        result_60 = QualificationService._determine_result(Decimal("60"))
        result_59 = QualificationService._determine_result(Decimal("59"))
        assert result_60 != result_59


class TestCheckPromotionEligibility:
    @patch.object(QualificationService, 'get_employee_qualification', return_value=None)
    def test_no_qualification(self, mock_method, mock_db):
        result = QualificationService.check_promotion_eligibility(mock_db, 1, 2)
        assert result['eligible'] is False
        assert '尚未获得' in result['reason']

    @patch.object(QualificationService, 'get_employee_qualification')
    def test_level_not_found(self, mock_method, mock_db):
        qual = MagicMock()
        qual.current_level_id = 1
        mock_method.return_value = qual
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = QualificationService.check_promotion_eligibility(mock_db, 1, 2)
        assert result['eligible'] is False

    @patch.object(QualificationService, 'get_employee_qualification')
    def test_target_level_lower(self, mock_method, mock_db):
        qual = MagicMock()
        qual.current_level_id = 2
        mock_method.return_value = qual
        current = MagicMock()
        current.level_order = 3
        target = MagicMock()
        target.level_order = 2
        mock_db.query.return_value.filter.return_value.first.side_effect = [current, target]
        result = QualificationService.check_promotion_eligibility(mock_db, 1, 1)
        assert result['eligible'] is False

    @patch.object(QualificationService, 'get_employee_qualification')
    def test_no_assessment(self, mock_method, mock_db):
        qual = MagicMock()
        qual.id = 1
        qual.current_level_id = 1
        mock_method.return_value = qual
        current = MagicMock()
        current.level_order = 1
        target = MagicMock()
        target.level_order = 2
        mock_db.query.return_value.filter.return_value.first.side_effect = [current, target]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = QualificationService.check_promotion_eligibility(mock_db, 1, 2)
        assert result['eligible'] is False
        assert '评估' in result['reason']

    @patch.object(QualificationService, 'get_employee_qualification')
    def test_eligible(self, mock_method, mock_db):
        from app.models.qualification import AssessmentResultEnum
        qual = MagicMock()
        qual.id = 1
        qual.current_level_id = 1
        mock_method.return_value = qual
        current = MagicMock()
        current.level_order = 1
        current.level_code = "L1"
        target = MagicMock()
        target.level_order = 2
        target.level_code = "L2"
        assessment = MagicMock()
        assessment.result = AssessmentResultEnum.PASS
        assessment.total_score = Decimal("90")
        mock_db.query.return_value.filter.return_value.first.side_effect = [current, target]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = assessment
        result = QualificationService.check_promotion_eligibility(mock_db, 1, 2)
        assert result['eligible'] is True


class TestGetAssessmentHistory:
    def test_empty(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = QualificationService.get_assessment_history(mock_db, 1)
        assert result == []

    def test_with_qualification_id(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [MagicMock()]
        result = QualificationService.get_assessment_history(mock_db, 1, qualification_id=1)
        assert len(result) == 1


class TestGetCompetencyModelsByPosition:
    def test_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.join.return_value.order_by.return_value.all.return_value = [MagicMock()]
        result = QualificationService.get_competency_models_by_position(mock_db, "ENGINEER")
        assert len(result) == 1

    def test_with_subtype(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.join.return_value.order_by.return_value.all.return_value = []
        result = QualificationService.get_competency_models_by_position(mock_db, "ENGINEER", "SOFTWARE")
        assert result == []
