# -*- coding: utf-8 -*-
"""
CostCollectionService 深度覆盖测试（N3组）

覆盖：
- collect_from_purchase_order (不存在/已归集更新/无项目/正常创建/预警失败不影响)
- collect_from_outsourcing_order (同上)
- collect_from_ecn (不存在/无成本影响/已归集/无项目/正常创建)
- remove_cost_from_source (不存在/成功删除/更新项目成本)
- collect_from_bom (不存在/未关联项目/未发布/零金额删除/BOM总金额/创建新/更新现有)
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_order(project_id=1, total_amount=Decimal("1000"), tax_amount=Decimal("100"),
                order_no="PO-001", order_title="采购订单", order_date=None,
                created_at=None):
    order = MagicMock()
    order.id = 1
    order.project_id = project_id
    order.total_amount = total_amount
    order.tax_amount = tax_amount
    order.order_no = order_no
    order.order_title = order_title
    order.order_date = order_date or date.today()
    order.created_at = created_at
    return order


def _make_project(project_id=1, actual_cost=0):
    proj = MagicMock()
    proj.id = project_id
    proj.actual_cost = actual_cost
    return proj


def _make_cost_record(source_id=1, amount=Decimal("500")):
    cost = MagicMock()
    cost.id = 1
    cost.source_id = source_id
    cost.amount = amount
    cost.project_id = 1
    return cost


# ---------------------------------------------------------------------------
# collect_from_purchase_order
# ---------------------------------------------------------------------------

class TestCollectFromPurchaseOrder:
    def test_returns_none_when_order_not_found(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_purchase_order(mock_db, 999)
        assert result is None

    def test_returns_none_when_no_project(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = _make_order(project_id=None)
        # First query: order, Second: existing cost (None)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None]
        result = CostCollectionService.collect_from_purchase_order(mock_db, 1)
        assert result is None

    def test_updates_existing_cost_record(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = _make_order(project_id=1, total_amount=Decimal("2000"), tax_amount=Decimal("200"))
        existing_cost = _make_cost_record()
        project = _make_project(actual_cost=5000)
        all_costs = [MagicMock(amount=Decimal("1000")), MagicMock(amount=Decimal("2000"))]
        all_costs[0].amount = Decimal("1000")
        all_costs[1].amount = Decimal("2000")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            order,  # order query
            existing_cost,  # existing cost query
            project,  # project query
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = all_costs

        result = CostCollectionService.collect_from_purchase_order(mock_db, 1)
        assert result is existing_cost
        assert existing_cost.amount == Decimal("2000")
        mock_db.add.assert_called()

    def test_creates_new_cost_record(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = _make_order(project_id=5, total_amount=Decimal("1500"))
        project = _make_project(project_id=5, actual_cost=1000)

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            order,  # order
            None,   # no existing cost
            project,  # project
        ]

        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_purchase_order(mock_db, 1, created_by=10)

        assert result is not None
        assert result.project_id == 5
        assert result.amount == Decimal("1500")
        mock_db.add.assert_called()

    def test_cost_alert_failure_doesnt_break_collection(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = _make_order(project_id=3, total_amount=Decimal("500"))
        project = _make_project(project_id=3, actual_cost=200)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None, project]

        with patch(
            "app.services.cost_collection_service.CostAlertService.check_budget_execution",
            side_effect=Exception("alert failed")
        ):
            result = CostCollectionService.collect_from_purchase_order(mock_db, 1)
        # Collection should succeed despite alert failure
        assert result is not None

    def test_updates_project_actual_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = _make_order(project_id=2, total_amount=Decimal("3000"))
        project = _make_project(project_id=2, actual_cost=1000)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None, project]

        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_purchase_order(mock_db, 1)
        assert project.actual_cost == pytest.approx(4000.0, abs=0.01)

    def test_uses_custom_cost_date(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = _make_order(project_id=1, total_amount=Decimal("100"))
        project = _make_project()
        custom_date = date(2025, 3, 15)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None, project]
        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_purchase_order(
                mock_db, 1, cost_date=custom_date
            )
        assert result.cost_date == custom_date


# ---------------------------------------------------------------------------
# collect_from_outsourcing_order
# ---------------------------------------------------------------------------

class TestCollectFromOutsourcingOrder:
    def _make_outsourcing(self, **kwargs):
        o = MagicMock()
        o.id = kwargs.get("id", 1)
        o.project_id = kwargs.get("project_id", 1)
        o.machine_id = kwargs.get("machine_id", None)
        o.total_amount = kwargs.get("total_amount", Decimal("2000"))
        o.tax_amount = kwargs.get("tax_amount", Decimal("0"))
        o.order_no = kwargs.get("order_no", "OUT-001")
        o.order_title = kwargs.get("order_title", "外协订单")
        o.created_at = kwargs.get("created_at", None)
        return o

    def test_returns_none_when_order_not_found(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_outsourcing_order(mock_db, 999)
        assert result is None

    def test_returns_none_when_no_project(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = self._make_outsourcing(project_id=None)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None]
        result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)
        assert result is None

    def test_creates_new_outsourcing_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = self._make_outsourcing(project_id=2, total_amount=Decimal("5000"))
        project = _make_project(project_id=2)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None, project]

        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)
        assert result is not None
        assert result.cost_type == "OUTSOURCING"
        assert result.cost_category == "OUTSOURCING"

    def test_updates_existing_outsourcing_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = self._make_outsourcing(project_id=2, total_amount=Decimal("7000"))
        existing_cost = _make_cost_record(amount=Decimal("5000"))
        project = _make_project(project_id=2)
        costs = [MagicMock(amount=Decimal("3000")), MagicMock(amount=Decimal("4000"))]
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, existing_cost, project]
        mock_db.query.return_value.filter.return_value.all.return_value = costs
        result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)
        assert result is existing_cost
        assert existing_cost.amount == Decimal("7000")

    def test_alert_failure_doesnt_break_collection(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        order = self._make_outsourcing(project_id=3)
        project = _make_project(project_id=3)
        mock_db.query.return_value.filter.return_value.first.side_effect = [order, None, project]
        with patch(
            "app.services.cost_collection_service.CostAlertService.check_budget_execution",
            side_effect=Exception("alert error")
        ):
            result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)
        assert result is not None


# ---------------------------------------------------------------------------
# collect_from_ecn
# ---------------------------------------------------------------------------

class TestCollectFromEcn:
    def _make_ecn(self, **kwargs):
        ecn = MagicMock()
        ecn.id = kwargs.get("id", 1)
        ecn.ecn_no = kwargs.get("ecn_no", "ECN-001")
        ecn.ecn_title = kwargs.get("ecn_title", "变更")
        ecn.project_id = kwargs.get("project_id", 1)
        ecn.machine_id = kwargs.get("machine_id", None)
        ecn.cost_impact = kwargs.get("cost_impact", Decimal("0"))
        return ecn

    def test_returns_none_when_ecn_not_found(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_ecn(mock_db, 999)
        assert result is None

    def test_returns_none_when_zero_cost_impact(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        ecn = self._make_ecn(cost_impact=Decimal("0"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is None

    def test_returns_none_when_negative_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        ecn = self._make_ecn(cost_impact=Decimal("-100"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is None

    def test_returns_none_when_no_project(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        ecn = self._make_ecn(project_id=None, cost_impact=Decimal("5000"))
        mock_db.query.return_value.filter.return_value.first.side_effect = [ecn, None]
        result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is None

    def test_creates_new_ecn_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        ecn = self._make_ecn(cost_impact=Decimal("10000"), project_id=3)
        project = _make_project(project_id=3)
        mock_db.query.return_value.filter.return_value.first.side_effect = [ecn, None, project]
        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is not None
        assert result.cost_type == "CHANGE"
        assert result.cost_category == "ECN"
        assert result.tax_amount == Decimal("0")

    def test_updates_existing_ecn_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        ecn = self._make_ecn(cost_impact=Decimal("8000"), project_id=4)
        existing_cost = _make_cost_record(amount=Decimal("5000"))
        project = _make_project(project_id=4)
        costs = [MagicMock(amount=Decimal("3000")), MagicMock(amount=Decimal("5000"))]
        mock_db.query.return_value.filter.return_value.first.side_effect = [ecn, existing_cost, project]
        mock_db.query.return_value.filter.return_value.all.return_value = costs
        result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is existing_cost
        assert existing_cost.amount == Decimal("8000")


# ---------------------------------------------------------------------------
# remove_cost_from_source
# ---------------------------------------------------------------------------

class TestRemoveCostFromSource:
    def test_returns_false_when_cost_not_found(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.remove_cost_from_source(
            mock_db, "PURCHASE", "PURCHASE_ORDER", 999
        )
        assert result is False

    def test_deletes_cost_and_updates_project(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        cost = _make_cost_record(amount=Decimal("1000"))
        cost.project_id = 2
        project = _make_project(project_id=2, actual_cost=3000)
        mock_db.query.return_value.filter.return_value.first.side_effect = [cost, project]
        result = CostCollectionService.remove_cost_from_source(
            mock_db, "PURCHASE", "PURCHASE_ORDER", 1
        )
        assert result is True
        mock_db.delete.assert_called_once_with(cost)
        assert project.actual_cost == pytest.approx(2000.0, abs=0.01)

    def test_project_cost_never_goes_below_zero(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        cost = _make_cost_record(amount=Decimal("9999"))
        cost.project_id = 1
        project = _make_project(project_id=1, actual_cost=100)
        mock_db.query.return_value.filter.return_value.first.side_effect = [cost, project]
        CostCollectionService.remove_cost_from_source(mock_db, "ECN", "ECN", 1)
        assert project.actual_cost == 0

    def test_handles_no_project_gracefully(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        cost = _make_cost_record(amount=Decimal("500"))
        cost.project_id = None
        mock_db.query.return_value.filter.return_value.first.side_effect = [cost, None]
        result = CostCollectionService.remove_cost_from_source(
            mock_db, "BOM", "BOM_COST", 1
        )
        assert result is True


# ---------------------------------------------------------------------------
# collect_from_bom
# ---------------------------------------------------------------------------

class TestCollectFromBom:
    def _make_bom(self, **kwargs):
        bom = MagicMock()
        bom.id = kwargs.get("id", 1)
        bom.project_id = kwargs.get("project_id", 1)
        bom.machine_id = kwargs.get("machine_id", None)
        bom.bom_no = kwargs.get("bom_no", "BOM-001")
        bom.bom_name = kwargs.get("bom_name", "测试BOM")
        bom.status = kwargs.get("status", "RELEASED")
        bom.total_amount = kwargs.get("total_amount", None)
        return bom

    def test_raises_when_bom_not_found(self):
        from app.services.cost_collection_service import CostCollectionService
        mock_db = MagicMock()
        with patch("app.services.cost_collection_service.CostCollectionService.collect_from_bom"):
            pass  # need to import models
        from app.models.material import BomHeader, BomItem

        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="BOM不存在"):
            CostCollectionService.collect_from_bom(mock_db, 999)

    def test_raises_when_no_project(self):
        from app.services.cost_collection_service import CostCollectionService
        from app.models.material import BomHeader
        mock_db = MagicMock()
        bom = self._make_bom(project_id=None)
        mock_db.query.return_value.filter.return_value.first.return_value = bom
        with pytest.raises(ValueError, match="未关联项目"):
            CostCollectionService.collect_from_bom(mock_db, 1)

    def test_raises_when_not_released(self):
        from app.services.cost_collection_service import CostCollectionService
        from app.models.material import BomHeader
        mock_db = MagicMock()
        bom = self._make_bom(status="DRAFT")
        mock_db.query.return_value.filter.return_value.first.return_value = bom
        with pytest.raises(ValueError, match="已发布"):
            CostCollectionService.collect_from_bom(mock_db, 1)

    def test_removes_existing_cost_when_bom_total_zero(self):
        from app.services.cost_collection_service import CostCollectionService
        from app.models.material import BomHeader, BomItem
        mock_db = MagicMock()
        bom = self._make_bom(status="RELEASED")
        existing_cost = _make_cost_record(amount=Decimal("500"))
        project = _make_project()
        item1 = MagicMock()
        item1.amount = Decimal("0")
        # BOM query first, existing cost second, project for update third
        mock_db.query.return_value.filter.return_value.first.side_effect = [bom, existing_cost, project]
        mock_db.query.return_value.filter.return_value.all.return_value = [item1]
        with patch("app.services.cost_collection_service.delete_obj") as mock_delete:
            result = CostCollectionService.collect_from_bom(mock_db, 1)
        assert result is None
        mock_delete.assert_called_once()

    def test_creates_new_bom_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        from app.models.material import BomHeader, BomItem
        mock_db = MagicMock()
        bom = self._make_bom(status="RELEASED")
        project = _make_project()
        item1 = MagicMock()
        item1.amount = Decimal("1000")
        item2 = MagicMock()
        item2.amount = Decimal("2000")
        mock_db.query.return_value.filter.return_value.first.side_effect = [bom, None, project]
        mock_db.query.return_value.filter.return_value.all.return_value = [item1, item2]
        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_bom(mock_db, 1)
        assert result is not None
        assert result.amount == Decimal("3000")
        assert result.cost_type == "MATERIAL"

    def test_uses_bom_total_amount_when_set(self):
        from app.services.cost_collection_service import CostCollectionService
        from app.models.material import BomHeader, BomItem
        mock_db = MagicMock()
        bom = self._make_bom(status="RELEASED", total_amount=Decimal("9999"))
        project = _make_project()
        item1 = MagicMock()
        item1.amount = Decimal("1000")  # items total < bom.total_amount
        mock_db.query.return_value.filter.return_value.first.side_effect = [bom, None, project]
        mock_db.query.return_value.filter.return_value.all.return_value = [item1]
        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_bom(mock_db, 1)
        # Should use bom.total_amount = 9999
        assert result.amount == Decimal("9999")

    def test_updates_existing_bom_cost(self):
        from app.services.cost_collection_service import CostCollectionService
        from app.models.material import BomHeader, BomItem
        mock_db = MagicMock()
        bom = self._make_bom(status="RELEASED")
        existing_cost = _make_cost_record(amount=Decimal("500"))
        project = _make_project(actual_cost=5000)
        item1 = MagicMock()
        item1.amount = Decimal("800")
        mock_db.query.return_value.filter.return_value.first.side_effect = [bom, existing_cost, project]
        mock_db.query.return_value.filter.return_value.all.return_value = [item1]
        result = CostCollectionService.collect_from_bom(mock_db, 1)
        assert result is existing_cost
        assert existing_cost.amount == Decimal("800")
        # project cost: 5000 - 500 + 800 = 5300
        assert project.actual_cost == pytest.approx(5300.0, abs=0.01)
