# -*- coding: utf-8 -*-
"""exception_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.exception_service import AlertExceptionsService

class TestAlertExceptionsServiceInit:
    def test_init(self):
        service = AlertExceptionsService(Mock())
        assert service is not None
