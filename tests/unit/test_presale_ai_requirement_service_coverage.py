# -*- coding: utf-8 -*-
"""售前AI需求服务单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_ai_requirement_service import AIRequirementAnalyzer, PresaleAIRequirementService

class TestAIRequirementAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AIRequirementAnalyzer(mock_db)
        assert service.db == mock_db

class TestPresaleAIRequirementServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PresaleAIRequirementService(mock_db)
        assert service.db == mock_db
