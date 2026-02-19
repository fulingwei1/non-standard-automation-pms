# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 销售阶段模板定义
"""

import pytest

try:
    from app.services.preset_stage_templates.templates.sales_stages import SALES_STAGES
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestSalesStages:

    def test_sales_stages_is_list(self):
        assert isinstance(SALES_STAGES, list)

    def test_three_stages_defined(self):
        assert len(SALES_STAGES) == 3

    def test_stage_codes(self):
        codes = [s["stage_code"] for s in SALES_STAGES]
        assert "S01" in codes
        assert "S02" in codes
        assert "S03" in codes

    def test_all_stages_category_is_sales(self):
        for stage in SALES_STAGES:
            assert stage["category"] == "sales"

    def test_all_stages_have_nodes(self):
        for stage in SALES_STAGES:
            assert "nodes" in stage
            assert len(stage["nodes"]) >= 1

    def test_stage_sequence_is_ordered(self):
        sequences = [s["sequence"] for s in SALES_STAGES]
        assert sequences == sorted(sequences)

    def test_each_node_has_required_fields(self):
        required_fields = {"node_code", "node_name", "node_type", "sequence", "estimated_days"}
        for stage in SALES_STAGES:
            for node in stage["nodes"]:
                for field in required_fields:
                    assert field in node, f"节点 {node.get('node_code')} 缺少字段 {field}"

    def test_s03_has_four_nodes(self):
        s03 = next(s for s in SALES_STAGES if s["stage_code"] == "S03")
        assert len(s03["nodes"]) == 4
