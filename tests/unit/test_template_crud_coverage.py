# -*- coding: utf-8 -*-
"""template_crud单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.template_crud import TemplateCrudMixin

class TestTemplateCrudMixinInit:
    def test_init(self):
        service = TemplateCrudMixin(Mock())
        assert service is not None
