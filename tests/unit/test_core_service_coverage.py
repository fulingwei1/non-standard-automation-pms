# -*- coding: utf-8 -*-
"""core_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project.core_service import ProjectCoreService

class TestProjectCoreServiceInit:
    def test_init(self):
        service = ProjectCoreService(Mock())
        assert service is not None
