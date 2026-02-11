# -*- coding: utf-8 -*-
"""工作日志服务测试"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.work_log_service import WorkLogService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return WorkLogService(db)


class TestCreateWorkLog:
    def test_content_too_long(self, service):
        work_log_in = MagicMock(content="x" * 301, work_date=date.today())
        with pytest.raises(ValueError, match="300字"):
            service.create_work_log(1, work_log_in)

    def test_duplicate_date(self, service, db):
        work_log_in = MagicMock(content="test", work_date=date.today())
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [existing, None]
        with pytest.raises(ValueError, match="已提交"):
            service.create_work_log(1, work_log_in)

    def test_user_not_found(self, service, db):
        work_log_in = MagicMock(content="test", work_date=date.today())
        db.query.return_value.filter.return_value.first.side_effect = [None, None]
        with pytest.raises(ValueError, match="用户不存在"):
            service.create_work_log(1, work_log_in)


class TestUpdateWorkLog:
    def test_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            service.update_work_log(1, 1, MagicMock())

    def test_wrong_user(self, service, db):
        work_log = MagicMock(user_id=2, status='DRAFT')
        db.query.return_value.filter.return_value.first.return_value = work_log
        with pytest.raises(ValueError, match="只能更新自己的"):
            service.update_work_log(1, 1, MagicMock())

    def test_not_draft(self, service, db):
        work_log = MagicMock(user_id=1, status='SUBMITTED')
        db.query.return_value.filter.return_value.first.return_value = work_log
        with pytest.raises(ValueError, match="草稿"):
            service.update_work_log(1, 1, MagicMock())

    def test_update_content_too_long(self, service, db):
        work_log = MagicMock(user_id=1, status='DRAFT')
        db.query.return_value.filter.return_value.first.return_value = work_log
        update_in = MagicMock(
            content="x" * 301,
            mentioned_projects=None, mentioned_machines=None, mentioned_users=None,
            work_hours=None, work_type=None, project_id=None, rd_project_id=None
        )
        with pytest.raises(ValueError, match="300字"):
            service.update_work_log(1, 1, update_in)


class TestGetMentionOptions:
    def test_returns_options(self, service, db):
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = service.get_mention_options(1)
        assert hasattr(result, 'projects')
        assert hasattr(result, 'machines')
        assert hasattr(result, 'users')
