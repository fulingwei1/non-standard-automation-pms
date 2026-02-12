# -*- coding: utf-8 -*-
"""员工档案聚合 单元测试"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.staff_matching.profile_aggregation import ProfileAggregator


class TestAggregateEmployeeProfile:
    def test_creates_profile_if_not_exists(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        with patch("app.services.staff_matching.profile_aggregation.HrEmployeeProfile") as MockProfile:
            profile = MagicMock()
            MockProfile.return_value = profile
            result = ProfileAggregator.aggregate_employee_profile(db, 1)
            db.add.assert_called_once()

    def test_existing_profile_updated(self):
        db = MagicMock()
        profile = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = profile
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = ProfileAggregator.aggregate_employee_profile(db, 1)
        db.commit.assert_called()


class TestUpdateEmployeeWorkload:
    def test_creates_profile_if_not_exists(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.staff_matching.profile_aggregation.HrEmployeeProfile") as MockProfile:
            MockProfile.return_value = MagicMock()
            ProfileAggregator.update_employee_workload(db, 1)
            db.add.assert_called_once()

    def test_calculates_workload(self):
        db = MagicMock()
        profile = MagicMock()
        user = MagicMock()
        user.id = 10

        assignment = MagicMock()
        assignment.allocation_pct = 50
        assignment.is_active = True

        # First query returns profile, second returns user, third returns assignments
        db.query.return_value.filter.return_value.first.side_effect = [profile, user]
        db.query.return_value.filter.return_value.all.return_value = [assignment]

        ProfileAggregator.update_employee_workload(db, 1)
        db.commit.assert_called()
