# -*- coding: utf-8 -*-
"""
工作日志服务单元测试
覆盖: app/services/work_log_service.py
"""
from datetime import date
from unittest.mock import MagicMock, patch, call

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.work_log_service import WorkLogService
    return WorkLogService(mock_db)


@pytest.fixture
def mock_work_log_create():
    from app.schemas.work_log import WorkLogCreate
    return WorkLogCreate(
        work_date=date(2024, 1, 15),
        content="今天完成了项目A的开发工作",
        mentioned_projects=[],
        mentioned_machines=[],
        mentioned_users=[],
        status="SUBMITTED",
        work_hours=8.0,
        work_type="NORMAL",
    )


# ─── 创建工作日志测试 ──────────────────────────────────────────────────────────

class TestCreateWorkLog:
    def test_content_too_long_raises_at_schema(self):
        """内容超过300字时 Pydantic schema 应拒绝"""
        from app.schemas.work_log import WorkLogCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            WorkLogCreate(
                work_date=date(2024, 1, 15),
                content="x" * 301,
                mentioned_projects=[],
                mentioned_machines=[],
                mentioned_users=[],
            )

    def test_duplicate_date_raises(self, service, mock_db, mock_work_log_create):
        """同一天已提交记录应抛出异常"""
        # existing record found
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with pytest.raises(ValueError, match="该日期已提交"):
            service.create_work_log(1, mock_work_log_create)

    def test_user_not_found_raises(self, service, mock_db, mock_work_log_create):
        """用户不存在应抛出异常"""
        # First query (existing check) returns None, second (user) returns None
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # no existing log
            None,  # user not found
        ]
        with pytest.raises(ValueError, match="用户不存在"):
            service.create_work_log(1, mock_work_log_create)

    def test_create_success(self, service, mock_db):
        """正常创建工作日志"""
        from app.schemas.work_log import WorkLogCreate
        wl_in = WorkLogCreate(
            work_date=date(2024, 1, 15),
            content="今天的工作内容",
            mentioned_projects=[],
            mentioned_machines=[],
            mentioned_users=[],
            status="SUBMITTED",
        )
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        # Setup: existing=None, user=mock_user
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,       # no existing log
            mock_user,  # user found
        ]
        mock_work_log = MagicMock()
        mock_work_log.id = 1

        with patch("app.services.work_log_service.WorkLog") as MockWorkLog:
            MockWorkLog.return_value = mock_work_log
            result = service.create_work_log(1, wl_in)

        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_with_work_hours_creates_timesheet(self, service, mock_db, mock_work_log_create):
        """提供工时时应创建工时记录"""
        mock_user = MagicMock()
        mock_user.real_name = "李四"
        mock_user.username = "lisi"
        mock_user.department_id = None

        mock_work_log = MagicMock()
        mock_work_log.id = 1

        # existing=None, user=mock_user, user again for timesheet
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,        # no existing log
            mock_user,   # user for log creation
            mock_user,   # user for timesheet
        ]

        with patch("app.services.work_log_service.WorkLog") as MockWorkLog, \
             patch("app.services.work_log_service.Timesheet") as MockTimesheet:
            MockWorkLog.return_value = mock_work_log
            mock_timesheet = MagicMock()
            mock_timesheet.id = 99
            MockTimesheet.return_value = mock_timesheet
            service.create_work_log(1, mock_work_log_create)


# ─── 更新工作日志测试 ──────────────────────────────────────────────────────────

class TestUpdateWorkLog:
    def test_not_found_raises(self, service, mock_db):
        """工作日志不存在应抛出异常"""
        from app.schemas.work_log import WorkLogUpdate
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="工作日志不存在"):
            service.update_work_log(99, 1, WorkLogUpdate())

    def test_permission_denied_raises(self, service, mock_db):
        """更新他人日志应抛出异常"""
        from app.schemas.work_log import WorkLogUpdate
        mock_log = MagicMock()
        mock_log.user_id = 2  # different user
        mock_db.query.return_value.filter.return_value.first.return_value = mock_log
        with pytest.raises(ValueError, match="只能更新自己"):
            service.update_work_log(1, 1, WorkLogUpdate())

    def test_non_draft_raises(self, service, mock_db):
        """非草稿状态日志不可更新"""
        from app.schemas.work_log import WorkLogUpdate
        mock_log = MagicMock()
        mock_log.user_id = 1
        mock_log.status = "SUBMITTED"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_log
        with pytest.raises(ValueError, match="只能更新草稿"):
            service.update_work_log(1, 1, WorkLogUpdate())

    def test_content_update_too_long_raises(self):
        """更新内容超过300字时 Pydantic schema 应拒绝"""
        from app.schemas.work_log import WorkLogUpdate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            WorkLogUpdate(content="x" * 301)

    def test_update_content_success(self, service, mock_db):
        """正常更新草稿内容"""
        from app.schemas.work_log import WorkLogUpdate
        mock_log = MagicMock()
        mock_log.user_id = 1
        mock_log.status = "DRAFT"
        mock_log.timesheet_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_log
        wl_upd = WorkLogUpdate(content="更新后的内容")
        service.update_work_log(1, 1, wl_upd)
        assert mock_log.content == "更新后的内容"
        mock_db.commit.assert_called_once()


# ─── 获取提及选项 ──────────────────────────────────────────────────────────────

class TestGetMentionOptions:
    def test_returns_options(self, service, mock_db):
        """应返回项目/设备/用户列表"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "项目A"

        mock_machine = MagicMock()
        mock_machine.id = 1
        mock_machine.machine_name = "设备X"

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        # project query, machine query, user query
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project],
            [mock_user],
        ]
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_machine]

        result = service.get_mention_options(1)
        assert result.projects[0].name == "项目A"
        assert result.machines[0].name == "设备X"
        assert result.users[0].name == "张三"

    def test_empty_options(self, service, mock_db):
        """空数据库时返回空列表"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = service.get_mention_options(1)
        assert result.projects == []
        assert result.machines == []
        assert result.users == []


# ─── 内部方法测试 ──────────────────────────────────────────────────────────────

class TestCreateMentions:
    def test_project_mention_created(self, service, mock_db):
        """项目提及应创建记录"""
        from app.schemas.work_log import WorkLogCreate
        mock_project = MagicMock()
        mock_project.project_name = "项目B"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        wl_in = WorkLogCreate(
            work_date=date(2024, 1, 15),
            content="内容",
            mentioned_projects=[1],
            mentioned_machines=[],
            mentioned_users=[],
        )
        with patch("app.services.work_log_service.WorkLogMention") as MockMention:
            service._create_mentions(1, wl_in)
        mock_db.add.assert_called()

    def test_no_mention_when_project_not_found(self, service, mock_db):
        """项目不存在时不创建提及"""
        from app.schemas.work_log import WorkLogCreate
        mock_db.query.return_value.filter.return_value.first.return_value = None

        wl_in = WorkLogCreate(
            work_date=date(2024, 1, 15),
            content="内容",
            mentioned_projects=[999],
            mentioned_machines=[],
            mentioned_users=[],
        )
        service._create_mentions(1, wl_in)
        mock_db.add.assert_not_called()
