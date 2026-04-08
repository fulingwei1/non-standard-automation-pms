# -*- coding: utf-8 -*-
"""project_filter单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_scope.project_filter import ProjectFilterService

class TestProjectFilterServiceInit:
    def test_init(self):
        service = ProjectFilterService(Mock())
        assert service is not None
