# -*- coding: utf-8 -*-
"""batch_tracing_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.material_tracking.batch_tracing_service import BatchTracingService

class TestBatchTracingServiceInit:
    def test_init(self):
        service = BatchTracingService(Mock())
        assert service is not None
