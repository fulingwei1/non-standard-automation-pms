# -*- coding: utf-8 -*-
"""库存管理 Facade 测试"""
from decimal import Decimal
from unittest.mock import Mock, MagicMock

import pytest

from app.models.inventory_tracking import MaterialStock, MaterialTransaction


class TestInventoryManagementFacade:
    """InventoryManagementService Facade 测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        db = Mock()
        db.query = MagicMock(return_value=Mock())
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def inventory_service(self, mock_db_session):
        """创建 InventoryManagementService 实例"""
        from app.services.inventory.inventory_management_facade import InventoryManagementService

        return InventoryManagementService(mock_db_session, tenant_id=1)

    def test_get_stock(self, inventory_service, mock_db_session):
        """测试查询库存"""
        mock_stock = Mock(spec=MaterialStock)
        mock_stock.id = 1
        mock_stock.material_id = 100
        mock_stock.quantity = Decimal("100")

        # 模拟返回
        mock_query = Mock()
        mock_query.filter = Mock(return_value=Mock(all=Mock(return_value=[mock_stock])))
        mock_db_session.query = Mock(return_value=mock_query)

        result = inventory_service.get_stock(material_id=100)

        assert len(result) == 1
        assert result[0].material_id == 100

    def test_get_available_quantity(self, inventory_service, mock_db_session):
        """测试获取可用数量"""

        mock_query = Mock()
        mock_query.filter = Mock(return_value=Mock(scalar=Mock(return_value=Decimal("500"))))
        mock_db_session.query = Mock(return_value=mock_query)

        result = inventory_service.get_available_quantity(material_id=100)

        assert result == Decimal("500")

    def test_get_total_quantity(self, inventory_service, mock_db_session):
        """测试获取总库存数量"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=Mock(scalar=Mock(return_value=Decimal("1000"))))
        mock_db_session.query = Mock(return_value=mock_query)

        result = inventory_service.get_total_quantity(material_id=100)

        assert result == Decimal("1000")

    def test_create_transaction(self, inventory_service, mock_db_session):
        """测试创建交易记录"""
        mock_transaction = Mock(spec=MaterialTransaction)
        mock_transaction.id = 1
        mock_transaction.material_id = 100

        # 模拟 query().filter().all() 返回空列表
        mock_query = Mock()
        mock_query.filter = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_db_session.query = Mock(return_value=mock_query)
        mock_db_session.add = Mock()
        mock_db_session.flush = Mock()
        mock_db_session.refresh = Mock(return_value=mock_transaction)

        result = inventory_service.create_transaction(
            material_id=100,
            transaction_type="PURCHASE_IN",
            quantity=Decimal("100")
        )

        assert result is not None
        mock_db_session.add.assert_called()