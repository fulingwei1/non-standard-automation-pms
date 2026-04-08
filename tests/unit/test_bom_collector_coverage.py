# -*- coding: utf-8 -*-
"""bom_collector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.bom_collector import BomCollector

class TestBomCollectorInit:
    def test_init(self):
        service = BomCollector(Mock())
        assert service is not None
