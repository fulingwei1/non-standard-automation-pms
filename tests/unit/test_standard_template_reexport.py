# -*- coding: utf-8 -*-
"""标准模板重导出单元测试"""
import pytest
from app.services.preset_stage_templates.templates.standard import STANDARD_TEMPLATE, STANDARD_STAGES


class TestStandardTemplateReexport:
    def test_standard_template_exists(self):
        assert STANDARD_TEMPLATE is not None
        assert "template_code" in STANDARD_TEMPLATE

    def test_standard_stages_exists(self):
        assert STANDARD_STAGES is not None
        assert isinstance(STANDARD_STAGES, list)
