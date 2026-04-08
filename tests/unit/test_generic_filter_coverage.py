# -*- coding: utf-8 -*-
"""generic_filter单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_scope.generic_filter import GenericFilterService

class TestGenericFilterServiceInit:
    def test_init(self):
        service = GenericFilterService(Mock())
        assert service is not None
