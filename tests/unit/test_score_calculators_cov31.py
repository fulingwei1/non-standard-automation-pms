# -*- coding: utf-8 -*-
"""
Unit tests for score_calculators (SkillScoreCalculator, DomainScoreCalculator, etc.) (第三十一批)
"""
from unittest.mock import MagicMock

import pytest

from app.services.staff_matching.score_calculators import (
    DomainScoreCalculator,
    SkillScoreCalculator,
)


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_skill_eval(tag_id, score, tag_name="技能A"):
    ev = MagicMock()
    ev.tag_id = tag_id
    ev.score = score
    ev.is_valid = True
    ev.tag = MagicMock()
    ev.tag.tag_name = tag_name
    return ev


# ---------------------------------------------------------------------------
# SkillScoreCalculator.calculate_skill_score
# ---------------------------------------------------------------------------

class TestSkillScoreCalculator:
    def test_no_required_skills_returns_60(self, mock_db):
        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[], preferred_skills=[]
        )
        assert result["score"] == 60.0

    def test_missing_required_skill_reduces_score(self, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = []  # 员工没有任何技能

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[{"tag_id": 10, "min_score": 3, "tag_name": "Python"}],
            preferred_skills=[]
        )
        assert result["score"] < 60.0
        assert "Python" in result["missing"]

    def test_matched_required_skill_above_min(self, mock_db):
        ev = _make_skill_eval(tag_id=10, score=4.0, tag_name="Python")
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = [ev]

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[{"tag_id": 10, "min_score": 3, "tag_name": "Python"}],
            preferred_skills=[]
        )
        assert result["score"] > 60.0
        assert "Python" in result["matched"]

    def test_preferred_skills_add_bonus(self, mock_db):
        ev = _make_skill_eval(tag_id=20, score=4.0, tag_name="Java")
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = [ev]

        result_with = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=[],
            preferred_skills=[{"tag_id": 20, "tag_name": "Java"}]
        )
        # 基础 60 + 加成 5
        assert result_with["score"] >= 65.0

    def test_score_capped_at_100(self, mock_db):
        evals = [_make_skill_eval(tag_id=i, score=5.0) for i in range(1, 6)]
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = evals

        required = [{"tag_id": i, "min_score": 3, "tag_name": f"S{i}"} for i in range(1, 6)]
        preferred = [{"tag_id": i, "tag_name": f"P{i}"} for i in range(1, 5)]

        result = SkillScoreCalculator.calculate_skill_score(
            mock_db, employee_id=1, profile=None,
            required_skills=required,
            preferred_skills=preferred
        )
        assert result["score"] <= 100.0


# ---------------------------------------------------------------------------
# DomainScoreCalculator.calculate_domain_score
# ---------------------------------------------------------------------------

class TestDomainScoreCalculator:
    def test_no_required_domains_returns_60(self, mock_db):
        score = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[]
        )
        assert score == 60.0

    def test_matched_domain_contributes_to_score(self, mock_db):
        ev = MagicMock()
        ev.tag_id = 5
        ev.score = 4.0
        ev.is_valid = True

        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = [ev]

        score = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[{"tag_id": 5, "min_score": 3}]
        )
        assert score > 0.0

    def test_unmatched_domain_reduces_score(self, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = []

        score = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[{"tag_id": 99, "min_score": 3}]
        )
        assert score == 0.0

    def test_below_min_score_reduces_contribution(self, mock_db):
        ev = MagicMock()
        ev.tag_id = 5
        ev.score = 2.0  # below min_score=3
        ev.is_valid = True

        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.join.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = [ev]

        score = DomainScoreCalculator.calculate_domain_score(
            mock_db, employee_id=1, profile=None,
            required_domains=[{"tag_id": 5, "min_score": 3}]
        )
        # 未达标时乘以50%，故 score = (2/5) * 50 = 20
        assert score == pytest.approx(20.0, rel=0.01)
