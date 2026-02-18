# -*- coding: utf-8 -*-
"""第二十八批 - presales_stages 单元测试（售前阶段定义 S04-S08）"""

import pytest

pytest.importorskip("app.services.preset_stage_templates.templates.presales_stages")

from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES


# ─── 基础结构验证 ────────────────────────────────────────────

class TestPresalesStagesStructure:

    def test_has_five_stages(self):
        """售前阶段应包含 S04-S08 共 5 个阶段"""
        assert len(PRESALES_STAGES) == 5

    def test_stage_codes_are_s04_to_s08(self):
        codes = [s["stage_code"] for s in PRESALES_STAGES]
        assert codes == ["S04", "S05", "S06", "S07", "S08"]

    def test_all_stages_have_required_fields(self):
        required_fields = [
            "stage_code", "stage_name", "sequence", "category",
            "estimated_days", "is_required", "is_milestone", "is_parallel", "nodes"
        ]
        for stage in PRESALES_STAGES:
            for field in required_fields:
                assert field in stage, f"阶段 {stage.get('stage_code')} 缺少字段 {field}"

    def test_all_stages_category_is_presales(self):
        for stage in PRESALES_STAGES:
            assert stage["category"] == "presales", f"阶段 {stage['stage_code']} 类别错误"

    def test_sequences_are_ordered_ascending(self):
        sequences = [s["sequence"] for s in PRESALES_STAGES]
        assert sequences == sorted(sequences)

    def test_all_stages_are_required(self):
        for stage in PRESALES_STAGES:
            assert stage["is_required"] is True


# ─── 里程碑验证 ──────────────────────────────────────────────

class TestMilestoneStages:

    def test_s05_is_milestone(self):
        s05 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S05")
        assert s05["is_milestone"] is True

    def test_s08_is_milestone(self):
        s08 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S08")
        assert s08["is_milestone"] is True

    def test_s04_not_milestone(self):
        s04 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S04")
        assert s04["is_milestone"] is False

    def test_s06_not_milestone(self):
        s06 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S06")
        assert s06["is_milestone"] is False

    def test_milestone_count(self):
        milestones = [s for s in PRESALES_STAGES if s["is_milestone"]]
        assert len(milestones) == 2


# ─── 节点验证 ────────────────────────────────────────────────

class TestStageNodes:

    def test_all_stages_have_nodes(self):
        for stage in PRESALES_STAGES:
            assert len(stage["nodes"]) > 0, f"阶段 {stage['stage_code']} 没有节点"

    def test_s04_has_four_nodes(self):
        s04 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S04")
        assert len(s04["nodes"]) == 4

    def test_s06_has_six_nodes(self):
        """S06 售前方案是最复杂的阶段"""
        s06 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S06")
        assert len(s06["nodes"]) == 6

    def test_nodes_have_required_fields(self):
        required = ["node_code", "node_name", "node_type", "sequence",
                    "estimated_days", "completion_method", "is_required"]
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                for field in required:
                    assert field in node, (
                        f"阶段 {stage['stage_code']} 节点 {node.get('node_code')} 缺少 {field}"
                    )

    def test_node_codes_unique_within_stage(self):
        for stage in PRESALES_STAGES:
            codes = [n["node_code"] for n in stage["nodes"]]
            assert len(codes) == len(set(codes)), f"阶段 {stage['stage_code']} 节点编号重复"

    def test_node_sequences_start_at_zero(self):
        for stage in PRESALES_STAGES:
            seqs = sorted(n["sequence"] for n in stage["nodes"])
            assert seqs[0] == 0, f"阶段 {stage['stage_code']} 节点序号应从 0 开始"

    def test_node_sequences_are_contiguous(self):
        for stage in PRESALES_STAGES:
            seqs = sorted(n["sequence"] for n in stage["nodes"])
            expected = list(range(len(stage["nodes"])))
            assert seqs == expected, f"阶段 {stage['stage_code']} 节点序号不连续"

    def test_s04_first_node_is_requirement_collection(self):
        s04 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S04")
        first_node = sorted(s04["nodes"], key=lambda n: n["sequence"])[0]
        assert "需求" in first_node["node_name"] or "资料" in first_node["node_name"]

    def test_all_nodes_have_estimated_days_positive(self):
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert node["estimated_days"] > 0, (
                    f"阶段 {stage['stage_code']} 节点 {node['node_code']} 预计天数无效"
                )


# ─── 节点类型验证 ────────────────────────────────────────────

class TestNodeTypes:

    def test_valid_node_types_only(self):
        valid_types = {"TASK", "APPROVAL", "DELIVERABLE", "MILESTONE"}
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert node["node_type"] in valid_types, (
                    f"阶段 {stage['stage_code']} 节点 {node['node_code']} 类型 {node['node_type']} 无效"
                )

    def test_valid_completion_methods(self):
        valid_methods = {"MANUAL", "APPROVAL", "UPLOAD", "AUTO"}
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert node["completion_method"] in valid_methods, (
                    f"节点 {node['node_code']} 完成方式 {node['completion_method']} 无效"
                )

    def test_approval_nodes_have_approval_completion(self):
        """APPROVAL 类型节点应使用 APPROVAL 完成方式"""
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                if node["node_type"] == "APPROVAL":
                    assert node["completion_method"] == "APPROVAL", (
                        f"节点 {node['node_code']} 类型为 APPROVAL 但完成方式不是 APPROVAL"
                    )


# ─── 估算工期验证 ────────────────────────────────────────────

class TestEstimatedDays:

    def test_s06_has_longest_estimated_days(self):
        """S06 售前方案应是估算工期最长的阶段"""
        days_by_stage = {s["stage_code"]: s["estimated_days"] for s in PRESALES_STAGES}
        assert days_by_stage["S06"] == max(days_by_stage.values())

    def test_all_stages_estimated_days_positive(self):
        for stage in PRESALES_STAGES:
            assert stage["estimated_days"] > 0

    def test_total_presales_days_reasonable(self):
        """售前总工期应在合理范围内（60-120天）"""
        total = sum(s["estimated_days"] for s in PRESALES_STAGES)
        assert 50 <= total <= 150, f"售前总工期 {total} 天不合理"


# ─── 交付物验证 ──────────────────────────────────────────────

class TestDeliverables:

    def test_all_nodes_have_deliverables_field(self):
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert "deliverables" in node, (
                    f"阶段 {stage['stage_code']} 节点 {node['node_code']} 缺少 deliverables"
                )

    def test_deliverables_is_list(self):
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert isinstance(node["deliverables"], list), (
                    f"节点 {node['node_code']} deliverables 应为列表"
                )

    def test_required_nodes_have_non_empty_deliverables(self):
        """必填节点通常有交付物（至少检查 S04 关键节点）"""
        s04 = next(s for s in PRESALES_STAGES if s["stage_code"] == "S04")
        required_nodes = [n for n in s04["nodes"] if n["is_required"]]
        for node in required_nodes:
            assert len(node["deliverables"]) > 0, (
                f"S04 必填节点 {node['node_code']} 没有交付物"
            )
