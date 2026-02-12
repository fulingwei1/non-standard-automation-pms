# -*- coding: utf-8 -*-
"""Tests for preset_stage_templates/templates/execution/testing_acceptance.py"""

import pytest


class TestTestingAcceptanceStages:
    def test_stages_is_list(self):
        from app.services.preset_stage_templates.templates.execution.testing_acceptance import TESTING_ACCEPTANCE_STAGES
        assert isinstance(TESTING_ACCEPTANCE_STAGES, list)
        assert len(TESTING_ACCEPTANCE_STAGES) > 0

    def test_stage_has_required_fields(self):
        from app.services.preset_stage_templates.templates.execution.testing_acceptance import TESTING_ACCEPTANCE_STAGES
        required = {"stage_code", "stage_name", "sequence", "category"}
        for stage in TESTING_ACCEPTANCE_STAGES:
            assert required.issubset(stage.keys())

    def test_all_stages_are_execution_category(self):
        from app.services.preset_stage_templates.templates.execution.testing_acceptance import TESTING_ACCEPTANCE_STAGES
        for stage in TESTING_ACCEPTANCE_STAGES:
            assert stage["category"] == "execution"

    def test_stage_codes_unique(self):
        from app.services.preset_stage_templates.templates.execution.testing_acceptance import TESTING_ACCEPTANCE_STAGES
        codes = [s["stage_code"] for s in TESTING_ACCEPTANCE_STAGES]
        assert len(codes) == len(set(codes))
