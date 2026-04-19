# -*- coding: utf-8 -*-
"""Auto-generated tests for timesheet modules"""
from unittest.mock import MagicMock


class TestTimesheetRecordsService:
    """Tests for current timesheet records service"""

    def test_service_init(self):
        from app.services.timesheet.records.service import TimesheetRecordsService

        mock_db = MagicMock()
        service = TimesheetRecordsService(mock_db)
        assert service.db == mock_db

    def test_create_timesheet_method_exists(self):
        from app.services.timesheet.records.service import TimesheetRecordsService

        service = TimesheetRecordsService(MagicMock())
        assert callable(service.create_timesheet)

    def test_batch_create_timesheets_method_exists(self):
        from app.services.timesheet.records.service import TimesheetRecordsService

        service = TimesheetRecordsService(MagicMock())
        assert callable(service.batch_create_timesheets)

    def test_list_timesheets_method_exists(self):
        from app.services.timesheet.records.service import TimesheetRecordsService

        service = TimesheetRecordsService(MagicMock())
        assert callable(service.list_timesheets)

    def test_get_timesheet_detail_method_exists(self):
        from app.services.timesheet.records.service import TimesheetRecordsService

        service = TimesheetRecordsService(MagicMock())
        assert callable(service.get_timesheet_detail)


class TestTimesheetReminderService:
    """Tests for current timesheet reminder service"""

    def test_service_init(self):
        from app.services.timesheet.reminders.service import TimesheetReminderService

        mock_db = MagicMock()
        service = TimesheetReminderService(mock_db)
        assert service.db == mock_db

    def test_create_reminder_config_method_exists(self):
        from app.services.timesheet.reminders.service import TimesheetReminderService

        service = TimesheetReminderService(MagicMock())
        assert callable(service.create_reminder_config)

    def test_list_pending_reminders_method_exists(self):
        from app.services.timesheet.reminders.service import TimesheetReminderService

        service = TimesheetReminderService(MagicMock())
        assert callable(service.list_pending_reminders)
