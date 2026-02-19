# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 采购申请处理时效分析
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

try:
    from app.services.procurement_analysis.request_efficiency import RequestEfficiencyAnalyzer
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_row(request_no, requested_at, order_created_at, status="APPROVED", total_amount=10000.0, source_type="MANUAL"):
    row = MagicMock()
    row.request_no = request_no
    row.requested_at = requested_at
    row.order_created_at = order_created_at
    row.status = status
    row.total_amount = total_amount
    row.source_type = source_type
    return row


class TestRequestEfficiencyAnalyzer:

    def test_returns_dict_with_expected_keys(self, mock_db):
        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert "efficiency_data" in result
        assert "summary" in result

    def test_empty_results_summary(self, mock_db):
        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        summary = result["summary"]
        assert summary["total_requests"] == 0
        assert summary["processed_count"] == 0
        assert summary["pending_count"] == 0
        assert summary["avg_processing_hours"] == 0

    def test_processed_row_calculates_hours(self, mock_db):
        requested_at = datetime(2024, 1, 1, 8, 0, 0)
        order_created_at = datetime(2024, 1, 1, 16, 0, 0)  # 8小时后
        row = _make_row("REQ-001", requested_at, order_created_at)

        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [row]
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["summary"]["processed_count"] == 1
        assert result["summary"]["pending_count"] == 0
        data = result["efficiency_data"][0]
        assert data["processing_hours"] == 8.0
        # processing_days = round(8.0/24, 1) = 0.3
        assert data["processing_days"] == pytest.approx(round(8.0 / 24, 1), abs=0.05)

    def test_pending_row_marked_as_pending(self, mock_db):
        requested_at = datetime(2024, 1, 1, 8, 0, 0)
        row = _make_row("REQ-002", requested_at, None)

        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [row]
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["summary"]["pending_count"] == 1
        assert result["efficiency_data"][0].get("is_pending") is True

    def test_within_24h_rate_calculation(self, mock_db):
        r1 = _make_row("R1", datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 1, 16, 0))  # 8h
        r2 = _make_row("R2", datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 3, 8, 0))   # 48h

        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [r1, r2]
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        summary = result["summary"]
        assert summary["processed_within_24h"] == 1
        assert summary["processed_within_48h"] == 2
        assert summary["within_24h_rate"] == 50.0

    def test_efficiency_data_sorted_by_hours_desc(self, mock_db):
        r1 = _make_row("R1", datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 1, 10, 0))  # 2h
        r2 = _make_row("R2", datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 2, 8, 0))   # 24h

        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [r1, r2]
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        hours = [d["processing_hours"] for d in result["efficiency_data"]]
        assert hours == sorted(hours, reverse=True)

    def test_amount_defaults_to_zero_when_none(self, mock_db):
        requested_at = datetime(2024, 1, 1, 8, 0, 0)
        row = _make_row("REQ-003", requested_at, None, total_amount=None)

        query_mock = MagicMock()
        query_mock.outerjoin.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [row]
        mock_db.query.return_value = query_mock

        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            mock_db, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["efficiency_data"][0]["amount"] == 0.0
