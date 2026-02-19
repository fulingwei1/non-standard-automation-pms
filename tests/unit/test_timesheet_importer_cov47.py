# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - unified_import/timesheet_importer.py
"""
import pytest

pytest.importorskip("app.services.unified_import.timesheet_importer")

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd

from app.services.unified_import.timesheet_importer import TimesheetImporter


# ---------- parse_progress ----------

def test_parse_progress_valid():
    row = pd.Series({"进度": 80})
    result = TimesheetImporter.parse_progress(row, "进度")
    assert result == 80


def test_parse_progress_none():
    row = pd.Series({"进度": float("nan")})
    result = TimesheetImporter.parse_progress(row, "进度")
    assert result is None


def test_parse_progress_invalid_string():
    row = pd.Series({"进度": "abc"})
    result = TimesheetImporter.parse_progress(row, "进度")
    assert result is None


def test_parse_progress_missing_key():
    row = pd.Series({})
    result = TimesheetImporter.parse_progress(row, "进度")
    assert result is None


# ---------- create_timesheet_record ----------

def test_create_timesheet_record_basic():
    user = MagicMock()
    user.id = 10
    user.real_name = "张三"
    user.username = "zhangsan"
    user.department_id = 2
    user.department = "研发部"

    ts = TimesheetImporter.create_timesheet_record(
        user=user,
        index=0,
        work_date=date(2025, 1, 1),
        hours=8.0,
        project_id=5,
        project_code="P001",
        project_name="测试项目",
        task_name="开发",
        overtime_type="NORMAL",
        work_content="写代码",
        work_result="完成功能",
        progress_before=50,
        progress_after=80,
        current_user_id=1
    )

    assert ts.user_id == 10
    assert ts.hours == Decimal("8.0")
    assert ts.status == "DRAFT"
    assert ts.project_code == "P001"


# ---------- import_timesheet_data ----------

def test_import_missing_columns():
    db = MagicMock()
    df = pd.DataFrame({"无效列": []})
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        TimesheetImporter.import_timesheet_data(db, df, current_user_id=1)


def test_import_empty_row_fails():
    db = MagicMock()
    df = pd.DataFrame({
        "工作日期*": [None],
        "人员姓名*": ["张三"],
        "工时(小时)*": [8],
    })
    _, _, failed = TimesheetImporter.import_timesheet_data(db, df, current_user_id=1)
    assert len(failed) == 1


def test_import_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    df = pd.DataFrame({
        "工作日期*": ["2025-01-01"],
        "人员姓名*": ["不存在的人"],
        "工时(小时)*": [8],
    })
    _, _, failed = TimesheetImporter.import_timesheet_data(db, df, current_user_id=1)
    assert any("未找到用户" in r["error"] for r in failed)


def test_import_update_existing():
    db = MagicMock()
    user = MagicMock()
    user.id = 1
    user.real_name = "李四"

    existing_ts = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model.__name__ == "User":
            q.filter.return_value.first.return_value = user
        elif model.__name__ == "Timesheet":
            q.filter.return_value.first.return_value = existing_ts
        elif model.__name__ == "Project":
            q.filter.return_value.first.return_value = None
        else:
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = lambda m: query_side(m)

    df = pd.DataFrame({
        "工作日期*": ["2025-01-01"],
        "人员姓名*": ["李四"],
        "工时(小时)*": [4],
    })
    _, updated, _ = TimesheetImporter.import_timesheet_data(db, df, current_user_id=1, update_existing=True)
    assert updated == 1
