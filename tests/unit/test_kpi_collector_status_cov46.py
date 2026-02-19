# -*- coding: utf-8 -*-
"""第四十六批 - KPI采集状态单元测试"""
import pytest
from datetime import datetime

pytest.importorskip("app.services.strategy.kpi_collector.status",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock
from app.services.strategy.kpi_collector.status import get_collection_status


def _make_kpi(data_source_type="AUTO", frequency="MONTHLY", current_value=None, collected_at=None):
    k = MagicMock()
    k.data_source_type = data_source_type
    k.frequency = frequency
    k.current_value = current_value
    k.last_collected_at = collected_at
    return k


class TestGetCollectionStatus:
    def test_returns_all_required_keys(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_collection_status(db, strategy_id=1)

        assert "total_kpis" in result
        assert "auto_kpis" in result
        assert "manual_kpis" in result
        assert "collected_kpis" in result
        assert "pending_kpis" in result
        assert "frequency_stats" in result
        assert "last_collected_at" in result

    def test_empty_returns_zeros(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_collection_status(db, strategy_id=1)
        assert result["total_kpis"] == 0
        assert result["auto_kpis"] == 0
        assert result["manual_kpis"] == 0
        assert result["last_collected_at"] is None

    def test_counts_auto_and_manual(self):
        db = MagicMock()
        kpis = [
            _make_kpi("AUTO", "MONTHLY"),
            _make_kpi("AUTO", "WEEKLY"),
            _make_kpi("MANUAL", "MONTHLY"),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis

        result = get_collection_status(db, strategy_id=1)
        assert result["auto_kpis"] == 2
        assert result["manual_kpis"] == 1
        assert result["total_kpis"] == 3

    def test_counts_collected_and_pending(self):
        db = MagicMock()
        kpis = [
            _make_kpi(current_value=10.0),
            _make_kpi(current_value=None),
            _make_kpi(current_value=20.0),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis

        result = get_collection_status(db, strategy_id=1)
        assert result["collected_kpis"] == 2
        assert result["pending_kpis"] == 1

    def test_frequency_stats_aggregated(self):
        db = MagicMock()
        kpis = [
            _make_kpi(frequency="MONTHLY", current_value=10),
            _make_kpi(frequency="MONTHLY", current_value=None),
            _make_kpi(frequency="WEEKLY", current_value=5),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis

        result = get_collection_status(db, strategy_id=1)
        assert result["frequency_stats"]["MONTHLY"]["total"] == 2
        assert result["frequency_stats"]["MONTHLY"]["collected"] == 1
        assert result["frequency_stats"]["WEEKLY"]["total"] == 1
        assert result["frequency_stats"]["WEEKLY"]["collected"] == 1

    def test_last_collected_at_is_max(self):
        db = MagicMock()
        t1 = datetime(2024, 1, 10)
        t2 = datetime(2024, 3, 5)
        kpis = [
            _make_kpi(collected_at=t1),
            _make_kpi(collected_at=t2),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis

        result = get_collection_status(db, strategy_id=1)
        assert result["last_collected_at"] == t2
