# -*- coding: utf-8 -*-
"""Tests for app.services.strategy.kpi_service.detail_history"""
from unittest.mock import MagicMock, patch

import pytest


class TestGetKpiDetail:
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi")
    def test_returns_none_when_not_found(self, mock_get):
        from app.services.strategy.kpi_service.detail_history import get_kpi_detail
        mock_get.return_value = None
        assert get_kpi_detail(MagicMock(), 999) is None

    @patch("app.services.strategy.kpi_service.detail_history.KPIDetailResponse")
    @patch("app.services.strategy.kpi_service.detail_history._calculate_trend")
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi")
    def test_returns_detail(self, mock_get, mock_trend, mock_resp):
        from app.services.strategy.kpi_service.detail_history import get_kpi_detail
        kpi = MagicMock()
        kpi.owner_user_id = None
        kpi.csf_id = 1
        mock_get.return_value = kpi
        mock_trend.return_value = "UP"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock(name="CSF", dimension="D")

        with patch("app.services.strategy.kpi_service.detail_history.calculate_kpi_health", return_value={"level": "GREEN"}):
            with patch("app.services.strategy.kpi_service.detail_history.calculate_kpi_completion_rate", return_value=80.0):
                mock_resp.return_value = MagicMock()
                result = get_kpi_detail(db, 1)
                assert result is not None


class TestGetKpiHistory:
    def test_returns_list(self):
        from app.services.strategy.kpi_service.detail_history import get_kpi_history
        db = MagicMock()
        h = MagicMock()
        h.id = 1
        h.kpi_id = 1
        h.snapshot_date = "2025-01-01"
        h.snapshot_period = "M"
        h.value = 80
        h.target_value = 100
        h.completion_rate = 80
        h.health_level = "GREEN"
        h.source_type = "AUTO"
        h.remark = None
        h.recorded_by = None
        h.created_at = "2025-01-01"
        h.updated_at = "2025-01-01"
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h]

        with patch("app.services.strategy.kpi_service.detail_history.KPIHistoryResponse") as MockResp:
            MockResp.side_effect = lambda **kw: MagicMock(**kw)
            result = get_kpi_history(db, 1)
            assert len(result) == 1


class TestGetKpiWithHistory:
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi_history")
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi_detail")
    def test_returns_none_when_no_detail(self, mock_detail, mock_history):
        from app.services.strategy.kpi_service.detail_history import get_kpi_with_history
        mock_detail.return_value = None
        assert get_kpi_with_history(MagicMock(), 999) is None

    @patch("app.services.strategy.kpi_service.detail_history.KPIWithHistoryResponse")
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi_history")
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi_detail")
    def test_returns_with_history(self, mock_detail, mock_history, mock_resp):
        from app.services.strategy.kpi_service.detail_history import get_kpi_with_history
        detail = MagicMock()
        detail.model_dump.return_value = {"id": 1}
        mock_detail.return_value = detail
        mock_history.return_value = []
        mock_resp.return_value = MagicMock()
        result = get_kpi_with_history(MagicMock(), 1)
        assert result is not None
