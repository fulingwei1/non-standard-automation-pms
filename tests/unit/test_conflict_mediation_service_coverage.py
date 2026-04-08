# -*- coding: utf-8 -*-
"""conflict_mediation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.conflict_mediation_service import ConflictMediationService

class TestConflictMediationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ConflictMediationService(mock_db)
        assert hasattr(service, 'db')
