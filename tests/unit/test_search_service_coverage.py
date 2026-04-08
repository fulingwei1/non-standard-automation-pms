# -*- coding: utf-8 -*-
"""search_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.knowledge.search_service import KnowledgeSearchService

class TestKnowledgeSearchServiceInit:
    def test_init(self):
        service = KnowledgeSearchService(Mock())
        assert service is not None
