# -*- coding: utf-8 -*-
"""timesheet_importer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.unified_import.timesheet_importer import TimesheetImporter

class TestTimesheetImporterInit:
    def test_init(self):
        service = TimesheetImporter(Mock())
        assert service is not None
