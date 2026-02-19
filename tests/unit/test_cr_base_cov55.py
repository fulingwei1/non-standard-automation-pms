# -*- coding: utf-8 -*-
"""
Tests for app/services/collaboration_rating/base.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.collaboration_rating.base import CollaborationRatingService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


def test_service_init(mock_db):
    """测试服务初始化"""
    with patch("app.services.collaboration_rating.base.CollaboratorSelector"), \
         patch("app.services.collaboration_rating.base.RatingManager"), \
         patch("app.services.collaboration_rating.base.RatingStatistics"):
        service = CollaborationRatingService(db=mock_db)
        assert service.db is mock_db
        assert service.selector is not None
        assert service.ratings is not None
        assert service.statistics is not None


def test_job_type_department_map():
    """测试岗位类型映射常量"""
    mapping = CollaborationRatingService.JOB_TYPE_DEPARTMENT_MAP
    assert "mechanical" in mapping
    assert "test" in mapping
    assert "electrical" in mapping
    assert "solution" in mapping


def test_get_average_collaboration_score_delegates(mock_db):
    """get_average_collaboration_score 委托给 statistics"""
    with patch("app.services.collaboration_rating.base.CollaboratorSelector"), \
         patch("app.services.collaboration_rating.base.RatingManager"), \
         patch("app.services.collaboration_rating.base.RatingStatistics") as MockStats:
        service = CollaborationRatingService(db=mock_db)
        service.statistics.get_average_collaboration_score.return_value = 85
        result = service.get_average_collaboration_score(1, 1)
        service.statistics.get_average_collaboration_score.assert_called_once_with(1, 1)


def test_get_rating_statistics_delegates(mock_db):
    """get_rating_statistics 委托给 statistics"""
    with patch("app.services.collaboration_rating.base.CollaboratorSelector"), \
         patch("app.services.collaboration_rating.base.RatingManager"), \
         patch("app.services.collaboration_rating.base.RatingStatistics"):
        service = CollaborationRatingService(db=mock_db)
        service.statistics.get_rating_statistics.return_value = {"total": 0}
        result = service.get_rating_statistics(period_id=1)
        service.statistics.get_rating_statistics.assert_called_once_with(period_id=1)


def test_submit_rating_delegates(mock_db):
    """submit_rating 委托给 ratings"""
    with patch("app.services.collaboration_rating.base.CollaboratorSelector"), \
         patch("app.services.collaboration_rating.base.RatingManager"), \
         patch("app.services.collaboration_rating.base.RatingStatistics"):
        service = CollaborationRatingService(db=mock_db)
        service.ratings.submit_rating.return_value = True
        result = service.submit_rating(1, 2, {})
        service.ratings.submit_rating.assert_called_once()


def test_auto_select_collaborators_delegates(mock_db):
    """auto_select_collaborators 委托给 selector"""
    with patch("app.services.collaboration_rating.base.CollaboratorSelector"), \
         patch("app.services.collaboration_rating.base.RatingManager"), \
         patch("app.services.collaboration_rating.base.RatingStatistics"):
        service = CollaborationRatingService(db=mock_db)
        service.selector.auto_select_collaborators.return_value = []
        result = service.auto_select_collaborators(1, 2)
        service.selector.auto_select_collaborators.assert_called_once()


def test_analyze_rating_quality_delegates(mock_db):
    """analyze_rating_quality 委托给 statistics"""
    with patch("app.services.collaboration_rating.base.CollaboratorSelector"), \
         patch("app.services.collaboration_rating.base.RatingManager"), \
         patch("app.services.collaboration_rating.base.RatingStatistics"):
        service = CollaborationRatingService(db=mock_db)
        service.statistics.analyze_rating_quality.return_value = {}
        result = service.analyze_rating_quality(period_id=99)
        service.statistics.analyze_rating_quality.assert_called_once_with(period_id=99)
