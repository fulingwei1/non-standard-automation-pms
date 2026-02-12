# -*- coding: utf-8 -*-
"""Tests for preset_stage_templates/templates/execution/procurement_assembly.py"""

import pytest


class TestProcurementAssemblyStages:
    def test_stages_is_list(self):
        from app.services.preset_stage_templates.templates.execution.procurement_assembly import PROCUREMENT_ASSEMBLY_STAGES
        assert isinstance(PROCUREMENT_ASSEMBLY_STAGES, list)
        assert len(PROCUREMENT_ASSEMBLY_STAGES) > 0

    def test_stage_has_required_fields(self):
        from app.services.preset_stage_templates.templates.execution.procurement_assembly import PROCUREMENT_ASSEMBLY_STAGES
        required = {"stage_code", "stage_name", "sequence", "category", "nodes"}
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            assert required.issubset(stage.keys())

    def test_all_stages_are_execution_category(self):
        from app.services.preset_stage_templates.templates.execution.procurement_assembly import PROCUREMENT_ASSEMBLY_STAGES
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            assert stage["category"] == "execution"

    def test_nodes_exist(self):
        from app.services.preset_stage_templates.templates.execution.procurement_assembly import PROCUREMENT_ASSEMBLY_STAGES
        for stage in PROCUREMENT_ASSEMBLY_STAGES:
            assert len(stage["nodes"]) > 0

    def test_stage_codes_unique(self):
        from app.services.preset_stage_templates.templates.execution.procurement_assembly import PROCUREMENT_ASSEMBLY_STAGES
        codes = [s["stage_code"] for s in PROCUREMENT_ASSEMBLY_STAGES]
        assert len(codes) == len(set(codes))
