# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：齐套率快照 (kit_rate_tasks.py)
J2组覆盖率提升
"""
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def _make_db():
    return MagicMock()


# ================================================================
#  _calculate_kit_rate_for_bom_items (纯逻辑函数)
# ================================================================

class TestCalculateKitRateForBomItems:

    def test_empty_bom_returns_zero(self):
        """BOM 为空 → kit_rate=0, kit_status=shortage"""
        db = _make_db()

        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items
        result = _calculate_kit_rate_for_bom_items(db, [])

        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "shortage"
        assert result["total_items"] == 0

    def test_all_items_fulfilled(self):
        """所有物料库存充足 → kit_rate=100, complete"""
        db = _make_db()

        item = MagicMock()
        item.quantity = 10
        item.received_qty = 5
        item.unit_price = 100
        item.material = MagicMock()
        item.material.current_stock = 10   # stock >= required
        item.material_id = 1

        # 无在途订单
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items
        result = _calculate_kit_rate_for_bom_items(db, [item])

        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"
        assert result["fulfilled_items"] == 1
        assert result["shortage_items"] == 0

    def test_partial_fulfillment(self):
        """部分物料不足 → partial 状态（80~100%）"""
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        item1 = MagicMock()
        item1.quantity = 10
        item1.received_qty = 5
        item1.unit_price = 50
        item1.material = MagicMock()
        item1.material.current_stock = 10  # 足够
        item1.material_id = 1

        item2 = MagicMock()
        item2.quantity = 10
        item2.received_qty = 0
        item2.unit_price = 50
        item2.material = MagicMock()
        item2.material.current_stock = 0   # 不足
        item2.material_id = 2

        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items
        result = _calculate_kit_rate_for_bom_items(db, [item1, item2])

        assert result["total_items"] == 2
        assert result["fulfilled_items"] == 1
        assert result["shortage_items"] == 1
        assert result["kit_rate"] == 50.0
        assert result["kit_status"] == "shortage"

    def test_in_transit_items_counted(self):
        """有在途订单时 transit_qty 被计入"""
        db = _make_db()

        item = MagicMock()
        item.quantity = 10
        item.received_qty = 0
        item.unit_price = 100
        item.material = MagicMock()
        item.material.current_stock = 0
        item.material_id = 5

        # 在途订单补足需求
        po_item = MagicMock()
        po_item.quantity = 10
        po_item.received_qty = 0
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [po_item]

        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items
        result = _calculate_kit_rate_for_bom_items(db, [item])

        assert result["in_transit_items"] == 1
        assert result["kit_rate"] == 100.0

    def test_calculate_by_amount(self):
        """按金额计算时使用 shortage_amount"""
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        item = MagicMock()
        item.quantity = 10
        item.received_qty = 0
        item.unit_price = 100
        item.material = MagicMock()
        item.material.current_stock = 5   # 只有一半
        item.material_id = 6

        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items
        result = _calculate_kit_rate_for_bom_items(db, [item], calculate_by="amount")

        # total_amount=1000, shortage_amount=500 → kit_rate=50%
        assert result["kit_rate"] == 50.0
        assert result["kit_status"] == "shortage"

    def test_item_without_material(self):
        """BOM 物料无 material 对象时不报错"""
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        item = MagicMock()
        item.quantity = 5
        item.received_qty = 0
        item.unit_price = 200
        item.material = None   # 没有 material
        item.material_id = None

        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items
        result = _calculate_kit_rate_for_bom_items(db, [item])

        # 库存为0，shortage
        assert result["shortage_items"] == 1


# ================================================================
#  create_kit_rate_snapshot
# ================================================================

class TestCreateKitRateSnapshot:

    @patch("app.utils.scheduled_tasks.kit_rate_tasks._calculate_kit_rate_for_bom_items")
    def test_project_not_found_returns_none(self, mock_calc):
        """项目不存在 → 返回 None"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        from app.utils.scheduled_tasks.kit_rate_tasks import create_kit_rate_snapshot
        result = create_kit_rate_snapshot(db, project_id=999)

        assert result is None
        mock_calc.assert_not_called()

    @patch("app.utils.scheduled_tasks.kit_rate_tasks._calculate_kit_rate_for_bom_items")
    def test_daily_snapshot_already_exists(self, mock_calc):
        """今日 DAILY 快照已存在 → 直接返回现有快照"""
        db = _make_db()
        project = MagicMock(id=1, project_code="P001", stage="S3", health="GREEN")
        existing_snapshot = MagicMock(id=5)

        call_count = 0

        def first_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return project     # Project query
            return existing_snapshot  # KitRateSnapshot query

        db.query.return_value.filter.return_value.first.side_effect = first_side_effect

        from app.utils.scheduled_tasks.kit_rate_tasks import create_kit_rate_snapshot
        result = create_kit_rate_snapshot(db, project_id=1, snapshot_type="DAILY")

        assert result == existing_snapshot
        mock_calc.assert_not_called()

    @patch("app.utils.scheduled_tasks.kit_rate_tasks._calculate_kit_rate_for_bom_items")
    def test_creates_new_snapshot(self, mock_calc):
        """无现有快照 → 创建新快照并 add/flush"""
        mock_calc.return_value = {
            "kit_rate": 85.0,
            "kit_status": "partial",
            "total_items": 10,
            "fulfilled_items": 8,
            "shortage_items": 2,
            "in_transit_items": 1,
            "total_amount": 50000.0,
            "shortage_amount": 5000.0,
        }

        db = _make_db()
        project = MagicMock(id=1, project_code="P002", stage="S2", health="YELLOW")
        machine = MagicMock(id=10)

        bom = MagicMock()
        bom_items = MagicMock()
        bom_items.all.return_value = [MagicMock()]
        bom.items = bom_items

        query_returns = {
            "Project": project,
            "KitRateSnapshot": None,  # 不存在现有快照
        }

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Project" in name:
                m.filter.return_value.first.return_value = project
                m.filter.return_value.filter.return_value.all.return_value = []
            elif "KitRateSnapshot" in name:
                # 代码使用单次 filter: .filter(cond1, cond2, cond3).first()
                m.filter.return_value.first.return_value = None
            elif "Machine" in name:
                m.filter.return_value.all.return_value = [machine]
            elif "BomHeader" in name:
                m.filter.return_value.filter.return_value.first.return_value = bom
            return m

        db.query.side_effect = q

        from app.utils.scheduled_tasks.kit_rate_tasks import create_kit_rate_snapshot
        result = create_kit_rate_snapshot(db, project_id=1, snapshot_type="MANUAL")

        assert db.add.called
        assert db.flush.called

    @patch("app.utils.scheduled_tasks.kit_rate_tasks._calculate_kit_rate_for_bom_items")
    def test_exception_returns_none(self, mock_calc):
        """创建快照异常 → 返回 None"""
        mock_calc.side_effect = Exception("计算失败")

        db = _make_db()
        project = MagicMock(id=1, project_code="P003", stage="S1", health="RED")

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Project" in name:
                m.filter.return_value.first.return_value = project
            elif "KitRateSnapshot" in name:
                # 代码: db.query(KitRateSnapshot).filter(cond1, cond2, cond3).first()  → 单次filter
                m.filter.return_value.first.return_value = None
            elif "Machine" in name:
                m.filter.return_value.all.return_value = [MagicMock(id=1)]
            elif "BomHeader" in name:
                bom = MagicMock()
                bom.items.all.return_value = []
                m.filter.return_value.filter.return_value.first.return_value = bom
            return m

        db.query.side_effect = q

        from app.utils.scheduled_tasks.kit_rate_tasks import create_kit_rate_snapshot
        result = create_kit_rate_snapshot(db, project_id=1, snapshot_type="DAILY")

        assert result is None


# ================================================================
#  daily_kit_rate_snapshot
# ================================================================

class TestDailyKitRateSnapshot:

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.kit_rate_tasks.create_kit_rate_snapshot")
    def test_no_active_projects(self, mock_create, mock_db_ctx):
        """无活跃项目 → created=0"""
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot
        result = daily_kit_rate_snapshot()

        assert result["success"] is True
        assert result["created"] == 0
        mock_create.assert_not_called()

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.kit_rate_tasks.create_kit_rate_snapshot")
    def test_creates_snapshots_for_active_projects(self, mock_create, mock_db_ctx):
        """有活跃项目 → 为每个项目调用 create_kit_rate_snapshot"""
        db = _make_db()
        p1 = MagicMock(id=1, project_code="P001")
        p2 = MagicMock(id=2, project_code="P002")
        db.query.return_value.filter.return_value.all.return_value = [p1, p2]

        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        # 新快照返回有 id 的对象
        new_snap = MagicMock()
        new_snap.id = 10
        mock_create.return_value = new_snap

        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot
        result = daily_kit_rate_snapshot()

        assert result["success"] is True
        assert mock_create.call_count == 2
        assert result["created"] == 2

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.kit_rate_tasks.create_kit_rate_snapshot")
    def test_snapshot_returns_none_counted_as_error(self, mock_create, mock_db_ctx):
        """create_kit_rate_snapshot 返回 None → 计入 error_count"""
        db = _make_db()
        p1 = MagicMock(id=1, project_code="P001")
        db.query.return_value.filter.return_value.all.return_value = [p1]
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_create.return_value = None

        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot
        result = daily_kit_rate_snapshot()

        assert result["errors"] == 1

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.kit_rate_tasks.create_kit_rate_snapshot")
    def test_project_exception_counted_as_error(self, mock_create, mock_db_ctx):
        """单个项目抛异常 → 计入 error，不影响整体"""
        db = _make_db()
        p1 = MagicMock(id=1, project_code="P001")
        db.query.return_value.filter.return_value.all.return_value = [p1]
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_create.side_effect = Exception("单项目失败")

        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot
        result = daily_kit_rate_snapshot()

        assert result["success"] is True
        assert result["errors"] == 1

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.get_db_session")
    def test_session_exception_returns_failure(self, mock_db_ctx):
        """整体 session 异常 → 返回 success=False"""
        mock_db_ctx.return_value.__enter__.side_effect = Exception("session 失败")

        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot
        result = daily_kit_rate_snapshot()

        assert result["success"] is False
        assert "error" in result


# ================================================================
#  create_stage_change_snapshot
# ================================================================

class TestCreateStageChangeSnapshot:

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.create_kit_rate_snapshot")
    def test_delegates_to_create_snapshot(self, mock_create):
        """调用 create_kit_rate_snapshot 并传入正确的 trigger_event"""
        db = _make_db()
        mock_create.return_value = MagicMock(id=1)

        from app.utils.scheduled_tasks.kit_rate_tasks import create_stage_change_snapshot
        result = create_stage_change_snapshot(db, project_id=5, from_stage="S1", to_stage="S2")

        mock_create.assert_called_once_with(
            db=db,
            project_id=5,
            snapshot_type="STAGE_CHANGE",
            trigger_event="S1 -> S2",
        )

    @patch("app.utils.scheduled_tasks.kit_rate_tasks.create_kit_rate_snapshot")
    def test_returns_snapshot_object(self, mock_create):
        """返回快照对象"""
        db = _make_db()
        snap = MagicMock(id=99)
        mock_create.return_value = snap

        from app.utils.scheduled_tasks.kit_rate_tasks import create_stage_change_snapshot
        result = create_stage_change_snapshot(db, project_id=3, from_stage="S2", to_stage="S3")

        assert result == snap
