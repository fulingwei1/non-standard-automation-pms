# -*- coding: utf-8 -*-
"""资源排程服务单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_scheduling.resource_scheduling_service import ResourceSchedulingService

class TestResourceSchedulingServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ResourceSchedulingService(mock_db)
        assert service.db == mock_db

class TestResourceSchedulingServiceMethods:
    @pytest.fixture
    def service(self):
        return ResourceSchedulingService(Mock())
    
    def test_schedule_resources_method_exists(self, service):
        assert hasattr(service, 'schedule_resources')
