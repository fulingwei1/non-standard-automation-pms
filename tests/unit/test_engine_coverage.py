# -*- coding: utf-8 -*-
"""engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.engine import PermissionError

class TestPermissionErrorInit:
    def test_init(self):
        service = PermissionError(Mock())
        assert service is not None
