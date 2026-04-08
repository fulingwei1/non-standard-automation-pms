# -*- coding: utf-8 -*-
"""initialization单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_instance.initialization import InitializationMixin

class TestInitializationMixinInit:
    def test_init(self):
        service = InitializationMixin(Mock())
        assert service is not None
