# -*- coding: utf-8 -*-
"""
第十四批：验收单审批适配器 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

try:
    from app.services.approval_engine.adapters.acceptance import AcceptanceOrderApprovalAdapter
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_order(**kwargs):
    order = MagicMock()
    order.id = 1
    order.order_no = "ACC-2025-001"
    order.acceptance_type = kwargs.get("acceptance_type", "FAT")
    order.status = kwargs.get("status", "DRAFT")
    order.overall_result = kwargs.get("overall_result", "PASSED")
    order.pass_rate = kwargs.get("pass_rate", 98.5)
    order.total_items = kwargs.get("total_items", 20)
    order.passed_items = kwargs.get("passed_items", 20)
    order.failed_items = kwargs.get("failed_items", 0)
    order.na_items = kwargs.get("na_items", 0)
    order.project_id = kwargs.get("project_id", 10)
    order.machine_id = kwargs.get("machine_id", None)
    order.template_id = kwargs.get("template_id", None)
    order.created_by = 1
    order.planned_date = None
    order.actual_start_date = None
    order.actual_end_date = None
    order.location = "上海"
    order.conclusion = "通过"
    order.conditions = kwargs.get("conditions", None)
    order.is_officially_completed = kwargs.get("is_officially_completed", False)
    order.officially_completed_at = None
    return order


class TestAcceptanceOrderApprovalAdapter:
    def _adapter(self, db=None):
        db = db or make_db()
        return AcceptanceOrderApprovalAdapter(db)

    def test_entity_type(self):
        assert AcceptanceOrderApprovalAdapter.entity_type == "ACCEPTANCE_ORDER"

    def test_get_entity(self):
        db = make_db()
        order = make_order()
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        result = adapter.get_entity(1)
        assert result is order

    def test_on_submit_sets_pending(self):
        db = make_db()
        order = make_order(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        adapter.on_submit(1, MagicMock())
        assert order.status == "PENDING_APPROVAL"
        db.flush.assert_called()

    def test_on_approved_fat_passed(self):
        db = make_db()
        order = make_order(acceptance_type="FAT", overall_result="PASSED")
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        adapter.on_approved(1, MagicMock())
        assert order.status == "COMPLETED"

    def test_on_approved_final_passed_sets_official(self):
        db = make_db()
        order = make_order(acceptance_type="FINAL", overall_result="PASSED")
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        adapter.on_approved(1, MagicMock())
        assert order.status == "COMPLETED"
        assert order.is_officially_completed is True

    def test_on_rejected(self):
        db = make_db()
        order = make_order()
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        adapter.on_rejected(1, MagicMock())
        assert order.status == "REJECTED"

    def test_on_withdrawn(self):
        db = make_db()
        order = make_order()
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        adapter.on_withdrawn(1, MagicMock())
        assert order.status == "DRAFT"

    def test_generate_title_fat(self):
        db = make_db()
        order = make_order(acceptance_type="FAT", overall_result="PASSED")
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        title = adapter.generate_title(1)
        assert "出厂验收" in title
        assert "ACC-2025-001" in title

    def test_validate_submit_missing_project(self):
        db = make_db()
        order = make_order(project_id=None, status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        ok, msg = adapter.validate_submit(1)
        assert not ok
        assert "项目" in msg

    def test_validate_submit_unchecked_items(self):
        db = make_db()
        order = make_order(
            total_items=10, passed_items=5, failed_items=0, na_items=0,
            overall_result="PASSED", status="DRAFT"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        adapter = self._adapter(db)
        ok, msg = adapter.validate_submit(1)
        assert not ok
        assert "未检查" in msg
