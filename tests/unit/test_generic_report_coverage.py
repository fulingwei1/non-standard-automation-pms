# -*- coding: utf-8 -*-
"""generic_report单元测试"""
import pytest
from unittest.mock import Mock
from services/template_report/generic_report import GenericReportMixin

class TestGenericReportMixinInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = GenericReportMixin(mock_db)
        assert hasattr(service, 'db')
