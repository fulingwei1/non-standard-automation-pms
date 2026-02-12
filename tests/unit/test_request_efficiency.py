# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from datetime import date, datetime
from app.services.procurement_analysis.request_efficiency import RequestEfficiencyAnalyzer


class TestRequestEfficiencyAnalyzer:
    def test_no_requests(self):
        db = MagicMock()
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = []
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(db, date(2024, 1, 1), date(2024, 3, 1))
        assert result["summary"]["total_requests"] == 0
        assert result["summary"]["avg_processing_hours"] == 0

    def test_with_processed_request(self):
        db = MagicMock()
        row = MagicMock()
        row.id = 1
        row.request_no = "PR001"
        row.requested_at = datetime(2024, 1, 1, 10, 0)
        row.status = "APPROVED"
        row.total_amount = 5000
        row.source_type = "PROJECT"
        row.order_created_at = datetime(2024, 1, 2, 10, 0)
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = [row]
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(db, date(2024, 1, 1), date(2024, 3, 1))
        assert result["summary"]["processed_count"] == 1
        assert result["summary"]["pending_count"] == 0
        assert result["efficiency_data"][0]["processing_hours"] == 24.0

    def test_with_pending_request(self):
        db = MagicMock()
        row = MagicMock()
        row.id = 2
        row.request_no = "PR002"
        row.requested_at = datetime.now()
        row.status = "PENDING"
        row.total_amount = 3000
        row.source_type = "PROJECT"
        row.order_created_at = None
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = [row]
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(db, date(2024, 1, 1), date(2024, 3, 1))
        assert result["summary"]["pending_count"] == 1
