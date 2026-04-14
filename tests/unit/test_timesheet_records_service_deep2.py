# -*- coding: utf-8 -*-
"""Deep coverage for app.services.timesheet.records.service."""

from collections import deque
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.timesheet.records import service as svc


class QueryStub:
    def __init__(self, *, first=None, all=None, count=None):
        self._first = first
        self._all = [] if all is None else all
        self._count = count if count is not None else len(self._all)
        self.offset_value = None
        self.limit_value = None

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, value):
        self.offset_value = value
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def first(self):
        return self._first

    def all(self):
        return self._all

    def count(self):
        return self._count


class FakeDB:
    def __init__(self, query_plan=None):
        self.query_plan = {}
        for key, value in (query_plan or {}).items():
            if isinstance(value, deque):
                self.query_plan[key] = value
            elif isinstance(value, list):
                self.query_plan[key] = deque(value)
            else:
                self.query_plan[key] = deque([value])
        self.added = []
        self.commits = 0

    def query(self, model):
        key = model if model in self.query_plan else str(model)
        queue = self.query_plan.get(key)
        if not queue:
            return QueryStub()
        return queue.popleft()

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = len(self.added)

    def commit(self):
        self.commits += 1


def q(*, first=None, all=None, count=None):
    return QueryStub(first=first, all=all, count=count)


def test_list_timesheets_applies_filters_and_returns_paginated_items(monkeypatch):
    import app.core.permissions.timesheet as permission_module

    query = q(all=[SimpleNamespace(id=1), SimpleNamespace(id=2)], count=2)
    db = FakeDB({svc.Timesheet: query})
    service = svc.TimesheetRecordsService(db)
    user = SimpleNamespace(id=7)

    monkeypatch.setattr(permission_module, "apply_timesheet_access_filter", lambda q, db, current_user: q)
    monkeypatch.setattr(service, "_build_timesheet_response", lambda ts: {"id": ts.id})

    items, total = service.list_timesheets(
        user,
        offset=5,
        limit=10,
        user_id=7,
        project_id=11,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
        status="DRAFT",
    )

    assert items == [{"id": 1}, {"id": 2}]
    assert total == 2
    assert query.offset_value == 5
    assert query.limit_value == 10


def test_create_timesheet_runs_validations_and_builds_persisted_object(monkeypatch):
    project = SimpleNamespace(id=11, project_code="PRJ-11", project_name="自动化项目")
    user_record = SimpleNamespace(id=3, real_name="张三", username="zhangsan", department_id=5)
    dept = SimpleNamespace(id=5, name="研发部")
    db = FakeDB(
        {
            svc.Project: [q(first=project), q(first=project)],
            svc.Timesheet: q(first=None),
            svc.User: q(first=user_record),
            svc.Department: q(first=dept),
        }
    )
    service = svc.TimesheetRecordsService(db)
    payload = svc.TimesheetCreate(
        project_id=11,
        work_date=date(2026, 4, 10),
        work_hours=Decimal("8"),
        work_type="OVERTIME",
        description="联调设备",
    )
    current_user = SimpleNamespace(id=3)
    saved = []

    def fake_save_obj(db_obj, timesheet):
        timesheet.id = 88
        saved.append(timesheet)

    monkeypatch.setattr(svc, "save_obj", fake_save_obj)
    monkeypatch.setattr(service, "get_timesheet_detail", lambda timesheet_id, user: {"id": timesheet_id, "user": user.id})

    result = service.create_timesheet(payload, current_user)

    assert result == {"id": 88, "user": 3}
    assert saved[0].user_name == "张三"
    assert saved[0].department_name == "研发部"
    assert saved[0].project_code == "PRJ-11"
    assert saved[0].work_content == "联调设备"
    assert saved[0].status == "DRAFT"


def test_batch_create_timesheets_counts_success_failures_and_errors(monkeypatch):
    project_ok = SimpleNamespace(id=11, project_code="PRJ-11", project_name="自动化项目")
    existing = SimpleNamespace(id=99)
    db = FakeDB(
        {
            svc.Project: [q(first=project_ok), q(first=None), q(first=project_ok), q(first=project_ok)],
            svc.Timesheet: [q(first=None), q(first=existing), q(first=None)],
        }
    )
    service = svc.TimesheetRecordsService(db)
    current_user = SimpleNamespace(id=3)
    payloads = [
        svc.TimesheetCreate(project_id=11, work_date=date(2026, 4, 1), work_hours=Decimal("8")),
        svc.TimesheetCreate(project_id=22, work_date=date(2026, 4, 2), work_hours=Decimal("8")),
        svc.TimesheetCreate(project_id=11, work_date=date(2026, 4, 3), work_hours=Decimal("8")),
        svc.TimesheetCreate(project_id=11, work_date=date(2026, 4, 4), work_hours=Decimal("8")),
    ]

    user_info_calls = iter([
        {"user_name": "张三", "department_id": 5, "department_name": "研发部"},
        RuntimeError("用户信息异常"),
    ])

    def fake_get_user_info(user_id):
        result = next(user_info_calls)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(service, "_get_user_info", fake_get_user_info)
    monkeypatch.setattr(service, "_get_project_info", lambda project_id: {"project_code": "PRJ-11", "project_name": "自动化项目"})

    result = service.batch_create_timesheets(payloads, current_user)

    assert result == {
        "success_count": 1,
        "failed_count": 3,
        "errors": [
            {"date": "2026-04-02", "error": "项目不存在"},
            {"date": "2026-04-03", "error": "该日期已有记录"},
            {"date": "2026-04-04", "error": "用户信息异常"},
        ],
    }
    assert db.commits == 1
    assert len(db.added) == 1
    assert db.added[0].project_code == "PRJ-11"


def test_get_timesheet_detail_checks_access_and_builds_response(monkeypatch):
    db = FakeDB()
    service = svc.TimesheetRecordsService(db)
    timesheet = SimpleNamespace(id=12, user_id=3)
    current_user = SimpleNamespace(id=3, is_superuser=False)

    monkeypatch.setattr(svc, "get_or_404", lambda db, model, pk, message: timesheet)
    checked = []
    monkeypatch.setattr(service, "_check_access_permission", lambda ts, user: checked.append((ts.id, user.id)))
    monkeypatch.setattr(service, "_build_timesheet_detail_response", lambda ts: {"id": ts.id})

    assert service.get_timesheet_detail(12, current_user) == {"id": 12}
    assert checked == [(12, 3)]


def test_update_timesheet_updates_mutable_fields_and_reloads_detail(monkeypatch):
    db = FakeDB()
    service = svc.TimesheetRecordsService(db)
    timesheet = SimpleNamespace(
        id=12,
        user_id=3,
        status="DRAFT",
        work_date=date(2026, 4, 1),
        hours=Decimal("8"),
        overtime_type="NORMAL",
        work_content="旧内容",
    )
    current_user = SimpleNamespace(id=3)
    payload = svc.TimesheetUpdate(
        work_date=date(2026, 4, 5),
        work_hours=Decimal("6"),
        work_type="OVERTIME",
        description="新内容",
    )
    saved = []

    monkeypatch.setattr(svc, "get_or_404", lambda db, model, pk, message: timesheet)
    monkeypatch.setattr(svc, "save_obj", lambda db, obj: saved.append(obj))
    monkeypatch.setattr(service, "get_timesheet_detail", lambda timesheet_id, user: {"id": timesheet_id, "user": user.id})

    result = service.update_timesheet(12, payload, current_user)

    assert result == {"id": 12, "user": 3}
    assert timesheet.work_date == date(2026, 4, 5)
    assert timesheet.hours == Decimal("6")
    assert timesheet.overtime_type == "OVERTIME"
    assert timesheet.work_content == "新内容"
    assert saved == [timesheet]


@pytest.mark.parametrize(
    ("timesheet", "current_user", "message", "operation"),
    [
        (SimpleNamespace(id=12, user_id=5, status="DRAFT"), SimpleNamespace(id=3), "无权修改此记录", "update"),
        (SimpleNamespace(id=12, user_id=3, status="SUBMITTED"), SimpleNamespace(id=3), "只能修改草稿状态的记录", "update"),
        (SimpleNamespace(id=12, user_id=5, status="DRAFT"), SimpleNamespace(id=3), "无权删除此记录", "delete"),
        (SimpleNamespace(id=12, user_id=3, status="APPROVED"), SimpleNamespace(id=3), "只能删除草稿状态的记录", "delete"),
    ],
)
def test_update_and_delete_timesheet_validate_permissions_and_status(monkeypatch, timesheet, current_user, message, operation):
    db = FakeDB()
    service = svc.TimesheetRecordsService(db)
    monkeypatch.setattr(svc, "get_or_404", lambda db, model, pk, msg: timesheet)

    with pytest.raises(HTTPException, match=message):
        if operation == "update":
            service.update_timesheet(12, svc.TimesheetUpdate(), current_user)
        else:
            service.delete_timesheet(12, current_user)


def test_delete_timesheet_removes_draft_owned_record(monkeypatch):
    db = FakeDB()
    service = svc.TimesheetRecordsService(db)
    timesheet = SimpleNamespace(id=12, user_id=3, status="DRAFT")
    current_user = SimpleNamespace(id=3)
    deleted = []

    monkeypatch.setattr(svc, "get_or_404", lambda db, model, pk, message: timesheet)
    monkeypatch.setattr(svc, "delete_obj", lambda db, obj: deleted.append(obj))

    service.delete_timesheet(12, current_user)

    assert deleted == [timesheet]


def test_validate_projects_requires_any_project_identifier():
    service = svc.TimesheetRecordsService(FakeDB())

    with pytest.raises(HTTPException, match="必须指定项目ID或研发项目ID"):
        service._validate_projects(None, None)


def test_validate_projects_rejects_missing_rd_project():
    from app.models.rd_project import RdProject

    db = FakeDB({RdProject: q(first=None)})
    service = svc.TimesheetRecordsService(db)

    with pytest.raises(HTTPException, match="研发项目不存在"):
        service._validate_projects(None, 9)


def test_validate_projects_checks_existing_standard_project(monkeypatch):
    db = FakeDB()
    service = svc.TimesheetRecordsService(db)
    called = []
    monkeypatch.setattr(svc, "get_or_404", lambda db, model, pk, message: called.append((model, pk, message)) or object())

    service._validate_projects(project_id=11, rd_project_id=None)

    assert called == [(svc.Project, 11, "项目不存在")]


def test_check_duplicate_timesheet_raises_when_existing_record_found():
    db = FakeDB({svc.Timesheet: q(first=SimpleNamespace(id=99))})
    service = svc.TimesheetRecordsService(db)

    with pytest.raises(HTTPException, match="该日期已有工时记录，请更新或删除后重试"):
        service._check_duplicate_timesheet(3, date(2026, 4, 1), 11, 21)


def test_get_user_and_project_info_return_fallbacks_when_records_missing():
    user_record = SimpleNamespace(id=3, real_name=None, username="zhangsan", department_id=5)
    department = SimpleNamespace(id=5, name="研发部")
    db = FakeDB(
        {
            svc.User: [q(first=user_record), q(first=None)],
            svc.Department: q(first=department),
            svc.Project: [q(first=SimpleNamespace(project_code="PRJ-11", project_name="自动化项目")), q(first=None)],
        }
    )
    service = svc.TimesheetRecordsService(db)

    assert service._get_user_info(3) == {
        "user_name": "zhangsan",
        "department_id": 5,
        "department_name": "研发部",
    }
    assert service._get_user_info(4) == {
        "user_name": None,
        "department_id": None,
        "department_name": None,
    }
    assert service._get_project_info(11) == {"project_code": "PRJ-11", "project_name": "自动化项目"}
    assert service._get_project_info(22) == {"project_code": None, "project_name": None}


@pytest.mark.parametrize(
    ("timesheet", "current_user", "should_raise"),
    [
        (SimpleNamespace(user_id=3), SimpleNamespace(id=3, is_superuser=False), False),
        (SimpleNamespace(user_id=3), SimpleNamespace(id=9, is_superuser=True), False),
        (SimpleNamespace(user_id=3), SimpleNamespace(id=9, is_superuser=False), True),
    ],
)
def test_check_access_permission_enforces_owner_or_superuser(timesheet, current_user, should_raise):
    service = svc.TimesheetRecordsService(FakeDB())

    if should_raise:
        with pytest.raises(HTTPException, match="无权访问此记录"):
            service._check_access_permission(timesheet, current_user)
    else:
        service._check_access_permission(timesheet, current_user)


def test_build_timesheet_response_and_detail_response_include_related_names():
    from app.models.progress import Task
    from app.models.rd_project import RdProject

    user = SimpleNamespace(id=3, real_name="张三", username="zhangsan")
    project = SimpleNamespace(id=11, project_name="自动化项目")
    task = SimpleNamespace(id=21, task_name="设备调试")
    rd_project = SimpleNamespace(id=31, project_name="研发平台")
    db = FakeDB(
        {
            svc.User: [q(first=user), q(first=user), q(first=user)],
            svc.Project: [q(first=project), q(first=project)],
            Task: q(first=task),
            RdProject: q(first=rd_project),
        }
    )
    service = svc.TimesheetRecordsService(db)

    list_response = service._build_timesheet_response(
        SimpleNamespace(
            id=1,
            user_id=3,
            project_id=11,
            rd_project_id=None,
            task_id=21,
            work_date=date(2026, 4, 10),
            hours=Decimal("7.5"),
            overtime_type="NORMAL",
            work_content="联调",
            status="DRAFT",
            approver_id=9,
            approve_time=datetime(2026, 4, 11, 9, 0, 0),
            created_at=datetime(2026, 4, 10, 8, 0, 0),
            updated_at=datetime(2026, 4, 10, 18, 0, 0),
        )
    )
    assert list_response.user_name == "张三"
    assert list_response.project_name == "自动化项目"
    assert list_response.task_name == "设备调试"
    assert list_response.work_hours == Decimal("7.5")

    detail_with_project = service._build_timesheet_detail_response(
        SimpleNamespace(
            id=2,
            user_id=3,
            project_id=11,
            rd_project_id=None,
            task_id=None,
            work_date=date(2026, 4, 11),
            hours=Decimal("8"),
            overtime_type="NORMAL",
            work_content="项目支持",
            status="DRAFT",
            approver_id=None,
            approve_time=None,
            created_at=datetime(2026, 4, 11, 8, 0, 0),
            updated_at=datetime(2026, 4, 11, 18, 0, 0),
        )
    )
    assert detail_with_project.project_name == "自动化项目"

    detail_response = service._build_timesheet_detail_response(
        SimpleNamespace(
            id=3,
            user_id=3,
            project_id=None,
            rd_project_id=31,
            task_id=None,
            work_date=date(2026, 4, 12),
            hours=None,
            overtime_type=None,
            work_content="研发支持",
            status=None,
            approver_id=None,
            approve_time=None,
            created_at=datetime(2026, 4, 12, 8, 0, 0),
            updated_at=datetime(2026, 4, 12, 18, 0, 0),
        )
    )
    assert detail_response.project_name == "研发平台"
    assert detail_response.work_hours == Decimal("0")
    assert detail_response.work_type == "NORMAL"
    assert detail_response.is_billable is True
