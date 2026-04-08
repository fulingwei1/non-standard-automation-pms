# -*- coding: utf-8 -*-
"""project_reports单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_data_generation.project_reports import ProjectReportMixin

class TestProjectReportMixinInit:
    def test_init(self):
        service = ProjectReportMixin(Mock())
        assert service is not None
