# -*- coding: utf-8 -*-
"""stage_flow单元测试"""
from app.services.stage_instance.stage_flow import StageFlowMixin


class TestStageFlowMixinInit:
    def test_init(self):
        assert StageFlowMixin is not None
