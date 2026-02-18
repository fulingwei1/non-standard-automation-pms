# -*- coding: utf-8 -*-
"""第十七批 - 装配齐套优化服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, timedelta
from decimal import Decimal

pytest.importorskip("app.services.assembly_kit_optimizer")


def _mock_db():
    return MagicMock()


class TestAssemblyKitOptimizer:

    def test_optimize_no_blocking_returns_original(self):
        """无阻塞缺料时返回原始预计日期"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        readiness = MagicMock()
        readiness.estimated_ready_date = date(2026, 3, 1)

        result = AssemblyKitOptimizer.optimize_estimated_ready_date(db, readiness)
        assert result == date(2026, 3, 1)

    def test_generate_suggestions_empty_when_no_shortages(self):
        """无阻塞缺料时 generate_optimization_suggestions 返回空列表"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        readiness = MagicMock()
        result = AssemblyKitOptimizer.generate_optimization_suggestions(db, readiness)
        assert result == []

    def test_suggest_expedite_purchase_no_material_id(self):
        """shortage.material_id 为 None 时返回 None"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        shortage = MagicMock()
        shortage.material_id = None

        result = AssemblyKitOptimizer._suggest_expedite_purchase(db, shortage)
        assert result is None

    def test_suggest_substitute_no_material_id(self):
        """shortage.material_id 为 None 时 _suggest_substitute 返回 None"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        shortage = MagicMock()
        shortage.material_id = None
        shortage.bom_item_id = 5

        # bom_item 找不到
        db.query.return_value.filter.return_value.first.return_value = None
        result = AssemblyKitOptimizer._suggest_substitute(db, shortage)
        assert result is None

    def test_suggest_priority_adjustment_urgent(self):
        """距需求日期不足 7 天时生成优先级建议"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        shortage = MagicMock()
        shortage.material_id = 10
        shortage.purchase_order_id = 20
        shortage.required_date = date.today() + timedelta(days=2)
        shortage.material_code = "MAT-001"
        shortage.material_name = "测试物料"

        po = MagicMock()
        po.order_no = "PO-001"
        db.query.return_value.filter.return_value.first.return_value = po

        result = AssemblyKitOptimizer._suggest_priority_adjustment(db, shortage)
        assert result is not None
        assert result["type"] == "ADJUST_PRIORITY"
        assert result["priority"] == "HIGH"

    def test_suggest_priority_no_required_date(self):
        """required_date 为 None 时返回 None"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        shortage = MagicMock()
        shortage.material_id = 10
        shortage.purchase_order_id = 20
        shortage.required_date = None

        po = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = po
        result = AssemblyKitOptimizer._suggest_priority_adjustment(db, shortage)
        assert result is None

    def test_optimize_by_purchase_order_no_material_id(self):
        """material_id 为 None 时 _optimize_by_purchase_order 返回 None"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        shortage = MagicMock()
        shortage.material_id = None

        result = AssemblyKitOptimizer._optimize_by_purchase_order(db, shortage)
        assert result is None

    def test_optimize_by_substitute_no_bom_item(self):
        """bom_item 不存在时 _optimize_by_substitute 返回 None"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        db = _mock_db()
        shortage = MagicMock()
        shortage.material_id = 1
        shortage.bom_item_id = 99

        db.query.return_value.filter.return_value.first.return_value = None
        result = AssemblyKitOptimizer._optimize_by_substitute(db, shortage)
        assert result is None
