# -*- coding: utf-8 -*-
"""design_collector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.design_collector import DesignCollector

class TestDesignCollectorInit:
    def test_init(self):
        service = DesignCollector(Mock())
        assert service is not None
