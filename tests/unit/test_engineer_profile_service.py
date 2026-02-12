# -*- coding: utf-8 -*-
"""Tests for app.services.engineer_performance.profile_service"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.engineer_performance.profile_service import ProfileService


def _make_service():
    db = MagicMock()
    return ProfileService(db)


class TestGetProfile:
    def test_returns_profile(self):
        s = _make_service()
        profile = MagicMock()
        s.db.query.return_value.filter.return_value.first.return_value = profile
        assert s.get_profile(1) == profile

    def test_returns_none(self):
        s = _make_service()
        s.db.query.return_value.filter.return_value.first.return_value = None
        assert s.get_profile(999) is None


class TestCreateProfile:
    def test_creates(self):
        s = _make_service()
        data = MagicMock()
        data.user_id = 1
        data.job_type = "ME"
        data.job_level = "senior"
        data.skills = ["CAD"]
        data.certifications = []
        data.job_start_date = None
        data.level_start_date = None

        with patch("app.services.engineer_performance.profile_service.EngineerProfile") as MockProf:
            MockProf.return_value = MagicMock()
            result = s.create_profile(data)
            s.db.add.assert_called_once()
            s.db.commit.assert_called()


class TestUpdateProfile:
    def test_returns_none_when_not_found(self):
        s = _make_service()
        s.db.query.return_value.filter.return_value.first.return_value = None
        data = MagicMock()
        data.model_dump.return_value = {}
        assert s.update_profile(999, data) is None

    def test_updates_fields(self):
        s = _make_service()
        profile = MagicMock()
        s.db.query.return_value.filter.return_value.first.return_value = profile
        data = MagicMock()
        data.model_dump.return_value = {"job_level": "senior"}
        result = s.update_profile(1, data)
        assert result is not None
        s.db.commit.assert_called()


class TestListProfiles:
    def test_returns_items_and_total(self):
        s = _make_service()
        q = s.db.query.return_value.join.return_value
        q.filter.return_value = q
        q.count.return_value = 5
        q.offset.return_value.limit.return_value.all.return_value = [MagicMock()] * 5
        items, total = s.list_profiles(limit=20, offset=0)
        assert total == 5
        assert len(items) == 5


class TestCountProfilesByConfig:
    def test_basic_count(self):
        s = _make_service()
        s.db.query.return_value.filter.return_value.count.return_value = 10
        assert s.count_profiles_by_config("ME") == 10
