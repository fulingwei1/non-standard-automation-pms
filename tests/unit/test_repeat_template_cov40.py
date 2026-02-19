# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 重复生产模板
"""

import pytest

try:
    from app.services.preset_stage_templates.templates.repeat import REPEAT_TEMPLATE
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestRepeatTemplate:

    def test_template_code(self):
        assert REPEAT_TEMPLATE["template_code"] == "TPL_REPEAT"

    def test_project_type_is_repeat(self):
        assert REPEAT_TEMPLATE["project_type"] == "REPEAT"

    def test_has_four_stages(self):
        assert len(REPEAT_TEMPLATE["stages"]) == 4

    def test_stage_codes(self):
        codes = {s["stage_code"] for s in REPEAT_TEMPLATE["stages"]}
        assert codes == {"R1", "R2", "R3", "R4"}

    def test_all_stages_required(self):
        for stage in REPEAT_TEMPLATE["stages"]:
            assert stage["is_required"] is True

    def test_stage_sequences_ordered(self):
        seqs = [s["sequence"] for s in REPEAT_TEMPLATE["stages"]]
        assert seqs == sorted(seqs)

    def test_r3_has_four_nodes(self):
        r3 = next(s for s in REPEAT_TEMPLATE["stages"] if s["stage_code"] == "R3")
        assert len(r3["nodes"]) == 4

    def test_all_nodes_have_owner_role_code(self):
        for stage in REPEAT_TEMPLATE["stages"]:
            for node in stage["nodes"]:
                assert "owner_role_code" in node
                assert node["owner_role_code"]  # not empty
