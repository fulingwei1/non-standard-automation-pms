# -*- coding: utf-8 -*-
"""shortage_reports_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.shortage.shortage_reports_service import ShortageReportsService

class TestShortageReportsServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ShortageReportsService(mock_db)
        assert hasattr(service, 'db')
