# -*- coding: utf-8 -*-
"""第四十二批：collaboration_rating/base.py 单元测试"""
import pytest

pytest.importorskip("app.services.collaboration_rating.base")

from unittest.mock import MagicMock, patch


def make_service():
    db = MagicMock()
    with patch("app.services.collaboration_rating.base.CollaboratorSelector") as S, \
         patch("app.services.collaboration_rating.base.RatingManager") as R, \
         patch("app.services.collaboration_rating.base.RatingStatistics") as St:

        S.return_value = MagicMock()
        R.return_value = MagicMock()
        St.return_value = MagicMock()

        from app.services.collaboration_rating.base import CollaborationRatingService
        svc = CollaborationRatingService(db)
        return svc, S.return_value, R.return_value, St.return_value


# ------------------------------------------------------------------ tests ---

def test_service_has_sub_modules():
    svc, selector, ratings, statistics = make_service()
    assert svc.selector is selector
    assert svc.ratings is ratings
    assert svc.statistics is statistics


def test_auto_select_collaborators_delegates():
    svc, selector, _, _ = make_service()
    selector.auto_select_collaborators.return_value = ["u1"]
    result = svc.auto_select_collaborators(1, 2)
    selector.auto_select_collaborators.assert_called_once_with(1, 2)
    assert result == ["u1"]


def test_submit_rating_delegates():
    svc, _, ratings, _ = make_service()
    ratings.submit_rating.return_value = {"status": "ok"}
    result = svc.submit_rating(1, 2, 90)
    ratings.submit_rating.assert_called_once()
    assert result == {"status": "ok"}


def test_get_pending_ratings_delegates():
    svc, _, ratings, _ = make_service()
    ratings.get_pending_ratings.return_value = [{"id": 1}]
    result = svc.get_pending_ratings(1)
    ratings.get_pending_ratings.assert_called_once_with(1)
    assert len(result) == 1


def test_get_average_collaboration_score_delegates():
    svc, _, _, statistics = make_service()
    from decimal import Decimal
    statistics.get_average_collaboration_score.return_value = Decimal("80.0")
    result = svc.get_average_collaboration_score(1, 2)
    statistics.get_average_collaboration_score.assert_called_once_with(1, 2)
    assert result == Decimal("80.0")


def test_get_rating_statistics_delegates():
    svc, _, _, statistics = make_service()
    statistics.get_rating_statistics.return_value = {"total": 10}
    result = svc.get_rating_statistics(1)
    statistics.get_rating_statistics.assert_called_once_with(1)
    assert result["total"] == 10


def test_job_type_department_map_has_expected_keys():
    from app.services.collaboration_rating.base import CollaborationRatingService
    keys = CollaborationRatingService.JOB_TYPE_DEPARTMENT_MAP
    assert "mechanical" in keys
    assert "electrical" in keys
