# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - preset_stage_templates/templates/quick.py
"""
import pytest

pytest.importorskip("app.services.preset_stage_templates.templates.quick",
                    reason="import failed, skip")


@pytest.fixture
def template():
    from app.services.preset_stage_templates.templates.quick import QUICK_TEMPLATE
    return QUICK_TEMPLATE


class TestQuickTemplate:

    def test_template_code(self, template):
        assert template["template_code"] == "TPL_QUICK"

    def test_template_has_stages(self, template):
        assert "stages" in template
        assert len(template["stages"]) > 0

    def test_all_stages_have_required_fields(self, template):
        for stage in template["stages"]:
            assert "stage_code" in stage
            assert "stage_name" in stage
            assert "sequence" in stage
            assert "nodes" in stage
            assert "is_required" in stage

    def test_stages_ordered_by_sequence(self, template):
        sequences = [s["sequence"] for s in template["stages"]]
        assert sequences == sorted(sequences)

    def test_all_nodes_have_required_fields(self, template):
        for stage in template["stages"]:
            for node in stage["nodes"]:
                assert "node_code" in node
                assert "node_name" in node
                assert "node_type" in node
                assert "owner_role_code" in node

    def test_stage_q4_contains_approval_node(self, template):
        q4 = next((s for s in template["stages"] if s["stage_code"] == "Q4"), None)
        assert q4 is not None
        approval_nodes = [n for n in q4["nodes"] if n["node_type"] == "APPROVAL"]
        assert len(approval_nodes) >= 1

    def test_project_type_is_simple(self, template):
        assert template["project_type"] == "SIMPLE"

    def test_total_stages_count(self, template):
        assert len(template["stages"]) == 4
