# -*- coding: utf-8 -*-
"""base_builder单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ppt_generator.base_builder import BaseSlideBuilder

class TestBaseSlideBuilderInit:
    def test_init(self):
        service = BaseSlideBuilder(Mock())
        assert service is not None
