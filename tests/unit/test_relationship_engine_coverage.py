# -*- coding: utf-8 -*-
"""relationship_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.engines.relationship_engine import RelationshipEngine

class TestRelationshipEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = RelationshipEngine(mock_db)
        assert hasattr(service, 'db')
