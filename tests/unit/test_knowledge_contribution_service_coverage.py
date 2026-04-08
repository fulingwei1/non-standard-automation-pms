# -*- coding: utf-8 -*-
"""knowledge_contribution_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.knowledge_contribution_service import KnowledgeContributionService

class TestKnowledgeContributionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = KnowledgeContributionService(mock_db)
        assert hasattr(service, 'db')
