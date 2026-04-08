# -*- coding: utf-8 -*-
"""employee_performance_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.employee_performance.employee_performance_service import EmployeePerformanceService

class TestEmployeePerformanceServiceInit:
    def test_init(self):
        service = EmployeePerformanceService(Mock())
        assert service is not None
