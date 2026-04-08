# -*- coding: utf-8 -*-
"""relationship_scoring_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.relationship_scoring_service import RelationshipScoringService

class TestRelationshipScoringServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = RelationshipScoringService(mock_db)
        assert hasattr(service, 'db')
