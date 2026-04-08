# -*- coding: utf-8 -*-
"""parser单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.expressions.parser import ExpressionError

class TestExpressionErrorInit:
    def test_init(self):
        service = ExpressionError(Mock())
        assert service is not None
