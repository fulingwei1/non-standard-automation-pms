# -*- coding: utf-8 -*-
"""第二十三批：customer_360_service 单元测试"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.customer_360_service")

from app.services.customer_360_service import Customer360Service, _decimal


class TestDecimalHelper:
    def test_none_returns_zero(self):
        assert _decimal(None) == Decimal("0")

    def test_int_converts(self):
        assert _decimal(100) == Decimal("100")

    def test_decimal_passthrough(self):
        assert _decimal(Decimal("3.14")) == Decimal("3.14")

    def test_string_converts(self):
        assert _decimal("99.5") == Decimal("99.5")

    def test_invalid_string_returns_zero(self):
        assert _decimal("abc") == Decimal("0")


def _make_db():
    return MagicMock()


def _mock_customer(cid=1, customer_name="测试客户"):
    c = MagicMock()
    c.id = cid
    c.customer_name = customer_name
    return c


class TestCustomer360ServiceBuildOverview:
    def test_customer_not_found_raises(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value.first.return_value = None
        db.query.return_value = q
        svc = Customer360Service(db)
        with pytest.raises(ValueError, match="客户不存在"):
            svc.build_overview(999)

    def test_returns_dict_with_summary(self):
        db = _make_db()
        customer = _mock_customer()

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            q.filter.return_value = q
            q.join.return_value = q
            q.order_by.return_value = q
            q.limit.return_value = q
            q.first.return_value = customer if call_count[0] == 1 else None
            q.all.return_value = []
            return q

        db.query.side_effect = query_side

        svc = Customer360Service(db)
        # build_overview will call _build_summary internally
        # Patch _build_summary to avoid deep model dependencies
        with patch.object(svc, "_build_summary", return_value={"total_contract": 0}) as mock_summary:
            result = svc.build_overview(1)
        mock_summary.assert_called_once()
        assert result is not None


class TestCustomer360ServiceInit:
    def test_init_stores_db(self):
        db = _make_db()
        svc = Customer360Service(db)
        assert svc.db is db
