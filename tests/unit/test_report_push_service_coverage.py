# -*- coding: utf-8 -*-
"""report_push_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_report_auto.report_push_service import ReportPushService

class TestReportPushServiceInit:
    def test_init(self):
        service = ReportPushService(Mock())
        assert service is not None
