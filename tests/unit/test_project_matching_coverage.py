# -*- coding: utf-8 -*-
"""project_matching单元测试"""
import pytest
from unittest.mock import Mock
from app.services.work_log_ai.project_matching import ProjectMatchingMixin

class TestProjectMatchingMixinInit:
    def test_init(self):
        service = ProjectMatchingMixin(Mock())
        assert service is not None
