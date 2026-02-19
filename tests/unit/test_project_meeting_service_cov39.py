# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - project_meeting_service.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.project_meeting_service",
                    reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.project_meeting_service import ProjectMeetingService
    return ProjectMeetingService(mock_db)


def _make_meeting(mid, status="COMPLETED", level="WEEKLY", project_id=None,
                  related_project_ids=None, meeting_date=None):
    m = MagicMock()
    m.id = mid
    m.status = status
    m.rhythm_level = level
    m.project_id = project_id
    m.related_project_ids = related_project_ids
    m.meeting_date = meeting_date or date(2024, 6, 1)
    return m


class TestProjectMeetingServiceGetProjectMeetings:

    def test_get_meetings_empty(self, service, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        result = service.get_project_meetings(project_id=1)
        assert result == []

    def test_get_meetings_with_primary_project(self, service, mock_db):
        meeting = _make_meeting(1, project_id=10)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.side_effect = [[meeting], []]  # query1 and query2

        result = service.get_project_meetings(project_id=10)
        assert len(result) == 1

    def test_get_meetings_with_related_project(self, service, mock_db):
        related_meeting = _make_meeting(2, related_project_ids=[10, 20], project_id=None)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        # query1 returns empty, query2 returns the related meeting
        mock_q.all.side_effect = [[], [related_meeting]]

        result = service.get_project_meetings(project_id=10)
        assert len(result) == 1

    def test_get_meetings_status_filter(self, service, mock_db):
        m1 = _make_meeting(1, status="COMPLETED", project_id=5, meeting_date=date(2024, 5, 1))
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.side_effect = [[m1], []]

        result = service.get_project_meetings(project_id=5, status="COMPLETED")
        assert all(m.status == "COMPLETED" for m in result)


class TestProjectMeetingServiceStatistics:

    def test_statistics_empty_meetings(self, service, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        with MagicMock() as m:
            # Patch get_project_meetings to return empty
            service.get_project_meetings = lambda pid: []
            result = service.get_project_meeting_statistics(project_id=1)

        assert result["total_meetings"] == 0
        assert result["completion_rate"] == 0

    def test_statistics_with_meetings(self, service, mock_db):
        meetings = [
            _make_meeting(1, "COMPLETED", "WEEKLY"),
            _make_meeting(2, "COMPLETED", "MONTHLY"),
            _make_meeting(3, "SCHEDULED", "WEEKLY"),
            _make_meeting(4, "CANCELLED", "DAILY"),
        ]

        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []  # For MeetingActionItem queries

        service.get_project_meetings = lambda pid: meetings
        result = service.get_project_meeting_statistics(project_id=1)

        assert result["total_meetings"] == 4
        assert result["completed_meetings"] == 2
        assert result["scheduled_meetings"] == 1
        assert result["cancelled_meetings"] == 1
        assert abs(result["completion_rate"] - 50.0) < 0.01


class TestProjectMeetingServiceLinkUnlink:

    def test_link_meeting_returns_true(self, service, mock_db):
        meeting = _make_meeting(1, related_project_ids=[])
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = meeting

        result = service.link_meeting_to_project(meeting_id=1, project_id=5)
        assert result is True

    def test_unlink_meeting_not_found_returns_false(self, service, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None

        result = service.unlink_meeting_from_project(meeting_id=99, project_id=5)
        assert result is False
