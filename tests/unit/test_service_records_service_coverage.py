# -*- coding: utf-8 -*-
"""service_records_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.service.service_records_service import ServiceRecordsService

class TestServiceRecordsServiceInit:
    def test_init(self):
        service = ServiceRecordsService(Mock())
        assert service is not None
