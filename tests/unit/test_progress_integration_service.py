# -*- coding: utf-8 -*-
"""进度跟踪联动服务测试"""
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.progress_integration_service import ProgressIntegrationService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return ProgressIntegrationService(db)


class TestHandleShortageAlertCreated:
    def test_no_project_id(self, service):
        alert = MagicMock(project_id=None)
        result = service.handle_shortage_alert_created(alert)
        assert result == []

    def test_low_level_alert(self, service, db):
        alert = MagicMock(
            project_id=1, alert_level='level1', alert_data=json.dumps({'impact_type': 'none', 'estimated_delay_days': 0})
        )
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.handle_shortage_alert_created(alert)
        assert result == []

    def test_critical_alert_blocks_tasks(self, service, db):
        alert = MagicMock(
            project_id=1, alert_level='CRITICAL', alert_no='ALERT-001',
            target_name='Material A',
            alert_data=json.dumps({'impact_type': 'stop', 'estimated_delay_days': 5})
        )
        task = MagicMock(status='IN_PROGRESS', plan_end=datetime.now())
        # The function chains multiple .filter() and .query() calls; make all return [task]
        mock_q = MagicMock()
        mock_q.all.return_value = [task]
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        db.query.return_value.filter.return_value = mock_q
        result = service.handle_shortage_alert_created(alert)
        assert len(result) == 1
        assert task.status == 'BLOCKED'


class TestHandleShortageAlertResolved:
    def test_no_project_id(self, service):
        alert = MagicMock(project_id=None)
        result = service.handle_shortage_alert_resolved(alert)
        assert result == []

    @patch('app.services.progress_integration_service.apply_keyword_filter')
    @patch('app.services.progress_integration_service.or_')
    def test_unblock_tasks(self, mock_or, mock_akf, service, db):
        alert = MagicMock(project_id=1, id=1, alert_no='ALERT-001', target_no='MAT-001')
        task = MagicMock(status='BLOCKED', block_reason='ALERT-001')
        # First query chain: Task query -> filter(project_id, status) -> filter(or_) -> all
        task_query_mock = MagicMock()
        task_query_mock.filter.return_value = task_query_mock
        task_query_mock.all.return_value = [task]
        # Second query chain: AlertRecord count
        alert_query_mock = MagicMock()
        alert_query_mock.filter.return_value = alert_query_mock
        alert_query_mock.count.return_value = 0
        # apply_keyword_filter returns a subquery
        mock_akf.return_value = MagicMock()
        db.query.side_effect = [task_query_mock, MagicMock(), MagicMock(), alert_query_mock]
        result = service.handle_shortage_alert_resolved(alert)
        assert len(result) == 1
        assert task.status == 'IN_PROGRESS'


class TestHandleEcnApproved:
    def test_no_project_id(self, service):
        ecn = MagicMock(project_id=None, schedule_impact_days=0, tasks=[])
        result = service.handle_ecn_approved(ecn)
        assert result['adjusted_tasks'] == []

    def test_minor_impact(self, service, db):
        ecn = MagicMock(project_id=1, schedule_impact_days=2, tasks=[], machine_id=None)
        result = service.handle_ecn_approved(ecn, threshold_days=3)
        assert result['adjusted_tasks'] == []

    def test_major_impact_adjusts_tasks(self, service, db):
        ecn = MagicMock(project_id=1, schedule_impact_days=5, machine_id=None, tasks=[])
        task = MagicMock(
            id=1, task_name='Test', plan_end=datetime.now(),
            actual_start=None, plan_start=None
        )
        db.query.return_value.filter.return_value.all.side_effect = [[task], []]
        result = service.handle_ecn_approved(ecn, threshold_days=3)
        assert len(result['adjusted_tasks']) == 1


class TestCheckMilestoneCompletionRequirements:
    def test_no_requirements(self, service):
        milestone = MagicMock(milestone_type='REGULAR', deliverables=None)
        # Remove acceptance_required so hasattr returns False
        del milestone.acceptance_required
        ok, missing = service.check_milestone_completion_requirements(milestone)
        assert ok is True

    def test_delivery_with_unapproved(self, service):
        deliverables = json.dumps([{'name': 'Doc1', 'status': 'PENDING'}])
        milestone = MagicMock(
            milestone_type='DELIVERY', deliverables=deliverables, project_id=1
        )
        del milestone.acceptance_required  # hasattr returns False
        ok, missing = service.check_milestone_completion_requirements(milestone)
        assert ok is False
        assert '交付物未全部审批' in missing


class TestHandleAcceptanceFailed:
    def test_not_failed(self, service):
        order = MagicMock(overall_result='PASSED')
        result = service.handle_acceptance_failed(order)
        assert result == []

    def test_blocks_milestones(self, service, db):
        order = MagicMock(
            overall_result='FAILED', acceptance_type='FAT',
            project_id=1, order_no='AC-001', created_by=1, id=1
        )
        milestone = MagicMock(stage_code='S6', status='PENDING', milestone_name='Test')
        db.query.return_value.filter.return_value.all.return_value = [milestone]
        result = service.handle_acceptance_failed(order)
        assert len(result) == 1
        assert milestone.status == 'BLOCKED'


class TestHandleAcceptancePassed:
    def test_not_passed(self, service):
        order = MagicMock(overall_result='FAILED')
        result = service.handle_acceptance_passed(order)
        assert result == []

    def test_unblocks_milestones(self, service, db):
        order = MagicMock(
            overall_result='PASSED', acceptance_type='FAT',
            project_id=1, id=1
        )
        milestone = MagicMock(stage_code='S6', status='BLOCKED')
        db.query.return_value.filter.return_value.all.return_value = [milestone]
        db.query.return_value.filter.return_value.count.return_value = 0
        result = service.handle_acceptance_passed(order)
        assert len(result) == 1
