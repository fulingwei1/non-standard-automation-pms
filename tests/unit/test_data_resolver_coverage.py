# -*- coding: utf-8 -*-
"""data_resolver单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.data_resolver import DataResolver

class TestDataResolverInit:
    def test_init(self):
        service = DataResolver(Mock())
        assert service is not None
