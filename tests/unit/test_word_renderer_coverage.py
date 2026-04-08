# -*- coding: utf-8 -*-
"""word_renderer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.renderers.word_renderer import WordRenderer

class TestWordRendererInit:
    def test_init(self):
        service = WordRenderer(Mock())
        assert service is not None
