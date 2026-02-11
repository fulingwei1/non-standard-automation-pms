# -*- coding: utf-8 -*-
"""成本自动归集服务测试"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.cost_collection_service import CostCollectionService


@pytest.fixture
def db():
    return MagicMock()


class TestCollectFromPurchaseOrder:
    def test_order_not_found(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_purchase_order(db, 1)
        assert result is None

    def test_no_project_id(self, db):
        order = MagicMock(project_id=None, total_amount=Decimal("100"))
        db.query.return_value.filter.return_value.first.side_effect = [order, None]
        result = CostCollectionService.collect_from_purchase_order(db, 1)
        assert result is None

    @patch('app.services.cost_collection_service.CostAlertService')
    def test_new_cost_created(self, mock_alert, db):
        order = MagicMock(
            project_id=1, total_amount=Decimal("500"), tax_amount=Decimal("50"),
            order_no="PO001", order_title="Test PO", order_date=date.today(),
            created_at=MagicMock(date=MagicMock(return_value=date.today()))
        )
        project = MagicMock(actual_cost=0)
        # first call: find order, second: find existing cost (None), third: find project
        db.query.return_value.filter.return_value.first.side_effect = [order, None, project]
        result = CostCollectionService.collect_from_purchase_order(db, 1, created_by=1)
        db.add.assert_called()

    def test_existing_cost_updated(self, db):
        order = MagicMock(
            project_id=1, total_amount=Decimal("500"), tax_amount=Decimal("50"),
            created_at=MagicMock(date=MagicMock(return_value=date.today()))
        )
        existing_cost = MagicMock(amount=Decimal("400"))
        project = MagicMock(actual_cost=400)
        db.query.return_value.filter.return_value.first.side_effect = [order, existing_cost, project]
        db.query.return_value.filter.return_value.all.return_value = [existing_cost]
        result = CostCollectionService.collect_from_purchase_order(db, 1)
        assert result == existing_cost


class TestCollectFromOutsourcingOrder:
    def test_order_not_found(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_outsourcing_order(db, 1)
        assert result is None

    def test_no_project(self, db):
        order = MagicMock(project_id=None)
        db.query.return_value.filter.return_value.first.side_effect = [order, None]
        result = CostCollectionService.collect_from_outsourcing_order(db, 1)
        assert result is None


class TestCollectFromEcn:
    def test_ecn_not_found(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.collect_from_ecn(db, 1)
        assert result is None

    def test_zero_cost_impact(self, db):
        ecn = MagicMock(cost_impact=Decimal("0"))
        db.query.return_value.filter.return_value.first.return_value = ecn
        result = CostCollectionService.collect_from_ecn(db, 1)
        assert result is None

    def test_no_project(self, db):
        ecn = MagicMock(cost_impact=Decimal("100"), project_id=None)
        db.query.return_value.filter.return_value.first.side_effect = [ecn, None]
        result = CostCollectionService.collect_from_ecn(db, 1)
        assert result is None


class TestRemoveCostFromSource:
    def test_no_cost_found(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = CostCollectionService.remove_cost_from_source(db, "PURCHASE", "PO", 1)
        assert result is False

    def test_cost_removed(self, db):
        cost = MagicMock(project_id=1, amount=Decimal("100"))
        project = MagicMock(actual_cost=100)
        db.query.return_value.filter.return_value.first.side_effect = [cost, project]
        result = CostCollectionService.remove_cost_from_source(db, "PURCHASE", "PO", 1)
        assert result is True
        db.delete.assert_called_with(cost)


class TestCollectFromBom:
    def test_bom_not_found(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="BOM不存在"):
            CostCollectionService.collect_from_bom(db, 1)

    def test_bom_no_project(self, db):
        bom = MagicMock(project_id=None, status="RELEASED")
        db.query.return_value.filter.return_value.first.return_value = bom
        with pytest.raises(ValueError, match="BOM未关联项目"):
            CostCollectionService.collect_from_bom(db, 1)

    def test_bom_not_released(self, db):
        bom = MagicMock(project_id=1, status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = bom
        with pytest.raises(ValueError, match="已发布"):
            CostCollectionService.collect_from_bom(db, 1)
