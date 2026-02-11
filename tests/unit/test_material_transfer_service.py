# -*- coding: utf-8 -*-
"""物料调拨服务测试"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.material_transfer_service import MaterialTransferService


@pytest.fixture
def db():
    return MagicMock()


class TestGetProjectMaterialStock:
    def test_from_project_material(self, db):
        pm = MagicMock(available_qty=Decimal("10"), reserved_qty=Decimal("2"), total_qty=Decimal("12"))
        db.query.return_value.filter.return_value.first.return_value = pm
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["available_qty"] == Decimal("10")
        assert result["source"] == "项目物料表"

    def test_from_inventory(self, db):
        db.query.return_value.filter.return_value.first.side_effect = [
            None,  # no project_material
            MagicMock(available_qty=Decimal("5"), reserved_qty=Decimal("0"), total_qty=Decimal("5"))
        ]
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["source"] == "库存表"

    def test_from_material_archive(self, db):
        db.query.return_value.filter.return_value.first.side_effect = [
            None, None, MagicMock(current_stock=Decimal("3"))
        ]
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["source"] == "物料档案"


class TestCheckTransferAvailable:
    def test_sufficient(self, db):
        pm = MagicMock(available_qty=Decimal("10"), reserved_qty=Decimal("0"), total_qty=Decimal("10"))
        db.query.return_value.filter.return_value.first.return_value = pm
        result = MaterialTransferService.check_transfer_available(db, 1, 1, Decimal("5"))
        assert result["is_sufficient"] is True

    def test_insufficient(self, db):
        pm = MagicMock(available_qty=Decimal("3"), reserved_qty=Decimal("0"), total_qty=Decimal("3"))
        db.query.return_value.filter.return_value.first.return_value = pm
        result = MaterialTransferService.check_transfer_available(db, 1, 1, Decimal("5"))
        assert result["is_sufficient"] is False
        assert result["shortage_qty"] == 2.0


class TestExecuteStockUpdate:
    def test_basic_transfer(self, db):
        transfer = MagicMock(
            from_project_id=1, to_project_id=2, material_id=1,
            transfer_qty=Decimal("5")
        )
        pm = MagicMock(available_qty=Decimal("10"), total_qty=Decimal("10"))
        db.query.return_value.filter.return_value.first.return_value = pm
        result = MaterialTransferService.execute_stock_update(db, transfer)
        assert "from_project" in result
        assert "to_project" in result


class TestSuggestTransferSources:
    def test_no_sources(self, db):
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None
        result = MaterialTransferService.suggest_transfer_sources(db, 1, 1, Decimal("5"))
        assert result == []

    def test_with_project_source(self, db):
        pm = MagicMock(project_id=2, available_qty=Decimal("10"))
        project = MagicMock(project_name='P2', project_code='PC2')
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [pm]
        db.query.return_value.filter.return_value.first.side_effect = [project, None]
        result = MaterialTransferService.suggest_transfer_sources(db, 1, 1, Decimal("5"))
        assert len(result) >= 1


class TestValidateTransferBeforeExecute:
    def test_valid(self, db):
        transfer = MagicMock(
            to_project_id=2, from_project_id=1, material_id=1,
            transfer_qty=Decimal("5"), status="APPROVED"
        )
        to_proj = MagicMock(is_active=True)
        from_proj = MagicMock(is_active=True)
        material = MagicMock()
        pm = MagicMock(available_qty=Decimal("10"), reserved_qty=Decimal("0"), total_qty=Decimal("10"))
        db.query.return_value.filter.return_value.first.side_effect = [to_proj, from_proj, material, pm]
        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)
        assert result["is_valid"] is True

    def test_wrong_status(self, db):
        transfer = MagicMock(
            to_project_id=2, from_project_id=None, material_id=1,
            transfer_qty=Decimal("5"), status="DRAFT"
        )
        to_proj = MagicMock(is_active=True)
        material = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [to_proj, material]
        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)
        assert result["is_valid"] is False
