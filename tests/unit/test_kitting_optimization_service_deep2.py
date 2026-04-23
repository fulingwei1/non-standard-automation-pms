# -*- coding: utf-8 -*-
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.material import BomItem, Material, MaterialCategory, MaterialShortage, MaterialSupplier
from app.models.inventory_tracking import MaterialStock, MaterialTransaction
from app.models.kitting_optimization import ExpediteRecord, MaterialAlternative
from app.models.purchase import GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem
from app.models.vendor import Vendor
from app.services.kitting_optimization_service import KittingOptimizationService


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


class TestKittingOptimizationServiceDeep2:
    def test_calculate_match_score_covers_exact_contains_and_token_overlap(self):
        service = KittingOptimizationService(MagicMock())

        original = _ns(
            category_id=1,
            specification="M3/10-SS",
            brand="ABB",
            unit="PCS",
            current_stock=0,
            last_price=10,
            standard_price=10,
        )

        exact = _ns(
            category_id=1,
            specification="M3/10-SS",
            brand="ABB",
            unit="PCS",
            current_stock=5,
            last_price=12,
            standard_price=12,
        )
        contained = _ns(
            category_id=1,
            specification="M3/10-SS EXTRA",
            brand="ABB",
            unit="PCS",
            current_stock=0,
            last_price=20,
            standard_price=20,
        )
        token_overlap = _ns(
            category_id=1,
            specification="M3-10 AL",
            brand="OTHER",
            unit="PCS",
            current_stock=0,
            last_price=0,
            standard_price=0,
        )

        assert service._calculate_match_score(original, exact) == 100
        assert service._calculate_match_score(original, contained) == 65
        assert service._calculate_match_score(original, token_overlap) == 40

    def test_get_safety_stock_alerts_returns_sorted_alerts_and_summary(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        critical = _ns(
            id=1,
            material_code="MAT-CRIT",
            material_name="关键料",
            specification="S1",
            category_id=10,
            is_key_material=True,
            current_stock=10,
            safety_stock=100,
            lead_time_days=5,
            min_order_qty=12,
            is_active=True,
        )
        warning = _ns(
            id=2,
            material_code="MAT-WARN",
            material_name="预警料",
            specification="S2",
            category_id=10,
            is_key_material=False,
            current_stock=40,
            safety_stock=100,
            lead_time_days=10,
            min_order_qty=5,
            is_active=True,
        )
        sufficient = _ns(
            id=3,
            material_code="MAT-OK",
            material_name="充足料",
            specification="S3",
            category_id=None,
            is_key_material=False,
            current_stock=120,
            safety_stock=100,
            lead_time_days=7,
            min_order_qty=1,
            is_active=True,
        )

        materials_query = MagicMock()
        materials_query.filter.return_value = materials_query
        materials_query.all.return_value = [critical, warning, sufficient]

        category_query = MagicMock()
        category_query.get.return_value = _ns(category_name="电子料")

        consumption_values = iter([90, 900])
        shortage_counts = iter([4, 1])

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                return materials_query
            if entity is MaterialCategory:
                return category_query
            if entity is MaterialShortage:
                shortage_query = MagicMock()
                shortage_query.filter.return_value.count.return_value = next(shortage_counts)
                return shortage_query

            scalar_query = MagicMock()
            scalar_query.filter.return_value.scalar.return_value = next(consumption_values)
            return scalar_query

        db.query.side_effect = query_side_effect

        result = service.get_safety_stock_alerts()

        assert result["total"] == 2
        assert result["critical_count"] == 1
        assert result["warning_count"] == 1
        assert result["summary"]["total_materials_monitored"] == 3
        assert result["summary"]["high_frequency_shortage_count"] == 1

        first, second = result["alerts"]
        assert first["material_code"] == "MAT-CRIT"
        assert first["alert_level"] == "CRITICAL"
        assert first["suggested_reorder_qty"] == 96
        assert first["category_name"] == "电子料"
        assert first["is_high_frequency_shortage"] is True

        assert second["material_code"] == "MAT-WARN"
        assert second["alert_level"] == "WARNING"
        assert second["suggested_reorder_qty"] == 160
        assert second["days_of_supply"] == 4.0

    def test_sync_project_kitting_rate_handles_empty_bom(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        project = _ns(project_code="P-EMPTY", kitting_rate=0)

        project_query = MagicMock()
        project_query.get.return_value = project
        bom_query = MagicMock()
        bom_query.join.return_value.filter.return_value.all.return_value = []

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_query
            if entity is BomItem:
                return bom_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        result = service.sync_project_kitting_rate(99)

        assert result == {
            "project_id": 99,
            "project_code": "P-EMPTY",
            "old_rate": 0.0,
            "new_rate": 0,
            "changed": False,
            "shortage_count": 0,
        }

    def test_sync_project_kitting_rate_updates_low_completion_project(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        project = _ns(
            id=1,
            project_code="P-LOW",
            kitting_rate=90,
            shortage_items_count=None,
            material_status=None,
        )
        bom_items = [
            _ns(quantity=10, received_qty=10, material_id=1),
            _ns(quantity=8, received_qty=2, material_id=2),
            _ns(quantity=0, received_qty=0, material_id=3),
        ]

        project_query = MagicMock()
        project_query.get.return_value = project
        bom_query = MagicMock()
        bom_query.join.return_value.filter.return_value.all.return_value = bom_items

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_query
            if entity is BomItem:
                return bom_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        result = service.sync_project_kitting_rate(1)

        assert result["new_rate"] == 33.3
        assert result["fulfilled_items"] == 1
        assert result["shortage_count"] == 1
        assert result["changed"] is True
        assert result["change_delta"] == -56.7
        assert project.kitting_rate == 33.3
        assert project.shortage_items_count == 1
        assert project.material_status == "缺料"

    def test_sync_project_kitting_rate_handles_missing_project(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        project_query = MagicMock()
        project_query.get.return_value = None
        db.query.side_effect = lambda entity, *args, **kwargs: project_query

        assert service.sync_project_kitting_rate(404) == {"project_id": 404, "error": "项目不存在"}

    def test_sync_project_kitting_rate_sets_full_partial_and_purchasing_status(self):
        cases = [
            (
                "齐套",
                100.0,
                [
                    _ns(quantity=5, received_qty=5, material_id=1),
                    _ns(quantity=6, received_qty=6, material_id=2),
                ],
            ),
            (
                "部分到货",
                80.0,
                [
                    _ns(quantity=5, received_qty=5, material_id=1),
                    _ns(quantity=6, received_qty=6, material_id=2),
                    _ns(quantity=8, received_qty=8, material_id=3),
                    _ns(quantity=10, received_qty=2, material_id=4),
                    _ns(quantity=4, received_qty=4, material_id=5),
                ],
            ),
            (
                "采购中",
                0.0,
                [
                    _ns(quantity=0, received_qty=0, material_id=1),
                ],
            ),
        ]

        for expected_status, expected_rate, bom_items in cases:
            db = MagicMock()
            service = KittingOptimizationService(db)
            project = _ns(
                id=1,
                project_code=f"P-{expected_status}",
                kitting_rate=0,
                shortage_items_count=None,
                material_status=None,
            )
            project_query = MagicMock()
            project_query.get.return_value = project
            bom_query = MagicMock()
            bom_query.join.return_value.filter.return_value.all.return_value = bom_items

            def query_side_effect(entity, *args, **kwargs):
                if getattr(entity, "__name__", "") == "Project":
                    return project_query
                if entity is BomItem:
                    return bom_query
                raise AssertionError(f"unexpected query entity: {entity}")

            db.query.side_effect = query_side_effect

            result = service.sync_project_kitting_rate(1)

            assert result["new_rate"] == expected_rate
            assert project.material_status == expected_status

    def test_get_expedite_stats_aggregates_counts_response_days_and_suppliers(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        base_query = MagicMock()
        base_query.filter.return_value = base_query
        base_query.count.return_value = 6
        delivered = [
            _ns(is_on_time=True),
            _ns(is_on_time=False),
            _ns(is_on_time=True),
        ]
        responded = [
            _ns(created_at=date(2026, 4, 1), response_at=date(2026, 4, 3)),
            _ns(created_at=date(2026, 4, 1), response_at=date(2026, 4, 2)),
        ]
        delivered_query = MagicMock()
        delivered_query.all.return_value = delivered
        responded_query = MagicMock()
        responded_query.all.return_value = responded

        urgency_queries = [
            MagicMock(count=MagicMock(return_value=1)),
            MagicMock(count=MagicMock(return_value=2)),
            MagicMock(count=MagicMock(return_value=1)),
            MagicMock(count=MagicMock(return_value=0)),
        ]
        base_query.filter.side_effect = [
            MagicMock(count=MagicMock(return_value=2)),
            delivered_query,
            responded_query,
            *urgency_queries,
        ]

        supplier_query = MagicMock()
        supplier_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (101, 3),
            (202, 1),
        ]
        vendor_query = MagicMock()
        vendor_query.get.side_effect = [
            _ns(supplier_name="供应商A"),
            None,
        ]

        def query_side_effect(entity, *args, **kwargs):
            if entity is ExpediteRecord:
                return base_query
            if entity is Vendor:
                return vendor_query
            return supplier_query

        db.query.side_effect = query_side_effect

        result = service.get_expedite_stats()

        assert result == {
            "total_expedited": 6,
            "resolved_count": 2,
            "on_time_count": 2,
            "on_time_rate": 66.7,
            "avg_response_days": 1.5,
            "by_urgency": {"CRITICAL": 1, "HIGH": 2, "NORMAL": 1, "LOW": 0},
            "by_supplier": [
                {"supplier_id": 101, "supplier_name": "供应商A", "expedite_count": 3},
                {"supplier_id": 202, "supplier_name": "未知", "expedite_count": 1},
            ],
        }

    def test_auto_adjust_project_priority_respects_protection_and_promotes_ready_projects(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        projects = [
            _ns(id=1, project_code="P1", project_name="低齐套", kitting_rate=60, priority="HIGH", contract_amount=0),
            _ns(id=2, project_code="P2", project_name="受保护", kitting_rate=50, priority="NORMAL", contract_amount=2000000),
            _ns(id=3, project_code="P3", project_name="高齐套", kitting_rate=98, priority="LOW", contract_amount=0),
            _ns(id=4, project_code="P4", project_name="紧急项目", kitting_rate=30, priority="URGENT", contract_amount=0),
        ]

        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = projects
        db.query.side_effect = lambda entity, *args, **kwargs: project_query

        result = service.auto_adjust_project_priority()

        assert result["total_adjusted"] == 2
        assert result["protected_count"] == 2
        assert [(item["project_code"], item["new_priority"]) for item in result["adjustments"]] == [
            ("P1", "NORMAL"),
            ("P3", "NORMAL"),
        ]
        assert projects[0].priority == "NORMAL"
        assert projects[1].priority == "NORMAL"
        assert projects[2].priority == "NORMAL"
        assert projects[3].priority == "URGENT"
        db.commit.assert_called_once()

    def test_forecast_material_delay_identifies_critical_items_and_project_risk(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        project = _ns(
            id=1,
            project_code="P-FC",
            project_name="预测项目",
            planned_end_date=today,
        )
        bom_items = [
            _ns(
                material_id=1,
                quantity=10,
                received_qty=0,
                required_date=today,
                material_code="MAT-1",
                material_name="关键缺料",
                is_key_item=True,
            ),
            _ns(
                material_id=2,
                quantity=8,
                received_qty=0,
                required_date=today,
                material_code="MAT-2",
                material_name="普通缺料",
                is_key_item=False,
            ),
        ]
        po_items_list = iter([
            [_ns(order_id=101, quantity=5, received_qty=0)],
            [_ns(order_id=202, quantity=8, received_qty=0)],
        ])
        purchase_orders = {
            101: _ns(
                promised_date=today.fromordinal(today.toordinal() + 20),
                required_date=today.fromordinal(today.toordinal() + 20),
            ),
            202: _ns(
                promised_date=today.fromordinal(today.toordinal() + 3),
                required_date=today.fromordinal(today.toordinal() + 3),
            ),
        }
        materials = {
            1: _ns(lead_time_days=25),
            2: _ns(lead_time_days=7),
        }
        alt_counts = iter([2, 0])

        project_query = MagicMock()
        project_query.get.return_value = project
        bom_query = MagicMock()
        bom_query.join.return_value.filter.return_value.all.return_value = bom_items
        po_item_query = MagicMock()
        po_item_query.join.return_value.filter.return_value.all.side_effect = lambda: next(po_items_list)
        po_query = MagicMock()
        po_query.get.side_effect = lambda order_id: purchase_orders[order_id]
        material_query = MagicMock()
        material_query.get.side_effect = lambda material_id: materials[material_id]

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_query
            if entity is BomItem:
                return bom_query
            if entity is PurchaseOrderItem:
                return po_item_query
            if entity is PurchaseOrder:
                return po_query
            if entity is Material:
                return material_query
            count_query = MagicMock()
            count_query.filter.return_value.scalar.return_value = next(alt_counts)
            return count_query

        db.query.side_effect = query_side_effect

        result = service.forecast_material_delay(1)

        assert result["project_code"] == "P-FC"
        assert result["max_delay_days"] == 25
        assert result["predicted_end_date"] == str(today.fromordinal(today.toordinal() + 25))
        assert result["critical_material_count"] == 2
        assert result["risk_level"] == "HIGH"
        assert result["overall_suggestions"] == [
            "中度延期风险，建议启动缺料应急方案",
            "1项关键物料缺料，需优先处理",
        ]
        assert [item["material_id"] for item in result["critical_materials"]] == [1, 2]
        assert result["critical_materials"][0]["suggestions"] == [
            "有2种替代料可用，建议评估替换",
            "有在途订单，建议催货加急",
            "延期较长，建议调整项目计划",
        ]
        assert result["critical_materials"][1]["delay_days"] == 3

    def test_forecast_material_delay_returns_low_risk_when_no_item_is_delayed(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        project = _ns(
            id=2,
            project_code="P-SAFE",
            project_name="安全项目",
            planned_end_date=today,
        )
        bom_items = [
            _ns(
                material_id=9,
                quantity=5,
                received_qty=0,
                required_date=today.fromordinal(today.toordinal() + 10),
                material_code="MAT-9",
                material_name="准时料",
                is_key_item=False,
            )
        ]

        project_query = MagicMock()
        project_query.get.return_value = project
        bom_query = MagicMock()
        bom_query.join.return_value.filter.return_value.all.return_value = bom_items
        po_item_query = MagicMock()
        po_item_query.join.return_value.filter.return_value.all.return_value = [
            _ns(order_id=301, quantity=5, received_qty=0)
        ]
        po_query = MagicMock()
        po_query.get.return_value = _ns(
            promised_date=today.fromordinal(today.toordinal() + 5),
            required_date=today.fromordinal(today.toordinal() + 6),
        )
        material_query = MagicMock()
        material_query.get.return_value = _ns(lead_time_days=30)

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_query
            if entity is BomItem:
                return bom_query
            if entity is PurchaseOrderItem:
                return po_item_query
            if entity is PurchaseOrder:
                return po_query
            if entity is Material:
                return material_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        result = service.forecast_material_delay(2)

        assert result["critical_material_count"] == 0
        assert result["critical_materials"] == []
        assert result["max_delay_days"] == 0
        assert result["overall_suggestions"] == ["当前无缺料延期风险"]
        assert result["risk_level"] == "LOW"
        assert result["predicted_end_date"] == str(today)

    def test_forecast_material_delay_handles_missing_project(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        project_query = MagicMock()
        project_query.get.return_value = None
        db.query.side_effect = lambda entity, *args, **kwargs: project_query

        assert service.forecast_material_delay(404) == {"error": "项目不存在"}

    def test_forecast_material_delay_uses_fallback_arrival_and_default_suggestion_for_light_risk(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        project = _ns(
            id=3,
            project_code="P-LIGHT",
            project_name="轻风险项目",
            planned_end_date=today,
        )
        bom_items = [
            _ns(
                material_id=11,
                quantity=0,
                received_qty=0,
                required_date=today,
                material_code="MAT-SKIP",
                material_name="跳过料",
                is_key_item=False,
            ),
            _ns(
                material_id=12,
                quantity=5,
                received_qty=0,
                required_date=today,
                material_code="MAT-LIGHT",
                material_name="轻风险料",
                is_key_item=False,
            ),
        ]
        po_items_list = iter([
            [_ns(order_id=401, quantity=8, received_qty=0)],
        ])

        project_query = MagicMock()
        project_query.get.return_value = project
        bom_query = MagicMock()
        bom_query.join.return_value.filter.return_value.all.return_value = bom_items
        po_item_query = MagicMock()
        po_item_query.join.return_value.filter.return_value.all.side_effect = lambda: next(po_items_list)
        po_query = MagicMock()
        po_query.get.return_value = _ns(promised_date=None, required_date=None)
        material_query = MagicMock()
        material_query.get.return_value = _ns(lead_time_days=5)
        alt_query = MagicMock()
        alt_query.filter.return_value.scalar.return_value = 0

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_query
            if entity is BomItem:
                return bom_query
            if entity is PurchaseOrderItem:
                return po_item_query
            if entity is PurchaseOrder:
                return po_query
            if entity is Material:
                return material_query
            return alt_query

        db.query.side_effect = query_side_effect

        result = service.forecast_material_delay(3)

        assert result["max_delay_days"] == 5
        assert result["risk_level"] == "MEDIUM"
        assert result["overall_suggestions"] == ["轻微延期风险，建议加强催货跟踪"]
        assert result["critical_material_count"] == 1
        assert result["critical_materials"][0]["estimated_arrival"] == str(today.fromordinal(today.toordinal() + 5))
        assert result["critical_materials"][0]["suggestions"] == ["建议立即下单采购并加急"]

    def test_forecast_material_delay_returns_critical_risk_for_severe_delay(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        project = _ns(
            id=4,
            project_code="P-CRIT",
            project_name="严重延期项目",
            planned_end_date=today,
        )
        bom_items = [
            _ns(
                material_id=21,
                quantity=10,
                received_qty=0,
                required_date=today,
                material_code="MAT-CRIT",
                material_name="严重延期料",
                is_key_item=False,
            )
        ]

        project_query = MagicMock()
        project_query.get.return_value = project
        bom_query = MagicMock()
        bom_query.join.return_value.filter.return_value.all.return_value = bom_items
        po_item_query = MagicMock()
        po_item_query.join.return_value.filter.return_value.all.return_value = []
        po_query = MagicMock()
        material_query = MagicMock()
        material_query.get.return_value = _ns(lead_time_days=45)
        alt_query = MagicMock()
        alt_query.filter.return_value.scalar.return_value = 0

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_query
            if entity is BomItem:
                return bom_query
            if entity is PurchaseOrderItem:
                return po_item_query
            if entity is PurchaseOrder:
                return po_query
            if entity is Material:
                return material_query
            return alt_query

        db.query.side_effect = query_side_effect

        result = service.forecast_material_delay(4)

        assert result["max_delay_days"] == 45
        assert result["risk_level"] == "CRITICAL"
        assert result["overall_suggestions"] == ["严重延期风险，建议调整项目计划并升级处理"]

    def test_detect_high_risk_shortages_covers_key_deadline_ratio_and_missing_material(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        shortages = [
            _ns(id=1, material_id=11, required_date=today.fromordinal(today.toordinal() + 30), required_qty=100, shortage_qty=10),
            _ns(id=2, material_id=22, required_date=today.fromordinal(today.toordinal() + 3), required_qty=100, shortage_qty=10),
            _ns(id=3, material_id=33, required_date=today.fromordinal(today.toordinal() + 30), required_qty=10, shortage_qty=8),
            _ns(id=4, material_id=44, required_date=today.fromordinal(today.toordinal() + 30), required_qty=100, shortage_qty=10),
        ]
        materials = {
            11: _ns(is_key_material=True),
            22: _ns(is_key_material=False),
            33: _ns(is_key_material=False),
            44: None,
        }

        shortage_query = MagicMock()
        shortage_query.filter.return_value = shortage_query
        shortage_query.all.return_value = shortages
        material_query = MagicMock()
        material_query.get.side_effect = lambda material_id: materials[material_id]

        def query_side_effect(entity, *args, **kwargs):
            if entity is MaterialShortage:
                return shortage_query
            if entity is Material:
                return material_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        result = service.detect_high_risk_shortages(project_id=99)

        assert [item.id for item in result] == [1, 2, 3]
        assert shortage_query.filter.call_count >= 2

    def test_build_expedite_record_uses_purchase_order_or_preferred_supplier(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        po_query = MagicMock()
        po_query.get.return_value = _ns(supplier_id=77, promised_date=date.today(), project_id=9)
        supplier_query = MagicMock()
        supplier_query.filter.return_value.order_by.return_value.first.return_value = _ns(supplier_id=88)

        def query_side_effect(entity, *args, **kwargs):
            if entity is PurchaseOrder:
                return po_query
            if entity is MaterialSupplier:
                return supplier_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        from_po = service._build_expedite_record(
            material=_ns(id=1, material_code="M1", material_name="物料1", default_supplier_id=None),
            shortage_id=1,
            purchase_order_id=1001,
            urgency_level="HIGH",
            notify_methods=["email"],
            remark="po",
            user_id=7,
        )
        from_supplier = service._build_expedite_record(
            material=_ns(id=2, material_code="M2", material_name="物料2", default_supplier_id=None),
            shortage_id=None,
            purchase_order_id=None,
            urgency_level="NORMAL",
            notify_methods=["email", "wechat"],
            remark="supplier",
            user_id=8,
            expedite_type="AUTO",
        )

        assert from_po.supplier_id == 77
        assert from_po.original_promised_date == date.today()
        assert from_po.project_id == 9
        assert from_supplier.supplier_id == 88
        assert from_supplier.notify_method == "MULTI"
        assert from_supplier.expedite_type == "AUTO"

    def test_create_expedite_records_batches_manual_and_auto_targets(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        manual_material = _ns(id=1, material_code="M1", material_name="手动物料")
        auto_material = _ns(id=2, material_code="M2", material_name="自动物料")
        auto_shortages = [
            _ns(id=21, material_id=21, shortage_qty=5, required_date=today, project_id=7),
            _ns(id=22, material_id=22, shortage_qty=9, required_date=today, project_id=8),
        ]

        material_query = MagicMock()
        material_query.get.side_effect = lambda material_id: {1: manual_material, 21: None, 22: auto_material}[material_id]
        recent_query = MagicMock()
        recent_query.filter.return_value.first.side_effect = [object(), None]

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                return material_query
            if entity is ExpediteRecord:
                return recent_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect
        service._build_expedite_record = MagicMock(side_effect=[
            _ns(material_code="M1", material_name="手动物料", urgency_level="NORMAL", shortage_qty=None, required_date=None, original_promised_date=None),
            _ns(material_code="M2", material_name="自动物料", urgency_level="HIGH", shortage_qty=9, required_date=today, original_promised_date=None),
        ])

        records = service.create_expedite_records(
            targets=[{"material_id": 1, "shortage_id": 5, "remark": "manual"}],
            notify_methods=["email"],
            auto_high_risk=auto_shortages,
            user_id=3,
        )

        assert len(records) == 2
        assert records[0].notify_status == "PENDING"
        assert "催货通知" in records[0].notify_content
        assert records[1].notify_status == "PENDING"
        assert "自动物料" in records[1].notify_content
        assert db.add.call_count == 2
        db.flush.assert_called_once()
        db.commit.assert_called_once()

    def test_get_supplier_delivery_analysis_builds_risk_levels_and_sorting(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        supplier_stats_query = MagicMock()
        supplier_stats_query.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (10, 2),
            (20, 3),
            (30, 4),
            (40, 1),
        ]

        vendor_query = MagicMock()
        vendor_query.get.side_effect = lambda supplier_id: {
            10: _ns(supplier_name="供应商A"),
            20: _ns(supplier_name="供应商B"),
            30: _ns(supplier_name="供应商C"),
            40: None,
        }[supplier_id]

        po_item_query = MagicMock()
        po_item_query.join.return_value.filter.return_value.all.side_effect = [
            [
                _ns(id=1001, required_date=date(2026, 4, 10)),
                _ns(id=1002, required_date=date(2026, 4, 10)),
            ],
            [
                _ns(id=2001, required_date=date(2026, 4, 10)),
                _ns(id=2002, required_date=date(2026, 4, 10)),
                _ns(id=2003, required_date=date(2026, 4, 10)),
            ],
            [
                _ns(id=3001, required_date=date(2026, 4, 10)),
                _ns(id=3002, required_date=date(2026, 4, 10)),
                _ns(id=3003, required_date=date(2026, 4, 10)),
                _ns(id=3004, required_date=date(2026, 4, 10)),
            ],
        ]

        receipt_query = MagicMock()
        receipt_query.join.return_value.filter.return_value.first.side_effect = [
            _ns(receipt=_ns(receipt_date=date(2026, 4, 10))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 15))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 10))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 10))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 12))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 9))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 10))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 8))),
            _ns(receipt=_ns(receipt_date=date(2026, 4, 10))),
        ]

        def query_side_effect(entity, *args, **kwargs):
            if entity is PurchaseOrder.supplier_id:
                return supplier_stats_query
            if entity is Vendor:
                return vendor_query
            if entity is PurchaseOrderItem:
                return po_item_query
            if entity is GoodsReceiptItem:
                return receipt_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        result = service._get_supplier_delivery_analysis()

        assert [item["supplier_id"] for item in result] == [10, 20, 30]
        assert result[0]["risk_level"] == "HIGH"
        assert result[0]["on_time_rate"] == 50.0
        assert result[0]["avg_delay_days"] == 5.0
        assert result[0]["max_delay_days"] == 5
        assert result[1]["risk_level"] == "MEDIUM"
        assert result[1]["on_time_rate"] == 66.7
        assert result[2]["risk_level"] == "LOW"
        assert result[2]["on_time_rate"] == 100.0

    def test_get_pre_purchase_suggestions_filters_and_orders_by_stock(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()
        materials = [
            _ns(id=1, material_code="M-URG", material_name="急件料", lead_time_days=20, current_stock=5, safety_stock=10, is_active=True),
            _ns(id=2, material_code="M-NOR", material_name="常规料", lead_time_days=15, current_stock=40, safety_stock=5, is_active=True),
            _ns(id=3, material_code="M-ZERO", material_name="无消耗", lead_time_days=18, current_stock=10, safety_stock=0, is_active=True),
            _ns(id=4, material_code="M-SAFE", material_name="库存足", lead_time_days=25, current_stock=100, safety_stock=10, is_active=True),
        ]

        materials_query = MagicMock()
        materials_query.filter.return_value.all.return_value = materials
        consumption_query = MagicMock()
        consumption_query.filter.return_value.scalar.side_effect = [90, 180, 0, 90]

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                return materials_query
            return consumption_query

        db.query.side_effect = query_side_effect

        result = service._get_pre_purchase_suggestions()

        assert [item["material_id"] for item in result] == [1, 2]
        assert result[0] == {
            "material_id": 1,
            "material_code": "M-URG",
            "material_name": "急件料",
            "lead_time_days": 20,
            "avg_monthly_usage": 30.0,
            "current_stock": 5.0,
            "reason": "采购周期20天，当前库存仅覆盖5.0天（已不足采购周期，急需下单）",
            "suggested_qty": 65.0,
            "suggested_order_date": today,
        }
        assert result[1]["material_id"] == 2
        assert result[1]["suggested_qty"] == 85.0
        assert result[1]["suggested_order_date"] == today.fromordinal(today.toordinal() + 5)

    def test_build_alternative_response_includes_stock_supplier_and_price_diff(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        original = _ns(id=1, last_price=100, standard_price=90)
        alt_material = _ns(
            id=2,
            material_code="ALT-2",
            material_name="替代料",
            specification="Spec-B",
            brand="ABB",
            unit="PCS",
            last_price=120,
            standard_price=110,
            lead_time_days=12,
        )
        alt_record = _ns(
            id=9,
            match_score=88,
            match_reason="人工验证",
            is_verified=True,
            ecn_no="ECN-1",
            ecn_status="APPROVED",
        )

        available_query = MagicMock()
        available_query.filter.return_value.scalar.return_value = 15
        total_query = MagicMock()
        total_query.filter.return_value.scalar.return_value = 20
        supplier_query = MagicMock()
        supplier_query.filter.return_value.count.return_value = 3
        db.query.side_effect = [available_query, total_query, supplier_query]

        result = service._build_alternative_response(original, alt_material, alt_record)

        assert result == {
            "id": 9,
            "alternative_material_id": 2,
            "material_code": "ALT-2",
            "material_name": "替代料",
            "specification": "Spec-B",
            "brand": "ABB",
            "unit": "PCS",
            "match_score": 88.0,
            "match_reason": "人工验证",
            "is_verified": True,
            "current_stock": 20.0,
            "available_stock": 15.0,
            "original_price": 100.0,
            "alternative_price": 120.0,
            "price_diff_pct": 20.0,
            "supplier_count": 3,
            "lead_time_days": 12,
            "ecn_no": "ECN-1",
            "ecn_status": "APPROVED",
        }

    def test_get_alternatives_handles_missing_material_and_merges_registered_auto(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        original = _ns(
            id=1,
            category_id=10,
            specification="M3/10-SS",
            material_code="ORG-1",
            material_name="原料",
            is_active=True,
        )
        reg_alt_mat = _ns(id=2, is_active=True)
        auto_alt_mat = _ns(id=3, is_active=True)
        skipped_alt_mat = _ns(id=4, is_active=True)
        reg_records = [
            _ns(alternative_material_id=2, is_verified=True, match_score=95),
            _ns(alternative_material_id=5, is_verified=False, match_score=80),
        ]

        material_get_map = {
            999: None,
            1: original,
            2: reg_alt_mat,
            5: _ns(id=5, is_active=True),
        }
        material_query = MagicMock()
        material_query.get.side_effect = lambda material_id: material_get_map.get(material_id)
        auto_query = MagicMock()
        auto_query.filter.return_value.limit.return_value.all.return_value = [auto_alt_mat, skipped_alt_mat]
        reg_query = MagicMock()
        reg_query.filter.return_value.order_by.return_value.all.return_value = reg_records

        state = {"material_query_calls": 0}

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                state["material_query_calls"] += 1
                return auto_query if state["material_query_calls"] == 3 else material_query
            if entity is MaterialAlternative:
                return reg_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect
        service._calculate_match_score = MagicMock(side_effect=[70, 35])
        service._build_alternative_response = MagicMock(side_effect=[
            {"alternative_material_id": 2, "match_score": 95.0},
            {"alternative_material_id": 3, "match_score": 70.0},
        ])

        assert service.get_alternatives(999) == {"error": "物料不存在"}
        state["material_query_calls"] = 0

        result = service.get_alternatives(1, include_unverified=False)

        assert result["original_material_id"] == 1
        assert result["alternatives"] == [
            {"alternative_material_id": 2, "match_score": 95.0},
            {"alternative_material_id": 3, "match_score": 70.0},
        ]
        assert result["total"] == 2

    def test_get_bottleneck_materials_with_and_without_delay(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        summary_rows = [
            _ns(
                material_id=101,
                material_code="MAT-A",
                material_name="瓶颈A",
                shortage_count=5,
                total_shortage_qty=12,
                affected_projects=3,
            ),
            _ns(
                material_id=202,
                material_code="MAT-B",
                material_name="瓶颈B",
                shortage_count=2,
                total_shortage_qty=5,
                affected_projects=1,
            ),
        ]
        summary_query = MagicMock()
        summary_query.filter.return_value = summary_query
        summary_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = summary_rows

        delay_query = MagicMock()
        delay_query.filter.return_value.all.side_effect = [
            [
                _ns(required_date=date(2026, 4, 1), actual_arrival_date=date(2026, 4, 10)),
                _ns(required_date=date(2026, 4, 5), actual_arrival_date=date(2026, 4, 8)),
            ],
            [],
        ]

        def query_side_effect(*args, **kwargs):
            if len(args) == 1 and args[0] is MaterialShortage:
                return delay_query
            return summary_query

        db.query.side_effect = query_side_effect

        result = service._get_bottleneck_materials(project_id=9)

        assert result == [
            {
                "material_id": 101,
                "material_code": "MAT-A",
                "material_name": "瓶颈A",
                "shortage_count": 5,
                "total_shortage_qty": 12.0,
                "avg_delay_days": 6.0,
                "affected_projects": 3,
                "suggestion": "建议设置更高的安全库存水位；建议纳入提前采购清单；建议与供应商签订框架协议确保供应",
            },
            {
                "material_id": 202,
                "material_code": "MAT-B",
                "material_name": "瓶颈B",
                "shortage_count": 2,
                "total_shortage_qty": 5.0,
                "avg_delay_days": None,
                "affected_projects": 1,
                "suggestion": "建议与供应商签订框架协议确保供应",
            },
        ]

    def test_generate_bottleneck_suggestion_covers_all_rules(self):
        service = KittingOptimizationService(MagicMock())

        assert service._generate_bottleneck_suggestion(5, 9.0, "MAT-X") == (
            "建议设置更高的安全库存水位；建议评估替代供应商或替代料；建议纳入提前采购清单；建议与供应商签订框架协议确保供应"
        )
        assert service._generate_bottleneck_suggestion(1, 3.0, "MAT-Y") == "建议与供应商签订框架协议确保供应"

    def test_get_improvement_target_handles_positive_gap_and_zero_floor(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        shortage_query = MagicMock()
        shortage_query.filter.return_value = shortage_query
        shortage_query.count.side_effect = [10, 120]
        bom_count_query = MagicMock()
        bom_count_query.filter.return_value.scalar.side_effect = [100, 0]

        def query_side_effect(*args, **kwargs):
            if len(args) == 1 and args[0] is MaterialShortage:
                return shortage_query
            return bom_count_query

        db.query.side_effect = query_side_effect

        result1 = service._get_improvement_target(project_id=7)
        result2 = service._get_improvement_target()

        assert result1 == {
            "current_rate": 90.0,
            "target_rate": 98.0,
            "gap": 8.0,
            "key_actions": [
                "处理TOP10瓶颈物料缺料问题，预计提升齐套率3.2%",
                "对高风险供应商启动交期改善计划",
                "建立长周期物料提前采购机制",
                "完善通用物料安全库存策略",
                "推进替代料验证，减少单一来源依赖",
            ],
            "estimated_timeline": "6个月",
        }
        assert result2 == {
            "current_rate": 0,
            "target_rate": 10,
            "gap": 10,
            "key_actions": [
                "处理TOP10瓶颈物料缺料问题，预计提升齐套率4.0%",
                "对高风险供应商启动交期改善计划",
                "建立长周期物料提前采购机制",
                "完善通用物料安全库存策略",
                "推进替代料验证，减少单一来源依赖",
            ],
            "estimated_timeline": "6个月",
        }

    def test_sync_all_projects_kitting_rate_collects_changes_errors_and_updates_health(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        projects = [
            _ns(id=1, project_code="P1", health="H1"),
            _ns(id=2, project_code="P2", health="H2"),
            _ns(id=3, project_code="P3", health="H1"),
        ]
        refreshed_projects = {
            1: _ns(id=1, health="H1"),
            2: _ns(id=2, health="H2"),
        }

        project_list_query = MagicMock()
        project_list_query.filter.return_value.all.return_value = projects
        project_get_query = MagicMock()
        project_get_query.get.side_effect = lambda project_id: refreshed_projects.get(project_id)

        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_get_query if kwargs.get("for_get") else project_list_query
            raise AssertionError(f"unexpected query entity: {entity}")

        def db_query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                return project_list_query if not hasattr(db_query_side_effect, "calls") or db_query_side_effect.calls == 0 else project_get_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db_query_side_effect.calls = 0
        def wrapped_query(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                db_query_side_effect.calls += 1
                return project_list_query if db_query_side_effect.calls == 1 else project_get_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = wrapped_query
        service.sync_project_kitting_rate = MagicMock(side_effect=[
            {"project_id": 1, "project_code": "P1", "changed": True, "change_delta": -8, "new_rate": 45},
            {"project_id": 2, "project_code": "P2", "changed": True, "change_delta": -3, "new_rate": 65},
            RuntimeError("boom"),
        ])

        result = service.sync_all_projects_kitting_rate(threshold=5)

        assert result == {
            "total_synced": 2,
            "significant_changes": [{"project_id": 1, "project_code": "P1", "changed": True, "change_delta": -8, "new_rate": 45}],
            "significant_count": 1,
            "errors": [{"project_id": 3, "project_code": "P3", "error": "boom"}],
            "error_count": 1,
            "threshold": 5,
        }
        assert refreshed_projects[1].health == "H3"
        assert refreshed_projects[2].health == "H2"
        assert db.commit.call_count == 2

    def test_get_common_stock_suggestions_filters_inactive_and_sufficient_stock(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        usage_stats_query = MagicMock()
        usage_stats_query.filter.return_value.group_by.return_value.having.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (1, 6)
        ]
        usage_query = MagicMock()
        usage_query.filter.return_value.group_by.return_value.having.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (1, 6),
            (2, 4),
            (3, 5),
        ]
        material_query = MagicMock()
        material_query.get.side_effect = lambda material_id: {
            1: _ns(id=1, material_code="M-COM", material_name="通用料", current_stock=10, safety_stock=20, is_active=True),
            2: _ns(id=2, material_code="M-SAFE", material_name="库存足", current_stock=100, safety_stock=50, is_active=True),
            3: _ns(id=3, material_code="M-OFF", material_name="停用料", current_stock=0, safety_stock=0, is_active=False),
        }[material_id]
        project_count_query = MagicMock()
        project_count_query.scalar.side_effect = [6, 4]
        consumption_query = MagicMock()
        consumption_query.filter.return_value.scalar.side_effect = [90, 60]

        generic_query = MagicMock()
        generic_query.join.return_value.filter.return_value.correlate.return_value.scalar_subquery.return_value = MagicMock()

        def query_side_effect(*args, **kwargs):
            first = args[0] if args else None
            if len(args) == 3 and first is BomItem.material_id:
                return usage_stats_query
            if len(args) == 2 and first is BomItem.material_id:
                return usage_query
            if len(args) == 1 and first is Material:
                return material_query
            first_str = str(first)
            if "sum(material_transactions.quantity)" in first_str:
                return consumption_query
            if "count(" in first_str:
                return project_count_query
            return generic_query

        db.query.side_effect = query_side_effect

        result = service._get_common_stock_suggestions()

        assert result == [
            {
                "material_id": 1,
                "material_code": "M-COM",
                "material_name": "通用料",
                "usage_frequency": 6,
                "project_coverage": 6,
                "current_stock": 10.0,
                "suggested_safety_stock": 20.0,
                "reason": "该物料在6个BOM中使用，属于高频通用物料，建议建立安全库存",
            }
        ]

    def test_sync_all_projects_kitting_rate_marks_h1_project_as_h2_when_under_70(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        projects = [_ns(id=2, project_code="P2", health="H1")]
        refreshed_project = _ns(id=2, health="H1")

        project_list_query = MagicMock()
        project_list_query.filter.return_value.all.return_value = projects
        project_get_query = MagicMock()
        project_get_query.get.return_value = refreshed_project

        state = {"calls": 0}
        def query_side_effect(entity, *args, **kwargs):
            if getattr(entity, "__name__", "") == "Project":
                state["calls"] += 1
                return project_list_query if state["calls"] == 1 else project_get_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect
        service.sync_project_kitting_rate = MagicMock(return_value={
            "project_id": 2,
            "project_code": "P2",
            "changed": True,
            "change_delta": -5,
            "new_rate": 65,
        })

        result = service.sync_all_projects_kitting_rate(threshold=5)

        assert result["total_synced"] == 1
        assert refreshed_project.health == "H2"

    def test_get_supplier_delivery_analysis_skips_supplier_without_evaluated_orders(self):
        db = MagicMock()
        service = KittingOptimizationService(db)

        supplier_stats_query = MagicMock()
        supplier_stats_query.join.return_value.filter.return_value.group_by.return_value.all.return_value = [(10, 2)]
        vendor_query = MagicMock()
        vendor_query.get.return_value = _ns(supplier_name="供应商A")
        po_item_query = MagicMock()
        po_item_query.join.return_value.filter.return_value.all.return_value = [
            _ns(id=1001, required_date=date(2026, 4, 10))
        ]
        receipt_query = MagicMock()
        receipt_query.join.return_value.filter.return_value.first.return_value = None

        def query_side_effect(entity, *args, **kwargs):
            if entity is PurchaseOrder.supplier_id:
                return supplier_stats_query
            if entity is Vendor:
                return vendor_query
            if entity is PurchaseOrderItem:
                return po_item_query
            if entity is GoodsReceiptItem:
                return receipt_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect

        assert service._get_supplier_delivery_analysis() == []

    def test_create_expedite_records_skips_missing_materials(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        today = date.today()

        material_query = MagicMock()
        material_query.get.return_value = None
        recent_query = MagicMock()
        recent_query.filter.return_value.first.return_value = None

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                return material_query
            if entity is ExpediteRecord:
                return recent_query
            raise AssertionError(f"unexpected query entity: {entity}")

        db.query.side_effect = query_side_effect
        service._build_expedite_record = MagicMock()

        result = service.create_expedite_records(
            targets=[{"material_id": 1, "shortage_id": 5}],
            notify_methods=["email"],
            auto_high_risk=[_ns(id=6, material_id=2, shortage_qty=3, required_date=today, project_id=1)],
            user_id=9,
        )

        assert result == []
        service._build_expedite_record.assert_not_called()

    def test_get_expedite_stats_applies_start_and_end_date_filters(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        base_query = MagicMock()
        filtered_start = MagicMock()
        filtered_end = MagicMock()
        filtered_end.count.return_value = 0
        filtered_end.filter.return_value.count.return_value = 0
        filtered_end.filter.return_value.all.return_value = []

        urgency_queries = [
            MagicMock(count=MagicMock(return_value=0)),
            MagicMock(count=MagicMock(return_value=0)),
            MagicMock(count=MagicMock(return_value=0)),
            MagicMock(count=MagicMock(return_value=0)),
        ]
        filtered_end.filter.side_effect = [
            MagicMock(count=MagicMock(return_value=0)),
            MagicMock(all=MagicMock(return_value=[])),
            MagicMock(all=MagicMock(return_value=[])),
            *urgency_queries,
        ]
        filtered_end.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        filtered_start.filter.return_value = filtered_end
        base_query.filter.return_value = filtered_start
        db.query.side_effect = lambda entity, *args, **kwargs: base_query

        result = service.get_expedite_stats(start_date=date(2026, 4, 1), end_date=date(2026, 4, 30))

        assert result["total_expedited"] == 0
        assert base_query.filter.called
        assert filtered_start.filter.called

    def test_get_safety_stock_alerts_respects_key_category_and_alert_level_filters(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        info_material = _ns(
            id=1,
            material_code="MAT-INFO",
            material_name="提示料",
            specification="S1",
            category_id=9,
            is_key_material=True,
            current_stock=90,
            safety_stock=100,
            lead_time_days=1,
            min_order_qty=1,
            is_active=True,
        )

        materials_query = MagicMock()
        materials_query.filter.return_value = materials_query
        materials_query.all.return_value = [info_material]
        category_query = MagicMock()
        category_query.get.return_value = _ns(category_name="电子料")
        consumption_query = MagicMock()
        consumption_query.filter.return_value.scalar.return_value = 0
        shortage_query = MagicMock()
        shortage_query.filter.return_value.count.return_value = 0

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                return materials_query
            if entity is MaterialCategory:
                return category_query
            if entity is MaterialShortage:
                return shortage_query
            return consumption_query

        db.query.side_effect = query_side_effect

        result = service.get_safety_stock_alerts(alert_level="CRITICAL", category_id=9, only_key_materials=True)

        assert result["alerts"] == []
        assert result["total"] == 0

    def test_get_pre_purchase_suggestions_skips_nonpositive_suggested_qty(self):
        db = MagicMock()
        service = KittingOptimizationService(db)
        materials = [
            _ns(id=1, material_code="M-HIGH", material_name="库存高", lead_time_days=20, current_stock=100, safety_stock=0, is_active=True),
        ]

        materials_query = MagicMock()
        materials_query.filter.return_value.all.return_value = materials
        consumption_query = MagicMock()
        consumption_query.filter.return_value.scalar.return_value = 90

        def query_side_effect(entity, *args, **kwargs):
            if entity is Material:
                return materials_query
            return consumption_query

        db.query.side_effect = query_side_effect

        assert service._get_pre_purchase_suggestions() == []
