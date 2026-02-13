# -*- coding: utf-8 -*-
"""执行阶段重导出单元测试"""
import pytest
from app.services.preset_stage_templates.templates.execution_stages import EXECUTION_STAGES


class TestExecutionStagesReexport:
    def test_execution_stages_exists(self):
        assert EXECUTION_STAGES is not None
        assert isinstance(EXECUTION_STAGES, list)
