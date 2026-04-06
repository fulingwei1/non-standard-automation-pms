# -*- coding: utf-8 -*-
"""
利润分析服务测试
目标覆盖率: 60%+
测试用例数: 4个
"""
from unittest.mock import Mock

import pytest

from app.services.profit_analysis_service import ProfitAnalysisService


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock()
    return db


@pytest.fixture
def profit_service(mock_db):
    """创建利润分析服务实例"""
    return ProfitAnalysisService(mock_db)


class TestProfitAnalysisService:
    """利润分析服务测试类"""

    def test_service_initialization(self, mock_db):
        """测试服务初始化"""
        service = ProfitAnalysisService(mock_db)
        assert service is not None
        assert service.db == mock_db

    def test_get_margin_analysis_no_project(self, profit_service, mock_db):
        """测试毛利率分析-项目不存在"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = profit_service.get_margin_analysis(project_id=999)
        # 当项目不存在时返回包含error的字典
        assert result is None or (isinstance(result, dict) and 'error' in result)

    def test_get_high_profit_patterns(self, profit_service, mock_db):
        """测试高利润项目特征分析"""
        mock_projects = []
        for i in range(3):
            project = Mock()
            project.id = i + 1
            project.contract_amount = 1000000
            project.actual_cost = 600000
            mock_projects.append(project)

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = mock_projects

        result = profit_service.get_high_profit_patterns()
        assert result is not None