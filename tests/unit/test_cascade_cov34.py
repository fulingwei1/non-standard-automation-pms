# -*- coding: utf-8 -*-
"""ECN BOM级联分析单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.ecn_bom_analysis_service.cascade")

try:
    from app.services.ecn_bom_analysis_service.cascade import analyze_cascade_impact
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    analyze_cascade_impact = None


def make_item(item_id, material_code, material_name, parent_id=None):
    item = MagicMock()
    item.id = item_id
    item.material_code = material_code
    item.material_name = material_name
    item.parent_item_id = parent_id
    return item


class TestAnalyzeCascadeImpact:
    def test_empty_bom_returns_empty(self):
        service = MagicMock()
        result = analyze_cascade_impact(service, [], set())
        assert result == []

    def test_no_affected_items_returns_empty(self):
        service = MagicMock()
        items = [make_item(1, "A001", "物料A")]
        result = analyze_cascade_impact(service, items, set())
        assert result == []

    def test_upward_cascade_detected(self):
        """子物料受影响，父物料应被标记 UPWARD"""
        service = MagicMock()
        parent = make_item(1, "P001", "父物料")
        child = make_item(2, "C001", "子物料", parent_id=1)
        result = analyze_cascade_impact(service, [parent, child], {2})
        upward = [r for r in result if r["cascade_type"] == "UPWARD"]
        assert len(upward) == 1
        assert upward[0]["material_code"] == "P001"

    def test_downward_cascade_detected(self):
        """父物料受影响，子物料应被标记 DOWNWARD"""
        service = MagicMock()
        parent = make_item(1, "P001", "父物料")
        child = make_item(2, "C001", "子物料", parent_id=1)
        result = analyze_cascade_impact(service, [parent, child], {1})
        downward = [r for r in result if r["cascade_type"] == "DOWNWARD"]
        assert len(downward) == 1
        assert downward[0]["material_code"] == "C001"

    def test_no_duplicate_processing(self):
        """已受影响的物料不应重复出现在结果中"""
        service = MagicMock()
        parent = make_item(1, "P001", "父物料")
        child = make_item(2, "C001", "子物料", parent_id=1)
        # Both parent and child are initially affected
        result = analyze_cascade_impact(service, [parent, child], {1, 2})
        # Neither should appear as cascade because both are already in affected_item_ids
        assert len(result) == 0

    def test_multi_level_cascade(self):
        """多层级联：孙物料受影响 -> 父物料 -> 祖物料"""
        service = MagicMock()
        grandparent = make_item(1, "GP001", "祖物料")
        parent = make_item(2, "P001", "父物料", parent_id=1)
        child = make_item(3, "C001", "子物料", parent_id=2)
        result = analyze_cascade_impact(service, [grandparent, parent, child], {3})
        codes = [r["material_code"] for r in result]
        assert "P001" in codes
        assert "GP001" in codes

    def test_result_has_expected_keys(self):
        service = MagicMock()
        parent = make_item(10, "X001", "物料X")
        child = make_item(11, "Y001", "物料Y", parent_id=10)
        result = analyze_cascade_impact(service, [parent, child], {11})
        assert len(result) > 0
        for item in result:
            assert "bom_item_id" in item
            assert "material_code" in item
            assert "cascade_type" in item
