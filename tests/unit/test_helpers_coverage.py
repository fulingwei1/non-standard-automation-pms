# -*- coding: utf-8 -*-
"""helpers单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.helpers import HelpersMixin

class TestHelpersMixinInit:
    def test_init(self):
        service = HelpersMixin(Mock())
        assert service is not None
