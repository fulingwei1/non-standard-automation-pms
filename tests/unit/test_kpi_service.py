# -*- coding: utf-8 -*-
"""
Tests for kpi_service module
Covers: app/services/kpi_service.py
Coverage Target: 0% → 60%+
Batch: P3 - 扩展服务模块测试
"""

import pytest
from decimal import Decimal
from datetime import date


class TestKPIService:
    """Test suite for KPI service functions."""

    def test_import_kpi_service(self):
        """Test importing KPI service module."""
        try:
            from app.services.kpi_service import (
                calculate_project_kpi,
                calculate_team_kpi,
                calculate_department_kpi,
                get_kpi_dashboard_data,
                generate_kpi_report
            )
            assert callable(calculate_project_kpi)
            assert callable(calculate_team_kpi)
            assert callable(calculate_department_kpi)
            assert callable(get_kpi_dashboard_data)
            assert callable(generate_kpi_report)
        except ImportError as e:
            pytest.fail(f"Cannot import KPI service: {e}")

    def test_calculate_project_kpi_basic(self):
        """Test basic project KPI calculation."""
        from app.services.kpi_service import calculate_project_kpi
        
        # Test data
        project_data = {
            "progress_pct": 75.0,
            "schedule_variance_days": 5,
            "cost_variance_rate": 5.0,
            "quality_score": 95.0,
            "client_satisfaction": 4.5,
        }
        
        result = calculate_project_kpi(project_data)
        
        # Verify structure
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "metrics" in result
        assert "assessment" in result

    def test_calculate_team_kpi_basic(self):
        """Test basic team KPI calculation."""
        from app.services.kpi_service import calculate_team_kpi
        
        # Test data
        team_data = [
            {
                "member_id": 1,
                "member_name": "张三",
                "completed_tasks": 15,
                "on_time_tasks": 12,
                "quality_score": 4.8,
                "productivity": 1.25,
            },
            {
                "member_id": 2,
                "member_name": "李四",
                "completed_tasks": 20,
                "on_time_tasks": 18,
                "quality_score": 4.9,
                "productivity": 1.5,
            },
        ]
        
        result = calculate_team_kpi(team_data)
        
        # Verify structure
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["member_name"] == "张三"
        assert result[1]["member_name"] == "李四"

    def test_calculate_department_kpi_basic(self):
        """Test basic department KPI calculation."""
        from app.services.kpi_service import calculate_department_kpi
        
        # Test data
        department_data = {
            "department_id": 1,
            "department_name": "研发部",
            "active_projects": 5,
            "completed_projects": 12,
            "avg_cycle_days": 85.0,
            "on_time_rate": 0.92,
            "budget_utilization": 0.88,
        }
        
        result = calculate_department_kpi(department_data)
        
        # Verify structure
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "metrics" in result
        assert "ranking" in result
