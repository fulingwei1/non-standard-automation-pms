# -*- coding: utf-8 -*-
"""service_tickets_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.service.service_tickets_service import ServiceTicketsService

class TestServiceTicketsServiceInit:
    def test_init(self):
        service = ServiceTicketsService(Mock())
        assert service is not None
