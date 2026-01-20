# -*- coding: utf-8 -*-
"""
齐套率计算工具函数单元测试
Covers: app/api/v1/endpoints/kit_rate/utils.py
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch


from app.api.v1.endpoints.kit_rate.utils import calculate_kit_rate


class TestCalculateKitRate:
    """Test suite for calculate_kit_rate function."""

    def test_empty_bom_items(self, db_session):
        """空 BOM 列表应返回完成状态。"""
        result = calculate_kit_rate(db_session, [])

        assert result["total_items"] == 0
        assert result["fulfilled_items"] == 0
        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "complete"

    def test_all_items_fulfilled_by_quantity(self, db_session):
        """所有物料齐套（按数量计算）应返回 100% 齐套率。"""
        # 创建 mock BOM items
        mock_material = MagicMock()
        mock_material.current_stock = 100

        mock_item = MagicMock()
        mock_item.material = mock_material
        mock_item.material_id = 1
        mock_item.quantity = 50
        mock_item.received_qty = 0
        mock_item.unit_price = Decimal("10.00")

        # Mock 采购订单查询返回空
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.filter.return_value.all.return_value = []

            result = calculate_kit_rate(db_session, [mock_item], calculate_by="quantity")

        assert result["fulfilled_items"] == 1
        assert result["shortage_items"] == 0
        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"

    def test_partial_fulfillment(self, db_session):
        """部分齐套应返回正确的齐套率和状态。"""
        # 创建两个 mock BOM items
        mock_material1 = MagicMock()
        mock_material1.current_stock = 100  # 足够

        mock_material2 = MagicMock()
        mock_material2.current_stock = 0  # 不足

        mock_item1 = MagicMock()
        mock_item1.material = mock_material1
        mock_item1.material_id = 1
        mock_item1.quantity = 50
        mock_item1.received_qty = 0
        mock_item1.unit_price = Decimal("10.00")

        mock_item2 = MagicMock()
        mock_item2.material = mock_material2
        mock_item2.material_id = 2
        mock_item2.quantity = 50
        mock_item2.received_qty = 0
        mock_item2.unit_price = Decimal("10.00")

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.filter.return_value.all.return_value = []

            result = calculate_kit_rate(db_session, [mock_item1, mock_item2])

        assert result["total_items"] == 2
        assert result["fulfilled_items"] == 1
        assert result["shortage_items"] == 1
        assert result["kit_rate"] == 50.0
        assert result["kit_status"] == "shortage"

    def test_kit_status_thresholds(self, db_session):
        """验证齐套状态阈值：>=100 complete, >=80 partial, <80 shortage。"""
        # 通过不同的 fulfilled/total 比例测试状态
        mock_material = MagicMock()
        mock_material.current_stock = 100

        # 创建 10 个 items
        items = []
        for i in range(10):
            mock_item = MagicMock()
            mock_item.material = mock_material if i < 8 else MagicMock(current_stock=0)
            mock_item.material_id = i + 1
            mock_item.quantity = 10
            mock_item.received_qty = 0
            mock_item.unit_price = Decimal("1.00")
            items.append(mock_item)

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.filter.return_value.all.return_value = []

            result = calculate_kit_rate(db_session, items)

        # 80% 齐套应该是 partial 状态
        assert result["kit_status"] == "partial"

    def test_calculate_by_amount(self, db_session):
        """按金额计算齐套率。"""
        mock_material = MagicMock()
        mock_material.current_stock = 100

        mock_item = MagicMock()
        mock_item.material = mock_material
        mock_item.material_id = 1
        mock_item.quantity = 50
        mock_item.received_qty = 0
        mock_item.unit_price = Decimal("20.00")

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.filter.return_value.all.return_value = []

            result = calculate_kit_rate(db_session, [mock_item], calculate_by="amount")

        assert result["calculate_by"] == "amount"
        assert result["total_amount"] == 1000.0  # 50 * 20
        assert result["fulfilled_amount"] == 1000.0

    def test_in_transit_items(self, db_session):
        """测试在途物料的计算。"""
        mock_material = MagicMock()
        mock_material.current_stock = 0  # 库存为0

        mock_item = MagicMock()
        mock_item.material = mock_material
        mock_item.material_id = 1
        mock_item.quantity = 50
        mock_item.received_qty = 0
        mock_item.unit_price = Decimal("10.00")

        # 创建在途采购订单
        mock_po_item = MagicMock()
        mock_po_item.quantity = 60
        mock_po_item.received_qty = 10  # 在途 50

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_po_item]

            result = calculate_kit_rate(db_session, [mock_item])

        # 在途数量 50 >= 需求 50，应该齐套
        assert result["fulfilled_items"] == 1
        assert result["kit_rate"] == 100.0
