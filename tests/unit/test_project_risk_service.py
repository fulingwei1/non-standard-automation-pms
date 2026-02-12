# -*- coding: utf-8 -*-
"""Tests for app/services/project/project_risk_service.py"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.project.project_risk_service import ProjectRiskService


class TestProjectRiskService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = ProjectRiskService(self.db)

    def test_risk_level_order(self):
        assert self.service.RISK_LEVEL_ORDER["LOW"] < self.service.RISK_LEVEL_ORDER["CRITICAL"]

    def test_is_risk_upgrade(self):
        assert self.service._is_risk_upgrade("LOW", "HIGH") is True
        assert self.service._is_risk_upgrade("HIGH", "LOW") is False
        assert self.service._is_risk_upgrade("LOW", "LOW") is False

    def test_calculate_risk_level_critical(self):
        factors = {"overdue_milestone_ratio": 0.6, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.service._calculate_risk_level(factors) == "CRITICAL"

    def test_calculate_risk_level_critical_by_risks(self):
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 1,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.service._calculate_risk_level(factors) == "CRITICAL"

    def test_calculate_risk_level_high(self):
        factors = {"overdue_milestone_ratio": 0.35, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.service._calculate_risk_level(factors) == "HIGH"

    def test_calculate_risk_level_high_by_variance(self):
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": -25}
        assert self.service._calculate_risk_level(factors) == "HIGH"

    def test_calculate_risk_level_medium(self):
        factors = {"overdue_milestone_ratio": 0.15, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.service._calculate_risk_level(factors) == "MEDIUM"

    def test_calculate_risk_level_low(self):
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.service._calculate_risk_level(factors) == "LOW"

    def test_calculate_project_risk_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            self.service.calculate_project_risk(999)

    def test_calculate_project_risk_success(self):
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.progress_pct = 50
        project.planned_end_date = None

        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.calculate_project_risk(1)
        assert result["project_id"] == 1
        assert result["risk_level"] == "LOW"
        assert "risk_factors" in result

    def test_get_risk_history(self):
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = self.service.get_risk_history(1)
        assert result == []

    def test_get_risk_trend(self):
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        result = self.service.get_risk_trend(1, days=30)
        assert result == []

    def test_calculate_progress_factors_no_planned_end(self):
        project = MagicMock()
        project.progress_pct = 50
        project.planned_end_date = None
        result = self.service._calculate_progress_factors(project)
        assert result["progress_pct"] == 50.0
        assert result["schedule_variance"] == 0
