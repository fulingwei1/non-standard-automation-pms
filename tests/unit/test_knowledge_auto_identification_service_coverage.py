# -*- coding: utf-8 -*-
"""knowledge_auto_identification_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.knowledge_auto_identification_service import KnowledgeAutoIdentificationService

class TestKnowledgeAutoIdentificationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = KnowledgeAutoIdentificationService(mock_db)
        assert hasattr(service, 'db')
