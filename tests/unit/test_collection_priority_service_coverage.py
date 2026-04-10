# -*- coding: utf-8 -*-
"""collection_priority_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.collection_priority_service import CollectionUrgency

class TestCollectionUrgencyInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CollectionUrgency(mock_db)
        assert hasattr(service, 'db')
