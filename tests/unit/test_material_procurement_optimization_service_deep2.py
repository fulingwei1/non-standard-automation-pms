# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.schemas.material_procurement_optimization import (
    DuplicatePurchaseCheckRequest,
    ShortageWasteCalculationRequest,
)
from app.services.material_procurement_optimization_service import (
    MaterialProcurementOptimizationService,
)



def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


class TestMaterialProcurementOptimizationServiceDeep2:
    def test_calculate_shortage_waste_covers_severity_and_entity_lookup(self):
        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)

        project_q = MagicMock()
        project_q.filter.return_value.first.return_value = _ns(
            id=11, project_code="P-11", project_name="项目11"
        )
        material_q = MagicMock()
        material_q.filter.return_value.first.return_value = _ns(
            id=22, material_code="M-22", material_name="电机"
        )
        db.query.side_effect = [project_q, material_q]

        payload = ShortageWasteCalculationRequest(
            project_id=11,
            material_id=22,
            shortage_reason="供应商延期",
            waiting_workers=10,
            labor_hourly_rate=Decimal("100"),
            waiting_hours=Decimal("20"),
            idle_machines=5,
            machine_hourly_rate=Decimal("200"),
            contract_amount=Decimal("1000000"),
            delay_days=10,
            daily_penalty_rate=Decimal("0.002"),
            daily_output_value=Decimal("3000"),
            include_management_buffer=True,
            management_buffer_rate=Decimal("0.1"),
        )

        result = service.calculate_shortage_waste(payload)

        assert result["project"]["project_name"] == "项目11"
        assert result["material"]["material_name"] == "电机"
        assert result["cost_breakdown"]["labor_idle_cost"] == Decimal("20000.00")
        assert result["cost_breakdown"]["machine_idle_cost"] == Decimal("20000.00")
        assert result["cost_breakdown"]["delay_penalty"] == Decimal("20000.00")
        assert result["cost_breakdown"]["opportunity_cost"] == Decimal("30000.00")
        assert result["cost_breakdown"]["management_buffer_cost"] == Decimal("9000.00")
        assert result["total_waste_amount"] == Decimal("99000.00")
        assert result["daily_waste_amount"] == Decimal("9900.00")
        assert result["hourly_waste_amount"] == Decimal("4950.00")
        assert result["severity"] == "紧急"
        assert len(result["action_suggestions"]) == 4

    def test_calculate_shortage_waste_covers_warning_severity_default_action_and_code_lookup(self):
        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)

        material_q = MagicMock()
        material_q.filter.return_value.first.return_value = _ns(
            id=9, material_code="M-9", material_name="传感器"
        )
        db.query.return_value = material_q

        payload = ShortageWasteCalculationRequest(
            material_code="M-9",
            waiting_workers=0,
            waiting_hours=Decimal("0"),
            idle_machines=0,
            contract_amount=Decimal("100000"),
            delay_days=2,
            daily_penalty_rate=Decimal("0.05"),
            daily_output_value=Decimal("0"),
        )

        result = service.calculate_shortage_waste(payload)

        assert result["material"]["material_name"] == "传感器"
        assert result["total_waste_amount"] == Decimal("10000.00")
        assert result["daily_waste_amount"] == Decimal("5000.00")
        assert result["hourly_waste_amount"] == Decimal("0.00")
        assert result["severity"] == "警告"
        assert result["action_suggestions"] == ["已存在延期罚款风险，采购需拉通供应商承诺交期并做日跟催"]

    def test_get_safety_stock_alerts_covers_sorting_vendor_and_actions(self):
        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)
        materials = [
            _ns(id=1, material_code="A", material_name="A料", specification="S1", unit="件", lead_time_days=10, min_order_qty=10, default_supplier_id=101),
            _ns(id=2, material_code="B", material_name="B料", specification="S2", unit="件", lead_time_days=5, min_order_qty=6, default_supplier_id=None),
            _ns(id=3, material_code="C", material_name="C料", specification="S3", unit="件", lead_time_days=7, min_order_qty=5, default_supplier_id=None),
            _ns(id=4, material_code="D", material_name="D料", specification="S4", unit=None, lead_time_days=7, min_order_qty=4, default_supplier_id=None),
        ]

        material_q = MagicMock()
        material_q.filter.return_value.all.return_value = materials
        vendor_q = MagicMock()
        vendor_q.filter.return_value.first.return_value = _ns(supplier_name="供应商A")
        db.query.side_effect = [material_q, vendor_q]

        stock_map = {1: Decimal("0"), 2: Decimal("10"), 3: Decimal("12"), 4: Decimal("5")}
        consumed_map = {1: Decimal("90"), 2: Decimal("180"), 3: Decimal("90"), 4: Decimal("0")}
        shortage_map = {1: 3, 2: 1, 3: 0, 4: 5}
        service._current_stock = MagicMock(side_effect=lambda material_id: stock_map[material_id])
        service._consumed_qty = MagicMock(side_effect=lambda material_id, cutoff: consumed_map[material_id])
        service._shortage_frequency = MagicMock(side_effect=lambda material_id, cutoff: shortage_map[material_id])

        result = service.get_safety_stock_alerts(days=90, safety_factor=Decimal("1.5"))

        assert result["summary"] == {
            "total_alerts": 4,
            "emergency_count": 1,
            "warning_count": 1,
            "notice_count": 2,
            "high_frequency_shortage_count": 2,
        }
        items = result["items"]
        assert [x["material_id"] for x in items] == [1, 2, 4, 3]
        assert items[0]["default_supplier_name"] == "供应商A"
        assert items[0]["actions"] == [
            "建议立即触发补货申请，并锁定采购交期",
            "建议补货 30.00 件，已按MOQ取整",
            "近90天缺料频繁，建议纳入重点物料周会清单",
        ]
        assert items[3]["actions"] == ["建议补货 10.00 件，已按MOQ取整"]
        assert "近90天几乎无消耗，补货前先确认是否为呆滞风险" in items[2]["actions"]

    def test_check_duplicate_purchase_covers_duplicates_transfer_and_default_suggestion(self):
        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)
        material = _ns(id=8, material_code="M8", material_name="接头", specification="X1")
        service._resolve_material = MagicMock(return_value=material)
        service._apply_material_match_filter = MagicMock(side_effect=lambda q, *args: q)
        service._project_allocatable_stock = MagicMock(side_effect=lambda material_id, project_id: Decimal("6") if project_id == 200 else Decimal("0"))
        service._bom_consistency = MagicMock(return_value={
            "project_id": 100,
            "requested_bom_version": "V1",
            "active_bom_versions": ["V1", "V2"],
            "latest_bom_version": "V2",
            "version_conflict": True,
        })

        req_q = MagicMock()
        req_q.join.return_value.filter.return_value = req_q
        req_q.all.return_value = [
            (_ns(id=1, request_no="PR-1", status="APPROVED", project_id=200), _ns(material_id=8, material_code="M8", material_name="接头", specification="X1", quantity=5, ordered_qty=1))
        ]
        po_q = MagicMock()
        po_q.join.return_value.filter.return_value = po_q
        po_q.all.return_value = [
            (_ns(id=2, order_no="PO-2", status="ORDERED", project_id=300, supplier_id=88), _ns(material_id=8, material_code="M8", material_name="接头", specification="X1", quantity=7, received_qty=2))
        ]
        project_q_200 = MagicMock()
        project_q_200.filter.return_value.first.return_value = _ns(project_code="P200", project_name="项目200")
        project_q_300 = MagicMock()
        project_q_300.filter.return_value.first.return_value = None
        db.query.side_effect = [req_q, po_q, project_q_200]

        payload = DuplicatePurchaseCheckRequest(project_id=100, material_id=8, requested_quantity=Decimal("9"), requested_bom_version="V1")
        result = service.check_duplicate_purchase(payload)

        assert result["duplicate_found"] is True
        assert len(result["duplicate_purchase_requests"]) == 1
        assert len(result["duplicate_purchase_orders"]) == 1
        assert result["transferable_stock_options"] == [{
            "project_id": 200,
            "project_code": "P200",
            "project_name": "项目200",
            "allocatable_stock": Decimal("6.00"),
        }]
        assert result["suggestions"] == [
            "检测到已有在途采购，优先评估并单/改量，别重复下单制造库存垃圾",
            "存在其他项目可调拨库存，建议先调拨再采购",
            "BOM版本不一致，先统一版本再审批采购申请",
        ]

        db2 = MagicMock()
        service2 = MaterialProcurementOptimizationService(db2)
        service2._resolve_material = MagicMock(return_value=None)
        service2._bom_consistency = MagicMock(return_value={
            "project_id": None,
            "requested_bom_version": None,
            "active_bom_versions": [],
            "latest_bom_version": None,
            "version_conflict": False,
        })
        payload2 = DuplicatePurchaseCheckRequest(material_code="M0", check_open_purchase_requests=False, check_open_purchase_orders=False)
        result2 = service2.check_duplicate_purchase(payload2)
        assert result2["duplicate_found"] is False
        assert result2["suggestions"] == ["未发现明显重复采购风险，可继续走采购流程"]

    def test_get_slow_moving_analysis_covers_categories_and_summary(self):
        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)
        now = datetime.now()
        materials = [
            _ns(id=1, material_code="A", material_name="A料", specification="S1", unit="件", last_price=Decimal("10"), standard_price=Decimal("8")),
            _ns(id=2, material_code="B", material_name="B料", specification="S2", unit="件", last_price=Decimal("5"), standard_price=Decimal("5")),
            _ns(id=3, material_code="C", material_name="C料", specification="S3", unit="件", last_price=Decimal("4"), standard_price=Decimal("4")),
            _ns(id=4, material_code="D", material_name="D料", specification="S4", unit="件", last_price=Decimal("3"), standard_price=Decimal("2")),
            _ns(id=5, material_code="E", material_name="E料", specification="S5", unit="件", last_price=Decimal("9"), standard_price=Decimal("9")),
        ]
        material_q = MagicMock()
        material_q.filter.return_value.all.return_value = materials
        last_txn_queries = []
        for tx in [
            _ns(transaction_date=now - timedelta(days=400)),
            _ns(transaction_date=now - timedelta(days=200)),
            _ns(transaction_date=now - timedelta(days=100)),
            _ns(transaction_date=now - timedelta(days=10)),
        ]:
            q = MagicMock()
            q.filter.return_value.order_by.return_value.first.return_value = tx
            last_txn_queries.append(q)
        q_none = MagicMock()
        q_none.filter.return_value.order_by.return_value.first.return_value = None
        db.query.side_effect = [material_q, *last_txn_queries, q_none]

        stock_map = {1: Decimal("10"), 2: Decimal("5"), 3: Decimal("8"), 4: Decimal("6"), 5: Decimal("0")}
        service._current_stock = MagicMock(side_effect=lambda material_id: stock_map[material_id])
        service._ecn_obsolete_signal = MagicMock(side_effect=lambda material_id: material_id == 4)
        reason_map = {
            1: "ECN变更/设计淘汰",
            2: "项目取消或停滞",
            3: "采购过量",
            4: "质量问题",
        }
        service._analyze_slow_moving_reason = MagicMock(side_effect=lambda material_id, category, last: reason_map[material_id])

        result = service.get_slow_moving_analysis()

        assert result["summary"] == {
            "slow_moving_count": 1,
            "stagnant_count": 1,
            "scrap_count": 2,
            "total_book_value": Decimal("175.00"),
            "total_potential_recovery_amount": Decimal("58.10"),
        }
        assert [x["material_id"] for x in result["items"]] == [1, 4, 2, 3]
        assert result["items"][0]["disposal_suggestion"] == "报废"
        assert result["items"][1]["category"] == "报废"
        assert result["items"][2]["disposal_suggestion"] == "内部调拨"
        assert result["items"][3]["disposal_suggestion"] == "退回供应商"

        db2 = MagicMock()
        service2 = MaterialProcurementOptimizationService(db2)
        quiet_material = [_ns(id=9, material_code="Q", material_name="Q料", specification="Q1", unit="件", last_price=Decimal("1"), standard_price=Decimal("1"))]
        material_q2 = MagicMock()
        material_q2.filter.return_value.all.return_value = quiet_material
        recent_q = MagicMock()
        recent_q.filter.return_value.order_by.return_value.first.return_value = _ns(transaction_date=now - timedelta(days=5))
        db2.query.side_effect = [material_q2, recent_q]
        service2._current_stock = MagicMock(return_value=Decimal("2"))
        service2._ecn_obsolete_signal = MagicMock(return_value=False)
        result2 = service2.get_slow_moving_analysis()
        assert result2["items"] == []

    def test_helpers_cover_numeric_lookup_and_match_paths(self):
        service = MaterialProcurementOptimizationService(MagicMock())

        assert service._d(None) == Decimal("0")
        assert service._d("bad", "2") == Decimal("2")
        assert service._round_money(Decimal("1.235")) == Decimal("1.24")
        assert service._safe_str("  abc  ") == "abc"
        assert service._round_up_to_moq(Decimal("13"), Decimal("5")) == Decimal("15.00")
        assert service._round_up_to_moq(Decimal("13"), Decimal("0")) == Decimal("13.00")
        assert service._round_up_to_moq(Decimal("0"), Decimal("5")) == Decimal("0")

        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)
        q1 = MagicMock()
        q1.filter.return_value.scalar.return_value = None
        q2 = MagicMock()
        q2.filter.return_value.scalar.return_value = Decimal("9")
        db.query.side_effect = [q1, q2]
        assert service._current_stock(1) == Decimal("9")

        db2 = MagicMock()
        service2 = MaterialProcurementOptimizationService(db2)
        q3 = MagicMock()
        q3.filter.return_value.scalar.return_value = Decimal("-7")
        q4 = MagicMock()
        q4.filter.return_value.count.return_value = 3
        db2.query.side_effect = [q3, q4]
        assert service2._consumed_qty(1, datetime.now()) == Decimal("7")
        assert service2._shortage_frequency(1, date.today()) == 3

    def test_helpers_cover_material_resolution_bom_ecn_reason_and_disposal(self):
        db = MagicMock()
        service = MaterialProcurementOptimizationService(db)
        q_id = MagicMock()
        q_id.filter.return_value.first.return_value = _ns(id=1)
        q_code = MagicMock()
        q_code.filter.return_value.first.return_value = _ns(id=2)
        q_name_spec = MagicMock()
        q_name_spec.filter.return_value = q_name_spec
        q_name_spec.first.return_value = _ns(id=3)
        db.query.side_effect = [q_id, q_code, q_name_spec]

        assert service._resolve_material(1, None, None, None).id == 1
        assert service._resolve_material(None, "M2", None, None).id == 2
        assert service._resolve_material(None, None, "物料", "规格").id == 3

        q = MagicMock()
        service._apply_material_match_filter(q, "id", "code", "name", "spec", None, None, None, None)
        q.filter.assert_not_called()
        service._apply_material_match_filter(q, "id", "code", "name", "spec", 1, "M", "N", "S")
        assert q.filter.called
        q2 = MagicMock()
        service._apply_material_match_filter(q2, "id", "code", "name", "spec", None, None, "N", None)
        q3 = MagicMock()
        service._apply_material_match_filter(q3, "id", "code", "name", "spec", None, None, None, "S")
        assert q2.filter.called and q3.filter.called

        db_alloc = MagicMock()
        service_alloc = MaterialProcurementOptimizationService(db_alloc)
        q_alloc = MagicMock()
        q_alloc.filter.return_value.scalar.return_value = Decimal("12")
        db_alloc.query.return_value = q_alloc
        assert service_alloc._project_allocatable_stock(9, 88) == Decimal("12")

        db2 = MagicMock()
        service2 = MaterialProcurementOptimizationService(db2)
        q_bom = MagicMock()
        q_bom.join.return_value.filter.return_value.distinct.return_value.all.return_value = [
            _ns(version="V1", is_latest=False),
            _ns(version="V2", is_latest=True),
        ]
        q_ecn = MagicMock()
        q_ecn.join.return_value.filter.return_value.order_by.return_value.first.return_value = _ns(is_obsolete_risk=True)
        db2.query.side_effect = [q_bom, q_ecn]

        bom = service2._bom_consistency(9, 10, "V1")
        assert bom["latest_bom_version"] == "V2"
        assert bom["version_conflict"] is True
        assert service2._ecn_obsolete_signal(9) is True
        assert service2._bom_consistency(None, 10, "V1")["version_conflict"] is False
        assert service2._ecn_obsolete_signal(0) is False
        assert service2._material_unit_value(_ns(last_price=None, standard_price=Decimal("8"))) == Decimal("8")

        db3 = MagicMock()
        service3 = MaterialProcurementOptimizationService(db3)
        q_ecn_reason = MagicMock()
        q_ecn_reason.filter.return_value.order_by.return_value.first.return_value = _ns(is_obsolete_risk=True)
        db3.query.side_effect = [q_ecn_reason]
        assert service3._analyze_slow_moving_reason(1, "慢动", datetime.now()) == "ECN变更/设计淘汰"

        db4 = MagicMock()
        service4 = MaterialProcurementOptimizationService(db4)
        q_ecn_none = MagicMock()
        q_ecn_none.filter.return_value.order_by.return_value.first.return_value = None
        q_cancel = MagicMock()
        q_cancel.join.return_value.join.return_value.filter.return_value.count.return_value = 1
        db4.query.side_effect = [q_ecn_none, q_cancel]
        assert service4._analyze_slow_moving_reason(2, "慢动", datetime.now()) == "项目取消或停滞"

        db5 = MagicMock()
        service5 = MaterialProcurementOptimizationService(db5)
        q_ecn_none2 = MagicMock()
        q_ecn_none2.filter.return_value.order_by.return_value.first.return_value = None
        q_cancel0 = MagicMock()
        q_cancel0.join.return_value.join.return_value.filter.return_value.count.return_value = 0
        q_po50 = MagicMock()
        q_po50.join.return_value.filter.return_value.scalar.return_value = Decimal("50")
        db5.query.side_effect = [q_ecn_none2, q_cancel0, q_po50]
        service5._consumed_qty = MagicMock(return_value=Decimal("20"))
        assert service5._analyze_slow_moving_reason(3, "慢动", datetime.now()) == "采购过量"

        db6 = MagicMock()
        service6 = MaterialProcurementOptimizationService(db6)
        q_ecn_none3 = MagicMock()
        q_ecn_none3.filter.return_value.order_by.return_value.first.return_value = None
        q_cancel00 = MagicMock()
        q_cancel00.join.return_value.join.return_value.filter.return_value.count.return_value = 0
        q_po0 = MagicMock()
        q_po0.join.return_value.filter.return_value.scalar.return_value = Decimal("0")
        q_scrap2 = MagicMock()
        q_scrap2.filter.return_value.scalar.return_value = Decimal("-1")
        db6.query.side_effect = [q_ecn_none3, q_cancel00, q_po0, q_scrap2]
        service6._consumed_qty = MagicMock(return_value=Decimal("20"))
        assert service6._analyze_slow_moving_reason(4, "呆滞", datetime.now()) == "质量问题"

        db7 = MagicMock()
        service7 = MaterialProcurementOptimizationService(db7)
        q_ecn_none4 = MagicMock()
        q_ecn_none4.filter.return_value.order_by.return_value.first.return_value = None
        q_cancel000 = MagicMock()
        q_cancel000.join.return_value.join.return_value.filter.return_value.count.return_value = 0
        q_po00 = MagicMock()
        q_po00.join.return_value.filter.return_value.scalar.return_value = Decimal("0")
        q_scrap00 = MagicMock()
        q_scrap00.filter.return_value.scalar.return_value = Decimal("0")
        db7.query.side_effect = [q_ecn_none4, q_cancel000, q_po00, q_scrap00, q_ecn_none4, q_cancel000, q_po00, q_scrap00]
        service7._consumed_qty = MagicMock(return_value=Decimal("20"))
        assert service7._analyze_slow_moving_reason(5, "呆滞", None) == "长期无消耗"
        assert service7._analyze_slow_moving_reason(5, "慢动", datetime.now()) == "需求下降导致慢动"

        assert service7._suggest_disposal("呆滞", "项目取消或停滞") == "内部调拨"
        assert service7._suggest_disposal("慢动", "采购过量") == "退回供应商"
        assert service7._suggest_disposal("慢动", "质量问题") == "拆解利用"
        assert service7._suggest_disposal("报废", "质量问题") == "报废"
        assert service7._suggest_disposal("慢动", "ECN变更/设计淘汰") == "折价变卖"
        assert service7._suggest_disposal("报废", "其他") == "报废"
        assert service7._suggest_disposal("慢动", "普通原因") == "内部调拨"
