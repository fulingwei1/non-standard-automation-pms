# -*- coding: utf-8 -*-
"""stage_management单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.stage_management import StageManagementMixin

class TestStageManagementMixinInit:
    def test_init(self):
        service = StageManagementMixin(Mock())
        assert service is not None
