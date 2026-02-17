# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：齐套率统计服务
Coverage target: app/services/kit_rate_statistics_service.py

分支覆盖：
1. calculate_date_range — 返回当月范围
2. calculate_project_kit_statistics — 正常/异常分支
3. calculate_summary_statistics — 空/有数据/各 group_by
4. calculate_daily_kit_statistics — 日期遍历
5. calculate_workshop_kit_statistics — 有无过滤
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.kit_rate_statistics_service import (
    calculate_date_range,
    calculate_project_kit_statistics,
    calculate_summary_statistics,
    calculate_daily_kit_statistics,
    calculate_workshop_kit_statistics,
)


# ─────────────────────────────────────────────────
# calculate_date_range
# ─────────────────────────────────────────────────

class TestCalculateDateRange:

    def test_returns_start_and_end_of_month(self):
        today = date(2026, 2, 15)
        start, end = calculate_date_range(today)
        assert start.month == 2
        assert end.month == 2
        assert start.day == 1
        assert start <= today <= end

    def test_month_start_is_first(self):
        today = date(2026, 7, 20)
        start, end = calculate_date_range(today)
        assert start.day == 1

    def test_range_is_valid(self):
        today = date(2026, 1, 1)
        start, end = calculate_date_range(today)
        assert start <= end


# ─────────────────────────────────────────────────
# calculate_project_kit_statistics
# ─────────────────────────────────────────────────

class TestCalculateProjectKitStatistics:

    def _make_project(self, pid=1, code="P001", name="项目1"):
        p = MagicMock()
        p.id = pid; p.project_code = code; p.project_name = name
        return p

    def test_returns_dict_with_required_keys(self):
        db = MagicMock()
        project = self._make_project()

        mock_kit = {
            "kit_rate": 85.0, "total_items": 10, "fulfilled_items": 8,
            "shortage_items": 2, "in_transit_items": 0, "kit_status": "partial"
        }

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = mock_kit
            MockSvc.return_value = mock_svc

            result = calculate_project_kit_statistics(db, project)

        assert result is not None
        assert result["project_id"] == 1
        assert result["kit_rate"] == 85.0
        assert result["kit_status"] == "partial"
        assert "total_items" in result

    def test_returns_none_on_exception(self):
        db = MagicMock()
        project = self._make_project()

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items",
                   side_effect=RuntimeError("DB error")):
            result = calculate_project_kit_statistics(db, project)

        assert result is None

    def test_returns_correct_project_info(self):
        db = MagicMock()
        project = self._make_project(pid=42, code="PJ042", name="特殊项目")

        mock_kit = {
            "kit_rate": 100.0, "total_items": 5, "fulfilled_items": 5,
            "shortage_items": 0, "in_transit_items": 0, "kit_status": "complete"
        }

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = mock_kit
            MockSvc.return_value = mock_svc

            result = calculate_project_kit_statistics(db, project)

        assert result["project_id"] == 42
        assert result["project_code"] == "PJ042"
        assert result["project_name"] == "特殊项目"


# ─────────────────────────────────────────────────
# calculate_summary_statistics
# ─────────────────────────────────────────────────

class TestCalculateSummaryStatistics:

    def test_empty_statistics_returns_zeros(self):
        result = calculate_summary_statistics([], "project")
        assert result["avg_kit_rate"] == 0.0
        assert result["max_kit_rate"] == 0.0
        assert result["min_kit_rate"] == 0.0
        assert result["total_count"] == 0

    def test_single_item_all_same(self):
        stats = [{"kit_rate": 75.0, "project_id": 1}]
        result = calculate_summary_statistics(stats, "project")
        assert result["avg_kit_rate"] == 75.0
        assert result["max_kit_rate"] == 75.0
        assert result["min_kit_rate"] == 75.0
        assert result["total_count"] == 1

    def test_multiple_items_correct_avg_max_min(self):
        stats = [
            {"kit_rate": 60.0}, {"kit_rate": 80.0}, {"kit_rate": 100.0}
        ]
        result = calculate_summary_statistics(stats, "project")
        assert result["avg_kit_rate"] == pytest.approx(80.0, abs=0.01)
        assert result["max_kit_rate"] == 100.0
        assert result["min_kit_rate"] == 60.0

    def test_workshop_group_by_works(self):
        stats = [{"kit_rate": 70.0}, {"kit_rate": 90.0}]
        result = calculate_summary_statistics(stats, "workshop")
        assert result["avg_kit_rate"] == pytest.approx(80.0, abs=0.01)

    def test_day_group_by_works(self):
        stats = [{"kit_rate": 50.0, "date": "2026-01-01"}]
        result = calculate_summary_statistics(stats, "day")
        assert result["avg_kit_rate"] == 50.0

    def test_total_count_matches_input_length(self):
        stats = [{"kit_rate": float(i * 10)} for i in range(1, 8)]
        result = calculate_summary_statistics(stats, "project")
        assert result["total_count"] == 7


# ─────────────────────────────────────────────────
# calculate_daily_kit_statistics
# ─────────────────────────────────────────────────

class TestCalculateDailyKitStatistics:

    def test_single_day_range(self):
        db = MagicMock()
        project = MagicMock(); project.id = 1

        mock_kit = {"kit_rate": 80.0}
        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = mock_kit
            MockSvc.return_value = mock_svc

            result = calculate_daily_kit_statistics(
                db, date(2026, 1, 5), date(2026, 1, 5), [project]
            )

        assert len(result) == 1
        assert result[0]["date"] == "2026-01-05"
        assert result[0]["project_count"] == 1

    def test_multi_day_range_count_correct(self):
        db = MagicMock()
        project = MagicMock(); project.id = 1

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = {"kit_rate": 70.0}
            MockSvc.return_value = mock_svc

            result = calculate_daily_kit_statistics(
                db, date(2026, 1, 1), date(2026, 1, 7), [project]
            )

        assert len(result) == 7

    def test_no_projects_zero_kit_rate(self):
        db = MagicMock()
        result = calculate_daily_kit_statistics(db, date(2026, 1, 1), date(2026, 1, 3), [])
        assert all(r["kit_rate"] == 0.0 for r in result)
        assert all(r["project_count"] == 0 for r in result)

    def test_exception_in_project_skipped(self):
        db = MagicMock()
        project = MagicMock(); project.id = 1

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items",
                   side_effect=ValueError("bad")):
            result = calculate_daily_kit_statistics(
                db, date(2026, 1, 1), date(2026, 1, 2), [project]
            )

        # 应不崩溃，项目被跳过
        assert len(result) == 2
        assert all(r["kit_rate"] == 0.0 for r in result)

    def test_date_format_iso(self):
        db = MagicMock()
        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = {"kit_rate": 90.0}
            MockSvc.return_value = mock_svc

            result = calculate_daily_kit_statistics(
                db, date(2026, 3, 15), date(2026, 3, 15), [MagicMock(id=1)]
            )

        assert result[0]["date"] == "2026-03-15"


# ─────────────────────────────────────────────────
# calculate_workshop_kit_statistics
# ─────────────────────────────────────────────────

class TestCalculateWorkshopKitStatistics:

    def test_returns_list_per_workshop(self):
        db = MagicMock()
        workshop = MagicMock(); workshop.id = 1; workshop.workshop_name = "车间A"
        db.query.return_value.all.return_value = [workshop]

        project = MagicMock(); project.id = 1
        projects = [project]

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = {
                "kit_rate": 80.0, "total_items": 10,
                "fulfilled_items": 8, "shortage_items": 2, "in_transit_items": 0
            }
            MockSvc.return_value = mock_svc

            result = calculate_workshop_kit_statistics(db, None, projects)

        assert len(result) == 1
        assert result[0]["workshop_id"] == 1
        assert "kit_rate" in result[0]

    def test_no_workshops_returns_empty(self):
        db = MagicMock()
        db.query.return_value.all.return_value = []
        result = calculate_workshop_kit_statistics(db, None, [])
        assert result == []

    def test_workshop_id_filter_applied(self):
        db = MagicMock()
        w1 = MagicMock(); w1.id = 1; w1.workshop_name = "车间A"
        w2 = MagicMock(); w2.id = 2; w2.workshop_name = "车间B"
        db.query.return_value.all.return_value = [w1, w2]

        with patch("app.services.kit_rate_statistics_service.get_project_bom_items", return_value=[]), \
             patch("app.services.kit_rate_statistics_service.KitRateService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.calculate_kit_rate.return_value = {
                "kit_rate": 60.0, "total_items": 5,
                "fulfilled_items": 3, "shortage_items": 2, "in_transit_items": 0
            }
            MockSvc.return_value = mock_svc

            # 只过滤 workshop_id=1
            result = calculate_workshop_kit_statistics(db, workshop_id=1, projects=[MagicMock(id=1)])

        assert len(result) == 1
        assert result[0]["workshop_id"] == 1
