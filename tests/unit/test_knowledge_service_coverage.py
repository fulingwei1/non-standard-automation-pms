# -*- coding: utf-8 -*-
"""knowledge_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.exception.knowledge_service import KnowledgeService

class TestKnowledgeServiceInit:
    def test_init(self):
        service = KnowledgeService(Mock())
        assert service is not None
