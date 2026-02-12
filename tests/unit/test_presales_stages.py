# -*- coding: utf-8 -*-
"""Tests for preset_stage_templates/templates/presales_stages.py"""

import pytest


class TestPresalesStages:
    """测试售前阶段模板数据"""

    def test_presales_stages_is_list(self):
        from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES
        assert isinstance(PRESALES_STAGES, list)
        assert len(PRESALES_STAGES) > 0

    def test_stage_has_required_fields(self):
        from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES
        required = {"stage_code", "stage_name", "sequence", "category", "nodes"}
        for stage in PRESALES_STAGES:
            assert required.issubset(stage.keys()), f"Stage {stage.get('stage_code')} missing fields"

    def test_stage_codes_start_with_s(self):
        from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES
        for stage in PRESALES_STAGES:
            assert stage["stage_code"].startswith("S"), f"Bad code: {stage['stage_code']}"

    def test_all_stages_are_presales_category(self):
        from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES
        for stage in PRESALES_STAGES:
            assert stage["category"] == "presales"

    def test_nodes_have_required_fields(self):
        from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES
        required = {"node_code", "node_name", "node_type", "sequence"}
        for stage in PRESALES_STAGES:
            for node in stage["nodes"]:
                assert required.issubset(node.keys()), f"Node {node.get('node_code')} missing fields"

    def test_stage_codes_are_unique(self):
        from app.services.preset_stage_templates.templates.presales_stages import PRESALES_STAGES
        codes = [s["stage_code"] for s in PRESALES_STAGES]
        assert len(codes) == len(set(codes))
