# -*- coding: utf-8 -*-
"""delay_root_cause_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.delay_root_cause_service import DelayRootCauseService

class TestDelayRootCauseServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DelayRootCauseService(mock_db)
        assert hasattr(service, 'db')
