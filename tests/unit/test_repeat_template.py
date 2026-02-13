# -*- coding: utf-8 -*-
"""repeat template 单元测试"""
from app.services.preset_stage_templates.templates.repeat import REPEAT_TEMPLATE


class TestRepeatTemplate:
    def test_template_code(self):
        assert REPEAT_TEMPLATE["template_code"] == "TPL_REPEAT"

    def test_template_has_stages(self):
        assert len(REPEAT_TEMPLATE["stages"]) == 4

    def test_stage_codes(self):
        codes = [s["stage_code"] for s in REPEAT_TEMPLATE["stages"]]
        assert codes == ["R1", "R2", "R3", "R4"]

    def test_stages_ordered(self):
        seqs = [s["sequence"] for s in REPEAT_TEMPLATE["stages"]]
        assert seqs == sorted(seqs)

    def test_each_stage_has_nodes(self):
        for stage in REPEAT_TEMPLATE["stages"]:
            assert len(stage["nodes"]) > 0

    def test_all_nodes_have_required_fields(self):
        for stage in REPEAT_TEMPLATE["stages"]:
            for node in stage["nodes"]:
                assert "node_code" in node
                assert "node_name" in node
                assert "owner_role_code" in node

    def test_project_type(self):
        assert REPEAT_TEMPLATE["project_type"] == "REPEAT"
