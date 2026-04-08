# -*- coding: utf-8 -*-
"""execution_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project.execution_service import ProjectExecutionService

class TestProjectExecutionServiceInit:
    def test_init(self):
        service = ProjectExecutionService(Mock())
        assert service is not None
