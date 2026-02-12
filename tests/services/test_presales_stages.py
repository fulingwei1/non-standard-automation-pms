# -*- coding: utf-8 -*-
"""售前阶段模板 (PRESALES_STAGES) 单元测试"""

import pytest

from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES


class TestPresalesStages:
    """验证 PRESALES_STAGES 数据结构完整性和正确性"""

    def test_is_list(self):
        assert isinstance(PRESALES_STAGES, list)

    def test_has_five_stages(self):
        assert len(PRESALES_STAGES) == 5

    def test_stage_codes(self):
        codes = [s["stage_code"] for s in PRESALES_STAGES]
        assert codes == ["S04", "S05", "S06", "S07", "S08"]

    def test_sequence_ascending(self):
        seqs = [s["sequence"] for s in PRESALES_STAGES]
        assert seqs == sorted(seqs)

    def test_all_presales_category(self):
        for stage in PRESALES_STAGES:
            assert stage["category"] == "presales"

    def test_required_fields_present(self):
        required = {"stage_code", "stage_name", "sequence", "category",
                     "estimated_days", "description", "is_required",
                     "is_milestone", "is_parallel", "nodes"}
        for stage in PRESALES_STAGES:
            assert required.issubset(stage.keys()), f"{stage['stage_code']} missing keys"

    def test_all_stages_required(self):
        for stage in PRESALES_STAGES:
            assert stage["is_required"] is True

    def test_milestones(self):
        milestones = [s["stage_code"] for s in PRESALES_STAGES if s["is_milestone"]]
        assert "S05" in milestones
        assert "S08" in milestones

    def test_no_parallel(self):
        for stage in PRESALES_STAGES:
            assert stage["is_parallel"] is False

    def test_estimated_days_positive(self):
        for stage in PRESALES_STAGES:
            assert stage["estimated_days"] > 0

    def test_each_stage_has_nodes(self):
        for stage in PRESALES_STAGES:
            assert len(stage["nodes"]) > 0

    def test_node_required_fields(self):
        required = {"node_code", "node_name", "node_type", "sequence",
                     "estimated_days", "completion_method", "is_required",
                     "description", "owner_role_code", "deliverables"}
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert required.issubset(node.keys()), \
                    f"{node['node_code']} missing keys: {required - node.keys()}"

    def test_node_codes_unique(self):
        all_codes = []
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                all_codes.append(node["node_code"])
        assert len(all_codes) == len(set(all_codes))

    def test_node_codes_prefix_matches_stage(self):
        for stage in PRESALES_STAGES:
            prefix = stage["stage_code"]
            for node in stage["nodes"]:
                assert node["node_code"].startswith(prefix), \
                    f"{node['node_code']} should start with {prefix}"

    def test_node_sequences_unique_per_stage(self):
        for stage in PRESALES_STAGES:
            seqs = [n["sequence"] for n in stage["nodes"]]
            assert len(seqs) == len(set(seqs))

    def test_node_types_valid(self):
        valid = {"TASK", "APPROVAL", "DELIVERABLE", "MILESTONE"}
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert node["node_type"] in valid, f"{node['node_code']} bad type"

    def test_completion_methods_valid(self):
        valid = {"MANUAL", "APPROVAL", "UPLOAD"}
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert node["completion_method"] in valid

    def test_deliverables_are_lists(self):
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert isinstance(node["deliverables"], list)
                assert len(node["deliverables"]) > 0

    def test_dependency_codes_reference_existing_nodes(self):
        for stage in PRESALES_STAGES:
            node_codes = {n["node_code"] for n in stage["nodes"]}
            for node in stage["nodes"]:
                deps = node.get("dependency_node_codes", [])
                for dep in deps:
                    assert dep in node_codes, \
                        f"{node['node_code']} depends on {dep} not in stage"

    def test_s04_needs_review(self):
        s04 = PRESALES_STAGES[0]
        assert s04["stage_name"] == "需求评审"
        assert len(s04["nodes"]) == 4

    def test_s06_has_most_nodes(self):
        s06 = [s for s in PRESALES_STAGES if s["stage_code"] == "S06"][0]
        assert len(s06["nodes"]) == 6

    def test_s06_longest_duration(self):
        s06 = [s for s in PRESALES_STAGES if s["stage_code"] == "S06"][0]
        assert s06["estimated_days"] == 30
        assert s06["estimated_days"] == max(s["estimated_days"] for s in PRESALES_STAGES)
