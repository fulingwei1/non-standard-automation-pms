# -*- coding: utf-8 -*-
"""template单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.template import TemplateReportAdapter

class TestTemplateReportAdapterInit:
    def test_init(self):
        service = TemplateReportAdapter(Mock())
        assert service is not None
