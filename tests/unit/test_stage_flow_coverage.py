# -*- coding: utf-8 -*-
"""stage_flow单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_instance.stage_flow import StageFlowMixin

class TestStageFlowMixinInit:
    def test_init(self):
        service = StageFlowMixin(Mock())
        assert service is not None
