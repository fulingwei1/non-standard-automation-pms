# -*- coding: utf-8 -*-
"""Tests for preset_stage_templates/templates/execution/project_initiation.py"""

import pytest


class TestProjectInitiationStages:
    def test_stages_is_list(self):
        from app.services.preset_stage_templates.templates.execution.project_initiation import PROJECT_INITIATION_STAGES
        assert isinstance(PROJECT_INITIATION_STAGES, list)
        assert len(PROJECT_INITIATION_STAGES) > 0

    def test_stage_has_required_fields(self):
        from app.services.preset_stage_templates.templates.execution.project_initiation import PROJECT_INITIATION_STAGES
        required = {"stage_code", "stage_name", "sequence", "category"}
        for stage in PROJECT_INITIATION_STAGES:
            assert required.issubset(stage.keys())

    def test_all_stages_are_execution_category(self):
        from app.services.preset_stage_templates.templates.execution.project_initiation import PROJECT_INITIATION_STAGES
        for stage in PROJECT_INITIATION_STAGES:
            assert stage["category"] == "execution"

    def test_has_milestone_stage(self):
        from app.services.preset_stage_templates.templates.execution.project_initiation import PROJECT_INITIATION_STAGES
        milestones = [s for s in PROJECT_INITIATION_STAGES if s.get("is_milestone")]
        assert len(milestones) > 0

    def test_stage_codes_unique(self):
        from app.services.preset_stage_templates.templates.execution.project_initiation import PROJECT_INITIATION_STAGES
        codes = [s["stage_code"] for s in PROJECT_INITIATION_STAGES]
        assert len(codes) == len(set(codes))
