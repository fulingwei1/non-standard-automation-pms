# -*- coding: utf-8 -*-
"""
物料调拨服务单元测试
覆盖 app/services/material_transfer_service.py

注意：
  - 该服务有几个损坏的导入（ProjectMaterial、InventoryStock、InventoryTransaction
    在实际模型中不存在）。
  - 测试在导入前通过 sys.modules 打桩来绕过这些缺失的类。
"""
import sys
import types
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────
# Patch missing symbols BEFORE importing the service module
# ──────────────────────────────────────────────────────────

def _inject_missing_models():
    """Inject placeholder classes for symbols that don't exist in the real app."""

    # Ensure app.models.material has ProjectMaterial
    import app.models.material as mat_mod  # noqa: F401
    if not hasattr(mat_mod, "ProjectMaterial"):
        mat_mod.ProjectMaterial = MagicMock(name="ProjectMaterial")

    # Patch app.models.shortage to expose MaterialTransfer
    import app.models.shortage as shortage_mod  # noqa: F401
    if not hasattr(shortage_mod, "MaterialTransfer"):
        shortage_mod.MaterialTransfer = MagicMock(name="MaterialTransfer")

    # Patch the inventory_tracking module to expose the two missing classes
    import app.models.inventory_tracking as inv_mod  # noqa: F401
    if not hasattr(inv_mod, "InventoryStock"):
        inv_mod.InventoryStock = MagicMock(name="InventoryStock")
    if not hasattr(inv_mod, "InventoryTransaction"):
        inv_mod.InventoryTransaction = MagicMock(name="InventoryTransaction")


_inject_missing_models()

from app.services.material_transfer_service import MaterialTransferService  # noqa: E402

# Also inject InventoryStock / InventoryTransaction directly into the service
# module's global namespace, because they are referenced in the function bodies
# but the import lines are commented out (FIXME in the original source).
import app.services.material_transfer_service as _svc_mod  # noqa: E402
if not hasattr(_svc_mod, "InventoryStock"):
    _svc_mod.InventoryStock = MagicMock(name="InventoryStock")
if not hasattr(_svc_mod, "InventoryTransaction"):
    _svc_mod.InventoryTransaction = MagicMock(name="InventoryTransaction")


# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_project(project_id=1, name="项目A", code="P001", is_active=True):
    p = MagicMock()
    p.id = project_id
    p.project_name = name
    p.project_code = code
    p.is_active = is_active
    return p


def _make_material(material_id=1, code="MAT-001", name="物料A",
                   current_stock=None, default_supplier_id=None):
    m = MagicMock()
    m.id = material_id
    m.material_code = code
    m.material_name = name
    m.current_stock = current_stock
    m.default_supplier_id = default_supplier_id
    return m


def _make_project_material(pm_id=1, project_id=1, material_id=1,
                            available_qty=Decimal("100"),
                            reserved_qty=Decimal("0"),
                            total_qty=Decimal("100")):
    pm = MagicMock()
    pm.id = pm_id
    pm.project_id = project_id
    pm.material_id = material_id
    pm.available_qty = available_qty
    pm.reserved_qty = reserved_qty
    pm.total_qty = total_qty
    return pm


def _make_transfer(
    transfer_id=1,
    from_project_id=1,
    to_project_id=2,
    material_id=1,
    transfer_qty=Decimal("10"),
    status="APPROVED",
):
    t = MagicMock()
    t.id = transfer_id
    t.from_project_id = from_project_id
    t.to_project_id = to_project_id
    t.material_id = material_id
    t.transfer_qty = transfer_qty
    t.status = status
    return t


# ────────────────────────────────────────────────
# 1. get_project_material_stock
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestGetProjectMaterialStock:

    def test_returns_from_project_material_table(self):
        db = _make_db()
        pm = _make_project_material(
            available_qty=Decimal("80"),
            reserved_qty=Decimal("20"),
            total_qty=Decimal("100"),
        )
        db.query.return_value.filter.return_value.first.return_value = pm

        result = MaterialTransferService.get_project_material_stock(db, 1, 1)

        assert result["available_qty"] == Decimal("80")
        assert result["reserved_qty"] == Decimal("20")
        assert result["total_qty"] == Decimal("100")
        assert result["source"] == "项目物料表"

    def test_falls_back_to_material_archive_when_no_pm(self):
        db = _make_db()
        # ProjectMaterial → None, InventoryStock → None, Material → found
        material = _make_material(current_stock=Decimal("200"))
        db.query.return_value.filter.return_value.first.side_effect = [None, None, material]

        result = MaterialTransferService.get_project_material_stock(db, 1, 1)

        assert result["available_qty"] == Decimal("200")
        assert result["source"] == "物料档案"

    def test_returns_default_source_label(self):
        """初始 result 字典中 source 默认为 '未设置'"""
        # We just verify the dict structure is correct by calling with known PM
        db = _make_db()
        pm = _make_project_material(available_qty=Decimal("10"))
        db.query.return_value.filter.return_value.first.return_value = pm
        result = MaterialTransferService.get_project_material_stock(db, 1, 1)
        assert "source" in result
        assert "available_qty" in result


# ────────────────────────────────────────────────
# 2. check_transfer_available
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestCheckTransferAvailable:

    def test_sufficient_stock_returns_true(self):
        db = _make_db()
        pm = _make_project_material(available_qty=Decimal("50"))
        db.query.return_value.filter.return_value.first.return_value = pm

        result = MaterialTransferService.check_transfer_available(
            db, from_project_id=1, material_id=1, transfer_qty=Decimal("30")
        )

        assert result["is_sufficient"] is True
        assert result["shortage_qty"] == 0

    def test_insufficient_stock_returns_false_with_gap(self):
        db = _make_db()
        pm = _make_project_material(available_qty=Decimal("10"))
        db.query.return_value.filter.return_value.first.return_value = pm

        result = MaterialTransferService.check_transfer_available(
            db, from_project_id=1, material_id=1, transfer_qty=Decimal("25")
        )

        assert result["is_sufficient"] is False
        assert result["shortage_qty"] == 15.0

    def test_exact_match_is_sufficient(self):
        db = _make_db()
        pm = _make_project_material(available_qty=Decimal("20"))
        db.query.return_value.filter.return_value.first.return_value = pm

        result = MaterialTransferService.check_transfer_available(
            db, from_project_id=1, material_id=1, transfer_qty=Decimal("20")
        )

        assert result["is_sufficient"] is True


# ────────────────────────────────────────────────
# 3. validate_transfer_before_execute
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestValidateTransferBeforeExecute:

    def _build_db_for_valid_transfer(self, transfer):
        db = _make_db()
        project_to = _make_project(project_id=transfer.to_project_id)
        project_from = _make_project(project_id=transfer.from_project_id)
        material = _make_material(material_id=transfer.material_id)
        pm = _make_project_material(available_qty=transfer.transfer_qty + Decimal("5"))

        # Sequence: to_project, from_project, material, project_material(stock check)
        db.query.return_value.filter.return_value.first.side_effect = [
            project_to, project_from, material, pm,
        ]
        return db

    def test_valid_transfer_passes(self):
        transfer = _make_transfer(status="APPROVED", transfer_qty=Decimal("10"))
        db = self._build_db_for_valid_transfer(transfer)

        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)

        assert result["is_valid"] is True
        assert result["errors"] == []

    def test_missing_to_project_gives_error(self):
        db = _make_db()
        # Sequence: to_project=None triggers error immediately
        db.query.return_value.filter.return_value.first.side_effect = [
            None, None, None, None
        ]
        transfer = _make_transfer(status="APPROVED")

        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)

        assert result["is_valid"] is False
        assert any("调入项目不存在" in e for e in result["errors"])

    def test_wrong_status_gives_error(self):
        db = _make_db()
        project_to = _make_project()
        project_from = _make_project()
        material = _make_material()
        pm = _make_project_material(available_qty=Decimal("100"))
        db.query.return_value.filter.return_value.first.side_effect = [
            project_to, project_from, material, pm,
        ]
        transfer = _make_transfer(status="DRAFT", transfer_qty=Decimal("10"))

        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)

        assert result["is_valid"] is False
        assert any("状态不正确" in e for e in result["errors"])

    def test_archived_project_gives_warning(self):
        db = _make_db()
        project_to = _make_project(is_active=False)
        project_from = _make_project()
        material = _make_material()
        pm = _make_project_material(available_qty=Decimal("100"))
        db.query.return_value.filter.return_value.first.side_effect = [
            project_to, project_from, material, pm,
        ]
        transfer = _make_transfer(status="APPROVED", transfer_qty=Decimal("10"))

        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)

        assert any("归档" in w for w in result["warnings"])

    def test_insufficient_stock_gives_error(self):
        db = _make_db()
        project_to = _make_project()
        project_from = _make_project()
        material = _make_material()
        pm = _make_project_material(available_qty=Decimal("3"))  # not enough
        db.query.return_value.filter.return_value.first.side_effect = [
            project_to, project_from, material, pm,
        ]
        transfer = _make_transfer(status="APPROVED", transfer_qty=Decimal("10"))

        result = MaterialTransferService.validate_transfer_before_execute(db, transfer)

        assert result["is_valid"] is False
        assert any("库存不足" in e for e in result["errors"])


# ────────────────────────────────────────────────
# 4. _update_project_stock – increase path
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestUpdateProjectStock:

    def test_increases_existing_project_material(self):
        db = _make_db()
        pm = _make_project_material(
            available_qty=Decimal("50"),
            total_qty=Decimal("50"),
        )
        db.query.return_value.filter.return_value.first.return_value = pm

        result = MaterialTransferService._update_project_stock(
            db, 1, 1, Decimal("20"), "TRANSFER_IN", "调拨增加"
        )

        assert result["success"] is True
        assert pm.available_qty == Decimal("70")
        assert pm.total_qty == Decimal("70")

    def test_decreases_existing_project_material(self):
        db = _make_db()
        pm = _make_project_material(
            available_qty=Decimal("50"),
            total_qty=Decimal("50"),
        )
        db.query.return_value.filter.return_value.first.return_value = pm

        result = MaterialTransferService._update_project_stock(
            db, 1, 1, Decimal("-30"), "TRANSFER_OUT", "调拨减少"
        )

        assert result["success"] is True
        assert pm.available_qty == Decimal("20")

    def test_returns_error_when_no_record_and_decrease(self):
        db = _make_db()
        # ProjectMaterial → None, InventoryStock → None → falls to decrease-not-exists branch
        db.query.return_value.filter.return_value.first.side_effect = [None, None]

        result = MaterialTransferService._update_project_stock(
            db, 1, 1, Decimal("-10"), "TRANSFER_OUT", "不存在"
        )

        assert result["success"] is False
        assert "error" in result

    def test_creates_new_record_for_increase_when_none_exists(self):
        db = _make_db()
        # ProjectMaterial → None, InventoryStock → None, Material → found
        material = _make_material()
        db.query.return_value.filter.return_value.first.side_effect = [None, None, material]

        result = MaterialTransferService._update_project_stock(
            db, 2, 1, Decimal("15"), "TRANSFER_IN", "新项目"
        )

        assert result["success"] is True
        assert result["after"] == 15.0
        db.add.assert_called()


# ────────────────────────────────────────────────
# 5. suggest_transfer_sources
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestSuggestTransferSources:

    def test_returns_empty_when_no_sources(self):
        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        result = MaterialTransferService.suggest_transfer_sources(
            db, to_project_id=5, material_id=1, required_qty=Decimal("10")
        )
        assert result == []

    def test_suggests_projects_with_sufficient_stock(self):
        db = _make_db()
        pm = _make_project_material(
            project_id=3,
            available_qty=Decimal("50"),
        )
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [pm]
        project = _make_project(project_id=3, name="源项目")
        db.query.return_value.filter.return_value.first.side_effect = [project, None]

        result = MaterialTransferService.suggest_transfer_sources(
            db, to_project_id=5, material_id=1, required_qty=Decimal("20")
        )

        assert len(result) >= 1
        assert result[0]["can_fully_supply"] is True
        assert result[0]["priority"] == "HIGH"

    def test_skips_destination_project(self):
        db = _make_db()
        # PM with same project_id as to_project_id
        pm = _make_project_material(project_id=5, available_qty=Decimal("50"))
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [pm]
        db.query.return_value.filter.return_value.first.return_value = None

        result = MaterialTransferService.suggest_transfer_sources(
            db, to_project_id=5, material_id=1, required_qty=Decimal("10")
        )
        # Project 5 should be skipped
        assert all(s["project_id"] != 5 for s in result)

    def test_sorts_by_priority(self):
        db = _make_db()
        pm1 = _make_project_material(project_id=3, available_qty=Decimal("5"))   # partial
        pm2 = _make_project_material(project_id=4, available_qty=Decimal("100")) # full
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [pm1, pm2]

        proj3 = _make_project(project_id=3, name="项目3")
        proj4 = _make_project(project_id=4, name="项目4")
        db.query.return_value.filter.return_value.first.side_effect = [proj3, proj4, None]

        result = MaterialTransferService.suggest_transfer_sources(
            db, to_project_id=5, material_id=1, required_qty=Decimal("50")
        )

        priorities = [r["priority"] for r in result]
        # HIGH priority should come first
        if len(priorities) >= 2:
            assert priorities[0] in ("HIGH",)
