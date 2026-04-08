# -*- coding: utf-8 -*-
"""timesheet_records单元测试"""
import pytest
from unittest.mock import Mock
from app.services.timesheet_records import TimesheetRecordsService

class TestTimesheetRecordsServiceInit:
    def test_init(self):
        service = TimesheetRecordsService(Mock())
        assert service is not None
