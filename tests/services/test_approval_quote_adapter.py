# -*- coding: utf-8 -*-
"""QuoteApprovalAdapter 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestQuoteApprovalAdapter:

    def _make_adapter(self):
        from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
        db = MagicMock()
        return QuoteApprovalAdapter(db), db

    # -- get_entity --

    def test_get_entity(self):
        adapter, db = self._make_adapter()
        quote = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = quote
        assert adapter.get_entity(1) == quote

    def test_get_entity_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        assert adapter.get_entity(999) is None

    # -- get_entity_data --

    def test_get_entity_data_with_version(self):
        adapter, db = self._make_adapter()
        version = MagicMock(
            version_no="V1", total_price=Decimal("10000"),
            cost_total=Decimal("8000"), gross_margin=Decimal("0.2"),
            lead_time_days=30, delivery_date=None,
        )
        quote = MagicMock(
            id=1, quote_code="Q001", status="DRAFT",
            customer_id=1, owner_id=1,
            current_version=version,
        )
        quote.customer = MagicMock(name="客户A")
        quote.owner = MagicMock(name="张三")
        db.query.return_value.filter.return_value.first.return_value = quote

        data = adapter.get_entity_data(1)
        assert data["quote_code"] == "Q001"
        assert data["total_price"] == 10000.0
        assert data["gross_margin"] == 20.0  # 0.2 * 100

    def test_get_entity_data_margin_already_percent(self):
        adapter, db = self._make_adapter()
        version = MagicMock(
            version_no="V1", total_price=Decimal("10000"),
            cost_total=Decimal("8000"), gross_margin=Decimal("25"),
            lead_time_days=30, delivery_date=None,
        )
        quote = MagicMock(id=1, quote_code="Q001", status="DRAFT",
                          customer_id=1, owner_id=1, current_version=version)
        quote.customer = MagicMock(name="客户A")
        quote.owner = MagicMock(name="张三")
        db.query.return_value.filter.return_value.first.return_value = quote

        data = adapter.get_entity_data(1)
        assert data["gross_margin"] == 25.0  # already percent, kept as-is

    def test_get_entity_data_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        assert adapter.get_entity_data(999) == {}

    def test_get_entity_data_no_version_fallback(self):
        adapter, db = self._make_adapter()
        quote = MagicMock(id=1, quote_code="Q001", status="DRAFT",
                          customer_id=1, owner_id=1, current_version=None)
        quote.customer = MagicMock(name="客户A")
        quote.owner = MagicMock(name="张三")

        def query_side(model):
            m = MagicMock()
            m.filter.return_value.first.return_value = quote
            m.filter.return_value.order_by.return_value.first.return_value = None
            return m
        db.query.side_effect = query_side

        data = adapter.get_entity_data(1)
        assert "quote_code" in data
        assert "version_no" not in data

    # -- callbacks --

    def test_on_submit(self):
        adapter, db = self._make_adapter()
        quote = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = quote
        adapter.on_submit(1, MagicMock())
        assert quote.status == "PENDING_APPROVAL"

    def test_on_approved(self):
        adapter, db = self._make_adapter()
        quote = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = quote
        adapter.on_approved(1, MagicMock())
        assert quote.status == "APPROVED"

    def test_on_rejected(self):
        adapter, db = self._make_adapter()
        quote = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = quote
        adapter.on_rejected(1, MagicMock())
        assert quote.status == "REJECTED"

    def test_on_withdrawn(self):
        adapter, db = self._make_adapter()
        quote = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = quote
        adapter.on_withdrawn(1, MagicMock())
        assert quote.status == "DRAFT"

    def test_callbacks_entity_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        # Should not raise
        adapter.on_submit(999, MagicMock())
        adapter.on_approved(999, MagicMock())
        adapter.on_rejected(999, MagicMock())
        adapter.on_withdrawn(999, MagicMock())

    # -- get_title / get_summary --

    def test_get_title(self):
        adapter, db = self._make_adapter()
        quote = MagicMock(quote_code="Q001")
        quote.customer = MagicMock(name="客户A")
        db.query.return_value.filter.return_value.first.return_value = quote
        title = adapter.get_title(1)
        assert "Q001" in title
        assert "客户A" in title

    def test_get_title_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        assert "#1" in adapter.get_title(1)

    def test_get_summary(self):
        adapter, db = self._make_adapter()
        with patch.object(adapter, 'get_entity_data', return_value={
            "customer_name": "客户", "total_price": 10000, "gross_margin": 20.0, "lead_time_days": 30,
        }):
            s = adapter.get_summary(1)
        assert "客户" in s
        assert "10,000" in s

    def test_get_summary_empty(self):
        adapter, db = self._make_adapter()
        with patch.object(adapter, 'get_entity_data', return_value={}):
            assert adapter.get_summary(1) == ""

    # -- validate_submit --

    def test_validate_submit_success(self):
        adapter, db = self._make_adapter()
        quote = MagicMock(status="DRAFT", current_version=MagicMock())
        db.query.return_value.filter.return_value.first.return_value = quote
        ok, msg = adapter.validate_submit(1)
        assert ok is True

    def test_validate_submit_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        ok, msg = adapter.validate_submit(1)
        assert ok is False
        assert "不存在" in msg

    def test_validate_submit_wrong_status(self):
        adapter, db = self._make_adapter()
        quote = MagicMock(status="APPROVED", current_version=MagicMock())
        db.query.return_value.filter.return_value.first.return_value = quote
        ok, msg = adapter.validate_submit(1)
        assert ok is False

    def test_validate_submit_no_version(self):
        adapter, db = self._make_adapter()
        quote = MagicMock(status="DRAFT", current_version=None)
        db.query.return_value.filter.return_value.first.return_value = quote
        db.query.return_value.filter.return_value.count.return_value = 0
        ok, msg = adapter.validate_submit(1)
        assert ok is False
        assert "版本" in msg
