# -*- coding: utf-8 -*-
"""
KitRateService 单元测试

测试范围：
- 套件齐套率计算
- 项目/机台物料状态查询
- 仪表盘统计
- 趋势分析
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.kit_rate.kit_rate_service import KitRateService


class MockMaterial:
    """Mock Material model"""
    def __init__(self, current_stock=0):
        self.current_stock = current_stock


class MockBomItem:
    """Mock BomItem model"""
    def __init__(
        self,
        id=1,
        item_no="001",
        material_id=1,
        material_code="MAT001",
        material_name="测试物料",
        specification="规格A",
        unit="个",
        quantity=10,
        unit_price=100,
        received_qty=0,
        is_key_item=False,
        required_date=None,
        material=None,
    ):
        self.id = id
        self.item_no = item_no
        self.material_id = material_id
        self.material_code = material_code
        self.material_name = material_name
        self.specification = specification
        self.unit = unit
        self.quantity = quantity
        self.unit_price = unit_price
        self.received_qty = received_qty
        self.is_key_item = is_key_item
        self.required_date = required_date
        self.material = material or MockMaterial()


class MockBomHeader:
    """Mock BomHeader model"""
    def __init__(self, id=1, bom_no="BOM001", bom_name="测试BOM", items=None):
        self.id = id
        self.bom_no = bom_no
        self.bom_name = bom_name
        self._items = items or []

    @property
    def items(self):
        mock = MagicMock()
        mock.all.return_value = self._items
        return mock


class MockMachine:
    """Mock Machine model"""
    def __init__(self, id=1, machine_no="MC001", machine_name="测试机台", project_id=1):
        self.id = id
        self.machine_no = machine_no
        self.machine_name = machine_name
        self.project_id = project_id


class MockProject:
    """Mock Project model"""
    def __init__(
        self,
        id=1,
        project_code="PJ001",
        project_name="测试项目",
        is_active=True,
        planned_end_date=None,
    ):
        self.id = id
        self.project_code = project_code
        self.project_name = project_name
        self.is_active = is_active
        self.planned_end_date = planned_end_date


@pytest.mark.unit
class TestKitRateServiceInit:
    """测试服务初始化"""

    def test_init(self):
        mock_db = MagicMock()
        service = KitRateService(mock_db)
        assert service.db == mock_db


@pytest.mark.unit
class TestGetProject:
    """测试获取项目"""

    def test_get_project_found(self):
        mock_db = MagicMock()
        mock_project = MockProject()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)
        result = service._get_project(1)

        assert result == mock_project

    def test_get_project_not_found(self):
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service._get_project(999)

        assert exc_info.value.status_code == 404
        assert "项目不存在" in exc_info.value.detail


@pytest.mark.unit
class TestGetMachine:
    """测试获取机台"""

    def test_get_machine_found(self):
        mock_db = MagicMock()
        mock_machine = MockMachine()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_machine
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)
        result = service._get_machine(1)

        assert result == mock_machine

    def test_get_machine_not_found(self):
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service._get_machine(999)

        assert exc_info.value.status_code == 404
        assert "机台不存在" in exc_info.value.detail


@pytest.mark.unit
class TestCalculateKitRate:
    """测试齐套率计算"""

    def test_calculate_kit_rate_empty_items(self):
        mock_db = MagicMock()
        service = KitRateService(mock_db)

        result = service.calculate_kit_rate([], "quantity")

        assert result["total_items"] == 0
        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "complete"

    def test_calculate_kit_rate_all_fulfilled(self):
        mock_db = MagicMock()

        # Mock _get_in_transit_qty to return 0
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        # Create items where available >= required
        material = MockMaterial(current_stock=20)
        items = [
            MockBomItem(id=1, quantity=10, received_qty=0, material=material),
            MockBomItem(id=2, quantity=5, received_qty=0, material=material),
        ]

        result = service.calculate_kit_rate(items, "quantity")

        assert result["total_items"] == 2
        assert result["fulfilled_items"] == 2
        assert result["shortage_items"] == 0
        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"

    def test_calculate_kit_rate_partial(self):
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        # 5 items: 4 fulfilled (80%), 1 shortage
        material_good = MockMaterial(current_stock=100)
        material_bad = MockMaterial(current_stock=0)
        items = [
            MockBomItem(id=1, quantity=10, material=material_good),
            MockBomItem(id=2, quantity=10, material=material_good),
            MockBomItem(id=3, quantity=10, material=material_good),
            MockBomItem(id=4, quantity=10, material=material_good),
            MockBomItem(id=5, quantity=10, material=material_bad),  # shortage
        ]

        result = service.calculate_kit_rate(items, "quantity")

        assert result["total_items"] == 5
        assert result["fulfilled_items"] == 4
        assert result["shortage_items"] == 1
        assert result["kit_rate"] == 80.0
        assert result["kit_status"] == "partial"

    def test_calculate_kit_rate_shortage(self):
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        # All items have shortage
        material_bad = MockMaterial(current_stock=0)
        items = [
            MockBomItem(id=1, quantity=10, material=material_bad),
            MockBomItem(id=2, quantity=10, material=material_bad),
        ]

        result = service.calculate_kit_rate(items, "quantity")

        assert result["total_items"] == 2
        assert result["fulfilled_items"] == 0
        assert result["shortage_items"] == 2
        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "shortage"

    def test_calculate_kit_rate_by_amount(self):
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        material_good = MockMaterial(current_stock=100)
        material_bad = MockMaterial(current_stock=0)

        # Item 1: qty=10, price=100, amount=1000, fulfilled
        # Item 2: qty=10, price=200, amount=2000, shortage
        # Total amount = 3000, fulfilled amount = 1000
        # Kit rate = 1000/3000 * 100 = 33.33%
        items = [
            MockBomItem(id=1, quantity=10, unit_price=100, material=material_good),
            MockBomItem(id=2, quantity=10, unit_price=200, material=material_bad),
        ]

        result = service.calculate_kit_rate(items, "amount")

        assert result["calculate_by"] == "amount"
        assert result["total_amount"] == 3000.0
        assert result["fulfilled_amount"] == 1000.0
        assert result["kit_rate"] == pytest.approx(33.33, rel=0.01)

    def test_calculate_kit_rate_invalid_calculate_by(self):
        mock_db = MagicMock()
        service = KitRateService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service.calculate_kit_rate([], "invalid")

        assert exc_info.value.status_code == 400
        assert "calculate_by" in exc_info.value.detail


@pytest.mark.unit
class TestGetMachineKitRate:
    """测试机台齐套率查询"""

    def test_get_machine_kit_rate_success(self):
        mock_db = MagicMock()
        mock_machine = MockMachine()
        material = MockMaterial(current_stock=100)
        mock_bom = MockBomHeader(items=[MockBomItem(quantity=10, material=material)])

        # Setup mock queries
        call_count = [0]

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if call_count[0] == 0:  # Machine query
                mock_q.first.return_value = mock_machine
            elif call_count[0] == 1:  # BomHeader query
                mock_q.first.return_value = mock_bom
            else:  # PurchaseOrderItem query
                mock_q.all.return_value = []
            call_count[0] += 1
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)
        result = service.get_machine_kit_rate(1, "quantity")

        assert result["machine_id"] == 1
        assert result["machine_no"] == "MC001"
        assert result["bom_id"] == 1
        assert "kit_rate" in result

    def test_get_machine_kit_rate_no_bom(self):
        mock_db = MagicMock()
        mock_machine = MockMachine()

        call_count = [0]

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if call_count[0] == 0:  # Machine query
                mock_q.first.return_value = mock_machine
            else:  # BomHeader query
                mock_q.first.return_value = None
            call_count[0] += 1
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_machine_kit_rate(1, "quantity")

        assert exc_info.value.status_code == 404
        assert "BOM" in exc_info.value.detail


@pytest.mark.unit
class TestGetProjectKitRate:
    """测试项目齐套率查询"""

    def test_get_project_kit_rate_success(self):
        mock_db = MagicMock()
        mock_project = MockProject()
        mock_machines = [MockMachine(id=1), MockMachine(id=2)]
        material = MockMaterial(current_stock=100)
        mock_bom = MockBomHeader(items=[MockBomItem(quantity=10, material=material)])

        call_count = [0]

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            model_name = str(model)
            if "Project" in model_name and call_count[0] == 0:
                mock_q.first.return_value = mock_project
            elif "Machine" in model_name:
                mock_q.all.return_value = mock_machines
            elif "BomHeader" in model_name:
                mock_q.first.return_value = mock_bom
            else:
                mock_q.all.return_value = []
                mock_q.first.return_value = None

            call_count[0] += 1
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)
        result = service.get_project_kit_rate(1, "quantity")

        assert result["project_id"] == 1
        assert result["project_code"] == "PJ001"
        assert "kit_rate" in result
        assert "machines" in result


@pytest.mark.unit
class TestGetInTransitQty:
    """测试在途数量计算"""

    def test_get_in_transit_qty_no_material(self):
        mock_db = MagicMock()
        service = KitRateService(mock_db)

        result = service._get_in_transit_qty(None)

        assert result == Decimal(0)

    def test_get_in_transit_qty_with_orders(self):
        mock_db = MagicMock()

        # Mock PO items: ordered 100, received 30 = in transit 70
        mock_po_item = MagicMock()
        mock_po_item.quantity = 100
        mock_po_item.received_qty = 30

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_po_item]
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)
        result = service._get_in_transit_qty(1)

        assert result == Decimal(70)

    def test_get_in_transit_qty_no_orders(self):
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)
        result = service._get_in_transit_qty(1)

        assert result == Decimal(0)


@pytest.mark.unit
class TestListBomItems:
    """测试BOM项目列表查询"""

    def test_list_bom_items_for_machine_no_bom(self):
        mock_db = MagicMock()
        mock_machine = MockMachine()

        call_count = [0]

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if call_count[0] == 0:
                mock_q.first.return_value = mock_machine
            else:
                mock_q.first.return_value = None
            call_count[0] += 1
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)
        result = service.list_bom_items_for_machine(1)

        assert result == []

    def test_list_bom_items_for_project_no_machines(self):
        mock_db = MagicMock()
        mock_project = MockProject()

        call_count = [0]

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if call_count[0] == 0:
                mock_q.first.return_value = mock_project
            else:
                mock_q.all.return_value = []
            call_count[0] += 1
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)
        result = service.list_bom_items_for_project(1)

        assert result == []


@pytest.mark.unit
class TestGetMachineMaterialStatus:
    """测试机台物料状态查询"""

    def test_get_machine_material_status_success(self):
        mock_db = MagicMock()
        mock_machine = MockMachine()
        material = MockMaterial(current_stock=50)
        mock_bom_item = MockBomItem(
            id=1,
            item_no="001",
            quantity=100,
            received_qty=20,
            material=material,
            is_key_item=True,
            required_date=date(2025, 6, 1),
        )
        mock_bom = MockBomHeader(items=[mock_bom_item])

        call_count = [0]

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if call_count[0] == 0:
                mock_q.first.return_value = mock_machine
            elif call_count[0] == 1:
                mock_q.first.return_value = mock_bom
            else:
                mock_q.all.return_value = []
            call_count[0] += 1
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)
        result = service.get_machine_material_status(1)

        assert result["machine_id"] == 1
        assert result["bom_id"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["required_qty"] == 100
        assert item["current_stock"] == 50
        assert item["received_qty"] == 20
        assert item["available_qty"] == 70  # 50 + 20
        assert item["is_key_item"] is True


@pytest.mark.unit
class TestGetDashboard:
    """测试仪表盘查询"""

    def test_get_dashboard_with_project_ids(self):
        mock_db = MagicMock()
        mock_project = MockProject()

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.all.return_value = [mock_project]
            mock_q.first.return_value = mock_project
            return mock_q

        mock_db.query.side_effect = mock_query_side_effect

        service = KitRateService(mock_db)

        # Mock get_project_kit_rate
        with patch.object(
            service,
            "get_project_kit_rate",
            return_value={
                "kit_rate": 100.0,
                "kit_status": "complete",
                "total_items": 10,
                "fulfilled_items": 10,
                "shortage_items": 0,
                "in_transit_items": 0,
            },
        ):
            result = service.get_dashboard(project_ids=[1])

        assert result["summary"]["total_projects"] == 1
        assert result["summary"]["complete_projects"] == 1
        assert len(result["projects"]) == 1


@pytest.mark.unit
class TestGetTrend:
    """测试趋势分析"""

    def test_get_trend_no_snapshots(self):
        mock_db = MagicMock()

        # Mock inspector for table check
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True

        mock_bind = MagicMock()
        mock_db.get_bind.return_value = mock_bind

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = KitRateService(mock_db)

        with patch(
            "app.services.kit_rate.kit_rate_service.inspect",
            return_value=mock_inspector,
        ):
            result = service.get_trend(
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
                group_by="day",
            )

        assert result["trend_data"] == []
        assert result["summary"]["data_points"] == 0
        assert "暂无快照数据" in result.get("note", "")

    def test_get_trend_table_not_exists(self):
        mock_db = MagicMock()

        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = False

        mock_bind = MagicMock()
        mock_db.get_bind.return_value = mock_bind

        service = KitRateService(mock_db)

        with patch(
            "app.services.kit_rate.kit_rate_service.inspect",
            return_value=mock_inspector,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.get_trend(
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 1, 31),
                    group_by="day",
                )

        assert exc_info.value.status_code == 500
        assert "快照表" in exc_info.value.detail
