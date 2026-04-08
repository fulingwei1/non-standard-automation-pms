# -*- coding: utf-8 -*-
"""manager_performance_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.manager_performance.manager_performance_service import ManagerPerformanceService

class TestManagerPerformanceServiceInit:
    def test_init(self):
        service = ManagerPerformanceService(Mock())
        assert service is not None
