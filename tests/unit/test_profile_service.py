# -*- coding: utf-8 -*-
"""工程师档案管理服务 单元测试"""
from unittest.mock import MagicMock

import pytest

from app.services.engineer_performance.profile_service import ProfileService


def _make_service():
    db = MagicMock()
    return ProfileService(db)


class TestGetProfile:
    def test_found(self):
        s = _make_service()
        profile = MagicMock()
        s.db.query.return_value.filter.return_value.first.return_value = profile
        assert s.get_profile(1) is profile

    def test_not_found(self):
        s = _make_service()
        s.db.query.return_value.filter.return_value.first.return_value = None
        assert s.get_profile(999) is None


class TestCreateProfile:
    def test_creates_and_commits(self):
        s = _make_service()
        data = MagicMock()
        data.user_id = 1
        data.job_type = "ME"
        data.job_level = "junior"
        data.skills = []
        data.certifications = []
        data.job_start_date = None
        data.level_start_date = None

        result = s.create_profile(data)
        s.db.add.assert_called_once()
        s.db.commit.assert_called_once()


class TestUpdateProfile:
    def test_not_found(self):
        s = _make_service()
        s.db.query.return_value.filter.return_value.first.return_value = None
        data = MagicMock()
        result = s.update_profile(999, data)
        assert result is None

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
    def test_returns_tuple(self):
        s = _make_service()
        query = MagicMock()
        s.db.query.return_value.join.return_value = query
        query.filter.return_value = query
        query.count.return_value = 1
        query.offset.return_value.limit.return_value.all.return_value = [MagicMock()]
        items, total = s.list_profiles()
        assert total == 1
        assert len(items) == 1


class TestCountProfilesByConfig:
    def test_basic_count(self):
        s = _make_service()
        s.db.query.return_value.filter.return_value.count.return_value = 5
        assert s.count_profiles_by_config("ME") == 5
