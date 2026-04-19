# -*- coding: utf-8 -*-
"""timesheet_importer单元测试"""
from app.services.unified_import.timesheet_importer import TimesheetImporter


class TestTimesheetImporterInit:
    def test_init(self):
        assert hasattr(TimesheetImporter, "create_timesheet_record")
        assert hasattr(TimesheetImporter, "import_timesheet_data")
