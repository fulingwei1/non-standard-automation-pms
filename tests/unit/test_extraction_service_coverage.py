# -*- coding: utf-8 -*-
"""extraction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.knowledge.extraction_service import KnowledgeExtractionService

class TestKnowledgeExtractionServiceInit:
    def test_init(self):
        service = KnowledgeExtractionService(Mock())
        assert service is not None
