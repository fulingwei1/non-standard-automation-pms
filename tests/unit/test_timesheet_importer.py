# -*- coding: utf-8 -*-
"""Tests for app.services.unified_import.timesheet_importer"""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd
from fastapi import HTTPException

from app.services.unified_import.timesheet_importer import TimesheetImporter


class TestTimesheetImporterCreateRecord(unittest.TestCase):

    def test_create_timesheet_record(self):
        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        user.department_id = 10
        user.department = "技术部"

        record = TimesheetImporter.create_timesheet_record(
            user=user, index=0, work_date=date(2025, 1, 1),
            hours=8.0, project_id=100, project_code="P001",
            project_name="项目A", task_name="开发",
            overtime_type="NORMAL", work_content="编码",
            work_result="完成", progress_before=50,
            progress_after=60, current_user_id=99
        )

        self.assertEqual(record.user_id, 1)
        self.assertEqual(record.hours, Decimal("8.0"))
        self.assertEqual(record.status, "DRAFT")
        self.assertEqual(record.created_by, 99)

    def test_parse_progress_valid(self):
        row = pd.Series({"进度": 50})
        result = TimesheetImporter.parse_progress(row, "进度")
        self.assertEqual(result, 50)

    def test_parse_progress_nan(self):
        row = pd.Series({"进度": float("nan")})
        result = TimesheetImporter.parse_progress(row, "进度")
        self.assertIsNone(result)

    def test_parse_progress_missing_field(self):
        row = pd.Series({"other": 1})
        result = TimesheetImporter.parse_progress(row, "进度")
        self.assertIsNone(result)

    def test_parse_progress_invalid_value(self):
        row = pd.Series({"进度": "abc"})
        result = TimesheetImporter.parse_progress(row, "进度")
        self.assertIsNone(result)


class TestTimesheetImporterImport(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

    @patch.object(TimesheetImporter, "check_required_columns", return_value=["工作日期*"])
    def test_import_missing_columns_raises(self, mock_check):
        df = pd.DataFrame()
        with self.assertRaises(HTTPException):
            TimesheetImporter.import_timesheet_data(self.db, df, 1)

    @patch.object(TimesheetImporter, "check_required_columns", return_value=[])
    @patch.object(TimesheetImporter, "parse_work_date", return_value=date(2025, 1, 1))
    @patch.object(TimesheetImporter, "parse_hours", return_value=8.0)
    def test_import_happy_path(self, mock_hours, mock_date, mock_check):
        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        user.department_id = 10
        user.department = "技术部"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            user,   # User query
            None,   # Project query (no project)
            None,   # existing timesheet check
        ]

        df = pd.DataFrame([{
            "工作日期*": "2025-01-01",
            "人员姓名*": "张三",
            "工时(小时)*": 8,
        }])

        imported, updated, failed = TimesheetImporter.import_timesheet_data(self.db, df, 99)
        self.assertEqual(imported, 1)
        self.assertEqual(updated, 0)

    @patch.object(TimesheetImporter, "check_required_columns", return_value=[])
    def test_import_missing_required_fields(self, mock_check):
        df = pd.DataFrame([{
            "工作日期*": None,
            "人员姓名*": "",
            "工时(小时)*": float("nan"),
        }])

        imported, updated, failed = TimesheetImporter.import_timesheet_data(self.db, df, 1)
        self.assertEqual(imported, 0)
        self.assertEqual(len(failed), 1)


if __name__ == "__main__":
    unittest.main()
