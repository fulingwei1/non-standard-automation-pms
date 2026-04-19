# -*- coding: utf-8 -*-
"""stage_management单元测试"""
from app.services.stage_template.stage_management import StageManagementMixin


class TestStageManagementMixinInit:
    def test_init(self):
        assert hasattr(StageManagementMixin, "create_stage") or hasattr(StageManagementMixin, "update_stage")
