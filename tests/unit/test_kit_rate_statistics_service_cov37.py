# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 齐套率统计服务
tests/unit/test_kit_rate_statistics_service_cov37.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.kit_rate_statistics_service")

from app.services.kit_rate_statistics_service import (
    calculate_date_range,
    calculate_project_kit_statistics,
    calculate_workshop_kit_statistics,
    calculate_daily_kit_statistics,
    calculate_summary_statistics,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_project(pid=1, name="项目A", code="P001"):
    p = MagicMock()
    p.id = pid
    p.project_name = name
    p.project_code = code
    return p


def _make_db_with_kit(kit_data=None):
    """返回已打好桩的 db + KitRateService mock"""
    db = MagicMock()
    if kit_data is None:
        kit_data = {
            "kit_rate": 0.85,
            "total_items": 10,
            "fulfilled_items": 8,
            "shortage_items": 2,
            "in_transit_items": 1,
            "kit_status": "partial",
        }
    with patch(
        "app.services.kit_rate_statistics_service.KitRateService"
    ) as MockKRS:
        instance = MockKRS.return_value
        instance.list_bom_items_for_project.return_value = []
        instance.calculate_kit_rate.return_value = kit_data
        return db, MockKRS, kit_data


# ── tests ─────────────────────────────────────────────────────────────────────

class TestCalculateDateRange:
    def test_returns_tuple_of_dates(self):
        today = date(2025, 6, 15)
        with patch(
            "app.services.kit_rate_statistics_service.get_month_range",
            return_value=(date(2025, 6, 1), date(2025, 6, 30)),
        ):
            start, end = calculate_date_range(today)
        assert start == date(2025, 6, 1)
        assert end == date(2025, 6, 30)

    def test_start_before_end(self):
        today = date(2025, 1, 10)
        with patch(
            "app.services.kit_rate_statistics_service.get_month_range",
            return_value=(date(2025, 1, 1), date(2025, 1, 31)),
        ):
            start, end = calculate_date_range(today)
        assert start <= end


class TestCalculateProjectKitStatistics:
    def test_returns_dict_on_success(self):
        project = _make_project()
        db = MagicMock()
        kit_data = {
            "kit_rate": 0.9, "total_items": 5, "fulfilled_items": 4,
            "shortage_items": 1, "in_transit_items": 0, "kit_status": "partial",
        }
        with patch("app.services.kit_rate_statistics_service.KitRateService") as MockKRS:
            inst = MockKRS.return_value
            inst.list_bom_items_for_project.return_value = []
            inst.calculate_kit_rate.return_value = kit_data

            result = calculate_project_kit_statistics(db, project)

        assert result is not None
        assert result["project_id"] == 1
        assert result["kit_rate"] == 0.9
        assert result["kit_status"] == "partial"

    def test_returns_none_on_exception(self):
        project = _make_project()
        db = MagicMock()
        with patch(
            "app.services.kit_rate_statistics_service.KitRateService",
            side_effect=Exception("db error"),
        ):
            result = calculate_project_kit_statistics(db, project)
        assert result is None


class TestCalculateSummaryStatistics:
    def test_empty_statistics(self):
        result = calculate_summary_statistics([], "project")
        assert result["avg_kit_rate"] == 0.0
        assert result["total_count"] == 0

    def test_project_group_by(self):
        stats = [{"kit_rate": 0.8}, {"kit_rate": 0.6}]
        result = calculate_summary_statistics(stats, "project")
        assert result["avg_kit_rate"] == 0.7
        assert result["max_kit_rate"] == 0.8
        assert result["min_kit_rate"] == 0.6
        assert result["total_count"] == 2

    def test_day_group_by(self):
        stats = [{"kit_rate": 1.0}, {"kit_rate": 0.5}]
        result = calculate_summary_statistics(stats, "day")
        assert result["avg_kit_rate"] == 0.75
        assert result["total_count"] == 2


class TestCalculateDailyKitStatistics:
    def test_single_day(self):
        db = MagicMock()
        project = _make_project()
        kit_data = {
            "kit_rate": 0.75, "total_items": 4, "fulfilled_items": 3,
        }
        with patch("app.services.kit_rate_statistics_service.KitRateService") as MockKRS:
            inst = MockKRS.return_value
            inst.list_bom_items_for_project.return_value = []
            inst.calculate_kit_rate.return_value = kit_data

            result = calculate_daily_kit_statistics(
                db, date(2025, 6, 1), date(2025, 6, 1), [project]
            )

        assert len(result) == 1
        assert result[0]["date"] == "2025-06-01"
        assert result[0]["project_count"] == 1

    def test_no_projects_returns_zero_kit_rate(self):
        db = MagicMock()
        result = calculate_daily_kit_statistics(
            db, date(2025, 6, 1), date(2025, 6, 1), []
        )
        assert result[0]["kit_rate"] == 0.0
