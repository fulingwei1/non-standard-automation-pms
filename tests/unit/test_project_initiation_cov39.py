# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - preset_stage_templates/templates/execution/project_initiation.py
"""
import pytest

pytest.importorskip(
    "app.services.preset_stage_templates.templates.execution.project_initiation",
    reason="import failed, skip"
)


@pytest.fixture
def stages():
    from app.services.preset_stage_templates.templates.execution.project_initiation import (
        PROJECT_INITIATION_STAGES,
    )
    return PROJECT_INITIATION_STAGES


class TestProjectInitiationStages:

    def test_stages_is_list(self, stages):
        assert isinstance(stages, list)
        assert len(stages) > 0

    def test_stage_codes_are_unique(self, stages):
        codes = [s["stage_code"] for s in stages]
        assert len(codes) == len(set(codes))

    def test_stage_s09_is_milestone(self, stages):
        s09 = next((s for s in stages if s["stage_code"] == "S09"), None)
        assert s09 is not None
        assert s09["is_milestone"] is True

    def test_stage_s11_is_parallel(self, stages):
        s11 = next((s for s in stages if s["stage_code"] == "S11"), None)
        assert s11 is not None
        assert s11["is_parallel"] is True

    def test_all_stages_have_nodes(self, stages):
        for stage in stages:
            assert "nodes" in stage
            assert len(stage["nodes"]) > 0

    def test_stage_sequences_ordered(self, stages):
        sequences = [s["sequence"] for s in stages]
        assert sequences == sorted(sequences)

    def test_node_dependency_codes_are_lists(self, stages):
        for stage in stages:
            for node in stage["nodes"]:
                if "dependency_node_codes" in node:
                    assert isinstance(node["dependency_node_codes"], list)

    def test_each_stage_has_category_execution(self, stages):
        for stage in stages:
            assert stage.get("category") == "execution"
