# -*- coding: utf-8 -*-
"""resource_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project.resource_service import ProjectResourceService

class TestProjectResourceServiceInit:
    def test_init(self):
        service = ProjectResourceService(Mock())
        assert service is not None
