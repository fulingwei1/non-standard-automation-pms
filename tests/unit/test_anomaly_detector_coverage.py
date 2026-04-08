# -*- coding: utf-8 -*-
"""anomaly_detector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.timesheet.reminder.anomaly_detector import TimesheetAnomalyDetector

class TestTimesheetAnomalyDetectorInit:
    def test_init(self):
        service = TimesheetAnomalyDetector(Mock())
        assert service is not None
