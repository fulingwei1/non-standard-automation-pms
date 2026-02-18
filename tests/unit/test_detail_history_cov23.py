# -*- coding: utf-8 -*-
"""第二十三批：strategy/kpi_service/detail_history 单元测试"""
import sys
import types
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

# 注入缺失的 health_calculator 模块，避免 ImportError
_hc_mod = types.ModuleType("app.services.strategy.kpi_service.health_calculator")
_hc_mod.calculate_kpi_health = lambda db, kpi_id: {"level": "GOOD"}
_hc_mod.calculate_kpi_completion_rate = lambda kpi: Decimal("80")
sys.modules.setdefault("app.services.strategy.kpi_service.health_calculator", _hc_mod)

pytest.importorskip("app.services.strategy.kpi_service.detail_history")

from app.services.strategy.kpi_service.detail_history import (
    get_kpi_detail,
    get_kpi_history,
    get_kpi_with_history,
)


def _make_db():
    return MagicMock()


def _mock_kpi(kpi_id=1):
    kpi = MagicMock()
    kpi.id = kpi_id
    kpi.csf_id = 10
    kpi.code = "KPI-001"
    kpi.name = "测试KPI"
    kpi.description = "描述"
    kpi.ipooc_type = "O"
    kpi.unit = "%"
    kpi.direction = "HIGHER"
    kpi.target_value = Decimal("100")
    kpi.baseline_value = Decimal("0")
    kpi.current_value = Decimal("80")
    kpi.excellent_threshold = Decimal("95")
    kpi.good_threshold = Decimal("80")
    kpi.warning_threshold = Decimal("60")
    kpi.data_source_type = "MANUAL"
    kpi.frequency = "MONTHLY"
    kpi.last_collected_at = None
    kpi.weight = 10
    kpi.owner_user_id = None  # no owner to avoid user lookup
    kpi.is_active = True
    kpi.created_at = None
    kpi.updated_at = None
    return kpi


def _mock_history_item(h_id=1, kpi_id=1):
    h = MagicMock()
    h.id = h_id
    h.kpi_id = kpi_id
    h.snapshot_date = date(2025, 1, 1)
    h.snapshot_period = "2025-01"
    h.value = Decimal("80")
    h.target_value = Decimal("100")
    h.completion_rate = Decimal("80")
    h.health_level = "GOOD"
    h.source_type = "MANUAL"
    h.remark = ""
    h.recorded_by = 1
    h.created_at = None
    h.updated_at = None
    return h


class TestGetKpiDetail:
    def test_returns_none_when_kpi_not_found(self):
        db = _make_db()
        with patch("app.services.strategy.kpi_service.detail_history.get_kpi", return_value=None):
            result = get_kpi_detail(db, 999)
        assert result is None

    def test_returns_detail_response(self):
        db = _make_db()
        kpi = _mock_kpi()
        mock_csf = MagicMock()
        mock_csf.name = "CSF1"
        mock_csf.dimension = "财务"

        q = MagicMock()
        q.filter.return_value.first.return_value = mock_csf
        db.query.return_value = q

        with patch("app.services.strategy.kpi_service.detail_history.get_kpi", return_value=kpi):
            with patch.object(_hc_mod, "calculate_kpi_health", return_value={"level": "GOOD"}):
                with patch.object(_hc_mod, "calculate_kpi_completion_rate", return_value=Decimal("80")):
                    with patch("app.services.strategy.kpi_service.detail_history._calculate_trend", return_value="UP"):
                        result = get_kpi_detail(db, 1)
        assert result is not None
        assert result.id == 1

    def test_no_owner_user_id_owner_name_none(self):
        db = _make_db()
        kpi = _mock_kpi()
        kpi.owner_user_id = None
        mock_csf = MagicMock()
        mock_csf.name = "CSF"
        mock_csf.dimension = "财务"
        q = MagicMock()
        q.filter.return_value.first.return_value = mock_csf
        db.query.return_value = q

        with patch("app.services.strategy.kpi_service.detail_history.get_kpi", return_value=kpi):
            with patch.object(_hc_mod, "calculate_kpi_health", return_value={"level": "GOOD"}):
                with patch.object(_hc_mod, "calculate_kpi_completion_rate", return_value=Decimal("80")):
                    with patch("app.services.strategy.kpi_service.detail_history._calculate_trend", return_value="STABLE"):
                        result = get_kpi_detail(db, 1)
        assert result.owner_name is None


class TestGetKpiHistory:
    def test_returns_history_list_reversed(self):
        db = _make_db()
        h1 = _mock_history_item(1)
        h2 = _mock_history_item(2)
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = [h2, h1]  # desc order
        db.query.return_value = q
        result = get_kpi_history(db, 1)
        # reversed → h1 comes first
        assert len(result) == 2
        assert result[0].id == 1

    def test_empty_history(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = get_kpi_history(db, 1)
        assert result == []

    def test_respects_limit(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = get_kpi_history(db, 1, limit=5)
        q.limit.assert_called_with(5)


class TestGetKpiWithHistory:
    def test_returns_none_when_no_detail(self):
        db = _make_db()
        with patch("app.services.strategy.kpi_service.detail_history.get_kpi_detail", return_value=None):
            result = get_kpi_with_history(db, 999)
        assert result is None

    def test_combines_detail_and_history(self):
        db = _make_db()
        mock_detail = MagicMock()
        mock_detail.model_dump.return_value = {
            "id": 1, "name": "KPI", "csf_id": 10,
            "code": "K1", "description": "", "ipooc_type": "O",
            "unit": "%", "direction": "HIGHER",
            "target_value": Decimal("100"), "baseline_value": Decimal("0"),
            "current_value": Decimal("80"), "excellent_threshold": Decimal("95"),
            "good_threshold": Decimal("80"), "warning_threshold": Decimal("60"),
            "data_source_type": "MANUAL", "frequency": "MONTHLY",
            "last_collected_at": None, "weight": 10,
            "owner_user_id": None, "is_active": True,
            "created_at": None, "updated_at": None,
            "owner_name": None, "csf_name": None,
            "csf_dimension": None, "completion_rate": Decimal("80"),
            "health_level": "GOOD", "trend": "UP"
        }
        mock_history = []
        with patch("app.services.strategy.kpi_service.detail_history.get_kpi_detail", return_value=mock_detail):
            with patch("app.services.strategy.kpi_service.detail_history.get_kpi_history", return_value=mock_history):
                result = get_kpi_with_history(db, 1)
        assert result is not None
