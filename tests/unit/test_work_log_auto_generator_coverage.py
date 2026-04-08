# -*- coding: utf-8 -*-
"""work_log_auto_generator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.work_log_auto_generator import WorkLogAutoGenerator

class TestWorkLogAutoGeneratorInit:
    def test_init(self):
        service = WorkLogAutoGenerator(Mock())
        assert service is not None
