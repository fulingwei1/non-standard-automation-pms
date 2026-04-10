# -*- coding: utf-8 -*-
"""knowledge_syncer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_review_ai.knowledge_syncer import ProjectKnowledgeSyncer

class TestProjectKnowledgeSyncerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectKnowledgeSyncer(mock_db)
        assert hasattr(service, 'db')
