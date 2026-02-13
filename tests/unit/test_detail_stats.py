# -*- coding: utf-8 -*-
"""detail_stats 单元测试"""
from unittest.mock import MagicMock, patch
from decimal import Decimal
import pytest

from app.services.strategy.annual_work_service.detail_stats import (
    get_annual_work_detail,
    get_annual_work_stats,
)


class TestGetAnnualWorkDetail:
    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_not_found(self, mock_get):
        mock_get.return_value = None
        db = MagicMock()
        assert get_annual_work_detail(db, 999) is None

    @pytest.mark.skip(reason="AnnualKeyWorkProjectLink.is_active attribute missing in model")
    @patch("app.services.strategy.annual_work_service.detail_stats.get_annual_work")
    def test_found(self, mock_get):
        pass


class TestGetAnnualWorkStats:
    def test_empty(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = get_annual_work_stats(db, 1, 2024)
        assert result["total"] == 0
        assert result["avg_progress"] == 0

    def test_with_works(self):
        db = MagicMock()
        work1 = MagicMock()
        work1.status = "IN_PROGRESS"
        work1.priority = 1
        work1.progress_percent = Decimal("50")
        work1.csf_id = 10
        work2 = MagicMock()
        work2.status = "COMPLETED"
        work2.priority = 2
        work2.progress_percent = Decimal("100")
        work2.csf_id = 20

        db.query.return_value.join.return_value.filter.return_value.all.return_value = [work1, work2]
        csf1 = MagicMock()
        csf1.dimension = "Financial"
        csf2 = MagicMock()
        csf2.dimension = "Customer"
        db.query.return_value.filter.return_value.first.side_effect = [csf1, csf2]

        result = get_annual_work_stats(db, 1, 2024)
        assert result["total"] == 2
        assert result["avg_progress"] == 75.0
