# -*- coding: utf-8 -*-
"""项目收尾阶段定义单元测试 - 第三十四批"""

import pytest

pytest.importorskip("app.services.preset_stage_templates.templates.closure_stages")

try:
    from app.services.preset_stage_templates.templates.closure_stages import CLOSURE_STAGES
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    CLOSURE_STAGES = None


class TestClosureStagesDefinition:
    def test_has_two_stages(self):
        assert len(CLOSURE_STAGES) == 2

    def test_stage_codes(self):
        codes = [s["stage_code"] for s in CLOSURE_STAGES]
        assert "S21" in codes
        assert "S22" in codes

    def test_s21_is_required(self):
        s21 = next(s for s in CLOSURE_STAGES if s["stage_code"] == "S21")
        assert s21["is_required"] is True

    def test_s21_has_five_nodes(self):
        s21 = next(s for s in CLOSURE_STAGES if s["stage_code"] == "S21")
        assert len(s21["nodes"]) == 5

    def test_s22_has_three_nodes(self):
        s22 = next(s for s in CLOSURE_STAGES if s["stage_code"] == "S22")
        assert len(s22["nodes"]) == 3

    def test_all_stages_have_category_closure(self):
        for stage in CLOSURE_STAGES:
            assert stage["category"] == "closure"

    def test_s21_last_node_is_milestone(self):
        s21 = next(s for s in CLOSURE_STAGES if s["stage_code"] == "S21")
        last_node = s21["nodes"][-1]
        assert last_node["node_type"] == "MILESTONE"

    def test_node_codes_unique(self):
        all_codes = []
        for stage in CLOSURE_STAGES:
            for node in stage["nodes"]:
                all_codes.append(node["node_code"])
        assert len(all_codes) == len(set(all_codes))

    def test_s22_long_estimated_days(self):
        s22 = next(s for s in CLOSURE_STAGES if s["stage_code"] == "S22")
        assert s22["estimated_days"] >= 365
