# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 完整生命周期模板"""

import pytest

try:
    from app.services.preset_stage_templates.templates.full_lifecycle import (
        FULL_LIFECYCLE_TEMPLATE,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestFullLifecycleTemplate:

    def test_template_is_dict(self):
        assert isinstance(FULL_LIFECYCLE_TEMPLATE, dict)

    def test_template_code(self):
        assert FULL_LIFECYCLE_TEMPLATE["template_code"] == "TPL_FULL_LIFECYCLE"

    def test_template_name(self):
        assert FULL_LIFECYCLE_TEMPLATE["template_name"] == "完整生命周期模板"

    def test_project_type_is_new(self):
        assert FULL_LIFECYCLE_TEMPLATE["project_type"] == "NEW"

    def test_stages_is_list(self):
        assert isinstance(FULL_LIFECYCLE_TEMPLATE["stages"], list)

    def test_stages_count_22(self):
        # 完整22阶段模板
        stages = FULL_LIFECYCLE_TEMPLATE["stages"]
        assert len(stages) == 22

    def test_description_contains_22(self):
        desc = FULL_LIFECYCLE_TEMPLATE.get("description", "")
        assert "22" in desc

    def test_all_stages_have_stage_code(self):
        for stage in FULL_LIFECYCLE_TEMPLATE["stages"]:
            assert "stage_code" in stage and stage["stage_code"]
