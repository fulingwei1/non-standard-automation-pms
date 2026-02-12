# -*- coding: utf-8 -*-
"""KPI详情和历史 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.strategy.kpi_service.detail_history import (
    get_kpi_detail,
    get_kpi_history,
    get_kpi_with_history,
)


class TestGetKpiDetail:
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi")
    def test_kpi_not_found(self, mock_get_kpi):
        mock_get_kpi.return_value = None
        db = MagicMock()
        result = get_kpi_detail(db, 999)
        assert result is None

    @patch("app.services.strategy.kpi_service.detail_history._calculate_trend")
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi")
    def test_kpi_found(self, mock_get_kpi, mock_trend):
        db = MagicMock()
        kpi = MagicMock()
        kpi.id = 1
        kpi.csf_id = 2
        kpi.code = "KPI001"
        kpi.name = "测试KPI"
        kpi.description = "desc"
        kpi.ipooc_type = "O"
        kpi.unit = "%"
        kpi.direction = "UP"
        kpi.target_value = 100
        kpi.baseline_value = 50
        kpi.current_value = 75
        kpi.excellent_threshold = 90
        kpi.good_threshold = 70
        kpi.warning_threshold = 50
        kpi.data_source_type = "MANUAL"
        kpi.frequency = "MONTHLY"
        kpi.last_collected_at = None
        kpi.weight = 1.0
        kpi.owner_user_id = None
        kpi.is_active = True
        kpi.created_at = None
        kpi.updated_at = None
        mock_get_kpi.return_value = kpi
        mock_trend.return_value = "UP"

        with patch("app.services.strategy.kpi_service.detail_history.calculate_kpi_health", return_value={"level": "GREEN"}):
            with patch("app.services.strategy.kpi_service.detail_history.calculate_kpi_completion_rate", return_value=75.0):
                # CSF query
                csf = MagicMock()
                csf.name = "CSF1"
                csf.dimension = "财务"
                db.query.return_value.filter.return_value.first.return_value = csf

                result = get_kpi_detail(db, 1)
                assert result is not None
                assert result.name == "测试KPI"


class TestGetKpiHistory:
    def test_returns_list(self):
        db = MagicMock()
        h = MagicMock()
        h.id = 1
        h.kpi_id = 1
        h.snapshot_date = None
        h.snapshot_period = "2025-01"
        h.value = 75
        h.target_value = 100
        h.completion_rate = 75
        h.health_level = "GREEN"
        h.source_type = "MANUAL"
        h.remark = None
        h.recorded_by = None
        h.created_at = None
        h.updated_at = None
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h]
        result = get_kpi_history(db, 1)
        assert len(result) == 1

    def test_empty_history(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = get_kpi_history(db, 1)
        assert result == []


class TestGetKpiWithHistory:
    @patch("app.services.strategy.kpi_service.detail_history.get_kpi_detail")
    def test_not_found(self, mock_detail):
        mock_detail.return_value = None
        db = MagicMock()
        result = get_kpi_with_history(db, 999)
        assert result is None
