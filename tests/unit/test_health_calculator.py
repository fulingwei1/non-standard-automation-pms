# -*- coding: utf-8 -*-
"""项目健康度计算器测试"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.health_calculator import HealthCalculator


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calc(db):
    return HealthCalculator(db)


class TestCalculateHealth:
    def test_closed_project(self, calc):
        project = MagicMock(status='ST30')
        assert calc.calculate_health(project) == 'H4'

    def test_cancelled_project(self, calc):
        project = MagicMock(status='ST99')
        assert calc.calculate_health(project) == 'H4'

    def test_blocked_status(self, calc, db):
        project = MagicMock(status='ST14', id=1)
        assert calc.calculate_health(project) == 'H3'

    def test_normal_project(self, calc, db):
        project = MagicMock(
            status='ST01', id=1,
            planned_end_date=date.today() + timedelta(days=100),
            planned_start_date=date.today() - timedelta(days=10),
            progress_pct=Decimal("10")
        )
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        assert calc.calculate_health(project) == 'H1'


class TestIsClosed:
    def test_st30(self, calc):
        assert calc._is_closed(MagicMock(status='ST30')) is True

    def test_active(self, calc):
        assert calc._is_closed(MagicMock(status='ST01')) is False


class TestIsBlocked:
    def test_blocked_status(self, calc, db):
        project = MagicMock(status='ST14', id=1)
        assert calc._is_blocked(project) is True

    def test_blocked_tasks(self, calc, db):
        project = MagicMock(status='ST01', id=1)
        db.query.return_value.filter.return_value.count.return_value = 1
        assert calc._is_blocked(project) is True

    def test_not_blocked(self, calc, db):
        project = MagicMock(status='ST01', id=1)
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        assert calc._is_blocked(project) is False


class TestHasRisks:
    def test_rectification_status(self, calc, db):
        project = MagicMock(status='ST22', id=1)
        assert calc._has_risks(project) is True

    def test_deadline_approaching(self, calc, db):
        project = MagicMock(
            status='ST01', id=1,
            planned_end_date=date.today() + timedelta(days=3),
            planned_start_date=date.today() - timedelta(days=30),
            progress_pct=Decimal("50")
        )
        assert calc._has_risks(project) is True


class TestDeadlineApproaching:
    def test_no_deadline(self, calc):
        project = MagicMock(planned_end_date=None)
        assert calc._is_deadline_approaching(project) is False

    def test_approaching(self, calc):
        project = MagicMock(planned_end_date=date.today() + timedelta(days=3))
        assert calc._is_deadline_approaching(project) is True

    def test_far_away(self, calc):
        project = MagicMock(planned_end_date=date.today() + timedelta(days=60))
        assert calc._is_deadline_approaching(project) is False


class TestScheduleVariance:
    def test_no_dates(self, calc):
        project = MagicMock(planned_end_date=None, planned_start_date=None)
        assert calc._has_schedule_variance(project) is False

    def test_behind_schedule(self, calc):
        project = MagicMock(
            planned_start_date=date.today() - timedelta(days=50),
            planned_end_date=date.today() + timedelta(days=50),
            progress_pct=Decimal("10")
        )
        assert calc._has_schedule_variance(project) is True

    def test_on_schedule(self, calc):
        project = MagicMock(
            planned_start_date=date.today() - timedelta(days=50),
            planned_end_date=date.today() + timedelta(days=50),
            progress_pct=Decimal("50")
        )
        assert calc._has_schedule_variance(project) is False


class TestCalculateAndUpdate:
    def test_no_change(self, calc, db):
        project = MagicMock(
            id=1, project_code='P001', health='H1', status='ST01',
            stage='S1', planned_end_date=date.today() + timedelta(days=100),
            planned_start_date=date.today() - timedelta(days=10),
            progress_pct=Decimal("10")
        )
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        result = calc.calculate_and_update(project)
        assert result['changed'] is False

    def test_health_changed(self, calc, db):
        project = MagicMock(
            id=1, project_code='P001', health='H1', status='ST30',
            stage='S9'
        )
        result = calc.calculate_and_update(project)
        assert result['changed'] is True
        assert result['new_health'] == 'H4'


class TestBatchCalculate:
    def test_batch(self, calc, db):
        project = MagicMock(
            id=1, project_code='P001', health='H1', status='ST01',
            is_active=True, is_archived=False, stage='S1',
            planned_end_date=date.today() + timedelta(days=100),
            planned_start_date=date.today(), progress_pct=Decimal("0")
        )
        query = MagicMock()
        query.count.return_value = 1
        query.offset.return_value.limit.return_value.all.return_value = [project]
        db.query.return_value.filter.return_value = query
        result = calc.batch_calculate()
        assert result['total'] == 1


class TestCalculateProjectHealth:
    def test_project_not_found(self, calc, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            calc.calculate_project_health(999)


class TestGetHealthDetails:
    def test_returns_details(self, calc, db):
        project = MagicMock(
            id=1, project_code='P001', health='H1', status='ST01',
            stage='S1', planned_end_date=date.today() + timedelta(days=100),
            planned_start_date=date.today(), progress_pct=Decimal("0")
        )
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        details = calc.get_health_details(project)
        assert 'checks' in details
        assert 'statistics' in details
