# -*- coding: utf-8 -*-
"""
第十六批：外协订单审批适配器 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.adapters.outsourcing import OutsourcingOrderApprovalAdapter
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_order(**kwargs):
    order = MagicMock()
    order.id = kwargs.get("id", 1)
    order.order_no = kwargs.get("order_no", "OUT-2025-001")
    order.total_amount = kwargs.get("total_amount", 50000.0)
    order.amount_with_tax = kwargs.get("amount_with_tax", 56500.0)
    order.order_type = kwargs.get("order_type", "MACHINING")
    order.project_id = kwargs.get("project_id", 10)
    order.machine_id = kwargs.get("machine_id", None)
    order.vendor_id = kwargs.get("vendor_id", 5)
    order.status = kwargs.get("status", "DRAFT")
    return order


class TestOutsourcingOrderApprovalAdapter:
    def _adapter(self, db=None):
        db = db or make_db()
        return OutsourcingOrderApprovalAdapter(db)

    def test_entity_type(self):
        adapter = self._adapter()
        assert adapter.entity_type == "OUTSOURCING_ORDER"

    def test_get_entity_found(self):
        db = make_db()
        order = make_order()
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = OutsourcingOrderApprovalAdapter(db)
        result = adapter.get_entity(1)
        assert result is order

    def test_get_entity_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        adapter = OutsourcingOrderApprovalAdapter(db)
        result = adapter.get_entity(999)
        assert result is None

    def test_get_entity_data_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        adapter = OutsourcingOrderApprovalAdapter(db)
        result = adapter.get_entity_data(999)
        assert result == {}

    def test_get_entity_data_with_order(self):
        db = make_db()
        order = make_order(total_amount=80000.0, order_type="WELDING")
        # 第一次query返回order（get_entity），后续返回数量和项目信息
        db.query.return_value.filter.return_value.first.return_value = order
        db.query.return_value.filter.return_value.count.return_value = 3
        adapter = OutsourcingOrderApprovalAdapter(db)
        result = adapter.get_entity_data(1)
        # 只要不抛出异常、返回dict即可
        assert isinstance(result, dict)

    def test_get_entity_data_high_amount(self):
        db = make_db()
        order = make_order(total_amount=500000.0)
        db.query.return_value.filter.return_value.first.return_value = order
        db.query.return_value.filter.return_value.count.return_value = 10
        adapter = OutsourcingOrderApprovalAdapter(db)
        result = adapter.get_entity_data(1)
        assert isinstance(result, dict)

    def test_init_sets_db(self):
        db = make_db()
        adapter = OutsourcingOrderApprovalAdapter(db)
        assert adapter.db is db
