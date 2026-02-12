# -*- coding: utf-8 -*-
"""项目收尾阶段定义 单元测试"""
import pytest

from app.services.preset_stage_templates.templates.closure_stages import CLOSURE_STAGES


class TestClosureStages:
    def test_has_two_stages(self):
        assert len(CLOSURE_STAGES) == 2

    def test_stage_codes(self):
        codes = [s["stage_code"] for s in CLOSURE_STAGES]
        assert "S21" in codes
        assert "S22" in codes

    def test_s21_has_five_nodes(self):
        s21 = [s for s in CLOSURE_STAGES if s["stage_code"] == "S21"][0]
        assert len(s21["nodes"]) == 5

    def test_s22_has_three_nodes(self):
        s22 = [s for s in CLOSURE_STAGES if s["stage_code"] == "S22"][0]
        assert len(s22["nodes"]) == 3

    def test_all_nodes_have_required_fields(self):
        for stage in CLOSURE_STAGES:
            for node in stage["nodes"]:
                assert "node_code" in node
                assert "node_name" in node
                assert "node_type" in node
                assert "sequence" in node

    def test_s21_category(self):
        s21 = CLOSURE_STAGES[0]
        assert s21["category"] == "closure"

    def test_s22_estimated_days(self):
        s22 = [s for s in CLOSURE_STAGES if s["stage_code"] == "S22"][0]
        assert s22["estimated_days"] == 365

    def test_node_sequences_ordered(self):
        for stage in CLOSURE_STAGES:
            seqs = [n["sequence"] for n in stage["nodes"]]
            assert seqs == sorted(seqs)

    def test_milestone_node_exists(self):
        s21 = CLOSURE_STAGES[0]
        milestones = [n for n in s21["nodes"] if n["node_type"] == "MILESTONE"]
        assert len(milestones) >= 1
