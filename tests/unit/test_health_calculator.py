# -*- coding: utf-8 -*-
"""
Tests for health_calculator service
Covers: app/services/health_calculator.py
Coverage Target: 0% → 60%+
Batch: P3 - 扩展服务模块测试
"""

import pytest
from decimal import Decimal


class TestHealthCalculator:
    """Test suite for health calculator functions."""

    def test_import_health_calculator(self):
        """Test importing health calculator module."""
        try:
            from app.services.health_calculator import (
                calculate_project_health,
                calculate_progress_health,
                calculate_cost_health,
                calculate_schedule_health
            )
            assert callable(calculate_project_health)
            assert callable(calculate_progress_health)
            assert callable(calculate_cost_health)
            assert callable(calculate_schedule_health)
        except ImportError as e:
            pytest.fail(f"Cannot import health calculator: {e}")

    def test_calculate_project_health_on_track(self):
        """Test calculating project health when on track."""
        from app.services.health_calculator import calculate_project_health
        
        # Basic test - on track, on budget, no delays
        result = calculate_project_health(
            progress_pct=70.0,
            on_budget=True,
            days_overdue=0,
            critical_issues=0,
            schedule_variance=0
        )
        
        # Should be healthy
        assert result["health"] == "H1"
        assert result["health_label"] == "正常"
        assert result["health_color"] == "green"

    def test_calculate_project_health_at_risk(self):
        """Test calculating project health when at risk."""
        from app.services.health_calculator import calculate_project_health
        
        # At risk - off budget, delays
        result = calculate_project_health(
            progress_pct=50.0,
            on_budget=False,
            days_overdue=5,
            critical_issues=1,
            schedule_variance=-10
        )
        
        # Should be at risk
        assert result["health"] == "H2"
        assert result["health_label"] == "有风险"
        assert result["health_color"] == "yellow"

    def test_calculate_project_health_critical(self):
        """Test calculating project health when critical."""
        from app.services.health_calculator import calculate_project_health
        
        # Critical - major delays, multiple critical issues
        result = calculate_project_health(
            progress_pct=30.0,
            on_budget=False,
            days_overdue=15,
            critical_issues=3,
            schedule_variance=-25
        )
        
        # Should be critical
        assert result["health"] in ["H3", "H4"]
        assert result["health_color"] == "red"

    def test_calculate_progress_health_good(self):
        """Test good progress health."""
        from app.services.health_calculator import calculate_progress_health
        
        result = calculate_progress_health(
            progress_pct=85.0,
            planned_progress=80.0,
            recent_velocity=2.0
        )
        
        # Good progress - ahead of plan
        assert result["status"] == "AHEAD"
        assert result["variance"] == pytest.approx(5.0, rel=0.01)

    def test_calculate_progress_health_lagging(self):
        """Test lagging progress health."""
        from app.services.health_calculator import calculate_progress_health
        
        result = calculate_progress_health(
            progress_pct=60.0,
            planned_progress=75.0,
            recent_velocity=0.8
        )
        
        # Lagging - behind plan
        assert result["status"] == "BEHIND"
        assert result["variance"] == pytest.approx(-15.0, rel=0.01)

    def test_calculate_cost_health_on_budget(self):
        """Test on budget cost health."""
        from app.services.health_calculator import calculate_cost_health
        
        result = calculate_cost_health(
            budget_amount=Decimal("100000.00"),
            actual_cost=Decimal("95000.00"),
            remaining_budget=Decimal("5000.00")
        )
        
        # On budget
        assert result["status"] == "UNDER_BUDGET"
        assert result["utilization_rate"] == pytest.approx(95.0, rel=0.01)

    def test_calculate_cost_health_over_budget(self):
        """Test over budget cost health."""
        from app.services.health_calculator import calculate_cost_health
        
        result = calculate_cost_health(
            budget_amount=Decimal("100000.00"),
            actual_cost=Decimal("105000.00"),
            remaining_budget=Decimal("-5000.00")
        )
        
        # Over budget
        assert result["status"] == "OVER_BUDGET"
        assert result["utilization_rate"] == pytest.approx(105.0, rel=0.01)

    def test_calculate_schedule_health_on_time(self):
        """Test on time schedule health."""
        from app.services.health_calculator import calculate_schedule_health
        
        result = calculate_schedule_health(
            planned_end_date_days=90,
            remaining_days=30,
            on_track=True
        )
        
        # On time
        assert result["status"] == "ON_TIME"
        assert result["days_variance"] == 0

    def test_calculate_schedule_health_late(self):
        """Test late schedule health."""
        from app.services.health_calculator import calculate_schedule_health
        
        result = calculate_schedule_health(
            planned_end_date_days=90,
            remaining_days=-5,
            on_track=False
        )
        
        # Late
        assert result["status"] == "LATE"
        assert result["days_variance"] == pytest.approx(5, rel=0.01)
