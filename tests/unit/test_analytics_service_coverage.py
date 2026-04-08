# -*- coding: utf-8 -*-
"""analytics_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project.analytics_service import ProjectAnalyticsService

class TestProjectAnalyticsServiceInit:
    def test_init(self):
        service = ProjectAnalyticsService(Mock())
        assert service is not None
