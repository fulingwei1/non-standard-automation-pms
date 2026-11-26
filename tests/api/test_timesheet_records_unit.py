# -*- coding: utf-8 -*-
"""
O1组 API层单元测试 - timesheet/records.py
使用 Method A: 直接调用端点函数 + MagicMock

覆盖：
  - list_timesheets
  - create_timesheet
  - get_timesheet_detail
  - update_timesheet
  - delete_timesheet
"""
import os
import sys
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from fastapi import HTTPException


def _make_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


def _make_user(user_id=1, is_superuser=True):
    user = MagicMock()
    user.id = user_id
    user.username = "admin"
    user.real_name = "管理员"
    user.is_superuser = is_superuser
    user.department_id = 1
    return user


def _make_timesheet(ts_id=1, user_id=1, status="DRAFT"):
    ts = MagicMock()
    ts.id = ts_id
    ts.user_id = user_id
    ts.status = status
    ts.work_date = date(2026, 2, 17)
    ts.hours = Decimal("8")
    return ts


def _make_pagination():
    pag = MagicMock()
    pag.offset = 0
    pag.limit = 20
    pag.page = 1
    pag.page_size = 20
    pag.pages_for_total = MagicMock(return_value=1)
    return pag


class TestListTimesheets:

    def test_list_timesheets_empty(self):
        """空列表查询"""
        from app.api.v1.endpoints.timesheet.records import list_timesheets

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.list_timesheets.return_value = ([], 0)
            result = list_timesheets(
                db=db,
                pagination=pagination,
                user_id=None,
                project_id=None,
                start_date=None,
                end_date=None,
                status=None,
                current_user=current_user,
            )

        assert result.total == 0
        assert result.items == []

    def test_list_timesheets_with_items(self):
        """有记录时正常返回"""
        from app.api.v1.endpoints.timesheet.records import list_timesheets

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        with (
            patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc,
            patch(
                "app.api.v1.endpoints.timesheet.records.TimesheetListResponse",
                side_effect=lambda **kw: MagicMock(**kw),
            ),
        ):
            MockSvc.return_value.list_timesheets.return_value = ([_make_timesheet()], 1)
            result = list_timesheets(
                db=db,
                pagination=pagination,
                user_id=None,
                project_id=None,
                start_date=None,
                end_date=None,
                status=None,
                current_user=current_user,
            )

        assert result.total == 1

    def test_list_timesheets_filter_by_user(self):
        """按user_id过滤透传到service"""
        from app.api.v1.endpoints.timesheet.records import list_timesheets

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.list_timesheets.return_value = ([], 0)
            list_timesheets(
                db=db,
                pagination=pagination,
                user_id=2,
                project_id=1,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                status="DRAFT",
                current_user=current_user,
            )

        MockSvc.return_value.list_timesheets.assert_called_once_with(
            current_user=current_user,
            offset=0,
            limit=20,
            user_id=2,
            project_id=1,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status="DRAFT",
        )


class TestCreateTimesheet:

    def test_create_timesheet_no_project_raises(self):
        """service抛出异常时透传"""
        from app.api.v1.endpoints.timesheet.records import create_timesheet

        db = _make_db()
        current_user = _make_user()
        ts_in = MagicMock()

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.create_timesheet.side_effect = HTTPException(
                status_code=400, detail="必须指定项目"
            )
            with pytest.raises(HTTPException) as exc_info:
                create_timesheet(db=db, timesheet_in=ts_in, current_user=current_user)

        assert exc_info.value.status_code == 400

    def test_create_timesheet_duplicate_raises(self):
        """重复记录抛出400"""
        from app.api.v1.endpoints.timesheet.records import create_timesheet

        db = _make_db()
        current_user = _make_user()
        ts_in = MagicMock()

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.create_timesheet.side_effect = HTTPException(
                status_code=400, detail="重复工时记录"
            )
            with pytest.raises(HTTPException) as exc_info:
                create_timesheet(db=db, timesheet_in=ts_in, current_user=current_user)

        assert exc_info.value.status_code == 400

    def test_create_timesheet_success(self):
        """正常创建工时记录"""
        from app.api.v1.endpoints.timesheet.records import create_timesheet

        db = _make_db()
        current_user = _make_user()
        ts_in = MagicMock()
        expected = MagicMock(id=1)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.create_timesheet.return_value = expected
            result = create_timesheet(db=db, timesheet_in=ts_in, current_user=current_user)

        assert result is expected
        MockSvc.return_value.create_timesheet.assert_called_once_with(ts_in, current_user)


class TestGetTimesheetDetail:

    def test_get_detail_success(self):
        """正常读取详情"""
        from app.api.v1.endpoints.timesheet.records import get_timesheet_detail

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts = _make_timesheet(user_id=1)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.get_timesheet_detail.return_value = ts
            result = get_timesheet_detail(timesheet_id=1, db=db, current_user=current_user)

        assert result.id == 1
        assert result.status == "DRAFT"

    def test_get_detail_not_found_raises_404(self):
        """不存在时映射为404"""
        from app.api.v1.endpoints.timesheet.records import get_timesheet_detail

        db = _make_db()
        current_user = _make_user(user_id=1)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.get_timesheet_detail.side_effect = ValueError("工时记录不存在")
            with pytest.raises(HTTPException) as exc_info:
                get_timesheet_detail(timesheet_id=999, db=db, current_user=current_user)

        assert exc_info.value.status_code == 404

    def test_get_detail_other_user_non_superuser_raises(self):
        """无权查看他人记录映射为403"""
        from app.api.v1.endpoints.timesheet.records import get_timesheet_detail

        db = _make_db()
        current_user = _make_user(user_id=99, is_superuser=False)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.get_timesheet_detail.side_effect = ValueError("无权查看该工时记录")
            with pytest.raises(HTTPException) as exc_info:
                get_timesheet_detail(timesheet_id=1, db=db, current_user=current_user)

        assert exc_info.value.status_code == 403


class TestUpdateTimesheet:

    def test_update_timesheet_success(self):
        """正常更新草稿工时"""
        from app.api.v1.endpoints.timesheet.records import update_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts_in = MagicMock()
        expected = MagicMock(id=1)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.update_timesheet.return_value = expected
            result = update_timesheet(
                db=db, timesheet_id=1, timesheet_in=ts_in, current_user=current_user
            )

        assert result is expected

    def test_update_timesheet_wrong_user_raises(self):
        """无权更新他人工时映射为403"""
        from app.api.v1.endpoints.timesheet.records import update_timesheet

        db = _make_db()
        current_user = _make_user(user_id=99)
        ts_in = MagicMock()

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.update_timesheet.side_effect = ValueError("无权修改该工时记录")
            with pytest.raises(HTTPException) as exc_info:
                update_timesheet(
                    db=db, timesheet_id=1, timesheet_in=ts_in, current_user=current_user
                )

        assert exc_info.value.status_code == 403

    def test_update_non_draft_raises(self):
        """非草稿工时不可更新映射为400"""
        from app.api.v1.endpoints.timesheet.records import update_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts_in = MagicMock()

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.update_timesheet.side_effect = ValueError("仅草稿状态可修改")
            with pytest.raises(HTTPException) as exc_info:
                update_timesheet(
                    db=db, timesheet_id=1, timesheet_in=ts_in, current_user=current_user
                )

        assert exc_info.value.status_code == 400


class TestDeleteTimesheet:

    def test_delete_timesheet_success(self):
        """正常删除草稿工时"""
        from app.api.v1.endpoints.timesheet.records import delete_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            result = delete_timesheet(db=db, timesheet_id=1, current_user=current_user)

        MockSvc.return_value.delete_timesheet.assert_called_once_with(1, current_user)
        assert result.message == "工时记录已删除"

    def test_delete_timesheet_wrong_user_raises(self):
        """无权删除他人工时映射为403"""
        from app.api.v1.endpoints.timesheet.records import delete_timesheet

        db = _make_db()
        current_user = _make_user(user_id=99)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.delete_timesheet.side_effect = ValueError("无权删除该工时记录")
            with pytest.raises(HTTPException) as exc_info:
                delete_timesheet(db=db, timesheet_id=1, current_user=current_user)

        assert exc_info.value.status_code == 403

    def test_delete_non_draft_raises(self):
        """非草稿工时不可删除映射为400"""
        from app.api.v1.endpoints.timesheet.records import delete_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)

        with patch("app.api.v1.endpoints.timesheet.records.TimesheetRecordsService") as MockSvc:
            MockSvc.return_value.delete_timesheet.side_effect = ValueError("仅草稿状态可删除")
            with pytest.raises(HTTPException) as exc_info:
                delete_timesheet(db=db, timesheet_id=1, current_user=current_user)

        assert exc_info.value.status_code == 400
