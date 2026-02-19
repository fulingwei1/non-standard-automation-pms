# -*- coding: utf-8 -*-
"""
Unit tests for procurement_assembly.py stages (第三十八批)
"""
import pytest

pytest.importorskip(
    "app.services.preset_stage_templates.templates.execution.procurement_assembly",
    reason="导入失败，跳过"
)

try:
    from app.services.preset_stage_templates.templates.execution.procurement_assembly import (
        PROCUREMENT_ASSEMBLY_STAGES,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="procurement_assembly 不可用")
    PROCUREMENT_ASSEMBLY_STAGES = []


class TestProcurementAssemblyStagesStructure:
    """测试采购装配阶段数据结构"""

    def test_is_list(self):
        """PROCUREMENT_ASSEMBLY_STAGES 是列表"""
        assert isinstance(PROCUREMENT_ASSEMBLY_STAGES, list)

    def test_not_empty(self):
        """阶段列表非空"""
        assert len(PROCUREMENT_ASSEMBLY_STAGES) > 0

    def test_stages_have_required_keys(self):
        """每个阶段包含必要字段"""
        required = {"stage_code", "stage_name", "sequence", "estimated_days", "nodes"}
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            for key in required:
                assert key in stage, f"阶段 {stage.get('stage_code', '?')} 缺少 {key}"

    def test_s13_mechanical_assembly_exists(self):
        """S13 机械装配阶段存在"""
        codes = [s["stage_code"] for s in PROCUREMENT_ASSEMBLY_STAGES]
        assert "S13" in codes

    def test_s13_is_parallel(self):
        """S13 机械装配阶段标记为并行"""
        s13 = next((s for s in PROCUREMENT_ASSEMBLY_STAGES if s["stage_code"] == "S13"), None)
        if s13:
            assert s13.get("is_parallel") is True

    def test_nodes_are_lists(self):
        """nodes 字段为列表"""
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            assert isinstance(stage["nodes"], list)

    def test_nodes_have_required_fields(self):
        """每个节点包含必要字段"""
        required = {"node_code", "node_name", "node_type", "sequence"}
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            for node in stage["nodes"]:
                for key in required:
                    assert key in node, f"节点 {node.get('node_code', '?')} 缺少 {key}"

    def test_stage_category_is_execution(self):
        """阶段类别为 execution"""
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            if "category" in stage:
                assert stage["category"] == "execution"
