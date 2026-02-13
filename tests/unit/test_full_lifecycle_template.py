# -*- coding: utf-8 -*-
"""完整生命周期模板单元测试"""
import pytest
from app.services.preset_stage_templates.templates.full_lifecycle import FULL_LIFECYCLE_TEMPLATE


class TestFullLifecycleTemplate:
    def test_template_structure(self):
        assert FULL_LIFECYCLE_TEMPLATE["template_code"] == "TPL_FULL_LIFECYCLE"
        assert "stages" in FULL_LIFECYCLE_TEMPLATE
        assert len(FULL_LIFECYCLE_TEMPLATE["stages"]) > 0

    def test_template_has_name(self):
        assert FULL_LIFECYCLE_TEMPLATE["template_name"] == "完整生命周期模板"

    def test_template_project_type(self):
        assert FULL_LIFECYCLE_TEMPLATE["project_type"] == "NEW"
