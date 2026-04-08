# -*- coding: utf-8 -*-
"""work_log_collector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.work_log_collector import WorkLogCollector

class TestWorkLogCollectorInit:
    def test_init(self):
        service = WorkLogCollector(Mock())
        assert service is not None
