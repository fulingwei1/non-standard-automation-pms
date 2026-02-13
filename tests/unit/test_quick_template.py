# -*- coding: utf-8 -*-
"""quick template 单元测试"""
from app.services.preset_stage_templates.templates.quick import QUICK_TEMPLATE


class TestQuickTemplate:
    def test_template_code(self):
        assert QUICK_TEMPLATE["template_code"] == "TPL_QUICK"

    def test_has_4_stages(self):
        assert len(QUICK_TEMPLATE["stages"]) == 4

    def test_stage_codes(self):
        codes = [s["stage_code"] for s in QUICK_TEMPLATE["stages"]]
        assert codes == ["Q1", "Q2", "Q3", "Q4"]

    def test_project_type(self):
        assert QUICK_TEMPLATE["project_type"] == "SIMPLE"

    def test_all_stages_required(self):
        for stage in QUICK_TEMPLATE["stages"]:
            assert stage["is_required"] is True

    def test_nodes_have_deliverables(self):
        for stage in QUICK_TEMPLATE["stages"]:
            for node in stage["nodes"]:
                assert "deliverables" in node
                assert len(node["deliverables"]) > 0
