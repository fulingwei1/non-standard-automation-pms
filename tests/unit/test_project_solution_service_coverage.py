# -*- coding: utf-8 -*-
"""project_solution_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_solution_service import ProjectSolutionService

class TestProjectSolutionServiceInit:
    def test_init(self):
        service = ProjectSolutionService(Mock())
        assert service is not None
