# -*- coding: utf-8 -*-
"""
缺料紧急采购服务单元测试
覆盖: app/services/urgent_purchase_from_shortage_service.py
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def make_alert(
    alert_no="ALERT-001",
    target_id=1,
    target_no="MAT-001",
    target_name="测试物料",
    project_id=None,
    alert_level="level3",
    status="PENDING",
    alert_data=None,
):
    a = MagicMock()
    a.alert_no = alert_no
    a.target_id = target_id
    a.target_no = target_no
    a.target_name = target_name
    a.project_id = project_id
    a.alert_level = alert_level
    a.status = status
    a.alert_data = alert_data
    a.id = 1
    return a


# ─── get_material_supplier ────────────────────────────────────────────────────

class TestGetMaterialSupplier:
    def test_returns_preferred_supplier(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_supplier

        preferred = MagicMock()
        preferred.supplier_id = 10
        mock_db.query.return_value.filter.return_value.first.return_value = preferred

        result = get_material_supplier(mock_db, 1)
        assert result == 10

    def test_falls_back_to_default_supplier(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_supplier

        material = MagicMock()
        material.default_supplier_id = 20

        # preferred = None, material has default
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,     # no preferred
            material, # material with default_supplier_id
        ]

        result = get_material_supplier(mock_db, 1)
        assert result == 20

    def test_falls_back_to_first_active_supplier(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_supplier

        material = MagicMock()
        material.default_supplier_id = None

        first_supplier = MagicMock()
        first_supplier.supplier_id = 30

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,           # no preferred
            material,       # material without default
            first_supplier, # first active supplier
        ]

        result = get_material_supplier(mock_db, 1)
        assert result == 30

    def test_returns_none_when_no_supplier(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_supplier

        material = MagicMock()
        material.default_supplier_id = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,     # no preferred
            material, # material without default
            None,     # no active supplier
        ]

        result = get_material_supplier(mock_db, 1)
        assert result is None


# ─── get_material_price ───────────────────────────────────────────────────────

class TestGetMaterialPrice:
    def test_returns_supplier_price(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_price

        supplier_rel = MagicMock()
        supplier_rel.price = Decimal("150.00")

        mock_db.query.return_value.filter.return_value.first.return_value = supplier_rel

        result = get_material_price(mock_db, 1, supplier_id=5)
        assert result == Decimal("150.00")

    def test_falls_back_to_last_price(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_price

        material = MagicMock()
        material.last_price = Decimal("120.00")
        material.standard_price = Decimal("100.00")

        # supplier rel has no price
        supplier_rel = MagicMock()
        supplier_rel.price = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            supplier_rel,
            material,
        ]

        result = get_material_price(mock_db, 1, supplier_id=5)
        assert result == Decimal("120.00")

    def test_falls_back_to_standard_price(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_price

        material = MagicMock()
        material.last_price = None
        material.standard_price = Decimal("80.00")

        supplier_rel = MagicMock()
        supplier_rel.price = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            supplier_rel,
            material,
        ]

        result = get_material_price(mock_db, 1, supplier_id=5)
        assert result == Decimal("80.00")

    def test_returns_zero_when_no_price(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_price

        material = MagicMock()
        material.last_price = None
        material.standard_price = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,     # no supplier relation
            material, # material without prices
        ]

        result = get_material_price(mock_db, 1)
        assert result == Decimal(0)

    def test_no_supplier_id_uses_material_price(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import get_material_price

        material = MagicMock()
        material.last_price = Decimal("200.00")
        material.standard_price = Decimal("180.00")

        mock_db.query.return_value.filter.return_value.first.return_value = material

        result = get_material_price(mock_db, 1)
        assert result == Decimal("200.00")


# ─── create_urgent_purchase_request_from_alert ────────────────────────────────

class TestCreateUrgentPurchaseRequestFromAlert:
    def test_no_material_id_returns_none(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import (
            create_urgent_purchase_request_from_alert
        )
        import json
        alert = make_alert(target_id=None, alert_data=json.dumps({}))
        result = create_urgent_purchase_request_from_alert(
            mock_db, alert, current_user_id=1, generate_request_no_func=MagicMock()
        )
        assert result is None

    def test_material_not_found_returns_none(self, mock_db):
        from app.services.urgent_purchase_from_shortage_service import (
            create_urgent_purchase_request_from_alert
        )
        import json
        alert = make_alert(
            target_id=999,
            alert_data=json.dumps({"shortage_qty": "10"})
        )
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = create_urgent_purchase_request_from_alert(
            mock_db, alert, current_user_id=1, generate_request_no_func=MagicMock()
        )
        assert result is None

    def test_no_supplier_marks_pending(self, mock_db):
        """找不到供应商时更新预警状态并返回 None"""
        from app.services.urgent_purchase_from_shortage_service import (
            create_urgent_purchase_request_from_alert
        )
        import json

        alert = make_alert(
            target_id=1,
            alert_data=json.dumps({"shortage_qty": "5"})
        )

        mock_material = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_material,  # material found
            None,           # no preferred supplier
            mock_material,  # material again for default supplier check
            None,           # no active supplier
        ]

        result = create_urgent_purchase_request_from_alert(
            mock_db, alert, current_user_id=1, generate_request_no_func=MagicMock()
        )
        assert result is None
        assert alert.status == "PENDING"

    def test_creates_purchase_request(self, mock_db):
        """成功创建紧急采购申请"""
        from app.services.urgent_purchase_from_shortage_service import (
            create_urgent_purchase_request_from_alert
        )
        import json

        alert = make_alert(
            target_id=1,
            alert_data=json.dumps({"shortage_qty": "10", "required_date": "2024-02-01"})
        )

        mock_material = MagicMock()
        mock_material.unit = "个"

        preferred_supplier = MagicMock()
        preferred_supplier.supplier_id = 5
        preferred_supplier.price = Decimal("100.00")

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.request_no = "PR-2024-001"

        # material_id found, preferred_supplier, supplier price
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_material,       # Material
            preferred_supplier,  # preferred MaterialSupplier (for get_material_supplier)
            preferred_supplier,  # MaterialSupplier with price (for get_material_price)
        ]

        generate_no = MagicMock(return_value="PR-2024-001")

        with patch("app.services.urgent_purchase_from_shortage_service.PurchaseRequest") as MockPR, \
             patch("app.services.urgent_purchase_from_shortage_service.PurchaseRequestItem"):
            MockPR.return_value = mock_request
            result = create_urgent_purchase_request_from_alert(
                mock_db, alert, current_user_id=1, generate_request_no_func=generate_no
            )

        assert mock_db.add.called


# ─── auto_trigger_urgent_purchase_for_alerts ─────────────────────────────────

class TestAutoTriggerUrgentPurchase:
    def test_no_alerts_returns_zero_counts(self, mock_db):
        from unittest.mock import patch as _patch
        import sys

        # Patch the problematic import inside the function
        mock_generate = MagicMock(return_value="PR-001")
        fake_module = MagicMock()
        fake_module.generate_request_no = mock_generate

        with _patch.dict(sys.modules, {"app.api.v1.endpoints.purchase": fake_module}):
            from app.services.urgent_purchase_from_shortage_service import (
                auto_trigger_urgent_purchase_for_alerts
            )
            mock_db.query.return_value.filter.return_value.all.return_value = []
            result = auto_trigger_urgent_purchase_for_alerts(mock_db, current_user_id=1)

        assert result["checked_count"] == 0
        assert result["created_count"] == 0

    def test_skips_already_processed(self, mock_db):
        """已有采购申请的预警跳过"""
        import json
        import sys
        from unittest.mock import patch as _patch

        mock_generate = MagicMock(return_value="PR-001")
        fake_module = MagicMock()
        fake_module.generate_request_no = mock_generate

        with _patch.dict(sys.modules, {"app.api.v1.endpoints.purchase": fake_module}):
            from app.services.urgent_purchase_from_shortage_service import (
                auto_trigger_urgent_purchase_for_alerts
            )
            alert = make_alert(alert_data=json.dumps({"related_po_no": "PR-001"}))
            alert.alert_no = "ALERT-001"
            alert.target_no = "MAT-001"

            mock_db.query.return_value.filter.return_value.all.return_value = [alert]

            with _patch(
                "app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert"
            ):
                result = auto_trigger_urgent_purchase_for_alerts(mock_db, current_user_id=1)

        assert result["skipped_count"] == 1
        assert result["created_count"] == 0
