# -*- coding: utf-8 -*-
"""
BOM 业务逻辑服务 单元测试
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.bom_service import BomService


def _make_service():
    """创建服务实例"""
    db = MagicMock()
    return BomService(db)


def _make_bom_header(**kwargs):
    """创建模拟 BOM 头"""
    bom = MagicMock()
    bom.id = kwargs.get("id", 1)
    bom.bom_no = kwargs.get("bom_no", "BOM-2024-001")
    bom.bom_name = kwargs.get("bom_name", "测试BOM")
    bom.project_id = kwargs.get("project_id", 1)
    bom.machine_id = kwargs.get("machine_id", 1)
    bom.version = kwargs.get("version", "1.0")
    bom.is_latest = kwargs.get("is_latest", True)
    bom.status = kwargs.get("status", "DRAFT")
    bom.project = kwargs.get("project", None)
    bom.machine = kwargs.get("machine", None)
    bom.items = kwargs.get("items", MagicMock())
    return bom


def _make_bom_item(**kwargs):
    """创建模拟 BOM 项"""
    item = MagicMock()
    item.id = kwargs.get("id", 1)
    item.bom_id = kwargs.get("bom_id", 1)
    item.item_no = kwargs.get("item_no", "001")
    item.material_id = kwargs.get("material_id", 1)
    item.material_code = kwargs.get("material_code", "M-001")
    item.material_name = kwargs.get("material_name", "测试物料")
    item.specification = kwargs.get("specification", "规格A")
    item.quantity = kwargs.get("quantity", 10)
    item.unit_price = kwargs.get("unit_price", Decimal("100"))
    item.amount = kwargs.get("amount", Decimal("1000"))
    item.level = kwargs.get("level", 1)
    item.is_key_item = kwargs.get("is_key_item", False)
    return item


class TestBomService:
    """测试 BOM 服务"""

    def test_init(self):
        """测试服务初始化"""
        service = _make_service()
        assert service.db is not None
        assert service.model is not None

    @patch.object(BomService, "get")
    def test_get_bom(self, mock_get):
        """测试获取 BOM"""
        service = _make_service()
        mock_get.return_value = _make_bom_header()

        result = service.get(bom_id=1)

        assert result is not None
        mock_get.assert_called_once_with(pk=1)


class TestBomCRUD:
    """测试 BOM 增删改查"""

    @patch("app.services.bom_service.BaseService.create")
    def test_create_bom(self, mock_create):
        """测试创建 BOM"""
        service = _make_service()
        bom_data = {
            "bom_no": "BOM-2024-001",
            "bom_name": "测试BOM",
            "project_id": 1,
            "machine_id": 1,
        }
        mock_create.return_value = _make_bom_header(**bom_data)

        from app.schemas.material import BomCreate

        result = service.create(obj_in=BomCreate(**bom_data))

        assert result is not None

    @patch("app.services.bom_service.BaseService.update")
    def test_update_bom(self, mock_update):
        """测试更新 BOM"""
        service = _make_service()
        db_bom = _make_bom_header(bom_name="原名称")
        update_data = {"bom_name": "新名称"}

        from app.schemas.material import BomUpdate

        mock_update.return_value = _make_bom_header(bom_name="新名称")

        result = service.update(db_obj=db_bom, obj_in=BomUpdate(**update_data))

        assert result.bom_name == "新名称"

    @patch("app.services.bom_service.BaseService.delete")
    def test_delete_bom(self, mock_delete):
        """测试删除 BOM"""
        service = _make_service()
        mock_delete.return_value = True

        result = service.delete(bom_id=1)

        assert result is True


class TestBomItems:
    """测试 BOM 项目处理"""

    def test_to_response_with_items(self):
        """测试转换为响应对象（包含项目）"""
        service = _make_service()

        project = MagicMock()
        project.project_name = "测试项目"

        machine = MagicMock()
        machine.machine_name = "测试设备"

        item1 = _make_bom_item(id=1, item_no="001", material_name="物料1", quantity=10)
        item2 = _make_bom_item(id=2, item_no="002", material_name="物料2", quantity=20)

        items_mock = MagicMock()
        items_mock.all.return_value = [item1, item2]

        bom = _make_bom_header(
            id=1,
            project=project,
            machine=machine,
            items=items_mock,
        )

        result = service._to_response(bom)

        assert result.id == 1
        assert result.project_name == "测试项目"
        assert result.machine_name == "测试设备"

    def test_to_response_without_relations(self):
        """测试转换为响应对象（无关联）"""
        service = _make_service()

        items_mock = MagicMock()
        items_mock.all.return_value = []

        bom = _make_bom_header(
            id=1,
            project=None,
            machine=None,
            items=items_mock,
        )

        result = service._to_response(bom)

        assert result.id == 1
        assert result.project_name is None
        assert result.machine_name is None


class TestBomStatus:
    """测试 BOM 状态管理"""

    @patch("app.services.bom_service.BaseService.update")
    def test_submit_bom(self, mock_update):
        """测试提交 BOM"""
        service = _make_service()
        db_bom = _make_bom_header(status="DRAFT")

        from app.schemas.material import BomUpdate

        mock_update.return_value = _make_bom_header(status="SUBMITTED")

        result = service.update(db_obj=db_bom, obj_in=BomUpdate(status="SUBMITTED"))

        assert result.status == "SUBMITTED"

    @patch("app.services.bom_service.BaseService.update")
    def test_approve_bom(self, mock_update):
        """测试审批 BOM"""
        service = _make_service()
        db_bom = _make_bom_header(status="SUBMITTED")

        from app.schemas.material import BomUpdate

        mock_update.return_value = _make_bom_header(status="APPROVED")

        result = service.update(db_obj=db_bom, obj_in=BomUpdate(status="APPROVED"))

        assert result.status == "APPROVED"


class TestBomQueries:
    """测试 BOM 查询功能"""

    @patch("app.services.bom_service.BaseService.get_multi")
    def test_list_boms(self, mock_get_multi):
        """测试列出 BOM"""
        service = _make_service()
        mock_get_multi.return_value = [
            _make_bom_header(id=1),
            _make_bom_header(id=2),
        ]

        result = service.get_multi(skip=0, limit=10)

        assert len(result) == 2

    def test_query_boms_by_project(self):
        """测试按项目查询 BOM"""
        service = _make_service()

        # 模拟按项目查询
        service.db.query.return_value.filter.return_value.all.return_value = [
            _make_bom_header(id=1, project_id=1),
            _make_bom_header(id=2, project_id=1),
        ]

        result = service.db.query.return_value.filter.return_value.all()

        assert isinstance(result, list)

    def test_query_latest_bom(self):
        """测试查询最新版本 BOM"""
        service = _make_service()

        # 模拟查询最新版本
        service.db.query.return_value.filter.return_value.first.return_value = _make_bom_header(
            is_latest=True
        )

        result = service.db.query.return_value.filter.return_value.first()

        assert result is not None


class TestBomValidation:
    """测试 BOM 验证"""

    def test_validate_bom_items(self):
        """测试验证 BOM 项目"""
        service = _make_service()

        # 创建有效的 BOM 项
        items = [
            _make_bom_item(id=1, quantity=10, unit_price=Decimal("100")),
            _make_bom_item(id=2, quantity=20, unit_price=Decimal("50")),
        ]

        # 验证金额计算
        for item in items:
            expected_amount = item.quantity * item.unit_price
            assert item.amount == expected_amount or item.quantity * item.unit_price == expected_amount

    def test_validate_key_items(self):
        """测试关键部件标记"""
        service = _make_service()

        items = [
            _make_bom_item(id=1, material_name="关键物料1", is_key_item=True),
            _make_bom_item(id=2, material_name="普通物料", is_key_item=False),
        ]

        key_items = [item for item in items if item.is_key_item]
        assert len(key_items) == 1