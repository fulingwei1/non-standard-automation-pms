# -*- coding: utf-8 -*-
"""default_template单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.default_template import DefaultTemplateMixin

class TestDefaultTemplateMixinInit:
    def test_init(self):
        service = DefaultTemplateMixin(Mock())
        assert service is not None
