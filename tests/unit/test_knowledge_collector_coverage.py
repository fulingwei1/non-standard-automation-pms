# -*- coding: utf-8 -*-
"""knowledge_collector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.knowledge_collector import KnowledgeCollector

class TestKnowledgeCollectorInit:
    def test_init(self):
        service = KnowledgeCollector(Mock())
        assert service is not None
