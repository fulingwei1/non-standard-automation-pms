# -*- coding: utf-8 -*-
"""failure_patterns单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_waste_analysis.failure_patterns import FailurePatternsMixin

class TestFailurePatternsMixinInit:
    def test_init(self):
        service = FailurePatternsMixin(Mock())
        assert service is not None
