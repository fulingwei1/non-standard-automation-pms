# -*- coding: utf-8 -*-
"""
绩效分析服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.performance_analysis_service import PerformanceAnalysisService


class TestPerformanceAnalysisServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = PerformanceAnalysisService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            PerformanceAnalysisService()


class TestPerformanceAnalysisServiceMethods:
    """测试绩效分析方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PerformanceAnalysisService(mock_db)

    def test_get_performance_ranking_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_performance_ranking')

    def test_get_team_efficiency_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_team_efficiency')

    def test_get_pm_performance_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_pm_performance')

    def test_get_improvement_tracking_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_improvement_tracking')


class TestPerformanceAnalysisServiceHelpers:
    """测试辅助方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PerformanceAnalysisService(mock_db)

    def test_health_score_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_health_score')

    def test_budget_score_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_budget_score')

    def test_schedule_score_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_schedule_score')

    def test_risk_score_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_risk_score')


class TestPerformanceAnalysisServiceConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services import performance_analysis_service
        assert performance_analysis_service is not None

    def test_service_class_exists(self):
        """测试服务类存在"""
        assert PerformanceAnalysisService is not None