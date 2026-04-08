# -*- coding: utf-8 -*-
"""content_builder单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ppt_generator.content_builder import ContentSlideBuilder

class TestContentSlideBuilderInit:
    def test_init(self):
        service = ContentSlideBuilder(Mock())
        assert service is not None
