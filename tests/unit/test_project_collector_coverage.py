# -*- coding: utf-8 -*-
"""project_collector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.project_collector import ProjectCollector

class TestProjectCollectorInit:
    def test_init(self):
        service = ProjectCollector(Mock())
        assert service is not None
