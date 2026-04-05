# -*- coding: utf-8 -*-
"""
健康趋势服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


class TestHealthTrendService:
    """健康趋势服务测试"""

    def test_get_health_trend(self):
        """测试获取健康趋势"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        # Mock project exists
        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.get_health_trend(project_id=1)
        assert isinstance(result, dict)

    def test_get_health_trend_no_project(self):
        """测试项目不存在"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = HealthTrendService(mock_db)

        result = service.get_health_trend(project_id=999)
        # Should return error or empty dict
        assert isinstance(result, (dict, type(None)))

    def test_get_risk_breakdown(self):
        """测试获取风险分解"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.get_risk_breakdown(project_id=1)
        assert isinstance(result, dict)

    def test_get_improvement_suggestions(self):
        """测试获取改进建议"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.get_improvement_suggestions(project_id=1)
        assert isinstance(result, dict)

    def test_calc_schedule_score(self):
        """测试计算进度评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        result = service._calc_schedule_score(mock_project)
        assert isinstance(result, int)

    def test_calc_cost_score(self):
        """测试计算成本评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        result = service._calc_cost_score(mock_project)
        assert isinstance(result, int)

    def test_calc_resource_score(self):
        """测试计算资源评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        result = service._calc_resource_score(mock_project)
        assert isinstance(result, int)

    def test_calc_quality_score(self):
        """测试计算质量评分"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        result = service._calc_quality_score(mock_project)
        assert isinstance(result, int)

    def test_get_project(self):
        """测试获取项目"""
        from app.services.health_trend_service import HealthTrendService

        mock_db = MagicMock()
        service = HealthTrendService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service._get_project(project_id=1)
        assert result == mock_project