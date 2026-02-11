# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock

from app.services.collaboration_rating.selector import CollaboratorSelector


class TestCollaboratorSelector:
    def setup_method(self):
        self.db = MagicMock()
        self.service = MagicMock()
        self.selector = CollaboratorSelector(self.db, self.service)

    def test_auto_select_no_period(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="考核周期不存在"):
            self.selector.auto_select_collaborators(1, 999)

    def test_auto_select_no_profile(self):
        period = MagicMock()
        self.db.query.return_value.filter.return_value.first.side_effect = [period, None]
        with pytest.raises(ValueError, match="工程师档案不存在"):
            self.selector.auto_select_collaborators(1, 1)

    def test_auto_select_no_projects(self):
        period = MagicMock(start_date="2025-01-01", end_date="2025-06-30")
        profile = MagicMock(job_type="mechanical")
        self.db.query.return_value.filter.return_value.first.side_effect = [period, profile]
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = self.selector.auto_select_collaborators(1, 1)
        assert result == []

    def test_auto_select_returns_collaborators(self):
        period = MagicMock(start_date="2025-01-01", end_date="2025-06-30")
        profile = MagicMock(job_type="mechanical")
        project = MagicMock(id=10)

        self.db.query.return_value.filter.return_value.first.side_effect = [period, profile]
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = [project]

        member1 = MagicMock(user_id=2)
        member2 = MagicMock(user_id=3)
        p1 = MagicMock(user_id=2, job_type="electrical")
        p2 = MagicMock(user_id=3, job_type="test")

        # members query, profiles query
        self.db.query.return_value.filter.return_value.all.side_effect = [[member1, member2], [p1, p2]]

        result = self.selector.auto_select_collaborators(1, 1, target_count=5)
        assert set(result) == {2, 3}

    def test_get_target_job_types(self):
        assert self.selector._get_target_job_types("mechanical") == ["electrical", "test"]
        assert self.selector._get_target_job_types("electrical") == ["mechanical", "test"]
        assert self.selector._get_target_job_types("test") == ["mechanical", "electrical"]
        assert self.selector._get_target_job_types("solution") == ["mechanical", "electrical", "test"]
        assert self.selector._get_target_job_types("unknown") == ["mechanical", "electrical", "test"]

    def test_get_collaborators_filters_by_job_type(self):
        member = MagicMock(user_id=5)
        profile = MagicMock(user_id=5, job_type="electrical")
        self.db.query.return_value.filter.return_value.all.side_effect = [[member], [profile]]

        result = self.selector._get_collaborators_from_projects(1, "mechanical", [10])
        assert result == [5]
