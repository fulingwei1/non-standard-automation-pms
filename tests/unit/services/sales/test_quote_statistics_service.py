# -*- coding: utf-8 -*-
"""
quote_statistics_service 单元测试
"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.sales import Quote
from app.services.sales.quote_statistics_service import QuoteStatisticsService


def _make_user(user_id=1):
    return SimpleNamespace(id=user_id, username="sales-user")


class TestQuoteStatisticsService:

    def test_get_statistics_applies_scope_and_aggregates(self):
        mock_db = MagicMock()
        service = QuoteStatisticsService(mock_db)
        current_user = _make_user()

        base_query = MagicMock()
        scoped_query = MagicMock()
        aggregate_query = MagicMock()

        mock_db.query.return_value = base_query
        scoped_query.outerjoin.return_value = aggregate_query
        aggregate_query.with_entities.return_value.one.return_value = (
            5,
            1,
            1,
            1,
            0,
            0,
            0,
            1,
            1,
            Decimal("1250000.00"),
            Decimal("22.50"),
            2,
        )

        with patch(
            "app.services.sales.quote_statistics_service.filter_sales_data_by_scope",
            return_value=scoped_query,
        ) as mock_filter:
            result = service.get_statistics(current_user=current_user)

        mock_filter.assert_called_once_with(
            base_query,
            current_user,
            mock_db,
            Quote,
            "owner_id",
        )
        assert result["total"] == 5
        assert result["converted"] == 1
        assert result["totalAmount"] == 1250000.0
        assert result["avgAmount"] == 250000.0
        assert result["avgMargin"] == 22.5
        assert result["conversionRate"] == 20.0
        assert result["expiringSoon"] == 2
        assert not scoped_query.all.called

    def test_get_statistics_with_period_range(self):
        mock_db = MagicMock()
        service = QuoteStatisticsService(mock_db)
        current_user = _make_user()

        base_query = MagicMock()
        scoped_query = MagicMock()
        aggregate_query = MagicMock()
        period_query = MagicMock()

        mock_db.query.return_value = base_query
        scoped_query.outerjoin.return_value = aggregate_query
        aggregate_query.with_entities.return_value.one.return_value = (
            3,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            1,
            Decimal("300000.00"),
            Decimal("18.20"),
            1,
        )
        scoped_query.filter.return_value = period_query
        period_query.count.side_effect = [3, 1]

        with patch(
            "app.services.sales.quote_statistics_service.filter_sales_data_by_scope",
            return_value=scoped_query,
        ):
            result = service.get_statistics(current_user=current_user, time_range="month")

        assert result["currentPeriod"] == 3
        assert result["previousPeriod"] == 1
        assert result["growth"] == 200.0
