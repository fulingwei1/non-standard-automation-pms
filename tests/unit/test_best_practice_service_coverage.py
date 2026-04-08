# -*- coding: utf-8 -*-
"""最佳实践服务单元测试"""
import pytest
from unittest.mock import Mock
from app.services.best_practice_service import BestPracticeService

class TestBestPracticeServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BestPracticeService(mock_db)
        assert service.db == mock_db

class TestBestPracticeServiceMethods:
    @pytest.fixture
    def service(self):
        return BestPracticeService(Mock())
    
    def test_get_best_practices_method_exists(self, service):
        assert hasattr(service, 'get_best_practices')
