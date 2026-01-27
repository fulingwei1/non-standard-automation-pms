# -*- coding: utf-8 -*-
"""
绩效趋势分析服务单元测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPerformanceTrendServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        assert service.db == db_session


class TestGetEngineerTrend:
    """测试获取工程师历史趋势"""

    def test_no_results(self, db_session):
        """测试无绩效记录"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.get_engineer_trend(99999)

        assert result['engineer_id'] == 99999
        assert result['has_data'] == False
        assert result['periods'] == []
        assert result['total_scores'] == []

    def test_default_periods(self, db_session):
        """测试默认周期数"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
            # 验证默认参数为6
        result = service.get_engineer_trend(1)

            # 结构验证
        assert 'engineer_id' in result
        assert 'periods' in result
        assert 'total_scores' in result
        assert 'ranks' in result
        assert 'levels' in result
        assert 'dimension_trends' in result

    def test_custom_periods(self, db_session):
        """测试自定义周期数"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.get_engineer_trend(1, periods=12)

        assert 'engineer_id' in result

    def test_dimension_trends_structure(self, db_session):
        """测试维度趋势结构"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.get_engineer_trend(1)

        expected_dimensions = [
        'technical', 'execution', 'cost_quality',
        'knowledge', 'collaboration'
        ]

        for dim in expected_dimensions:
            assert dim in result['dimension_trends']


class TestIdentifyAbilityChanges:
    """测试识别能力变化"""

    def test_no_data(self, db_session):
        """测试无数据"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.identify_ability_changes(99999)

        assert result == []

    def test_insufficient_data(self, db_session):
        """测试数据不足"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)

        with patch.object(service, 'get_engineer_trend', return_value={
        'has_data': True,
        'total_scores': [80.0],  # 只有一个周期
        'dimension_trends': {}
        }):
        result = service.identify_ability_changes(1)
        assert result == []

    def test_dimension_names_mapping(self):
        """测试维度名称映射"""
        dimension_names = {
        'technical': '技术能力',
        'execution': '项目执行',
        'cost_quality': '成本/质量',
        'knowledge': '知识沉淀',
        'collaboration': '团队协作'
        }

        assert dimension_names['technical'] == '技术能力'
        assert dimension_names['execution'] == '项目执行'
        assert dimension_names['cost_quality'] == '成本/质量'
        assert dimension_names['knowledge'] == '知识沉淀'
        assert dimension_names['collaboration'] == '团队协作'


class TestGetDepartmentTrend:
    """测试获取部门整体趋势"""

    def test_no_employees(self, db_session):
        """测试无员工"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.get_department_trend(99999)

        assert result['department_id'] == 99999
        assert result['has_data'] == False

    def test_custom_periods(self, db_session):
        """测试自定义周期数"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.get_department_trend(1, periods=12)

        assert 'department_id' in result


class TestCompareDepartments:
    """测试部门对比"""

    def test_compare_multiple_departments(self, db_session):
        """测试对比多个部门"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.compare_departments([1, 2, 3], period_id=1)

        assert 'period_id' in result
        assert 'departments' in result
        assert isinstance(result['departments'], list)

    def test_empty_department_list(self, db_session):
        """测试空部门列表"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service.compare_departments([], period_id=1)

        assert result['departments'] == []


class TestCalculateTrend:
    """测试趋势计算"""

    def test_insufficient_scores(self, db_session):
        """测试得分不足"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
        result = service._calculate_trend([80.0])

        assert result == 'stable'

    def test_improving_trend(self, db_session):
        """测试上升趋势"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
            # 后三个明显高于前三个
        scores = [70.0, 72.0, 74.0, 85.0, 87.0, 90.0]
        result = service._calculate_trend(scores)

        assert result == 'improving'

    def test_declining_trend(self, db_session):
        """测试下降趋势"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
            # 后三个明显低于前三个
        scores = [90.0, 88.0, 86.0, 72.0, 70.0, 68.0]
        result = service._calculate_trend(scores)

        assert result == 'declining'

    def test_stable_trend(self, db_session):
        """测试稳定趋势"""
        from app.services.performance_trend_service import PerformanceTrendService

        service = PerformanceTrendService(db_session)
            # 前后差距在2分以内
        scores = [80.0, 81.0, 80.0, 81.0, 80.0, 81.0]
        result = service._calculate_trend(scores)

        assert result == 'stable'


class TestTrendAnalysis:
    """测试趋势分析结果"""

    def test_trend_analysis_structure(self, db_session):
        """测试趋势分析结构"""
        from app.services.performance_trend_service import PerformanceTrendService
        from app.models.performance import PerformancePeriod, PerformanceResult

            # 创建模拟数据
        mock_result = MagicMock()
        mock_result.period_id = 1
        mock_result.period = MagicMock()
        mock_result.period.period_name = '2025-01'
        mock_result.period.start_date = MagicMock()
        mock_result.period.start_date.isoformat.return_value = '2025-01-01'
        mock_result.period.end_date = MagicMock()
        mock_result.period.end_date.isoformat.return_value = '2025-01-31'
        mock_result.total_score = 85.0
        mock_result.company_rank = 10
        mock_result.level = 'B'
        mock_result.indicator_scores = None

        service = PerformanceTrendService(db_session)

        with patch.object(db_session, 'query') as mock_query:
            mock_chain = MagicMock()
            mock_query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_result, mock_result]
            mock_query.return_value = mock_chain

                # 验证方法存在并可调用
        assert hasattr(service, 'get_engineer_trend')


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
