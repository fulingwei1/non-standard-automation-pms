# -*- coding: utf-8 -*-
"""
成本自动归集服务单元测试
覆盖: app/services/cost_collection_service.py
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


# ─── collect_from_purchase_order ──────────────────────────────────────────────

class TestCollectFromPurchaseOrder:
    def test_order_not_found_returns_none(self, mock_db):
        from app.services.cost_collection_service import CostCollectionService
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_purchase_order(mock_db, 999)
        assert result is None

    def test_no_project_id_returns_none(self, mock_db):
        """采购订单未关联项目时不创建成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_order = MagicMock()
        mock_order.project_id = None
        mock_order.total_amount = Decimal("5000")

        def first_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_order  # PurchaseOrder
            return None  # no existing cost

        call_count = [0]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_order,  # PurchaseOrder found
            None,        # no existing cost
        ]

        result = CostCollectionService.collect_from_purchase_order(mock_db, 1)
        assert result is None

    def test_creates_new_cost_record(self, mock_db):
        """正常创建新成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_order = MagicMock()
        mock_order.project_id = 10
        mock_order.order_no = "PO-001"
        mock_order.order_title = "测试采购"
        mock_order.total_amount = Decimal("10000")
        mock_order.tax_amount = Decimal("1300")
        mock_order.order_date = date(2024, 1, 10)
        mock_order.created_at = None

        mock_project = MagicMock()
        mock_project.actual_cost = 0.0

        mock_project_costs = []

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_order,     # PurchaseOrder
            None,           # no existing cost
            mock_project,   # Project
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_project_costs

        with patch("app.services.cost_collection_service.ProjectCost") as MockCost:
            mock_cost = MagicMock()
            MockCost.return_value = mock_cost
            result = CostCollectionService.collect_from_purchase_order(
                mock_db, 1, created_by=1, cost_date=date(2024, 1, 10)
            )

        mock_db.add.assert_called()

    def test_updates_existing_cost_record(self, mock_db):
        """已存在成本记录时应更新"""
        from app.services.cost_collection_service import CostCollectionService

        mock_order = MagicMock()
        mock_order.project_id = 10
        mock_order.total_amount = Decimal("12000")
        mock_order.tax_amount = Decimal("1560")
        mock_order.created_at = MagicMock()
        mock_order.created_at.date.return_value = date(2024, 1, 10)

        existing_cost = MagicMock()
        existing_cost.amount = Decimal("10000")

        mock_project = MagicMock()
        mock_project_costs = [existing_cost]

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_order,      # PurchaseOrder
            existing_cost,   # existing ProjectCost
            mock_project,    # Project
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_project_costs

        result = CostCollectionService.collect_from_purchase_order(mock_db, 1)
        assert existing_cost.amount == Decimal("12000")


# ─── collect_from_outsourcing_order ───────────────────────────────────────────

class TestCollectFromOutsourcingOrder:
    def test_order_not_found_returns_none(self, mock_db):
        from app.services.cost_collection_service import CostCollectionService
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_outsourcing_order(mock_db, 999)
        assert result is None

    def test_no_project_returns_none(self, mock_db):
        from app.services.cost_collection_service import CostCollectionService

        mock_order = MagicMock()
        mock_order.project_id = None
        mock_order.total_amount = Decimal("3000")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_order,
            None,  # no existing cost
        ]
        result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)
        assert result is None

    def test_creates_outsourcing_cost(self, mock_db):
        """正常创建外协成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_order = MagicMock()
        mock_order.project_id = 5
        mock_order.order_no = "OS-001"
        mock_order.order_title = "外协加工"
        mock_order.total_amount = Decimal("8000")
        mock_order.tax_amount = Decimal("800")
        mock_order.order_date = date(2024, 2, 1)

        mock_project = MagicMock()
        mock_project.actual_cost = 0.0

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_order,
            None,  # no existing cost
            mock_project,
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.cost_collection_service.ProjectCost") as MockCost:
            mock_cost = MagicMock()
            MockCost.return_value = mock_cost
            result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)

        mock_db.add.assert_called()


# ─── collect_from_ecn ─────────────────────────────────────────────────────────

class TestCollectFromEcn:
    def test_ecn_not_found_returns_none(self, mock_db):
        from app.services.cost_collection_service import CostCollectionService
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_ecn(mock_db, 999)
        assert result is None

    def test_ecn_no_project_returns_none(self, mock_db):
        """ECN 有成本但无项目ID时返回 None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_ecn = MagicMock()
        mock_ecn.project_id = None
        mock_ecn.cost_impact = Decimal("5000")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_ecn,
            None,  # no existing cost
        ]
        result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is None

    def test_ecn_no_cost_returns_none(self, mock_db):
        """ECN 没有变更成本时返回 None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_ecn = MagicMock()
        mock_ecn.project_id = 3
        mock_ecn.cost_impact = Decimal("0")  # zero cost => returns None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_ecn,
        ]
        result = CostCollectionService.collect_from_ecn(mock_db, 1)
        assert result is None


# ─── remove_cost_from_source ──────────────────────────────────────────────────

class TestRemoveCostFromSource:
    def test_source_not_found_returns_false(self, mock_db):
        """来源成本记录不存在时返回 False"""
        from app.services.cost_collection_service import CostCollectionService
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.remove_cost_from_source(mock_db, "PURCHASE", "PURCHASE_ORDER", 999)
        assert result is False

    def test_removes_cost_record(self, mock_db):
        """找到成本记录时删除并返回 True"""
        from app.services.cost_collection_service import CostCollectionService

        mock_cost = MagicMock()
        mock_cost.project_id = 5
        mock_cost.amount = Decimal("5000")

        mock_project = MagicMock()
        mock_project.actual_cost = 5000.0

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_cost,
            mock_project,
        ]

        result = CostCollectionService.remove_cost_from_source(
            mock_db, "PURCHASE", "PURCHASE_ORDER", 1
        )
        assert result is True
        mock_db.delete.assert_called_once_with(mock_cost)
