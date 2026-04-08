# -*- coding: utf-8 -*-
"""ecn_collector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.ecn_collector import EcnCollector

class TestEcnCollectorInit:
    def test_init(self):
        service = EcnCollector(Mock())
        assert service is not None
