# -*- coding: utf-8 -*-
"""物料调拨服务单元测试"""
import sys
import types
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

# Stub missing model modules before importing the service
_inventory_stock_mock = MagicMock()
_inventory_transaction_mock = MagicMock()
_stubs = {
    "app.models.inventory": {"InventoryStock": _inventory_stock_mock, "InventoryTransaction": _inventory_transaction_mock},
}
for mod_name, attrs in _stubs.items():
    if mod_name not in sys.modules:
        stub = types.ModuleType(mod_name)
        for k, v in attrs.items():
            setattr(stub, k, v)
        sys.modules[mod_name] = stub

import app.models.material as _mat_mod
if not hasattr(_mat_mod, "ProjectMaterial"):
    _mat_mod.ProjectMaterial = MagicMock()

from app.services.material_transfer_service import MaterialTransferService


def _make_db():
    """Create a mock db where each db.query() call returns independent chain."""
    db = MagicMock()
    # Each call to db.query() returns a new mock chain
    db.query.side_effect = lambda *a, **k: MagicMock()
    return db


def _make_db_with_query_results(results_by_call_index):
    """
    Create db mock where the i-th db.query().filter().first() returns results_by_call_index[i].
    """
    db = MagicMock()
    chains = []
    for result in results_by_call_index:
        chain = MagicMock()
        chain.filter.return_value.first.return_value = result
        # Also support filter chaining
        chain.filter.return_value.filter.return_value.first.return_value = result
        chain.filter.return_value.order_by.return_value.all.return_value = result if isinstance(result, list) else [result] if result else []
        chains.append(chain)

    db.query.side_effect = chains
    return db


class TestGetProjectMaterialStock:
    def test_from_project_material(self):
        pm = MagicMock(available_qty=Decimal("100"), reserved_qty=Decimal("10"), total_qty=Decimal("110"))
        db = _make_db_with_query_results([pm])
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["available_qty"] == Decimal("100")
        assert result["source"] == "项目物料表"

    def test_from_inventory(self):
        inv = MagicMock(available_qty=Decimal("50"), reserved_qty=Decimal("5"), total_qty=Decimal("55"))
        db = _make_db_with_query_results([None, inv])
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["available_qty"] == Decimal("50")
        assert result["source"] == "库存表"

    def test_from_material(self):
        mat = MagicMock(current_stock=Decimal("200"))
        db = _make_db_with_query_results([None, None, mat])
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["available_qty"] == Decimal("200")
        assert result["source"] == "物料档案"

    def test_nothing_found(self):
        db = _make_db_with_query_results([None, None, None])
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert result["available_qty"] == Decimal("0")
        assert result["source"] == "未设置"


class TestCheckTransferAvailable:
    def test_sufficient(self):
        db = MagicMock()
        with patch.object(MaterialTransferService, "get_project_material_stock", return_value={
            "available_qty": Decimal("100"), "source": "项目物料表"
        }):
            result = MaterialTransferService.check_transfer_available(db, 1, 1, Decimal("50"))
        assert result["is_sufficient"] is True
        assert result["shortage_qty"] == 0

    def test_insufficient(self):
        db = MagicMock()
        with patch.object(MaterialTransferService, "get_project_material_stock", return_value={
            "available_qty": Decimal("10"), "source": "项目物料表"
        }):
            result = MaterialTransferService.check_transfer_available(db, 1, 1, Decimal("50"))
        assert result["is_sufficient"] is False
        assert result["shortage_qty"] == 40.0


class TestExecuteStockUpdate:
    def test_basic(self):
        db = MagicMock()
        transfer = MagicMock(
            from_project_id=1, to_project_id=2, material_id=10,
            transfer_qty=Decimal("20")
        )
        with patch.object(MaterialTransferService, "_update_project_stock",
                          return_value={"before": 100, "after": 80, "success": True}):
            result = MaterialTransferService.execute_stock_update(db, transfer)
        assert "from_project" in result
        assert "to_project" in result

    def test_no_from_project(self):
        db = _make_db_with_query_results([MagicMock(current_stock=Decimal("100"))])
        transfer = MagicMock(
            from_project_id=None, to_project_id=2, material_id=10,
            transfer_qty=Decimal("20")
        )
        with patch.object(MaterialTransferService, "_update_project_stock",
                          return_value={"before": 0, "after": 20, "success": True}):
            result = MaterialTransferService.execute_stock_update(db, transfer)
        assert result["from_project"]["before"] == 0


class TestUpdateProjectStock:
    def test_update_project_material(self):
        pm = MagicMock(available_qty=Decimal("100"), total_qty=Decimal("100"))
        db = _make_db_with_query_results([pm])
        with patch.object(MaterialTransferService, "_record_transaction"):
            result = MaterialTransferService._update_project_stock(
                db, 1, 1, Decimal("-20"), "TRANSFER_OUT", "调出"
            )
        assert result["success"] is True
        assert result["before"] == 100.0

    def test_create_new_record_on_increase(self):
        db = _make_db_with_query_results([None, None])
        with patch("app.services.material_transfer_service.ProjectMaterial") as MockPM, \
             patch.object(MaterialTransferService, "_record_transaction"):
            MockPM.return_value = MagicMock()
            result = MaterialTransferService._update_project_stock(
                db, 1, 1, Decimal("20"), "TRANSFER_IN", "调入"
            )
        assert result["success"] is True

    def test_decrease_no_record_fails(self):
        db = _make_db_with_query_results([None, None])
        result = MaterialTransferService._update_project_stock(
            db, 1, 1, Decimal("-20"), "TRANSFER_OUT", "调出"
        )
        assert result["success"] is False
        assert "error" in result


class TestSuggestTransferSources:
    def test_with_sources(self):
        pm = MagicMock(project_id=2, material_id=1, available_qty=Decimal("50"))
        project = MagicMock(project_name="项目B", project_code="PB")
        chain1 = MagicMock()
        chain1.filter.return_value.order_by.return_value.all.return_value = [pm]
        chain2 = MagicMock()
        chain2.filter.return_value.first.return_value = project
        chain3 = MagicMock()
        chain3.filter.return_value.first.return_value = None

        db = MagicMock()
        db.query.side_effect = [chain1, chain2, chain3]
        # ProjectMaterial.available_qty > 0 fails because MagicMock doesn't support >
        # Patch ProjectMaterial in the service module with a mock that has proper column attrs
        mock_pm_cls = MagicMock()
        mock_pm_cls.available_qty.__gt__ = lambda self, other: MagicMock()
        with patch("app.services.material_transfer_service.ProjectMaterial", mock_pm_cls):
            result = MaterialTransferService.suggest_transfer_sources(db, 1, 1, Decimal("30"))
        assert len(result) >= 1
        assert result[0]["project_name"] == "项目B"

    def test_empty(self):
        chain1 = MagicMock()
        chain1.filter.return_value.order_by.return_value.all.return_value = []
        chain2 = MagicMock()
        chain2.filter.return_value.first.return_value = None

        db = MagicMock()
        db.query.side_effect = [chain1, chain2]
        mock_pm_cls = MagicMock()
        mock_pm_cls.available_qty.__gt__ = lambda self, other: MagicMock()
        with patch("app.services.material_transfer_service.ProjectMaterial", mock_pm_cls):
            result = MaterialTransferService.suggest_transfer_sources(db, 1, 1, Decimal("30"))
        assert result == []


class TestValidateTransferBeforeExecute:
    def test_valid(self):
        to_proj = MagicMock(is_active=True)
        from_proj = MagicMock(is_active=True)
        material = MagicMock()
        db = _make_db_with_query_results([to_proj, from_proj, material])
        transfer = MagicMock(
            to_project_id=2, from_project_id=1, material_id=10,
            transfer_qty=Decimal("20"), status="APPROVED"
        )
        with patch.object(MaterialTransferService, "check_transfer_available", return_value={"is_sufficient": True}):
            result = MaterialTransferService.validate_transfer_before_execute(db, transfer)
        assert result["is_valid"] is True

    def test_invalid_status(self):
        to_proj = MagicMock(is_active=True)
        material = MagicMock()
        db = _make_db_with_query_results([to_proj, material])
        transfer = MagicMock(
            to_project_id=2, from_project_id=None, material_id=10,
            transfer_qty=Decimal("20"), status="DRAFT"
        )
        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)
        assert result["is_valid"] is False
        assert any("状态不正确" in e for e in result["errors"])
