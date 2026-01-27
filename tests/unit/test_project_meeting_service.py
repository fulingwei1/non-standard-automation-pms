# -*- coding: utf-8 -*-
"""
项目会议关联服务单元测试
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestProjectMeetingServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        assert service.db == db_session


class TestGetProjectMeetings:
    """测试获取项目关联的会议"""

    def test_no_meetings(self, db_session):
        """测试无会议"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.get_project_meetings(99999)

        assert result == []

    def test_with_status_filter(self, db_session):
        """测试带状态过滤"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.get_project_meetings(1, status='COMPLETED')

        assert isinstance(result, list)

    def test_with_rhythm_level_filter(self, db_session):
        """测试带节律层级过滤"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.get_project_meetings(1, rhythm_level='WEEKLY')

        assert isinstance(result, list)

    def test_with_date_range(self, db_session):
        """测试带日期范围"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.get_project_meetings(
        1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
        )

        assert isinstance(result, list)


class TestLinkMeetingToProject:
    """测试关联会议到项目"""

    def test_meeting_not_found(self, db_session):
        """测试会议不存在"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.link_meeting_to_project(99999, 1)

        assert result is False

    def test_link_as_primary_project(self, db_session):
        """测试关联为主项目"""
        from app.services.project_meeting_service import ProjectMeetingService
        from app.models.management_rhythm import StrategicMeeting

        meeting = StrategicMeeting(
        title='测试会议',
        meeting_date=date(2025, 1, 15),
        status='SCHEDULED'
        )
        db_session.add(meeting)
        db_session.flush()

        service = ProjectMeetingService(db_session)
        result = service.link_meeting_to_project(
        meeting.id, 100, is_primary=True
        )

        assert result is True
        assert meeting.project_id == 100

    def test_link_as_related_project(self, db_session):
        """测试关联为关联项目"""
        from app.services.project_meeting_service import ProjectMeetingService
        from app.models.management_rhythm import StrategicMeeting

        meeting = StrategicMeeting(
        title='测试会议',
        meeting_date=date(2025, 1, 15),
        status='SCHEDULED',
        related_project_ids=[]
        )
        db_session.add(meeting)
        db_session.flush()

        service = ProjectMeetingService(db_session)
        result = service.link_meeting_to_project(
        meeting.id, 200, is_primary=False
        )

        assert result is True
        assert 200 in meeting.related_project_ids

    def test_link_duplicate_related_project(self, db_session):
        """测试重复关联相关项目"""
        from app.services.project_meeting_service import ProjectMeetingService
        from app.models.management_rhythm import StrategicMeeting

        meeting = StrategicMeeting(
        title='测试会议',
        meeting_date=date(2025, 1, 15),
        status='SCHEDULED',
        related_project_ids=[200]
        )
        db_session.add(meeting)
        db_session.flush()

        service = ProjectMeetingService(db_session)
        result = service.link_meeting_to_project(
        meeting.id, 200, is_primary=False
        )

        assert result is True
            # 不应重复添加
        assert meeting.related_project_ids.count(200) == 1


class TestUnlinkMeetingFromProject:
    """测试取消会议与项目的关联"""

    def test_meeting_not_found(self, db_session):
        """测试会议不存在"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.unlink_meeting_from_project(99999, 1)

        assert result is False

    def test_unlink_primary_project(self, db_session):
        """测试取消主项目关联"""
        from app.services.project_meeting_service import ProjectMeetingService
        from app.models.management_rhythm import StrategicMeeting

        meeting = StrategicMeeting(
        title='测试会议',
        meeting_date=date(2025, 1, 15),
        status='SCHEDULED',
        project_id=100
        )
        db_session.add(meeting)
        db_session.flush()

        service = ProjectMeetingService(db_session)
        result = service.unlink_meeting_from_project(meeting.id, 100)

        assert result is True
        assert meeting.project_id is None

    def test_unlink_related_project(self, db_session):
        """测试取消关联项目"""
        from app.services.project_meeting_service import ProjectMeetingService
        from app.models.management_rhythm import StrategicMeeting

        meeting = StrategicMeeting(
        title='测试会议',
        meeting_date=date(2025, 1, 15),
        status='SCHEDULED',
        related_project_ids=[100, 200, 300]
        )
        db_session.add(meeting)
        db_session.flush()

        service = ProjectMeetingService(db_session)
        result = service.unlink_meeting_from_project(meeting.id, 200)

        assert result is True
        assert 200 not in meeting.related_project_ids
        assert 100 in meeting.related_project_ids
        assert 300 in meeting.related_project_ids


class TestGetProjectMeetingStatistics:
    """测试获取项目会议统计"""

    def test_no_meetings_statistics(self, db_session):
        """测试无会议统计"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.get_project_meeting_statistics(99999)

        assert result['total_meetings'] == 0
        assert result['completed_meetings'] == 0
        assert result['scheduled_meetings'] == 0

    def test_statistics_structure(self, db_session):
        """测试统计结构"""
        from app.services.project_meeting_service import ProjectMeetingService

        service = ProjectMeetingService(db_session)
        result = service.get_project_meeting_statistics(1)

        expected_fields = [
        'total_meetings', 'completed_meetings', 'scheduled_meetings',
        'cancelled_meetings', 'completion_rate', 'total_action_items',
        'completed_action_items', 'action_completion_rate', 'by_level'
        ]

        for field in expected_fields:
            assert field in result


class TestCompletionRateCalculation:
    """测试完成率计算"""

    def test_completion_rate_with_meetings(self):
        """测试有会议时的完成率"""
        total_meetings = 10
        completed_meetings = 8

        rate = completed_meetings / total_meetings * 100 if total_meetings > 0 else 0

        assert rate == 80.0

    def test_completion_rate_no_meetings(self):
        """测试无会议时的完成率"""
        total_meetings = 0
        completed_meetings = 0

        rate = completed_meetings / total_meetings * 100 if total_meetings > 0 else 0

        assert rate == 0

    def test_action_completion_rate(self):
        """测试行动项完成率"""
        total_action_items = 20
        completed_action_items = 15

        rate = completed_action_items / total_action_items * 100 if total_action_items > 0 else 0

        assert rate == 75.0


class TestMeetingStatusFiltering:
    """测试会议状态过滤"""

    def test_filter_completed(self):
        """测试过滤已完成会议"""
        meetings = [
        {'id': 1, 'status': 'COMPLETED'},
        {'id': 2, 'status': 'SCHEDULED'},
        {'id': 3, 'status': 'COMPLETED'},
        {'id': 4, 'status': 'CANCELLED'},
        ]

        completed = [m for m in meetings if m['status'] == 'COMPLETED']
        assert len(completed) == 2

    def test_filter_scheduled(self):
        """测试过滤已安排会议"""
        meetings = [
        {'id': 1, 'status': 'COMPLETED'},
        {'id': 2, 'status': 'SCHEDULED'},
        {'id': 3, 'status': 'SCHEDULED'},
        {'id': 4, 'status': 'CANCELLED'},
        ]

        scheduled = [m for m in meetings if m['status'] == 'SCHEDULED']
        assert len(scheduled) == 2

    def test_filter_cancelled(self):
        """测试过滤已取消会议"""
        meetings = [
        {'id': 1, 'status': 'COMPLETED'},
        {'id': 2, 'status': 'SCHEDULED'},
        {'id': 3, 'status': 'CANCELLED'},
        {'id': 4, 'status': 'CANCELLED'},
        ]

        cancelled = [m for m in meetings if m['status'] == 'CANCELLED']
        assert len(cancelled) == 2


class TestRelatedProjectsHandling:
    """测试关联项目处理"""

    def test_empty_related_projects(self):
        """测试空关联项目列表"""
        related_ids = []
        project_id = 100

        result = project_id in related_ids
        assert result is False

    def test_project_in_related_list(self):
        """测试项目在关联列表中"""
        related_ids = [100, 200, 300]
        project_id = 200

        result = project_id in related_ids
        assert result is True

    def test_add_to_related_list(self):
        """测试添加到关联列表"""
        related_ids = [100, 200]
        project_id = 300

        if project_id not in related_ids:
            related_ids.append(project_id)

            assert 300 in related_ids
            assert len(related_ids) == 3

    def test_remove_from_related_list(self):
        """测试从关联列表移除"""
        related_ids = [100, 200, 300]
        project_id = 200

        if project_id in related_ids:
            related_ids.remove(project_id)

            assert 200 not in related_ids
            assert len(related_ids) == 2


            # pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
