# -*- coding: utf-8 -*-
"""exception_events_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.exception_events_service import ExceptionEventsService

class TestExceptionEventsServiceInit:
    def test_init(self):
        service = ExceptionEventsService(Mock())
        assert service is not None
