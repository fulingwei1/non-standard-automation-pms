# -*- coding: utf-8 -*-
"""meeting单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.meeting import MeetingReportAdapter

class TestMeetingReportAdapterInit:
    def test_init(self):
        service = MeetingReportAdapter(Mock())
        assert service is not None
