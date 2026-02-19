# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - sales/quotes_service.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.sales.quotes_service", reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.sales.quotes_service import QuotesService
    return QuotesService(mock_db)


def _make_quote(quote_id=1, status="draft"):
    q = MagicMock()
    q.id = quote_id
    q.quote_code = f"QT202401010001"
    q.opportunity_id = 10
    q.customer_id = 5
    q.status = status
    q.valid_until = date(2024, 12, 31)
    q.owner_id = 1
    q.customer = MagicMock(customer_name="客户A")
    q.owner = MagicMock(real_name="张三")
    q.created_at = date(2024, 1, 1)
    q.updated_at = date(2024, 1, 2)
    return q


class TestQuotesServiceGetQuotes:

    def test_get_quotes_returns_paginated(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [_make_quote()]

        with patch("app.services.sales.quotes_service.apply_keyword_filter",
                   return_value=mock_query), \
             patch("app.services.sales.quotes_service.apply_pagination",
                   return_value=mock_query), \
             patch("app.services.sales.quotes_service.get_pagination_params") as mock_pp:
            mock_pagination = MagicMock()
            mock_pagination.page = 1
            mock_pagination.page_size = 20
            mock_pagination.offset = 0
            mock_pagination.limit = 20
            mock_pagination.pages_for_total.return_value = 1
            mock_pp.return_value = mock_pagination

            result = service.get_quotes(page=1, page_size=20)
            assert result.total == 1

    def test_get_quotes_with_status_filter(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        with patch("app.services.sales.quotes_service.apply_keyword_filter",
                   return_value=mock_query), \
             patch("app.services.sales.quotes_service.apply_pagination",
                   return_value=mock_query), \
             patch("app.services.sales.quotes_service.get_pagination_params") as mock_pp:
            mock_pagination = MagicMock()
            mock_pagination.page = 1
            mock_pagination.page_size = 20
            mock_pagination.offset = 0
            mock_pagination.limit = 20
            mock_pagination.pages_for_total.return_value = 0
            mock_pp.return_value = mock_pagination

            result = service.get_quotes(status="approved")
            assert result.total == 0


class TestQuotesServiceCreateQuote:

    def test_create_quote_returns_quote(self, service, mock_db):
        mock_user = MagicMock(id=1)
        mock_quote_data = MagicMock(
            customer_id=5,
            title="Test Quote",
            description="desc",
            total_amount=10000,
            valid_until=date(2024, 12, 31),
            terms="Net 30"
        )

        with patch("app.services.sales.quotes_service.save_obj") as mock_save, \
             patch.object(service, "_generate_quote_number", return_value="QT2024010100001"):
            mock_quote = MagicMock()
            with patch("app.services.sales.quotes_service.Quote", return_value=mock_quote):
                result = service.create_quote(mock_quote_data, mock_user)
                assert result is not None

    def test_generate_quote_number_format(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3

        number = service._generate_quote_number()
        today = date.today()
        assert number.startswith(f"QT{today.strftime('%Y%m%d')}")
        assert number.endswith("0004")  # count+1 = 4

    def test_generate_quote_number_first_of_day(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        number = service._generate_quote_number()
        assert number.endswith("0001")
