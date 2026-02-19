# -*- coding: utf-8 -*-
"""
Unit tests for staff_matching score calculators (第三十批)
"""
from unittest.mock import MagicMock

import pytest

from app.services.staff_matching.score_calculators import (
    SkillScoreCalculator,
    DomainScoreCalculator,
    AttitudeScoreCalculator,
)


@pytest.fixture
def mock_db():
    return MagicMock()


# ---------------------------------------------------------------------------
# SkillScoreCalculator
# ---------------------------------------------------------------------------

class TestSkillScoreCalculator:
    def test_returns_60_base_when_no_required_skills(self, mock_db):
        profile = MagicMock()
        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=profile,
            required_skills=[], preferred_skills=[]
        )
        assert result["score"] == 60.0

    def test_returns_result_dict_with_expected_keys(self, mock_db):
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[{"tag_id": 1, "min_score": 3, "tag_name": "Python"}],
            preferred_skills=[]
        )
        assert "score" in result
        assert "matched" in result
        assert "missing" in result

    def test_adds_to_missing_when_skill_not_found(self, mock_db):
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[{"tag_id": 99, "min_score": 4, "tag_name": "Kubernetes"}],
            preferred_skills=[]
        )
        assert "Kubernetes" in result["missing"] or "Tag-99" in result["missing"]

    def test_adds_to_matched_when_employee_has_skill(self, mock_db):
        skill_eval = MagicMock()
        skill_eval.tag_id = 1
        skill_eval.score = 4
        skill_eval.tag = MagicMock()
        skill_eval.tag.tag_name = "Python"

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [skill_eval]

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[{"tag_id": 1, "min_score": 3, "tag_name": "Python"}],
            preferred_skills=[]
        )
        assert "Python" in result["matched"]
        assert result["score"] > 0

    def test_preferred_skills_add_bonus(self, mock_db):
        skill_eval = MagicMock()
        skill_eval.tag_id = 2
        skill_eval.score = 4
        skill_eval.tag = MagicMock()
        skill_eval.tag.tag_name = "Docker"

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [skill_eval]

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[],
            preferred_skills=[{"tag_id": 2, "tag_name": "Docker"}]
        )
        # With preferred skill having score >= 3, should add bonus
        assert result["score"] >= 60.0

    def test_score_capped_at_100(self, mock_db):
        """Score should never exceed 100"""
        skill_evals = []
        for i in range(10):
            e = MagicMock()
            e.tag_id = i
            e.score = 5
            e.tag = MagicMock()
            e.tag.tag_name = f"Skill{i}"
            skill_evals.append(e)

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = skill_evals

        required = [{"tag_id": i, "min_score": 3, "tag_name": f"Skill{i}"} for i in range(10)]
        preferred = [{"tag_id": i} for i in range(5)]

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=required, preferred_skills=preferred
        )
        assert result["score"] <= 100


# ---------------------------------------------------------------------------
# DomainScoreCalculator
# ---------------------------------------------------------------------------

class TestDomainScoreCalculator:
    def test_returns_60_base_when_no_required_domains(self, mock_db):
        result = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None, required_domains=[]
        )
        assert result == 60.0

    def test_returns_score_when_employee_has_matching_domain(self, mock_db):
        domain_eval = MagicMock()
        domain_eval.tag_id = 10
        domain_eval.score = 4

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [domain_eval]

        result = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[{"tag_id": 10, "min_score": 3}]
        )
        assert result > 0

    def test_returns_reduced_score_when_below_min(self, mock_db):
        domain_eval = MagicMock()
        domain_eval.tag_id = 10
        domain_eval.score = 2  # below min_score=3

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [domain_eval]

        result_met = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[{"tag_id": 10, "min_score": 3}]
        )
        domain_eval.score = 4  # above min_score=3
        result_unmet = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[{"tag_id": 10, "min_score": 3}]
        )
        assert result_met <= result_unmet


# ---------------------------------------------------------------------------
# AttitudeScoreCalculator
# ---------------------------------------------------------------------------

class TestAttitudeScoreCalculator:
    def test_uses_profile_attitude_score_when_available(self, mock_db):
        profile = MagicMock()
        profile.attitude_score = 4.0

        result = AttitudeScoreCalculator.calculate_attitude_score(
            mock_db, employee_id=1, profile=profile,
            required_attitudes=[]
        )
        # The service directly uses float(profile.attitude_score) as base_score
        assert result == 4.0

    def test_calculates_from_evaluations_when_no_profile(self, mock_db):
        profile = MagicMock()
        profile.attitude_score = None

        eval1 = MagicMock()
        eval1.score = 3.5
        eval2 = MagicMock()
        eval2.score = 4.5

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [eval1, eval2]

        result = AttitudeScoreCalculator.calculate_attitude_score(
            mock_db, employee_id=1, profile=profile,
            required_attitudes=[]
        )
        # avg_score = 4.0, base_score = (4.0 / 5.0) * 100 = 80
        assert result == 80.0

    def test_returns_60_base_when_no_evaluations(self, mock_db):
        profile = MagicMock()
        profile.attitude_score = None

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = AttitudeScoreCalculator.calculate_attitude_score(
            mock_db, employee_id=1, profile=profile,
            required_attitudes=[]
        )
        assert result == 60.0
