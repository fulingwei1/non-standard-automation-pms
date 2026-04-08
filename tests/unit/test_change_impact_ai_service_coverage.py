# -*- coding: utf-8 -*-
"""变更影响AI服务单元测试"""
import pytest
from unittest.mock import Mock
from app.services.change_impact_ai_service import ChangeImpactAIService

class TestChangeImpactAIServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ChangeImpactAIService(mock_db)
        assert service.db == mock_db

class TestChangeImpactAIServiceMethods:
    @pytest.fixture
    def service(self):
        return ChangeImpactAIService(Mock())
    
    def test_analyze_impact_method_exists(self, service):
        assert hasattr(service, 'analyze_impact')
