# -*- coding: utf-8 -*-
"""check单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_integrity.check import DataCheckMixin

class TestDataCheckMixinInit:
    def test_init(self):
        service = DataCheckMixin(Mock())
        assert service is not None
