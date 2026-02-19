# -*- coding: utf-8 -*-
"""第四十六批 - KPI服务值更新单元测试"""
import pytest
from decimal import Decimal

pytest.importorskip("app.services.strategy.kpi_service.value",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.strategy.kpi_service.value import update_kpi_value


class TestUpdateKpiValue:
    def test_returns_none_when_kpi_not_found(self):
        db = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=None):
            result = update_kpi_value(db, 99, Decimal("50"), recorded_by=1)
        assert result is None

    def test_updates_current_value(self):
        db = MagicMock()
        kpi = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, 1, Decimal("88"), recorded_by=5)
        assert kpi.current_value == Decimal("88")

    def test_sets_last_collected_at(self):
        db = MagicMock()
        kpi = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, 1, Decimal("55"), recorded_by=3)
        assert kpi.last_collected_at is not None

    def test_calls_create_snapshot(self):
        db = MagicMock()
        kpi = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, 1, Decimal("70"), recorded_by=7, remark="手动更新")
        mock_snap.assert_called_once_with(db, 1, "MANUAL", 7, "手动更新")

    def test_commits_and_refreshes(self):
        db = MagicMock()
        kpi = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, 1, Decimal("60"), recorded_by=2)
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_with_none_remark(self):
        db = MagicMock()
        kpi = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, 1, Decimal("30"), recorded_by=1)
        mock_snap.assert_called_once_with(db, 1, "MANUAL", 1, None)
