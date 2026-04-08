# -*- coding: utf-8 -*-
"""json_renderer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.renderers.json_renderer import CustomJSONEncoder

class TestCustomJSONEncoderInit:
    def test_init(self):
        service = CustomJSONEncoder(Mock())
        assert service is not None
