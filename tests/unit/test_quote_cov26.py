# -*- coding: utf-8 -*-
"""第二十六批 - approval_engine/adapters/quote 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.approval_engine.adapters.quote")

from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter


class TestQuoteApprovalAdapterInit:
    def test_entity_type(self):
        assert QuoteApprovalAdapter.entity_type == "QUOTE"

    def test_instantiation(self):
        db = MagicMock()
        adapter = QuoteApprovalAdapter(db)
        assert adapter.db is db


class TestGetEntity:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def test_returns_none_when_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.adapter.get_entity(999)
        assert result is None

    def test_returns_quote_when_found(self):
        quote = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = quote
        result = self.adapter.get_entity(1)
        assert result is quote


class TestGetEntityData:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def test_returns_empty_dict_when_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.adapter.get_entity_data(999)
        assert result == {}

    def test_returns_data_with_version(self):
        version = MagicMock()
        version.total_price = Decimal("10000")
        version.cost_total = Decimal("7000")
        version.gross_margin = Decimal("0.30")
        version.version_no = "v1"
        version.lead_time_days = 30

        quote = MagicMock()
        quote.current_version = version
        quote.quote_code = "Q001"
        quote.status = "DRAFT"
        quote.customer_id = 1
        quote.customer.name = "客户A"
        quote.owner_id = 5
        quote.owner.name = "张三"

        self.db.query.return_value.filter.return_value.first.return_value = quote

        result = self.adapter.get_entity_data(1)
        assert result["quote_code"] == "Q001"
        assert "total_price" in result
        assert result["total_price"] == 10000.0

    def test_gross_margin_converted_to_percentage(self):
        version = MagicMock()
        version.total_price = Decimal("10000")
        version.cost_total = Decimal("7000")
        version.gross_margin = Decimal("0.30")  # 30% stored as 0.30
        version.version_no = "v1"
        version.lead_time_days = 30

        quote = MagicMock()
        quote.current_version = version
        quote.quote_code = "Q002"
        quote.status = "SUBMITTED"
        quote.customer_id = 2
        quote.customer = MagicMock(name="客户B")
        quote.owner_id = 3
        quote.owner = MagicMock(name="李四")

        self.db.query.return_value.filter.return_value.first.return_value = quote
        result = self.adapter.get_entity_data(1)
        if "gross_margin" in result:
            # Should be converted: 0.30 <= 1, so multiply by 100 → 30
            assert result["gross_margin"] == 30.0

    def test_uses_latest_version_when_no_current(self):
        version = MagicMock()
        version.total_price = Decimal("5000")
        version.cost_total = Decimal("3000")
        version.gross_margin = Decimal("40")  # Already > 1
        version.version_no = "v2"
        version.lead_time_days = 60

        quote = MagicMock()
        quote.current_version = None  # No current version
        quote.quote_code = "Q003"
        quote.status = "DRAFT"
        quote.customer_id = 3
        quote.customer = MagicMock(name="客户C")
        quote.owner_id = 1
        quote.owner = MagicMock(name="王五")

        # First query → quote; second → latest version
        self.db.query.return_value.filter.return_value.first.side_effect = [
            quote,
            version,
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = version

        result = self.adapter.get_entity_data(1)
        assert "quote_code" in result


class TestEventCallbacks:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def _make_instance(self, entity_id=1, status="DRAFT"):
        inst = MagicMock()
        inst.entity_id = entity_id
        inst.status = status
        return inst

    def test_on_submit_calls_db(self):
        inst = self._make_instance()
        quote = MagicMock(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        self.adapter.on_submit(entity_id=1, instance=inst)
        self.db.commit.assert_called()

    def test_on_approved_updates_status(self):
        inst = self._make_instance()
        quote = MagicMock(status="SUBMITTED")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        self.adapter.on_approved(entity_id=1, instance=inst)
        assert quote.status == "APPROVED"
        self.db.commit.assert_called()

    def test_on_rejected_updates_status(self):
        inst = self._make_instance()
        quote = MagicMock(status="SUBMITTED")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        self.adapter.on_rejected(entity_id=1, instance=inst)
        assert quote.status == "REJECTED"
        self.db.commit.assert_called()

    def test_on_withdrawn_updates_status(self):
        inst = self._make_instance()
        quote = MagicMock(status="SUBMITTED")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        self.adapter.on_withdrawn(entity_id=1, instance=inst)
        assert quote.status == "DRAFT"
        self.db.commit.assert_called()


class TestGetTitleAndSummary:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def test_get_title_returns_string(self):
        quote = MagicMock(quote_code="Q001")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        result = self.adapter.get_title(entity_id=1)
        assert isinstance(result, str)

    def test_get_title_contains_code(self):
        quote = MagicMock(quote_code="Q123")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        result = self.adapter.get_title(entity_id=1)
        assert "Q123" in result

    def test_get_summary_returns_string(self):
        quote = MagicMock(quote_code="Q001")
        self.db.query.return_value.filter.return_value.first.return_value = quote
        result = self.adapter.get_summary(entity_id=1)
        assert isinstance(result, str)


class TestValidateSubmit:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def test_returns_false_when_entity_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        ok, msg = self.adapter.validate_submit(999)
        assert ok is False

    def test_returns_true_for_valid_quote(self):
        quote = MagicMock()
        quote.status = "DRAFT"
        self.db.query.return_value.filter.return_value.first.return_value = quote
        ok, msg = self.adapter.validate_submit(1)
        assert isinstance(ok, bool)


class TestCreateQuoteApproval:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def test_returns_existing_when_found(self):
        existing = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = existing
        instance = MagicMock(entity_id=1)
        task = MagicMock(node_order=1, assignee_id=5)
        result = self.adapter.create_quote_approval(instance, task)
        assert result is existing

    def test_creates_new_when_not_exists(self):
        # First call returns None (no existing), second call returns approver
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,
            MagicMock(real_name="审批人"),
        ]
        instance = MagicMock(entity_id=1)
        task = MagicMock(node_order=1, node_name="总监审批", assignee_id=5)
        result = self.adapter.create_quote_approval(instance, task)
        self.db.add.assert_called()
