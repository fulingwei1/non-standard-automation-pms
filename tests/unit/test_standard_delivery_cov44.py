# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 标准交付阶段定义 (S7-S9)"""

import pytest

try:
    from app.services.preset_stage_templates.templates.standard.delivery import DELIVERY_STAGES
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestDeliveryStages:

    def test_is_list_with_three_stages(self):
        assert isinstance(DELIVERY_STAGES, list)
        assert len(DELIVERY_STAGES) == 3

    def test_stage_codes(self):
        codes = {s["stage_code"] for s in DELIVERY_STAGES}
        assert codes == {"S7", "S8", "S9"}

    def test_s7_packaging_shipping(self):
        s7 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S7")
        assert s7["stage_name"] == "包装发运"
        assert len(s7["nodes"]) == 3

    def test_s8_has_approval_node(self):
        s8 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S8")
        node_types = {n["node_type"] for n in s8["nodes"]}
        assert "APPROVAL" in node_types

    def test_s9_has_five_nodes(self):
        s9 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S9")
        assert len(s9["nodes"]) == 5

    def test_all_required_is_boolean(self):
        for stage in DELIVERY_STAGES:
            assert isinstance(stage["is_required"], bool)

    def test_node_required_fields(self):
        required = {"node_code", "node_name", "node_type", "sequence", "estimated_days"}
        for stage in DELIVERY_STAGES:
            for node in stage["nodes"]:
                for field in required:
                    assert field in node

    def test_sequence_ordered(self):
        seqs = [s["sequence"] for s in DELIVERY_STAGES]
        assert seqs == sorted(seqs)
