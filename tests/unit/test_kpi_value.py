# -*- coding: utf-8 -*-
"""KPI值更新单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.strategy.kpi_service.value import update_kpi_value


class TestUpdateKpiValue:
    @patch("app.services.strategy.kpi_service.value.create_kpi_snapshot")
    @patch("app.services.strategy.kpi_service.value.get_kpi")
    def test_update_success(self, mock_get, mock_snapshot):
        db = MagicMock()
        kpi = MagicMock()
        mock_get.return_value = kpi
        result = update_kpi_value(db, 1, Decimal("85.5"), 10, "更新")
        assert kpi.current_value == Decimal("85.5")
        db.commit.assert_called_once()
        mock_snapshot.assert_called_once()

    @patch("app.services.strategy.kpi_service.value.get_kpi")
    def test_update_not_found(self, mock_get):
        db = MagicMock()
        mock_get.return_value = None
        result = update_kpi_value(db, 999, Decimal("85.5"), 10)
        assert result is None
