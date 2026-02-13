# -*- coding: utf-8 -*-
"""ECN级联影响分析单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.ecn_bom_analysis_service.cascade import analyze_cascade_impact


class TestAnalyzeCascadeImpact:
    def test_empty_items(self):
        result = analyze_cascade_impact(MagicMock(), [], set())
        assert result == []

    def test_upward_cascade(self):
        parent = MagicMock()
        parent.id = 1
        parent.parent_item_id = None
        parent.material_code = "M001"
        parent.material_name = "父物料"
        child = MagicMock()
        child.id = 2
        child.parent_item_id = 1
        child.material_code = "M002"
        child.material_name = "子物料"
        result = analyze_cascade_impact(MagicMock(), [parent, child], {2})
        assert any(r['cascade_type'] == 'UPWARD' for r in result)

    def test_downward_cascade(self):
        parent = MagicMock()
        parent.id = 1
        parent.parent_item_id = None
        parent.material_code = "M001"
        parent.material_name = "父物料"
        child = MagicMock()
        child.id = 2
        child.parent_item_id = 1
        child.material_code = "M002"
        child.material_name = "子物料"
        result = analyze_cascade_impact(MagicMock(), [parent, child], {1})
        assert any(r['cascade_type'] == 'DOWNWARD' for r in result)

    def test_no_cascade_needed(self):
        item = MagicMock()
        item.id = 1
        item.parent_item_id = None
        result = analyze_cascade_impact(MagicMock(), [item], {1})
        assert result == []
