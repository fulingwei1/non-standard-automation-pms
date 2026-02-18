# -*- coding: utf-8 -*-
"""第二十八批 - quote (审批适配器) 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.approval_engine.adapters.quote")

from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_quote(
    quote_id=1,
    quote_code="Q-2024-001",
    status="DRAFT",
    customer_name="测试客户",
    owner_name="销售甲",
    version=None,
):
    q = MagicMock()
    q.id = quote_id
    q.quote_code = quote_code
    q.status = status

    customer = MagicMock()
    customer.name = customer_name
    q.customer = customer
    q.customer_id = 10

    owner = MagicMock()
    owner.name = owner_name
    q.owner = owner
    q.owner_id = 5

    q.current_version = version
    return q


def _make_version(
    version_id=1,
    version_no=1,
    total_price=Decimal("500000"),
    cost_total=Decimal("300000"),
    gross_margin=Decimal("0.4"),
    lead_time_days=30,
):
    v = MagicMock()
    v.id = version_id
    v.version_no = version_no
    v.total_price = total_price
    v.cost_total = cost_total
    v.gross_margin = gross_margin
    v.lead_time_days = lead_time_days
    v.delivery_date = None
    return v


def _make_adapter(db=None):
    if db is None:
        db = MagicMock()
    return QuoteApprovalAdapter(db)


# ─── get_entity ──────────────────────────────────────────────

class TestGetEntity:

    def test_returns_quote_when_found(self):
        db = MagicMock()
        quote = _make_quote()
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        result = adapter.get_entity(1)
        assert result is quote

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        adapter = _make_adapter(db)
        result = adapter.get_entity(999)
        assert result is None


# ─── get_entity_data ─────────────────────────────────────────

class TestGetEntityData:

    def test_returns_empty_dict_when_quote_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        adapter = _make_adapter(db)
        result = adapter.get_entity_data(999)
        assert result == {}

    def test_includes_quote_code_and_status(self):
        db = MagicMock()
        version = _make_version()
        quote = _make_quote(version=version)
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        result = adapter.get_entity_data(1)
        assert result["quote_code"] == "Q-2024-001"
        assert result["status"] == "DRAFT"

    def test_gross_margin_converted_to_percentage(self):
        """毛利率 <= 1 时应乘以 100 转为百分比"""
        db = MagicMock()
        version = _make_version(gross_margin=Decimal("0.4"))
        quote = _make_quote(version=version)
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        result = adapter.get_entity_data(1)
        assert abs(result["gross_margin"] - 40.0) < 0.01

    def test_gross_margin_not_doubled_when_already_percentage(self):
        """毛利率 > 1 时直接使用（已是百分比形式）"""
        db = MagicMock()
        version = _make_version(gross_margin=Decimal("40"))
        quote = _make_quote(version=version)
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        result = adapter.get_entity_data(1)
        assert abs(result["gross_margin"] - 40.0) < 0.01

    def test_total_price_returned_as_float(self):
        db = MagicMock()
        version = _make_version(total_price=Decimal("1234567.89"))
        quote = _make_quote(version=version)
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        result = adapter.get_entity_data(1)
        assert isinstance(result["total_price"], float)
        assert abs(result["total_price"] - 1234567.89) < 0.01


# ─── 状态回调 ─────────────────────────────────────────────────

class TestStatusCallbacks:

    def test_on_submit_sets_pending_approval(self):
        db = MagicMock()
        quote = _make_quote(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        instance = MagicMock()
        adapter.on_submit(entity_id=1, instance=instance)

        assert quote.status == "PENDING_APPROVAL"
        db.flush.assert_called_once()

    def test_on_approved_sets_approved(self):
        db = MagicMock()
        quote = _make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        adapter.on_approved(entity_id=1, instance=MagicMock())
        assert quote.status == "APPROVED"

    def test_on_rejected_sets_rejected(self):
        db = MagicMock()
        quote = _make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        adapter.on_rejected(entity_id=1, instance=MagicMock())
        assert quote.status == "REJECTED"

    def test_on_withdrawn_sets_draft(self):
        db = MagicMock()
        quote = _make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        adapter.on_withdrawn(entity_id=1, instance=MagicMock())
        assert quote.status == "DRAFT"

    def test_callback_does_nothing_when_quote_not_found(self):
        """找不到报价时回调应静默处理"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        adapter = _make_adapter(db)
        # Should not raise
        adapter.on_submit(entity_id=999, instance=MagicMock())
        adapter.on_approved(entity_id=999, instance=MagicMock())


# ─── get_title / get_summary ─────────────────────────────────

class TestGetTitleAndSummary:

    def test_get_title_includes_quote_code(self):
        db = MagicMock()
        quote = _make_quote(quote_code="Q-9999", customer_name="大客户")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        title = adapter.get_title(1)
        assert "Q-9999" in title
        assert "大客户" in title

    def test_get_title_fallback_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        adapter = _make_adapter(db)
        title = adapter.get_title(42)
        assert "42" in title

    def test_get_summary_includes_total_price(self):
        db = MagicMock()
        version = _make_version(total_price=Decimal("888000"))
        quote = _make_quote(version=version, customer_name="客户A")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        summary = adapter.get_summary(1)
        assert "888" in summary  # 金额在摘要中

    def test_get_summary_empty_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        adapter = _make_adapter(db)
        summary = adapter.get_summary(99)
        assert summary == ""


# ─── validate_submit ─────────────────────────────────────────

class TestValidateSubmit:

    def test_fails_when_quote_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        adapter = _make_adapter(db)
        ok, msg = adapter.validate_submit(999)
        assert ok is False
        assert "不存在" in msg

    def test_fails_when_status_not_draft_or_rejected(self):
        db = MagicMock()
        quote = _make_quote(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        ok, msg = adapter.validate_submit(1)
        assert ok is False
        assert "PENDING_APPROVAL" in msg

    def test_passes_for_draft_status(self):
        db = MagicMock()
        version = _make_version()
        quote = _make_quote(status="DRAFT", version=version)
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        ok, msg = adapter.validate_submit(1)
        assert ok is True
        assert msg == ""

    def test_passes_for_rejected_status(self):
        db = MagicMock()
        version = _make_version()
        quote = _make_quote(status="REJECTED", version=version)
        db.query.return_value.filter.return_value.first.return_value = quote

        adapter = _make_adapter(db)
        ok, msg = adapter.validate_submit(1)
        assert ok is True
