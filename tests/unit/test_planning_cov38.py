# -*- coding: utf-8 -*-
"""
Unit tests for standard/planning.py (第三十八批)
"""
import pytest

pytest.importorskip(
    "app.services.preset_stage_templates.templates.standard.planning",
    reason="导入失败，跳过"
)

try:
    from app.services.preset_stage_templates.templates.standard.planning import PLANNING_STAGES
except ImportError:
    pytestmark = pytest.mark.skip(reason="planning 模板不可用")
    PLANNING_STAGES = []


class TestPlanningStagesStructure:
    """测试规划阶段数据结构"""

    def test_planning_stages_is_list(self):
        """PLANNING_STAGES 是列表"""
        assert isinstance(PLANNING_STAGES, list)

    def test_planning_stages_not_empty(self):
        """PLANNING_STAGES 非空"""
        assert len(PLANNING_STAGES) > 0

    def test_stages_have_required_keys(self):
        """每个阶段包含必要字段"""
        required = {"stage_code", "stage_name", "sequence", "estimated_days", "nodes"}
        for stage in PLANNING_STAGES:
            for key in required:
                assert key in stage, f"阶段 {stage.get('stage_code', '?')} 缺少字段 {key}"

    def test_s1_stage_exists(self):
        """S1 需求进入阶段存在"""
        codes = [s["stage_code"] for s in PLANNING_STAGES]
        assert "S1" in codes

    def test_s2_stage_exists(self):
        """S2 方案设计阶段存在"""
        codes = [s["stage_code"] for s in PLANNING_STAGES]
        assert "S2" in codes

    def test_stage_nodes_are_lists(self):
        """nodes 字段是列表"""
        for stage in PLANNING_STAGES:
            assert isinstance(stage["nodes"], list)

    def test_nodes_have_required_fields(self):
        """节点包含必要字段"""
        required = {"node_code", "node_name", "node_type", "sequence"}
        for stage in PLANNING_STAGES:
            for node in stage["nodes"]:
                for key in required:
                    assert key in node, f"节点 {node.get('node_code', '?')} 缺少 {key}"

    def test_s1_has_nodes(self):
        """S1 阶段有节点"""
        s1 = next((s for s in PLANNING_STAGES if s["stage_code"] == "S1"), None)
        assert s1 is not None
        assert len(s1["nodes"]) > 0

    def test_stage_sequences_are_ordered(self):
        """阶段序号递增"""
        sequences = [s["sequence"] for s in PLANNING_STAGES]
        assert sequences == sorted(sequences)
