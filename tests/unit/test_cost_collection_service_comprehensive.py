# -*- coding: utf-8 -*-
"""
CostCollectionService 综合单元测试

测试覆盖:
- collect_from_purchase_order: 从采购订单归集成本
- collect_from_outsourcing_order: 从外协订单归集成本
- collect_from_ecn: 从ECN变更归集成本
- remove_cost_from_source: 删除来源成本记录
- collect_from_bom: 从BOM归集成本
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestCollectFromPurchaseOrder:
    """测试 collect_from_purchase_order 方法"""

    def test_returns_none_when_order_not_found(self):
        """测试订单不存在时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.collect_from_purchase_order(mock_db, 999)

        assert result is None

    def test_returns_none_when_no_project_id(self):
        """测试订单无项目ID时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = None

        # First query returns order, second returns None (no existing cost)
        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_order
            else:
                result.first.return_value = None
            return result

        mock_db.query.return_value.filter = filter_side_effect

        result = CostCollectionService.collect_from_purchase_order(mock_db, 1)

        assert result is None

    def test_creates_new_cost_record(self):
        """测试创建新成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 10
        mock_order.order_no = "PO001"
        mock_order.order_title = "测试采购"
        mock_order.total_amount = Decimal("5000")
        mock_order.tax_amount = Decimal("500")
        mock_order.order_date = date.today()

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 0

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_order
            elif call_count[0] == 2:
                result.first.return_value = None  # No existing cost
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        with patch('app.services.cost_collection_service.CostAlertService'):
            result = CostCollectionService.collect_from_purchase_order(mock_db, 1, created_by=100)

        mock_db.add.assert_called()
        assert result.project_id == 10
        assert result.cost_type == "MATERIAL"
        assert result.source_module == "PURCHASE"

    def test_updates_existing_cost_record(self):
        """测试更新现有成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 10
        mock_order.total_amount = Decimal("6000")
        mock_order.tax_amount = Decimal("600")
        mock_order.created_at = MagicMock()
        mock_order.created_at.date.return_value = date.today()

        mock_existing_cost = MagicMock()
        mock_existing_cost.amount = Decimal("5000")

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 5000

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_order
            elif call_count[0] == 2:
                result.first.return_value = mock_existing_cost
            elif call_count[0] == 3:
                result.first.return_value = mock_project
            else:
                result.all.return_value = [mock_existing_cost]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        result = CostCollectionService.collect_from_purchase_order(mock_db, 1)

        assert result == mock_existing_cost
        assert mock_existing_cost.amount == Decimal("6000")


class TestCollectFromOutsourcingOrder:
    """测试 collect_from_outsourcing_order 方法"""

    def test_returns_none_when_order_not_found(self):
        """测试订单不存在时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.collect_from_outsourcing_order(mock_db, 999)

        assert result is None

    def test_creates_outsourcing_cost_record(self):
        """测试创建外协成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.project_id = 10
        mock_order.machine_id = 5
        mock_order.order_no = "OS001"
        mock_order.order_title = "外协加工"
        mock_order.total_amount = Decimal("3000")
        mock_order.tax_amount = Decimal("300")
        mock_order.created_at = MagicMock()
        mock_order.created_at.date.return_value = date.today()

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 0

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_order
            elif call_count[0] == 2:
                result.first.return_value = None  # No existing cost
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        with patch('app.services.cost_collection_service.CostAlertService'):
            result = CostCollectionService.collect_from_outsourcing_order(mock_db, 1)

        assert result.cost_type == "OUTSOURCING"
        assert result.source_module == "OUTSOURCING"
        assert result.machine_id == 5


class TestCollectFromEcn:
    """测试 collect_from_ecn 方法"""

    def test_returns_none_when_ecn_not_found(self):
        """测试ECN不存在时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.collect_from_ecn(mock_db, 999)

        assert result is None

    def test_returns_none_when_no_cost_impact(self):
        """测试无成本影响时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_ecn = MagicMock()
        mock_ecn.cost_impact = Decimal("0")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

        result = CostCollectionService.collect_from_ecn(mock_db, 1)

        assert result is None

    def test_returns_none_when_negative_cost_impact(self):
        """测试负成本影响时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_ecn = MagicMock()
        mock_ecn.cost_impact = Decimal("-100")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

        result = CostCollectionService.collect_from_ecn(mock_db, 1)

        assert result is None

    def test_creates_ecn_cost_record(self):
        """测试创建ECN成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.project_id = 10
        mock_ecn.machine_id = 5
        mock_ecn.ecn_no = "ECN001"
        mock_ecn.ecn_title = "设计变更"
        mock_ecn.cost_impact = Decimal("2000")

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 0

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_ecn
            elif call_count[0] == 2:
                result.first.return_value = None  # No existing cost
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        with patch('app.services.cost_collection_service.CostAlertService'):
            result = CostCollectionService.collect_from_ecn(mock_db, 1)

        assert result.cost_type == "CHANGE"
        assert result.source_module == "ECN"
        assert result.amount == Decimal("2000")


class TestRemoveCostFromSource:
    """测试 remove_cost_from_source 方法"""

    def test_returns_false_when_cost_not_found(self):
        """测试成本记录不存在时返回False"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.remove_cost_from_source(
            mock_db, "PURCHASE", "PURCHASE_ORDER", 999
        )

        assert result is False

    def test_deletes_cost_and_updates_project(self):
        """测试删除成本并更新项目"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.project_id = 10
        mock_cost.amount = Decimal("5000")

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 10000

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_cost
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        result = CostCollectionService.remove_cost_from_source(
            mock_db, "PURCHASE", "PURCHASE_ORDER", 1
        )

        assert result is True
        mock_db.delete.assert_called_once_with(mock_cost)
        assert mock_project.actual_cost == 5000

    def test_prevents_negative_project_cost(self):
        """测试防止项目成本为负"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.project_id = 10
        mock_cost.amount = Decimal("15000")

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 10000

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_cost
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        CostCollectionService.remove_cost_from_source(
            mock_db, "PURCHASE", "PURCHASE_ORDER", 1
        )

        assert mock_project.actual_cost == 0


class TestCollectFromBom:
    """测试 collect_from_bom 方法"""

    def test_raises_error_when_bom_not_found(self):
        """测试BOM不存在时抛出错误"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="BOM不存在"):
            CostCollectionService.collect_from_bom(mock_db, 999)

    def test_raises_error_when_no_project(self):
        """测试BOM未关联项目时抛出错误"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_bom = MagicMock()
        mock_bom.project_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_bom

        with pytest.raises(ValueError, match="未关联项目"):
            CostCollectionService.collect_from_bom(mock_db, 1)

    def test_raises_error_when_not_released(self):
        """测试BOM未发布时抛出错误"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()
        mock_bom = MagicMock()
        mock_bom.project_id = 10
        mock_bom.status = "DRAFT"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_bom

        with pytest.raises(ValueError, match="已发布"):
            CostCollectionService.collect_from_bom(mock_db, 1)

    def test_creates_bom_cost_record(self):
        """测试创建BOM成本记录"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = 10
        mock_bom.machine_id = 5
        mock_bom.bom_no = "BOM001"
        mock_bom.bom_name = "测试BOM"
        mock_bom.status = "RELEASED"
        mock_bom.total_amount = None

        mock_item1 = MagicMock()
        mock_item1.amount = Decimal("1000")
        mock_item2 = MagicMock()
        mock_item2.amount = Decimal("2000")

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 0

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_bom
            elif call_count[0] == 2:
                result.first.return_value = None  # No existing cost
            elif call_count[0] == 3:
                result.all.return_value = [mock_item1, mock_item2]
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        with patch('app.services.cost_collection_service.CostAlertService'):
            result = CostCollectionService.collect_from_bom(mock_db, 1)

        assert result.cost_type == "MATERIAL"
        assert result.cost_category == "BOM"
        assert result.amount == Decimal("3000")

    def test_returns_none_when_zero_amount(self):
        """测试BOM金额为0时返回None"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = 10
        mock_bom.status = "RELEASED"
        mock_bom.total_amount = None

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_bom
            elif call_count[0] == 2:
                result.first.return_value = None  # No existing cost
            elif call_count[0] == 3:
                result.all.return_value = []  # No items
            return result

        mock_db.query.return_value.filter = filter_side_effect

        result = CostCollectionService.collect_from_bom(mock_db, 1)

        assert result is None

    def test_uses_bom_total_amount_if_available(self):
        """测试使用BOM表头总金额"""
        from app.services.cost_collection_service import CostCollectionService

        mock_db = MagicMock()

        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.project_id = 10
        mock_bom.machine_id = 5
        mock_bom.bom_no = "BOM001"
        mock_bom.bom_name = "测试BOM"
        mock_bom.status = "RELEASED"
        mock_bom.total_amount = Decimal("5000")

        mock_item = MagicMock()
        mock_item.amount = Decimal("1000")

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.actual_cost = 0

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_bom
            elif call_count[0] == 2:
                result.first.return_value = None
            elif call_count[0] == 3:
                result.all.return_value = [mock_item]
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        with patch('app.services.cost_collection_service.CostAlertService'):
            result = CostCollectionService.collect_from_bom(mock_db, 1)

        # 使用BOM表头的total_amount而非明细之和
        assert float(result.amount) == 5000.0
