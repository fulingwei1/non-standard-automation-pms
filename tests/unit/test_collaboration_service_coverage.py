# -*- coding: utf-8 -*-
"""collaboration_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.collaboration_service import CollaborationService

class TestCollaborationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CollaborationService(mock_db)
        assert hasattr(service, 'db')
