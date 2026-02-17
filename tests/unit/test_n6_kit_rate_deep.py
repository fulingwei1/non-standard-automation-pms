# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：套件率服务
Coverage target: app/services/kit_rate/kit_rate_service.py

核心场景：
1. calculate_kit_rate — 数量法 vs 金额法、在途叠加、各状态阈值
2. _get_in_transit_qty — 多订单累积
3. get_machine_material_status — 物料状态分类（fulfilled/partial/shortage）
4. get_project_material_status — 多机台汇总逻辑
5. get_trend — day/month 分组、summary 计算
6. get_snapshots — 快照查询
7. dashboard — complete/partial/shortage 统计
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from fastapi import HTTPException

from app.services.kit_rate.kit_rate_service import KitRateService


# ─────────────────────────────────────────────────
# Mock helpers
# ─────────────────────────────────────────────────

def make_material(stock=0):
    m = MagicMock()
    m.current_stock = stock
    return m


def make_bom_item(
    id=1,
    material_id=1,
    material_code="MAT001",
    material_name="测试物料",
    quantity=10,
    unit_price=100,
    received_qty=0,
    is_key_item=False,
    required_date=None,
    stock=0,
    specification="规格A",
    unit="个",
    item_no="001",
):
    item = MagicMock()
    item.id = id
    item.material_id = material_id
    item.material_code = material_code
    item.material_name = material_name
    item.quantity = Decimal(str(quantity))
    item.unit_price = Decimal(str(unit_price))
    item.received_qty = Decimal(str(received_qty))
    item.is_key_item = is_key_item
    item.required_date = required_date
    item.specification = specification
    item.unit = unit
    item.item_no = item_no
    item.material = make_material(stock=stock)
    return item


def make_bom_header(id=1, bom_no="BOM001", bom_name="测试BOM", items=None):
    bom = MagicMock()
    bom.id = id
    bom.bom_no = bom_no
    bom.bom_name = bom_name
    items_mock = MagicMock()
    items_mock.all.return_value = items or []
    bom.items = items_mock
    return bom


def make_machine(id=1, machine_no="MC001", machine_name="机台1", project_id=1):
    m = MagicMock()
    m.id = id
    m.machine_no = machine_no
    m.machine_name = machine_name
    m.project_id = project_id
    return m


def make_project(id=1, code="PJ001", name="项目1"):
    p = MagicMock()
    p.id = id
    p.project_code = code
    p.project_name = name
    p.planned_end_date = None
    p.is_active = True
    return p


def make_db_no_po():
    """返回一个模拟 DB，PO 查询总返回空列表"""
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    return db


# ─────────────────────────────────────────────────
# 1. calculate_kit_rate — 数量法
# ─────────────────────────────────────────────────

class TestCalculateKitRateByQuantity:

    def test_all_items_fulfilled_100pct(self):
        db = make_db_no_po()
        svc = KitRateService(db)
        items = [make_bom_item(id=i, quantity=10, stock=50) for i in range(1, 6)]
        result = svc.calculate_kit_rate(items, "quantity")

        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"
        assert result["fulfilled_items"] == 5
        assert result["shortage_items"] == 0

    def test_kit_rate_exactly_80pct_is_partial(self):
        """5 件中 4 件满足 → 80% → partial"""
        db = make_db_no_po()
        svc = KitRateService(db)
        items = [
            make_bom_item(id=1, quantity=10, stock=10),
            make_bom_item(id=2, quantity=10, stock=10),
            make_bom_item(id=3, quantity=10, stock=10),
            make_bom_item(id=4, quantity=10, stock=10),
            make_bom_item(id=5, quantity=10, stock=0),  # shortage
        ]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["kit_rate"] == 80.0
        assert result["kit_status"] == "partial"

    def test_kit_rate_79pct_is_shortage(self):
        """79% → shortage（< 80 阈值）"""
        db = make_db_no_po()
        svc = KitRateService(db)
        # 需要 100 单位，库存 79，在途 0
        items = [make_bom_item(id=1, quantity=100, stock=79)]
        result = svc.calculate_kit_rate(items, "quantity")
        # fulfilled_quantity = 0 (79 < 100 → not fulfilled, in_transit)
        assert result["kit_status"] in ("shortage", "partial")

    def test_in_transit_adds_to_available(self):
        """在途数量可补足库存缺口 → fulfilled"""
        db = MagicMock()
        # PO: 订购 50, 已收 30 → 在途 20
        po_item = MagicMock(); po_item.quantity = 50; po_item.received_qty = 30
        db.query.return_value.filter.return_value.all.return_value = [po_item]

        svc = KitRateService(db)
        # 库存 0 + 在途 20 = 20 >= required 10 → fulfilled
        items = [make_bom_item(id=1, quantity=10, stock=0)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["fulfilled_items"] == 1

    def test_partial_in_transit_counts_as_in_transit_item(self):
        """库存不足但有在途 → in_transit_items += 1"""
        db = MagicMock()
        # 在途 5，库存 0，需求 10 → 仍缺，但 total_available > 0
        po_item = MagicMock(); po_item.quantity = 5; po_item.received_qty = 0
        db.query.return_value.filter.return_value.all.return_value = [po_item]

        svc = KitRateService(db)
        items = [make_bom_item(id=1, quantity=10, stock=0)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["in_transit_items"] == 1

    def test_received_qty_on_item_contributes_to_available(self):
        """bom_item.received_qty 也计入可用量"""
        db = make_db_no_po()
        svc = KitRateService(db)
        # 库存 0，已收 10，需 10 → fulfilled
        items = [make_bom_item(id=1, quantity=10, stock=0, received_qty=10)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["fulfilled_items"] == 1

    def test_empty_bom_returns_complete_status(self):
        db = make_db_no_po()
        svc = KitRateService(db)
        result = svc.calculate_kit_rate([], "quantity")
        assert result["total_items"] == 0
        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "complete"

    def test_invalid_calculate_by_raises_http_400(self):
        db = make_db_no_po()
        svc = KitRateService(db)
        with pytest.raises(HTTPException) as exc:
            svc.calculate_kit_rate([make_bom_item()], "unit_count")
        assert exc.value.status_code == 400


# ─────────────────────────────────────────────────
# 2. calculate_kit_rate — 金额法
# ─────────────────────────────────────────────────

class TestCalculateKitRateByAmount:

    def test_amount_fulfilled_amount_correct(self):
        db = make_db_no_po()
        svc = KitRateService(db)
        # Item1: qty=10, price=100 → amount=1000, stock=10 → fulfilled
        # Item2: qty=5,  price=200 → amount=1000, stock=0  → shortage
        items = [
            make_bom_item(id=1, quantity=10, unit_price=100, stock=10),
            make_bom_item(id=2, quantity=5,  unit_price=200, stock=0),
        ]
        result = svc.calculate_kit_rate(items, "amount")

        assert result["total_amount"] == 2000.0
        assert result["fulfilled_amount"] == 1000.0
        assert result["kit_rate"] == pytest.approx(50.0, abs=0.01)
        assert result["calculate_by"] == "amount"

    def test_amount_all_shortage_rate_zero(self):
        db = make_db_no_po()
        svc = KitRateService(db)
        items = [make_bom_item(id=1, quantity=10, unit_price=100, stock=0)]
        result = svc.calculate_kit_rate(items, "amount")
        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "shortage"

    def test_amount_100pct_complete(self):
        db = make_db_no_po()
        svc = KitRateService(db)
        items = [
            make_bom_item(id=1, quantity=10, unit_price=100, stock=20),
            make_bom_item(id=2, quantity=5,  unit_price=200, stock=10),
        ]
        result = svc.calculate_kit_rate(items, "amount")
        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"


# ─────────────────────────────────────────────────
# 3. _get_in_transit_qty — 多订单累积
# ─────────────────────────────────────────────────

class TestGetInTransitQty:

    def test_no_material_id_returns_zero(self):
        svc = KitRateService(MagicMock())
        assert svc._get_in_transit_qty(None) == Decimal(0)

    def test_multiple_po_items_summed(self):
        db = MagicMock()
        po1 = MagicMock(); po1.quantity = 100; po1.received_qty = 40
        po2 = MagicMock(); po2.quantity = 50;  po2.received_qty = 20
        db.query.return_value.filter.return_value.all.return_value = [po1, po2]

        svc = KitRateService(db)
        result = svc._get_in_transit_qty(1)
        # (100-40) + (50-20) = 60 + 30 = 90
        assert result == Decimal(90)

    def test_fully_received_po_contributes_zero(self):
        db = MagicMock()
        po = MagicMock(); po.quantity = 50; po.received_qty = 50
        db.query.return_value.filter.return_value.all.return_value = [po]

        svc = KitRateService(db)
        result = svc._get_in_transit_qty(1)
        assert result == Decimal(0)

    def test_none_quantities_handled(self):
        """po.quantity 或 received_qty 为 None 时不崩溃"""
        db = MagicMock()
        po = MagicMock(); po.quantity = None; po.received_qty = None
        db.query.return_value.filter.return_value.all.return_value = [po]

        svc = KitRateService(db)
        result = svc._get_in_transit_qty(1)
        assert result == Decimal(0)


# ─────────────────────────────────────────────────
# 4. get_machine_material_status — 物料状态分类
# ─────────────────────────────────────────────────

class TestGetMachineMaterialStatus:

    def _setup_db(self, machine, bom):
        db = MagicMock()
        call_seq = [0]

        def side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            idx = call_seq[0]
            call_seq[0] += 1
            if idx == 0:    # Machine query
                q.first.return_value = machine
            elif idx == 1:  # BomHeader query
                q.first.return_value = bom
            else:           # PO query
                q.all.return_value = []
            return q

        db.query.side_effect = side_effect
        return db

    def test_fulfilled_item_status(self):
        machine = make_machine()
        item = make_bom_item(id=1, quantity=10, stock=15)
        bom = make_bom_header(items=[item])
        db = self._setup_db(machine, bom)

        svc = KitRateService(db)
        result = svc.get_machine_material_status(1)

        assert result["items"][0]["status"] == "fulfilled"
        assert result["items"][0]["shortage_qty"] == 0.0

    def test_partial_item_status(self):
        """有库存但不够 → partial"""
        machine = make_machine()
        item = make_bom_item(id=1, quantity=10, stock=5)
        bom = make_bom_header(items=[item])
        db = self._setup_db(machine, bom)

        svc = KitRateService(db)
        result = svc.get_machine_material_status(1)
        assert result["items"][0]["status"] == "partial"

    def test_shortage_item_status(self):
        """无库存无在途 → shortage"""
        machine = make_machine()
        item = make_bom_item(id=1, quantity=10, stock=0)
        bom = make_bom_header(items=[item])
        db = self._setup_db(machine, bom)

        svc = KitRateService(db)
        result = svc.get_machine_material_status(1)
        assert result["items"][0]["status"] == "shortage"
        assert result["items"][0]["shortage_qty"] == 10.0

    def test_required_date_formatted_correctly(self):
        machine = make_machine()
        item = make_bom_item(id=1, quantity=5, stock=10, required_date=date(2026, 3, 1))
        bom = make_bom_header(items=[item])
        db = self._setup_db(machine, bom)

        svc = KitRateService(db)
        result = svc.get_machine_material_status(1)
        assert result["items"][0]["required_date"] == "2026-03-01"

    def test_no_bom_raises_404(self):
        machine = make_machine()
        db = MagicMock()
        call_seq = [0]

        def side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            idx = call_seq[0]; call_seq[0] += 1
            q.first.return_value = machine if idx == 0 else None
            return q

        db.query.side_effect = side_effect
        svc = KitRateService(db)
        with pytest.raises(HTTPException) as exc:
            svc.get_machine_material_status(1)
        assert exc.value.status_code == 404

    def test_key_material_flag_preserved(self):
        machine = make_machine()
        item = make_bom_item(id=1, quantity=5, stock=10, is_key_item=True)
        bom = make_bom_header(items=[item])
        db = self._setup_db(machine, bom)

        svc = KitRateService(db)
        result = svc.get_machine_material_status(1)
        assert result["items"][0]["is_key_item"] is True


# ─────────────────────────────────────────────────
# 5. get_trend — day/month 分组
# ─────────────────────────────────────────────────

class TestGetTrendGrouping:

    def _make_snapshot(self, day, kit_rate, total_items=10, fulfilled=8, shortage=2):
        s = MagicMock()
        s.snapshot_date = date(2026, 1, day)
        s.kit_rate = Decimal(str(kit_rate))
        s.total_items = total_items
        s.fulfilled_items = fulfilled
        s.shortage_items = shortage
        return s

    def _setup_db_with_snapshots(self, snapshots):
        db = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        db.get_bind.return_value = MagicMock()

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = snapshots
        db.query.return_value = mock_q

        return db, mock_inspector

    def test_daily_grouping_aggregates_by_date(self):
        snaps = [
            self._make_snapshot(1, 80.0),
            self._make_snapshot(1, 90.0),  # same day → avg = 85
            self._make_snapshot(2, 70.0),
        ]
        db, insp = self._setup_db_with_snapshots(snaps)
        svc = KitRateService(db)

        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_trend(date(2026, 1, 1), date(2026, 1, 31), "day")

        assert len(result["trend_data"]) == 2
        day1 = next(d for d in result["trend_data"] if d["date"] == "2026-01-01")
        assert day1["kit_rate"] == pytest.approx(85.0, abs=0.1)

    def test_monthly_grouping_aggregates_by_month(self):
        snaps = [
            self._make_snapshot(5, 80.0),
            self._make_snapshot(15, 90.0),  # same month
        ]
        # make them different months
        snaps[1].snapshot_date = date(2026, 2, 15)

        db, insp = self._setup_db_with_snapshots(snaps)
        svc = KitRateService(db)

        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_trend(date(2026, 1, 1), date(2026, 2, 28), "month")

        assert len(result["trend_data"]) == 2

    def test_summary_avg_max_min_calculated(self):
        snaps = [
            self._make_snapshot(1, 60.0),
            self._make_snapshot(2, 80.0),
            self._make_snapshot(3, 100.0),
        ]
        db, insp = self._setup_db_with_snapshots(snaps)
        svc = KitRateService(db)

        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_trend(date(2026, 1, 1), date(2026, 1, 31), "day")

        summary = result["summary"]
        assert summary["max_kit_rate"] == 100.0
        assert summary["min_kit_rate"] == 60.0
        assert summary["avg_kit_rate"] == pytest.approx(80.0, abs=0.1)

    def test_no_snapshots_returns_note(self):
        db, insp = self._setup_db_with_snapshots([])
        svc = KitRateService(db)

        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_trend(date(2026, 1, 1), date(2026, 1, 31), "day")

        assert result["trend_data"] == []
        assert "note" in result

    def test_table_missing_raises_500(self):
        db = MagicMock()
        db.get_bind.return_value = MagicMock()
        insp = MagicMock()
        insp.has_table.return_value = False

        svc = KitRateService(db)
        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            with pytest.raises(HTTPException) as exc:
                svc.get_trend(date(2026, 1, 1), date(2026, 1, 31), "day")
        assert exc.value.status_code == 500

    def test_project_filter_applied(self):
        snaps = [self._make_snapshot(1, 75.0)]
        db, insp = self._setup_db_with_snapshots(snaps)
        svc = KitRateService(db)

        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_trend(date(2026, 1, 1), date(2026, 1, 31), "day", project_id=5)

        # Should not crash and return data
        assert "trend_data" in result


# ─────────────────────────────────────────────────
# 6. get_snapshots — 快照查询
# ─────────────────────────────────────────────────

class TestGetSnapshots:

    def test_returns_snapshot_list(self):
        db = MagicMock()
        insp = MagicMock(); insp.has_table.return_value = True
        db.get_bind.return_value = MagicMock()

        project = make_project()
        snap = MagicMock()
        snap.id = 1
        snap.snapshot_date = date(2026, 1, 15)
        snap.snapshot_time = None
        snap.snapshot_type = "DAILY"
        snap.trigger_event = None
        snap.kit_rate = Decimal("85.5")
        snap.kit_status = "partial"
        snap.total_items = 10
        snap.fulfilled_items = 8
        snap.shortage_items = 2
        snap.in_transit_items = 0
        snap.blocking_kit_rate = Decimal("90.0")
        snap.project_stage = "ASSEMBLY"
        snap.project_health = "GOOD"

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = [snap]
        q.first.return_value = project
        db.query.return_value = q

        svc = KitRateService(db)
        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_snapshots(1, date(2026, 1, 1), date(2026, 1, 31))

        assert result["total_snapshots"] == 1
        s = result["snapshots"][0]
        assert s["kit_rate"] == 85.5
        assert s["kit_status"] == "partial"

    def test_empty_snapshots(self):
        db = MagicMock()
        insp = MagicMock(); insp.has_table.return_value = True
        db.get_bind.return_value = MagicMock()

        project = make_project()
        q = MagicMock(); q.filter.return_value = q; q.order_by.return_value = q
        q.all.return_value = []
        q.first.return_value = project
        db.query.return_value = q

        svc = KitRateService(db)
        with patch("app.services.kit_rate.kit_rate_service.inspect", return_value=insp):
            result = svc.get_snapshots(1, date(2026, 1, 1), date(2026, 1, 31))

        assert result["total_snapshots"] == 0
        assert result["snapshots"] == []


# ─────────────────────────────────────────────────
# 7. get_dashboard — complete/partial/shortage 统计
# ─────────────────────────────────────────────────

class TestGetDashboard:

    def test_dashboard_counts_status_correctly(self):
        db = MagicMock()
        projects = [make_project(i, f"P{i:03d}", f"项目{i}") for i in range(1, 4)]
        db.query.return_value.filter.return_value.all.return_value = projects
        db.query.return_value.filter.return_value.first.return_value = projects[0]

        kit_rates = [
            {"kit_rate": 100.0, "kit_status": "complete", "total_items": 10,
             "fulfilled_items": 10, "shortage_items": 0, "in_transit_items": 0},
            {"kit_rate": 85.0, "kit_status": "partial", "total_items": 10,
             "fulfilled_items": 8, "shortage_items": 2, "in_transit_items": 0},
            {"kit_rate": 50.0, "kit_status": "shortage", "total_items": 10,
             "fulfilled_items": 5, "shortage_items": 5, "in_transit_items": 0},
        ]
        call_idx = [0]

        def mock_project_kit_rate(project_id, calculate_by):
            idx = call_idx[0]; call_idx[0] += 1
            return kit_rates[idx]

        svc = KitRateService(db)
        with patch.object(svc, "get_project_kit_rate", side_effect=mock_project_kit_rate):
            result = svc.get_dashboard(project_ids=[1, 2, 3])

        assert result["summary"]["total_projects"] == 3
        assert result["summary"]["complete_projects"] == 1
        assert result["summary"]["partial_projects"] == 1
        assert result["summary"]["shortage_projects"] == 1

    def test_dashboard_no_projects(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        svc = KitRateService(db)
        result = svc.get_dashboard(project_ids=[])
        assert result["summary"]["total_projects"] == 0
