# -*- coding: utf-8 -*-
"""
资源计划服务单元测试
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock


from app.services.resource_plan_service import ResourcePlanService


class TestResourcePlanService:
    """资源计划服务测试"""

    def test_calculate_fill_rate_empty(self):
        """测试空需求的填充率"""
        result = ResourcePlanService.calculate_fill_rate([])
        assert result == 100.0  # 无需求时视为100%

    def test_calculate_fill_rate_partial(self):
        """测试部分填充的填充率"""
        requirements = [
            MagicMock(headcount=2, assignment_status="ASSIGNED"),
            MagicMock(headcount=1, assignment_status="PENDING"),
        ]
        result = ResourcePlanService.calculate_fill_rate(requirements)
        # 2 assigned / 3 total = 66.67%
        assert abs(result - 66.67) < 0.01

    def test_calculate_fill_rate_full(self):
        """测试完全填充的填充率"""
        requirements = [
            MagicMock(headcount=2, assignment_status="ASSIGNED"),
            MagicMock(headcount=1, assignment_status="ASSIGNED"),
        ]
        result = ResourcePlanService.calculate_fill_rate(requirements)
        assert result == 100.0

    def test_calculate_fill_rate_none(self):
        """测试无分配的填充率"""
        requirements = [
            MagicMock(headcount=2, assignment_status="PENDING"),
            MagicMock(headcount=1, assignment_status="PENDING"),
        ]
        result = ResourcePlanService.calculate_fill_rate(requirements)
        assert result == 0.0

    def test_detect_date_overlap_no_overlap(self):
        """测试无重叠日期"""
        result = ResourcePlanService.calculate_date_overlap(
            date(2026, 1, 1),
            date(2026, 1, 31),
            date(2026, 2, 1),
            date(2026, 2, 28),
        )
        assert result is None

    def test_detect_date_overlap_with_overlap(self):
        """测试有重叠日期"""
        result = ResourcePlanService.calculate_date_overlap(
            date(2026, 1, 15),
            date(2026, 2, 15),
            date(2026, 2, 1),
            date(2026, 2, 28),
        )
        assert result == (date(2026, 2, 1), date(2026, 2, 15))

    def test_detect_date_overlap_contained(self):
        """测试完全包含的日期"""
        result = ResourcePlanService.calculate_date_overlap(
            date(2026, 1, 1),
            date(2026, 3, 31),
            date(2026, 2, 1),
            date(2026, 2, 28),
        )
        assert result == (date(2026, 2, 1), date(2026, 2, 28))

    def test_detect_date_overlap_none_dates(self):
        """测试包含 None 的日期"""
        result = ResourcePlanService.calculate_date_overlap(
            date(2026, 1, 1),
            date(2026, 1, 31),
            None,
            date(2026, 2, 28),
        )
        assert result is None

    def test_calculate_conflict_severity_high(self):
        """测试高严重度冲突"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal("180"))
        assert severity == "HIGH"

    def test_calculate_conflict_severity_medium(self):
        """测试中严重度冲突"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal("130"))
        assert severity == "MEDIUM"

    def test_calculate_conflict_severity_low(self):
        """测试低严重度冲突"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal("110"))
        assert severity == "LOW"

    def test_calculate_conflict_severity_edge_150(self):
        """测试边界值 150"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal("150"))
        assert severity == "HIGH"

    def test_calculate_conflict_severity_edge_120(self):
        """测试边界值 120"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal("120"))
        assert severity == "MEDIUM"
