# -*- coding: utf-8 -*-
"""project_evaluation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_evaluation_service import ProjectEvaluationService

class TestProjectEvaluationServiceInit:
    def test_init(self):
        service = ProjectEvaluationService(Mock())
        assert service is not None
