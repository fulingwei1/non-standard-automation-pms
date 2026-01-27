"""
Unit tests for work log service
Tests coverage for:
- app.services.work_log_service.WorkLogService
"""

import pytest
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project, Machine
from app.models.timesheet import Timesheet
from app.models.work_log import (
    WorkLog,
)


class TestCreateWorkLog:
    """测试工作日志创建"""

    @pytest.fixture
    def service(self, db_session: Session):
        """创建 WorkLogService 实例"""
        from app.services.work_log_service import WorkLogService

        return WorkLogService(db_session)

    @pytest.fixture
    def user(self, db_session: Session):
        """创建模拟用户"""
        user = MagicMock(spec=User)
        user.id = 1
        user.username = "test_user"
        user.real_name = "测试用户"
        user.is_active = True
        return user

    @pytest.fixture
    def project(self):
        """创建模拟项目"""
        project = MagicMock(spec=Project)
        project.id = 10
        project.project_code = "PJ260101001"
        project.project_name = "测试项目"
        project.status = "IN_PROGRESS"
        return project

    @pytest.fixture
    def machine(self):
        """创建模拟设备"""
        machine = MagicMock(spec=Machine)
        machine.id = 20
        machine.machine_code = "PN020"
        return machine

    @pytest.fixture
    def timesheet(self, db_session: Session, user):
        """创建模拟工时表"""
        timesheet = MagicMock(spec=Timesheet)
        timesheet.id = 30
        return timesheet

    def test_create_work_log_success(self, service: Any, user, project):
        """测试成功创建工作日志"""
        work_log_in = {
            "work_date": date.today(),
            "content": "Test work log content",
            "status": "SUBMITTED",
        }

        with patch.object(service.db, "query") as mock_query:
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.username = "test_user"
            mock_user.real_name = "测试用户"
            mock_user.is_active = True
            mock_query.return_value.filter.return_value.first.return_value = mock_user

        result = service.create_work_log(user_id=user.id, work_log_in=work_log_in)

        assert result is not None
        assert result.content == work_log_in["content"]
        assert result.status == WorkLogStatusEnum.SUBMITTED
        assert result.work_date == work_log_in["work_date"]

    def test_create_work_log_with_hours(
        self, service: Any, user, project, timesheet
    ):
        """测试创建带工时的工作日志"""
        work_log_in = {
            "work_date": date.today(),
            "content": "Test work with hours",
            "status": "SUBMITTED",
            "work_hours": 8.0,
        }

        with patch.object(service, "_create_timesheet_from_worklog") as mock_create:
            mock_create.return_value = MagicMock(spec=Timesheet)
            mock_create.id = 10

            with patch.object(service.db, "flush"):
                service.db.flush()

            result = service.create_work_log(user_id=user.id, work_log_in=work_log_in)

            assert result is not None
            assert result.work_hours == 8.0
            mock_create.assert_called_once_with(
                result.id, user.id, work_log_in["work_date"], work_log_in["work_hours"]
            )

    def test_create_work_log_too_long_content(self, service: Any, user):
        """测试创建过长内容（>300 字）"""
        long_content = "a" * 301

        with pytest.raises(ValueError) as exc_info:
            service.create_work_log(
                user_id=user.id,
                work_log_in={
                    "work_date": date.today(),
                    "content": long_content,
                    "status": "SUBMITTED",
                },
            )

        assert "工作内容不能超过300字" in str(exc_info.value)

    def test_create_work_log_duplicate_date_non_draft(
        self, service: Any, user, project
    ):
        """测试重复日期（非草稿）"""
        existing_log = MagicMock(spec=WorkLog)
        existing_log.status = WorkLogStatusEnum.SUBMITTED
        existing_log.work_date = date.today()

        with patch.object(service.db, "query") as mock_query:
            mock_query.filter.return_value.first.return_value = existing_log

            with pytest.raises(ValueError) as exc_info:
                service.create_work_log(
                    user_id=user.id,
                    work_log_in={
                        "work_date": date.today(),
                        "content": "Duplicate content",
                        "status": "SUBMITTED",
                    },
                )

            assert "该日期已提交工作日志" in str(exc_info.value)

    def test_create_work_log_duplicate_date_draft_allowed(
        self, service: Any, user, project
    ):
        """测试重复日期（草稿状态允许）"""
        existing_log = MagicMock(spec=WorkLog)
        existing_log.status = WorkLogStatusEnum.DRAFT
        existing_log.work_date = date.today()

        with patch.object(service.db, "query") as mock_query:
            mock_query.filter.return_value.first.return_value = existing_log

        result = service.create_work_log(
            user_id=user.id,
            work_log_in={
                "work_date": date.today(),
                "content": "Draft duplicate content",
                "status": "DRAFT",
            },
        )

        assert result is not None
        assert result.status == WorkLogStatusEnum.DRAFT

    def test_create_work_log_user_not_found(self, service: Any):
        """测试用户不存在"""
        with patch.object(service.db, "query") as mock_query:
            mock_query.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            service.create_work_log(
                user_id=user.id,
                work_log_in={
                    "work_date": date.today(),
                    "content": "Test content",
                    "status": "SUBMITTED",
                },
            )

        assert "用户不存在" in str(exc_info.value)


class TestUpdateWorkLog:
    """测试工作日志更新"""

    @pytest.fixture
    def service(self, db_session: Session):
        """创建 WorkLogService 实例"""
        from app.services.work_log_service import WorkLogService

        return WorkLogService(db_session)

    @pytest.fixture
    def existing_log(self, db_session: Session, user):
        """创建现有工作日志"""
        log = MagicMock(spec=WorkLog)
        log.id = 1
        log.user_id = 1
        log.work_date = date.today()
        log.content = "Test content"
        log.status = WorkLogStatusEnum.DRAFT
        log.user = user
        return log

    def test_update_work_log_success(self, service: Any, existing_log, user):
        """测试成功更新工作日志"""
        update_data = {"content": "Updated content"}

        with patch.object(service, "update_work_log") as mock_update:
            result = service.update_work_log(
                work_log_id=existing_log.id, user_id=user.id, work_log_in=update_data
            )

            assert result is not None
            assert result.content == "Updated content"
            mock_update.assert_called_once_with(
                existing_log.id, user.id, work_log_in=update_data
            )

    def test_update_work_log_invalid_status(
        self, service: Any, existing_log, user
    ):
        """测试无效状态转换"""
        update_data = {"content": "Updated content", "status": "COMPLETED"}

        with pytest.raises(ValueError) as exc_info:
            service.update_work_log(
                work_log_id=existing_log.id, user_id=user.id, work_log_in=update_data
            )

        assert "只能更新草稿状态的工作日志" in str(exc_info.value)

    def test_update_work_log_not_author(self, service: Any, existing_log):
        """测试非作者更新"""
        other_user = MagicMock(spec=User)
        other_user.id = 999

        update_data = {"content": "Updated content"}

        with patch.object(service, "update_work_log") as mock_update:
            mock_update.return_value = existing_log
            mock_user.filter.return_value.first.return_value = other_user

        with pytest.raises(ValueError) as exc_info:
            service.update_work_log(
                work_log_id=existing_log.id, user_id=user.id, work_log_in=update_data
            )

        assert "只能更新自己创建的工作日志" in str(exc_info.value)


class TestCreateMentions:
    """测试提及创建"""

    @pytest.fixture
    def service(self, db_session: Session):
        """创建 WorkLogService 实例"""
        from app.services.work_log_service import WorkLogService

        return WorkLogService(db_session)

    @pytest.fixture
    def work_log(self, user, project):
        """创建工作日志"""
        return WorkLog(
            id=1,
            user_id=user.id,
            work_date=date.today(),
            content="Test @project1",
            status=WorkLogStatusEnum.SUBMITTED,
        )

    @pytest.fixture
    def work_log_with_project(self, project):
        """创建带项目提及的工作日志"""
        log = WorkLog(
            id=2,
            user_id=user.id,
            work_date=date.today(),
            content="Test @project1",
            status=WorkLogStatusEnum.SUBMITTED,
        )

        log.mentioned_projects = [project.id]

        return log

    def test_create_mentions_success(self, service: Any, work_log):
        """测试成功创建提及"""
        with patch.object(service, "_create_mentions") as mock_create:
            mock_create.return_value = MagicMock(spec=WorkLog)
            mock_create.id = 10

            result = service._create_mentions(
                work_log_id=work_log.id, user_id=user.id, work_log_in=work_log
            )

            assert result is not None
            assert result.mentioned_projects == [project.id]
            mock_create.assert_called_once_with(work_log.id, work_log_in)

    def test_create_mentions_project_not_found(self, service: Any, work_log):
        """测试项目不存在"""
        work_log_with_project.mentioned_projects = []

        with patch.object(service, "_create_mentions") as mock_create:
            mock_create.return_value = MagicMock(spec=WorkLog)

            with patch.object(service.db, "query") as mock_query:
                mock_project = MagicMock(spec=Project)
                mock_query.return_value.filter.return_value.first.return_value = None

            result = service._create_mentions(
                work_log_id=work_log.id, work_log_in=work_log_with_project
            )

            assert result is not None
            assert result.mentioned_projects == []

    def test_create_mentions_machine_not_found(
        self, service: Any, work_log, project
    ):
        """测试设备不存在"""
        work_log_with_machine.mentioned_machines = []

        with patch.object(service, "_create_mentions") as mock_create:
            mock_create.return_value = MagicMock(spec=Machine)
            mock_machine.filter.return_value.first.return_value = None

            result = service._create_mentions(
                work_log_id=work_log.id, work_log_in=work_log_with_machine
            )

            assert result is not None
            assert result.mentioned_machines == []


class TestCreateTimesheet:
    """测试工时表自动创建"""

    @pytest.fixture
    def service(self, db_session: Session, user):
        """创建 WorkLogService 实例"""
        from app.services.work_log_service import WorkLogService

        return WorkLogService(db_session)

    def test_create_timesheet_from_worklog_success(
        self, service: Any, work_log
    ):
        """测试成功创建工时表"""
        work_log_in = {
            "work_date": date.today(),
            "content": "Test work log",
            "status": "SUBMITTED",
            "work_hours": 8.0,
        }

        with patch.object(service, "_create_timesheet_from_worklog") as mock_create:
            mock_create.return_value = MagicMock(spec=Timesheet)
            mock_create.id = 10

            with patch.object(service.db, "flush"):
                service.db.flush()

            result = service._create_timesheet_from_worklog(
                work_log_id=work_log_in, user_id=user.id, work_log_in=work_log_in
            )

            assert result is not None
            assert result.timesheet_id == 10

            mock_create.assert_called_once_with(
                result.id, user.id, work_log_in["work_date"], work_log_in["work_hours"]
            )

    def test_create_timesheet_no_hours(self, service: Any, work_log):
        """测试无工时记录时不创建工时表"""
        work_log_in = {
            "work_date": date.today(),
            "content": "Test work log",
            "status": "SUBMITTED",
        }

        with patch.object(service, "_create_timesheet_from_worklog") as mock_create:
            mock_create.return_value = MagicMock(spec=Timesheet)
            mock_create.id = 10

            with patch.object(service.db, "query") as mock_query:
                mock_timesheet = MagicMock(spec=Timesheet)
                mock_query.return_value.filter.return_value.first.return_value = None

            result = service._create_timesheet_from_worklog(
                work_log_id=work_log_in, work_log_in=work_log_in
            )

            assert result is not None
            assert result.timesheet_id is None
            mock_create.assert_not_called()


class TestLinkToProgress:
    """测试项目/设备进展关联"""

    @pytest.fixture
    def service(self, db_session: Session, user, project):
        """创建 WorkLogService 实例"""
        from app.services.work_log_service import WorkLogService

        return WorkLogService(db_session)

    @pytest.fixture
    def work_log(self, user, project):
        """创建工作日志"""
        return WorkLog(
            id=1,
            user_id=user.id,
            work_date=date.today(),
            content="Test work log",
            status=WorkLogStatusEnum.SUBMITTED,
        )

    def test_link_to_progress_success(self, service: Any, work_log, project):
        """测试成功关联项目进展"""
        with patch.object(service, "_link_to_progress") as mock_link:
            result = service._link_to_progress(
                work_log_id=work_log.id, user_id=user.id, project_id=project.id
            )

            assert result is not None
            mock_link.assert_called_once_with(
                work_log.id, user_id=user.id, project_id=project.id
            )

    def test_link_to_progress_project_not_found(
        self, service: Any, work_log
    ):
        """测试项目不存在"""
        with patch.object(service, "_link_to_progress") as mock_link:
            result = service._link_to_progress(
                work_log_id=work_log.id, user_id=user.id, project_id=999
            )

            assert result is not None
            mock_link.assert_not_called_with(
                work_log.id, user_id=user.id, project_id=999
            )

    def test_link_to_progress_machine_not_found(
        self, service: Any, work_log, machine
    ):
        """测试设备不存在"""
        with patch.object(service, "_link_to_progress") as mock_link:
            result = service._link_to_progress(
                work_log_id=work_log.id, user_id=user.id, machine_id=999
            )

            assert result is not None
            mock_link.assert_not_called_with(
                work_log.id, user_id=user.id, machine_id=999
            )
