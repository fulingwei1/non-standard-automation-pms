# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 调试和验收阶段定义 (S17-S20)"""

import pytest

try:
    from app.services.preset_stage_templates.templates.execution.testing_acceptance import (
        TESTING_ACCEPTANCE_STAGES,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestTestingAcceptanceStages:

    def test_is_list_with_four_stages(self):
        assert isinstance(TESTING_ACCEPTANCE_STAGES, list)
        assert len(TESTING_ACCEPTANCE_STAGES) == 4

    def test_stage_codes_present(self):
        codes = {s["stage_code"] for s in TESTING_ACCEPTANCE_STAGES}
        assert codes == {"S17", "S18", "S19", "S20"}

    def test_all_stages_category_execution(self):
        for stage in TESTING_ACCEPTANCE_STAGES:
            assert stage["category"] == "execution"

    def test_milestone_stages(self):
        milestones = {s["stage_code"] for s in TESTING_ACCEPTANCE_STAGES if s.get("is_milestone")}
        assert "S17" in milestones
        assert "S20" in milestones
        assert "S18" not in milestones

    def test_each_stage_has_nodes(self):
        for stage in TESTING_ACCEPTANCE_STAGES:
            assert "nodes" in stage and len(stage["nodes"]) >= 1

    def test_node_required_fields(self):
        required = {"node_code", "node_name", "node_type", "sequence", "estimated_days"}
        for stage in TESTING_ACCEPTANCE_STAGES:
            for node in stage["nodes"]:
                for field in required:
                    assert field in node, f"节点 {node.get('node_code')} 缺少字段 {field}"

    def test_sequence_monotone_increasing(self):
        seqs = [s["sequence"] for s in TESTING_ACCEPTANCE_STAGES]
        assert seqs == sorted(seqs)

    def test_s17_has_five_nodes(self):
        s17 = next(s for s in TESTING_ACCEPTANCE_STAGES if s["stage_code"] == "S17")
        assert len(s17["nodes"]) == 5

    def test_s20_last_node_is_milestone(self):
        s20 = next(s for s in TESTING_ACCEPTANCE_STAGES if s["stage_code"] == "S20")
        last_node = max(s20["nodes"], key=lambda n: n["sequence"])
        assert last_node["node_type"] == "MILESTONE"
