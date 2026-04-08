# -*- coding: utf-8 -*-
"""finance_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project.finance_service import ProjectFinanceService

class TestProjectFinanceServiceInit:
    def test_init(self):
        service = ProjectFinanceService(Mock())
        assert service is not None
