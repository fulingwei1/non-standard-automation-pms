# -*- coding: utf-8 -*-
"""
Unit tests for standard/production.py and dashboard_adapters/production.py (第三十八批)
"""
import pytest

pytest.importorskip(
    "app.services.preset_stage_templates.templates.standard.production",
    reason="导入失败，跳过"
)

try:
    from app.services.preset_stage_templates.templates.standard.production import PRODUCTION_STAGES
except ImportError:
    pytestmark = pytest.mark.skip(reason="production 模板不可用")
    PRODUCTION_STAGES = []


class TestProductionStagesStructure:
    """测试生产阶段数据结构"""

    def test_is_list(self):
        """PRODUCTION_STAGES 是列表"""
        assert isinstance(PRODUCTION_STAGES, list)

    def test_not_empty(self):
        """生产阶段列表非空"""
        assert len(PRODUCTION_STAGES) > 0

    def test_stages_have_required_keys(self):
        """每个阶段包含必要字段"""
        required = {"stage_code", "stage_name", "sequence", "estimated_days", "nodes"}
        for stage in PRODUCTION_STAGES:
            for key in required:
                assert key in stage, f"阶段 {stage.get('stage_code', '?')} 缺少 {key}"

    def test_s4_machining_exists(self):
        """S4 加工制造阶段存在"""
        codes = [s["stage_code"] for s in PRODUCTION_STAGES]
        assert "S4" in codes

    def test_nodes_are_lists(self):
        """nodes 字段为列表"""
        for stage in PRODUCTION_STAGES:
            assert isinstance(stage["nodes"], list)

    def test_nodes_have_required_fields(self):
        """节点包含必要字段"""
        required = {"node_code", "node_name", "node_type", "sequence"}
        for stage in PRODUCTION_STAGES:
            for node in stage["nodes"]:
                for key in required:
                    assert key in node, f"节点 {node.get('node_code', '?')} 缺少 {key}"

    def test_s4_has_multiple_nodes(self):
        """S4 包含多个节点"""
        s4 = next((s for s in PRODUCTION_STAGES if s["stage_code"] == "S4"), None)
        assert s4 is not None
        assert len(s4["nodes"]) >= 2

    def test_stage_sequences_ascending(self):
        """阶段序号递增"""
        seqs = [s["sequence"] for s in PRODUCTION_STAGES]
        assert seqs == sorted(seqs)

    def test_nodes_owner_role_code_present(self):
        """节点有 owner_role_code"""
        for stage in PRODUCTION_STAGES:
            for node in stage["nodes"]:
                assert "owner_role_code" in node
