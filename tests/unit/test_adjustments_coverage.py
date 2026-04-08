# -*- coding: utf-8 -*-
"""adjustments单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_instance.adjustments import AdjustmentsMixin

class TestAdjustmentsMixinInit:
    def test_init(self):
        service = AdjustmentsMixin(Mock())
        assert service is not None
