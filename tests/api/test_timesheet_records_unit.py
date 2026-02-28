import uuid
# -*- coding: utf-8 -*-
"""
O1组 API层单元测试 - timesheet/records.py
使用 Method A: 直接调用端点函数 + MagicMock

覆盖：
  - list_timesheets
  - create_timesheet
  - batch_create_timesheets
  - get_timesheet_detail
  - update_timesheet
  - delete_timesheet
"""
import sys
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

import os
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from fastapi import HTTPException


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

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
    ts.project_id = 1
    ts.rd_project_id = None
    ts.task_id = None
    ts.work_date = date(2026, 2, 17)
    ts.hours = Decimal("8")
    ts.overtime_type = "NORMAL"
    ts.work_content = "编写测试代码"
    ts.status = status
    ts.approver_id = None
    ts.approve_time = None
    ts.created_at = None
    ts.updated_at = None
    return ts


def _make_pagination():
    pag = MagicMock()
    pag.offset = 0
    pag.limit = 20
    pag.page = 1
    pag.page_size = 20
    pag.pages_for_total = MagicMock(return_value=1)
    return pag


# ──────────────────────────────────────────────
# Tests: list_timesheets
# ──────────────────────────────────────────────

class TestListTimesheets:

    def test_list_timesheets_empty(self):
        """空列表查询"""
        from app.api.v1.endpoints.timesheet.records import list_timesheets

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        db.query.return_value = mock_query

        with patch("app.core.permissions.timesheet.apply_timesheet_access_filter", return_value=mock_query), \
             patch("app.api.v1.endpoints.timesheet.records.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []

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
        ts = _make_timesheet()

        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        db.query.return_value = mock_query

        user_mock = MagicMock(real_name="张三", username="zhangsan")
        project_mock = MagicMock(project_name="比亚迪项目")

        # db.query(User).filter(...).first() -> user_mock
        # db.query(Project).filter(...).first() -> project_mock
        db.query.side_effect = lambda model: {
            MagicMock: mock_query,
        }.get(model, mock_query)

        # Simplify: all returns from db.query call the mock_query
        with patch("app.core.permissions.timesheet.apply_timesheet_access_filter", return_value=mock_query), \
             patch("app.api.v1.endpoints.timesheet.records.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [ts]
            # user and project queries
            mock_query.filter.return_value.first.side_effect = [user_mock, project_mock]

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
        """按user_id过滤"""
        from app.api.v1.endpoints.timesheet.records import list_timesheets

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        db.query.return_value = mock_query

        with patch("app.core.permissions.timesheet.apply_timesheet_access_filter", return_value=mock_query), \
             patch("app.api.v1.endpoints.timesheet.records.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []

            result = list_timesheets(
                db=db,
                pagination=pagination,
                user_id=2,
                project_id=1,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                status="DRAFT",
                current_user=current_user,
            )

        assert mock_query.filter.called


# ──────────────────────────────────────────────
# Tests: create_timesheet
# ──────────────────────────────────────────────

class TestCreateTimesheet:

    def test_create_timesheet_no_project_raises(self):
        """没有指定项目ID时应抛出400"""
        from app.api.v1.endpoints.timesheet.records import create_timesheet

        db = _make_db()
        current_user = _make_user()

        ts_in = MagicMock()
        ts_in.project_id = None
        ts_in.rd_project_id = None
        ts_in.work_date = date(2026, 2, 17)
        ts_in.work_hours = Decimal("8")
        ts_in.work_type = "NORMAL"
        ts_in.description = "测试"
        ts_in.task_id = None

        with pytest.raises(HTTPException) as exc_info:
            create_timesheet(db=db, timesheet_in=ts_in, current_user=current_user)

        assert exc_info.value.status_code == 400

    def test_create_timesheet_duplicate_raises(self):
        """同一天已有记录时应抛出400"""
        from app.api.v1.endpoints.timesheet.records import create_timesheet

        db = _make_db()
        current_user = _make_user()

        ts_in = MagicMock()
        ts_in.project_id = 1
        ts_in.rd_project_id = None
        ts_in.work_date = date(2026, 2, 17)
        ts_in.work_hours = Decimal("8")
        ts_in.work_type = "NORMAL"
        ts_in.description = "测试"
        ts_in.task_id = None

        existing_ts = _make_timesheet()

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404") as mock_get:
            mock_get.return_value = MagicMock()  # project exists
            # duplicate check returns existing
            db.query.return_value.filter.return_value.first.return_value = existing_ts

            with pytest.raises(HTTPException) as exc_info:
                create_timesheet(db=db, timesheet_in=ts_in, current_user=current_user)

        assert exc_info.value.status_code == 400

    def test_create_timesheet_success(self):
        """正常创建工时记录"""
        from app.api.v1.endpoints.timesheet.records import create_timesheet

        db = _make_db()
        current_user = _make_user()

        ts_in = MagicMock()
        ts_in.project_id = 1
        ts_in.rd_project_id = None
        ts_in.work_date = date(2026, 2, 17)
        ts_in.work_hours = Decimal("8")
        ts_in.work_type = "NORMAL"
        ts_in.description = "编写测试代码"
        ts_in.task_id = None

        project_mock = MagicMock(project_code=f"P0001-{uuid.uuid4().hex[:8]}", project_name="比亚迪项目")
        user_mock = MagicMock(real_name="管理员", username="admin", department_id=1)
        department_mock = MagicMock(id=1, name="技术部")
        ts_instance = _make_timesheet()

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=project_mock), \
             patch("app.api.v1.endpoints.timesheet.records.save_obj"), \
             patch("app.api.v1.endpoints.timesheet.records.get_timesheet_detail") as mock_detail:
            # no duplicate, then user, dept, project queries
            db.query.return_value.filter.return_value.first.side_effect = [
                None,          # duplicate check
                user_mock,     # user lookup
                department_mock,  # dept lookup
                project_mock,  # project code/name lookup
            ]
            mock_detail.return_value = MagicMock(id=1)

            with patch("app.api.v1.endpoints.timesheet.records.Timesheet") as MockTs:
                MockTs.return_value = ts_instance
                result = create_timesheet(db=db, timesheet_in=ts_in, current_user=current_user)

        mock_detail.assert_called_once()


# ──────────────────────────────────────────────
# Tests: get_timesheet_detail
# ──────────────────────────────────────────────

class TestGetTimesheetDetail:

    def test_get_detail_success(self):
        """正常读取详情"""
        from app.api.v1.endpoints.timesheet.records import get_timesheet_detail

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts = _make_timesheet(user_id=1)

        user_mock = MagicMock(real_name="管理员", username="admin")
        project_mock = MagicMock(project_name="比亚迪项目")

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            db.query.return_value.filter.return_value.first.side_effect = [user_mock, project_mock]
            result = get_timesheet_detail(timesheet_id=1, db=db, current_user=current_user)

        assert result.id == 1
        assert result.status == "DRAFT"

    def test_get_detail_other_user_superuser_ok(self):
        """超级管理员可查看他人记录"""
        from app.api.v1.endpoints.timesheet.records import get_timesheet_detail

        db = _make_db()
        current_user = _make_user(user_id=99, is_superuser=True)
        ts = _make_timesheet(user_id=1)

        user_mock = MagicMock(real_name="张三", username="zhangsan")
        project_mock = MagicMock(project_name="比亚迪项目")

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            db.query.return_value.filter.return_value.first.side_effect = [user_mock, project_mock]
            result = get_timesheet_detail(timesheet_id=1, db=db, current_user=current_user)

        assert result is not None

    def test_get_detail_other_user_non_superuser_raises(self):
        """普通用户不能查看他人记录"""
        from app.api.v1.endpoints.timesheet.records import get_timesheet_detail

        db = _make_db()
        current_user = _make_user(user_id=99, is_superuser=False)
        ts = _make_timesheet(user_id=1)

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            with pytest.raises(HTTPException) as exc_info:
                get_timesheet_detail(timesheet_id=1, db=db, current_user=current_user)

        assert exc_info.value.status_code == 403


# ──────────────────────────────────────────────
# Tests: update_timesheet
# ──────────────────────────────────────────────

class TestUpdateTimesheet:

    def test_update_timesheet_success(self):
        """正常更新草稿工时"""
        from app.api.v1.endpoints.timesheet.records import update_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts = _make_timesheet(user_id=1, status="DRAFT")

        ts_in = MagicMock()
        ts_in.work_date = date(2026, 2, 18)
        ts_in.work_hours = Decimal("4")
        ts_in.work_type = "OVERTIME"
        ts_in.description = "更新的工作内容"

        user_mock = MagicMock(real_name="管理员", username="admin")
        project_mock = MagicMock(project_name="比亚迪项目")

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts), \
             patch("app.api.v1.endpoints.timesheet.records.save_obj"), \
             patch("app.api.v1.endpoints.timesheet.records.get_timesheet_detail") as mock_detail:
            db.query.return_value.filter.return_value.first.side_effect = [user_mock, project_mock]
            mock_detail.return_value = MagicMock(id=1)

            result = update_timesheet(db=db, timesheet_id=1, timesheet_in=ts_in, current_user=current_user)  # noqa: E501

        mock_detail.assert_called_once()

    def test_update_timesheet_wrong_user_raises(self):
        """更新他人工时时抛出403"""
        from app.api.v1.endpoints.timesheet.records import update_timesheet

        db = _make_db()
        current_user = _make_user(user_id=99)
        ts = _make_timesheet(user_id=1, status="DRAFT")

        ts_in = MagicMock()
        ts_in.work_date = None
        ts_in.work_hours = None
        ts_in.work_type = None
        ts_in.description = None

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            with pytest.raises(HTTPException) as exc_info:
                update_timesheet(db=db, timesheet_id=1, timesheet_in=ts_in, current_user=current_user)  # noqa: E501

        assert exc_info.value.status_code == 403

    def test_update_non_draft_raises(self):
        """非草稿工时不可更新"""
        from app.api.v1.endpoints.timesheet.records import update_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts = _make_timesheet(user_id=1, status="SUBMITTED")

        ts_in = MagicMock()
        ts_in.work_date = None
        ts_in.work_hours = None
        ts_in.work_type = None
        ts_in.description = None

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            with pytest.raises(HTTPException) as exc_info:
                update_timesheet(db=db, timesheet_id=1, timesheet_in=ts_in, current_user=current_user)  # noqa: E501

        assert exc_info.value.status_code == 400


# ──────────────────────────────────────────────
# Tests: delete_timesheet
# ──────────────────────────────────────────────

class TestDeleteTimesheet:

    def test_delete_timesheet_success(self):
        """正常删除草稿工时"""
        from app.api.v1.endpoints.timesheet.records import delete_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts = _make_timesheet(user_id=1, status="DRAFT")

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts), \
             patch("app.api.v1.endpoints.timesheet.records.delete_obj") as mock_delete:
            result = delete_timesheet(db=db, timesheet_id=1, current_user=current_user)

        mock_delete.assert_called_once()
        assert result.message == "工时记录已删除"

    def test_delete_timesheet_wrong_user_raises(self):
        """删除他人工时时抛出403"""
        from app.api.v1.endpoints.timesheet.records import delete_timesheet

        db = _make_db()
        current_user = _make_user(user_id=99)
        ts = _make_timesheet(user_id=1, status="DRAFT")

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            with pytest.raises(HTTPException) as exc_info:
                delete_timesheet(db=db, timesheet_id=1, current_user=current_user)

        assert exc_info.value.status_code == 403

    def test_delete_non_draft_raises(self):
        """非草稿工时不可删除"""
        from app.api.v1.endpoints.timesheet.records import delete_timesheet

        db = _make_db()
        current_user = _make_user(user_id=1)
        ts = _make_timesheet(user_id=1, status="APPROVED")

        with patch("app.api.v1.endpoints.timesheet.records.get_or_404", return_value=ts):
            with pytest.raises(HTTPException) as exc_info:
                delete_timesheet(db=db, timesheet_id=1, current_user=current_user)

        assert exc_info.value.status_code == 400
