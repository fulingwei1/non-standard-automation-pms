# -*- coding: utf-8 -*-
"""第十八批 - 调试问题同步服务单元测试"""
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest

try:
    from app.services.debug_issue_sync_service import DebugIssueSyncService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return DebugIssueSyncService(db)


def make_issue(category="PROJECT", issue_type="DEFECT", status="OPEN",
               resolved_at=None, report_date=None, tags=None, issue_no="ISS-001",
               issue_id=1):
    issue = MagicMock()
    issue.id = issue_id
    issue.category = category
    issue.issue_type = issue_type
    issue.status = status
    issue.resolved_at = resolved_at
    issue.report_date = report_date
    issue.tags = tags or []
    issue.issue_no = issue_no
    issue.project_id = 10
    issue.reporter_id = 2
    issue.assignee_id = 3
    issue.description = "test desc"
    issue.severity = "HIGH"
    issue.solution = "fixed"
    issue.root_cause = "code bug"
    issue.title = "Test Issue"
    return issue


class TestDebugIssueSyncServiceInit:
    def test_init_sets_db(self, db, service):
        assert service.db is db


class TestSyncMechanicalDebugIssue:
    def test_returns_none_if_issue_not_found(self, db, service):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_mechanical_debug_issue(99)
        assert result is None

    def test_returns_none_if_not_project_defect(self, db, service):
        issue = make_issue(category="PROJECT", issue_type="BUG")
        db.query.return_value.filter.return_value.first.return_value = issue
        result = service.sync_mechanical_debug_issue(1)
        assert result is None

    def test_returns_existing_if_not_force(self, db, service):
        issue = make_issue()
        existing = MagicMock()

        def _query_side(*args, **kwargs):
            m = MagicMock()
            # First call: Issue lookup
            # Second call: existing debug lookup
            return m

        # Simulate two different query calls
        issue_q = MagicMock()
        issue_q.filter.return_value.first.return_value = issue
        debug_q = MagicMock()
        debug_q.filter.return_value.first.return_value = existing

        db.query.side_effect = [issue_q, debug_q]
        result = service.sync_mechanical_debug_issue(1, force_update=False)
        assert result is existing

    def test_creates_new_debug_issue(self, db, service):
        issue = make_issue()
        issue_q = MagicMock()
        issue_q.filter.return_value.first.return_value = issue
        debug_q = MagicMock()
        debug_q.filter.return_value.first.return_value = None
        db.query.side_effect = [issue_q, debug_q]

        new_debug = MagicMock()
        db.refresh.return_value = None
        db.add.return_value = None

        with patch("app.services.debug_issue_sync_service.MechanicalDebugIssue", return_value=new_debug):
            result = service.sync_mechanical_debug_issue(1, force_update=False)
        db.add.assert_called_once()
        db.commit.assert_called()


class TestSyncIssue:
    def test_issue_not_found_returns_error(self, db, service):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_issue(999)
        assert result["synced"] is False
        assert "不存在" in result["error"]

    def test_project_defect_syncs_mechanical(self, db, service):
        issue = make_issue(category="PROJECT", issue_type="DEFECT")
        db.query.return_value.filter.return_value.first.return_value = issue

        with patch.object(service, "sync_mechanical_debug_issue") as mock_sync:
            mock_debug = MagicMock()
            mock_debug.id = 42
            mock_sync.return_value = mock_debug
            result = service.sync_issue(1)

        assert result["synced"] is True
        assert result["type"] == "mechanical_debug"

    def test_project_bug_syncs_test_bug(self, db, service):
        issue = make_issue(category="PROJECT", issue_type="BUG")
        db.query.return_value.filter.return_value.first.return_value = issue

        with patch.object(service, "sync_test_bug_record") as mock_sync:
            mock_bug = MagicMock()
            mock_bug.id = 55
            mock_sync.return_value = mock_bug
            result = service.sync_issue(1)

        assert result["synced"] is True
        assert result["type"] == "test_bug"
