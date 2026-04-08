# -*- coding: utf-8 -*-
"""worker_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.worker_service import WorkerService

class TestWorkerServiceInit:
    def test_init(self):
        service = WorkerService(Mock())
        assert service is not None
