# -*- coding: utf-8 -*-
"""requirement_extraction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.requirement_extraction_service import RequirementExtractionService

class TestRequirementExtractionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = RequirementExtractionService(mock_db)
        assert hasattr(service, 'db')
