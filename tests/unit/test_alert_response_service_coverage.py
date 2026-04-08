# -*- coding: utf-8 -*-
"""alert_response_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.alert_response_service import AlertResponseService

class TestAlertResponseServiceInit:
    def test_init(self):
        service = AlertResponseService(Mock())
        assert service is not None
