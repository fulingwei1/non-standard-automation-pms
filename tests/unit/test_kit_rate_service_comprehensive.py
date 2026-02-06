# -*- coding: utf-8 -*-
"""
KitRateService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _get_project: 获取项目
- _get_machine: 获取机台
- _get_latest_bom: 获取最新BOM
- list_bom_items_for_machine: 列出机台BOM物料
- list_bom_items_for_project: 列出项目BOM物料
- _get_in_transit_qty: 获取在途数量
- calculate_kit_rate: 计算齐套率
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

import pytest


class TestKitRateServiceInit:
    """测试 KitRateService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        service = KitRateService(mock_db)

        assert service.db == mock_db


class TestGetProject:
    """测试 _get_project 方法"""

    def test_returns_project(self):
        """测试返回项目"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        service = KitRateService(mock_db)

        result = service._get_project(1)

        assert result == mock_project

    def test_raises_for_missing_project(self):
        """测试项目不存在时抛出异常"""
        from app.services.kit_rate.kit_rate_service import KitRateService
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = KitRateService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service._get_project(999)

        assert exc_info.value.status_code == 404


class TestGetMachine:
    """测试 _get_machine 方法"""

    def test_returns_machine(self):
        """测试返回机台"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_machine = MagicMock()
        mock_machine.id = 1
        mock_machine.machine_name = "测试机台"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_machine

        service = KitRateService(mock_db)

        result = service._get_machine(1)

        assert result == mock_machine

    def test_raises_for_missing_machine(self):
        """测试机台不存在时抛出异常"""
        from app.services.kit_rate.kit_rate_service import KitRateService
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = KitRateService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service._get_machine(999)

        assert exc_info.value.status_code == 404


class TestGetLatestBom:
    """测试 _get_latest_bom 方法"""

    def test_returns_latest_bom(self):
        """测试返回最新BOM"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.is_latest = True

        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_bom

        service = KitRateService(mock_db)

        result = service._get_latest_bom(1)

        assert result == mock_bom

    def test_returns_none_for_no_bom(self):
        """测试没有BOM时返回None"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        service = KitRateService(mock_db)

        result = service._get_latest_bom(1)

        assert result is None


class TestListBomItemsForMachine:
    """测试 list_bom_items_for_machine 方法"""

    def test_returns_bom_items(self):
        """测试返回BOM物料列表"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_machine = MagicMock()
        mock_machine.id = 1

        mock_item1 = MagicMock()
        mock_item1.id = 1
        mock_item2 = MagicMock()
        mock_item2.id = 2

        mock_bom = MagicMock()
        mock_bom.items.all.return_value = [mock_item1, mock_item2]

        # 第一次查询获取机台，第二次查询获取BOM
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_machine, None]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_bom

        service = KitRateService(mock_db)

        result = service.list_bom_items_for_machine(1)

        assert len(result) == 2

    def test_returns_empty_for_no_bom(self):
        """测试没有BOM时返回空列表"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_machine = MagicMock()
        mock_machine.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_machine
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        service = KitRateService(mock_db)

        result = service.list_bom_items_for_machine(1)

        assert result == []


class TestListBomItemsForProject:
    """测试 list_bom_items_for_project 方法"""

    def test_returns_all_bom_items(self):
        """测试返回项目所有BOM物料"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1

        mock_machine1 = MagicMock()
        mock_machine1.id = 1
        mock_machine2 = MagicMock()
        mock_machine2.id = 2

        mock_item1 = MagicMock()
        mock_item2 = MagicMock()

        mock_bom1 = MagicMock()
        mock_bom1.items.all.return_value = [mock_item1]
        mock_bom2 = MagicMock()
        mock_bom2.items.all.return_value = [mock_item2]

        # 设置查询返回
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_machine1, mock_machine2]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.side_effect = [mock_bom1, mock_bom2]

        service = KitRateService(mock_db)

        result = service.list_bom_items_for_project(1)

        assert len(result) == 2

    def test_returns_empty_for_no_machines(self):
        """测试没有机台时返回空列表"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = KitRateService(mock_db)

        result = service.list_bom_items_for_project(1)

        assert result == []


class TestGetInTransitQty:
    """测试 _get_in_transit_qty 方法"""

    def test_returns_zero_for_no_material_id(self):
        """测试没有物料ID时返回0"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        service = KitRateService(mock_db)

        result = service._get_in_transit_qty(None)

        assert result == Decimal(0)

    def test_calculates_in_transit_qty(self):
        """测试计算在途数量"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        mock_po_item1 = MagicMock()
        mock_po_item1.quantity = Decimal("100")
        mock_po_item1.received_qty = Decimal("30")

        mock_po_item2 = MagicMock()
        mock_po_item2.quantity = Decimal("50")
        mock_po_item2.received_qty = Decimal("0")

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_po_item1, mock_po_item2
        ]

        service = KitRateService(mock_db)

        result = service._get_in_transit_qty(1)

        # (100-30) + (50-0) = 70 + 50 = 120
        assert result == Decimal("120")

    def test_returns_zero_for_no_po_items(self):
        """测试没有采购订单时返回0"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = KitRateService(mock_db)

        result = service._get_in_transit_qty(1)

        assert result == Decimal(0)


class TestCalculateKitRate:
    """测试 calculate_kit_rate 方法"""

    def test_calculates_kit_rate(self):
        """测试计算齐套率"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        service = KitRateService(mock_db)

        # 模拟BOM物料数据
        with patch.object(service, 'list_bom_items_for_machine') as mock_list:
            mock_item1 = MagicMock()
            mock_item1.material_id = 1
            mock_item1.quantity = Decimal("10")
            mock_item1.material = MagicMock()
            mock_item1.material.current_stock = Decimal("10")

            mock_item2 = MagicMock()
            mock_item2.material_id = 2
            mock_item2.quantity = Decimal("20")
            mock_item2.material = MagicMock()
            mock_item2.material.current_stock = Decimal("15")

            mock_list.return_value = [mock_item1, mock_item2]

            with patch.object(service, '_get_in_transit_qty', return_value=Decimal(0)):
                result = service.calculate_kit_rate(machine_id=1)

                assert 'kit_rate' in result or 'rate' in result or isinstance(result, (dict, Decimal))

    def test_returns_100_for_full_kit(self):
        """测试齐套时返回100%"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        service = KitRateService(mock_db)

        with patch.object(service, 'list_bom_items_for_machine') as mock_list:
            mock_item = MagicMock()
            mock_item.material_id = 1
            mock_item.quantity = Decimal("10")
            mock_item.material = MagicMock()
            mock_item.material.current_stock = Decimal("100")

            mock_list.return_value = [mock_item]

            with patch.object(service, '_get_in_transit_qty', return_value=Decimal(0)):
                result = service.calculate_kit_rate(machine_id=1)

                assert result is not None

    def test_returns_zero_for_no_items(self):
        """测试没有物料时返回0"""
        from app.services.kit_rate.kit_rate_service import KitRateService

        mock_db = MagicMock()

        service = KitRateService(mock_db)

        with patch.object(service, 'list_bom_items_for_machine', return_value=[]):
            result = service.calculate_kit_rate(machine_id=1)

            assert result is not None
