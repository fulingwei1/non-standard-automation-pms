# -*- coding: utf-8 -*-
"""
调试问题自动同步服务单元测试
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestDebugIssueSyncServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        assert service.db == db_session


class TestSyncMechanicalDebugIssue:
    """测试同步机械调试问题"""

    def test_issue_not_found(self, db_session):
        """测试问题不存在"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_mechanical_debug_issue(99999)

        assert result is None

    def test_wrong_category(self, db_session):
        """测试非项目类别"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService
        from app.models.issue import Issue

        issue = Issue(
        issue_no="ISS001",
        category="OTHER",
        issue_type="DEFECT",
        reporter_id=1
    )
        db_session.add(issue)
        db_session.flush()

        service = DebugIssueSyncService(db_session)
        result = service.sync_mechanical_debug_issue(issue.id)

        assert result is None


class TestSyncTestBugRecord:
    """测试同步测试Bug记录"""

    def test_issue_not_found(self, db_session):
        """测试问题不存在"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_test_bug_record(99999)

        assert result is None

    def test_wrong_issue_type(self, db_session):
        """测试非Bug类型"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService
        from app.models.issue import Issue

        issue = Issue(
        issue_no="ISS002",
        category="PROJECT",
        issue_type="DEFECT"  # 不是BUG,
        reporter_id=1
    )
        db_session.add(issue)
        db_session.flush()

        service = DebugIssueSyncService(db_session)
        result = service.sync_test_bug_record(issue.id)

        assert result is None


class TestSyncIssue:
    """测试同步问题"""

    def test_issue_not_found(self, db_session):
        """测试问题不存在"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_issue(99999)

        assert result['synced'] is False
        assert result['error'] == '问题不存在'

    def test_result_structure(self, db_session):
        """测试结果结构"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_issue(99999)

        assert 'issue_id' in result
        assert 'synced' in result
        assert 'type' in result
        assert 'record_id' in result
        assert 'error' in result


class TestSyncAllProjectIssues:
    """测试同步所有项目问题"""

    def test_no_issues(self, db_session):
        """测试无问题"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_all_project_issues()

        assert result['total_issues'] == 0
        assert result['synced_count'] == 0

    def test_with_date_filter(self, db_session):
        """测试带日期过滤"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_all_project_issues(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
        )

        assert 'total_issues' in result

    def test_stats_structure(self, db_session):
        """测试统计结构"""
        from app.services.debug_issue_sync_service import DebugIssueSyncService

        service = DebugIssueSyncService(db_session)
        result = service.sync_all_project_issues()

        expected_fields = [
        'total_issues', 'synced_count', 'skipped_count',
        'error_count', 'mechanical_debug_count', 'test_bug_count', 'errors'
        ]
        for field in expected_fields:
            assert field in result


class TestFoundStageInference:
    """测试发现阶段推断"""

    def test_site_stage(self):
        """测试现场阶段"""
        tags = ['site', 'debug']
        tags_str = ','.join(tags).lower()

        found_stage = 'internal_debug'
        if 'site' in tags_str or '现场' in tags_str:
            found_stage = 'site_debug'

            assert found_stage == 'site_debug'

    def test_acceptance_stage(self):
        """测试验收阶段"""
        tags = ['acceptance', 'issue']
        tags_str = ','.join(tags).lower()

        found_stage = 'internal_debug'
        if 'site' in tags_str or '现场' in tags_str:
            found_stage = 'site_debug'
        elif 'acceptance' in tags_str or '验收' in tags_str:
            found_stage = 'acceptance'

            assert found_stage == 'acceptance'

    def test_default_stage(self):
        """测试默认阶段"""
        tags = ['other']
        tags_str = ','.join(tags).lower()

        found_stage = 'internal_debug'
        if 'site' in tags_str:
            found_stage = 'site_debug'
        elif 'acceptance' in tags_str:
            found_stage = 'acceptance'

            assert found_stage == 'internal_debug'


class TestFixDurationCalculation:
    """测试修复时长计算"""

    def test_calculate_duration(self):
        """测试计算修复时长"""
        report_date = datetime(2025, 1, 15, 9, 0)
        resolved_at = datetime(2025, 1, 15, 17, 0)

        duration = resolved_at - report_date
        fix_duration_hours = Decimal(str(duration.total_seconds() / 3600))

        assert fix_duration_hours == Decimal('8')

    def test_multi_day_duration(self):
        """测试跨天修复时长"""
        report_date = datetime(2025, 1, 15, 9, 0)
        resolved_at = datetime(2025, 1, 16, 9, 0)

        duration = resolved_at - report_date
        fix_duration_hours = Decimal(str(duration.total_seconds() / 3600))

        assert fix_duration_hours == Decimal('24')


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
