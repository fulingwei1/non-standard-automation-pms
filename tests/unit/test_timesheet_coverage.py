# -*- coding: utf-8 -*-
"""timesheet单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.timesheet import TimesheetApprovalAdapter

class TestTimesheetApprovalAdapterInit:
    def test_init(self):
        service = TimesheetApprovalAdapter(Mock())
        assert service is not None
