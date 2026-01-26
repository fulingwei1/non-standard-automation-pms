# -*- coding: utf-8 -*-
"""
PerformanceFeedbackService 单元测试
测试绩效反馈服务的各项功能
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.engineer_performance import EngineerProfile
from app.models.performance import PerformancePeriod, PerformanceResult
from app.services.performance_feedback_service import PerformanceFeedbackService


class TestPerformanceFeedbackServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock(spec=Session)
        service = PerformanceFeedbackService(mock_db)
        assert service.db == mock_db


class TestGetEngineerFeedback:
    """测试获取工程师绩效反馈"""

    def test_period_not_found_raises_error(self):
        """测试考核周期不存在时抛出异常"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = PerformanceFeedbackService(mock_db)

        with pytest.raises(ValueError, match="考核周期不存在"):
            service.get_engineer_feedback(engineer_id=1, period_id=999)

    def test_no_result_returns_no_data_message(self):
        """测试无绩效结果时返回无数据消息"""
        mock_db = MagicMock(spec=Session)

        mock_period = Mock(spec=PerformancePeriod)
        mock_period.id = 1
        mock_period.period_name = "2024年Q1"

        # 第一次查询返回周期，第二次查询返回None（无结果）
        query_period = MagicMock()
        query_period.filter.return_value.first.return_value = mock_period

        query_result = MagicMock()
        query_result.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_period, query_result]

        service = PerformanceFeedbackService(mock_db)
        result = service.get_engineer_feedback(engineer_id=1, period_id=1)

        assert result['has_data'] is False
        assert result['message'] == '绩效数据尚未计算'

    def test_get_feedback_with_indicator_scores(self):
        """测试有指标得分的反馈"""
        mock_db = MagicMock(spec=Session)

        mock_period = Mock(spec=PerformancePeriod)
        mock_period.id = 1
        mock_period.period_name = "2024年Q1"
        mock_period.start_date = date(2024, 1, 1)

        mock_result = Mock(spec=PerformanceResult)
        mock_result.total_score = Decimal("85.5")
        mock_result.level = "A"
        mock_result.dept_rank = 2
        mock_result.company_rank = 10
        mock_result.highlights = ["表现优秀"]
        mock_result.improvements = ["继续加油"]
        mock_result.indicator_scores = {
            'technical_score': 88,
            'execution_score': 85,
            'cost_quality_score': 82,
            'knowledge_score': 80,
            'collaboration_score': 90
        }

        # 配置查询
        query_period = MagicMock()
        query_period.filter.return_value.first.return_value = mock_period

        query_result = MagicMock()
        query_result.filter.return_value.first.return_value = mock_result

        query_previous = MagicMock()
        query_previous.join.return_value.filter.return_value.order_by.return_value.first.return_value = None

        query_profile = MagicMock()
        query_profile.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_period, query_result, query_previous, query_profile]

        service = PerformanceFeedbackService(mock_db)
        result = service.get_engineer_feedback(engineer_id=1, period_id=1)

        assert result['has_data'] is True
        assert result['current_performance']['total_score'] == 85.5
        assert result['current_performance']['level'] == "A"
        assert result['current_performance']['dimension_scores']['technical'] == 88.0

    def test_get_feedback_with_comparison(self):
        """测试有历史对比的反馈"""
        mock_db = MagicMock(spec=Session)

        mock_period = Mock(spec=PerformancePeriod)
        mock_period.id = 2
        mock_period.period_name = "2024年Q2"
        mock_period.start_date = date(2024, 4, 1)

        mock_result = Mock(spec=PerformanceResult)
        mock_result.total_score = Decimal("88")
        mock_result.level = "A"
        mock_result.dept_rank = 1
        mock_result.company_rank = 5
        mock_result.highlights = []
        mock_result.improvements = []
        mock_result.indicator_scores = {
            'technical_score': 90,
            'execution_score': 88,
            'cost_quality_score': 85,
            'knowledge_score': 85,
            'collaboration_score': 92
        }

        mock_previous = Mock(spec=PerformanceResult)
        mock_previous.total_score = Decimal("82")
        mock_previous.level = "B"
        mock_previous.dept_rank = 3
        mock_previous.company_rank = 12
        mock_previous.indicator_scores = {
            'technical_score': 80,
            'execution_score': 82,
            'cost_quality_score': 80,
            'knowledge_score': 78,
            'collaboration_score': 85
        }

        # 配置查询
        query_period = MagicMock()
        query_period.filter.return_value.first.return_value = mock_period

        query_result = MagicMock()
        query_result.filter.return_value.first.return_value = mock_result

        query_previous = MagicMock()
        query_previous.join.return_value.filter.return_value.order_by.return_value.first.return_value = mock_previous

        query_profile = MagicMock()
        query_profile.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_period, query_result, query_previous, query_profile]

        service = PerformanceFeedbackService(mock_db)
        result = service.get_engineer_feedback(engineer_id=1, period_id=2)

        assert result['comparison']['score_change'] == 6.0
        assert result['comparison']['rank_change'] == -7  # 排名上升
        assert result['comparison']['level_change'] is True


class TestGetDimensionName:
    """测试获取维度中文名称"""

    def test_get_known_dimension_names(self):
        """测试获取已知维度名称"""
        mock_db = MagicMock(spec=Session)
        service = PerformanceFeedbackService(mock_db)

        assert service._get_dimension_name('technical') == '技术能力'
        assert service._get_dimension_name('execution') == '项目执行'
        assert service._get_dimension_name('cost_quality') == '成本/质量'
        assert service._get_dimension_name('knowledge') == '知识沉淀'
        assert service._get_dimension_name('collaboration') == '团队协作'
        assert service._get_dimension_name('solution_success') == '方案成功率'

    def test_get_unknown_dimension_name(self):
        """测试获取未知维度名称返回原名"""
        mock_db = MagicMock(spec=Session)
        service = PerformanceFeedbackService(mock_db)

        assert service._get_dimension_name('unknown') == 'unknown'


class TestGenerateFeedbackMessage:
    """测试生成反馈消息"""

    @patch.object(PerformanceFeedbackService, 'get_engineer_feedback')
    def test_generate_message_no_data(self, mock_get_feedback):
        """测试无数据时生成消息"""
        mock_db = MagicMock(spec=Session)
        mock_get_feedback.return_value = {
            'has_data': False,
            'period_name': '2024年Q1'
        }

        service = PerformanceFeedbackService(mock_db)
        result = service.generate_feedback_message(engineer_id=1, period_id=1)

        assert '尚未计算' in result

    @patch.object(PerformanceFeedbackService, 'get_engineer_feedback')
    def test_generate_message_with_data(self, mock_get_feedback):
        """测试有数据时生成消息"""
        mock_db = MagicMock(spec=Session)
        mock_get_feedback.return_value = {
            'has_data': True,
            'period_name': '2024年Q1',
            'current_performance': {
                'total_score': 85.5,
                'level': 'A',
                'dept_rank': 2,
                'company_rank': 10,
                'dimension_scores': {
                    'technical': 88.0,
                    'execution': 85.0,
                    'cost_quality': 82.0,
                    'knowledge': 80.0,
                    'collaboration': 90.0
                }
            },
            'comparison': {},
            'highlights': ['表现优秀'],
            'improvements': ['继续加油']
        }

        service = PerformanceFeedbackService(mock_db)
        result = service.generate_feedback_message(engineer_id=1, period_id=1)

        assert '2024年Q1' in result
        assert '85.5分' in result
        assert '等级：A' in result
        assert '技术能力' in result
        assert '表现优秀' in result

    @patch.object(PerformanceFeedbackService, 'get_engineer_feedback')
    def test_generate_message_with_score_improvement(self, mock_get_feedback):
        """测试得分提升时的消息"""
        mock_db = MagicMock(spec=Session)
        mock_get_feedback.return_value = {
            'has_data': True,
            'period_name': '2024年Q2',
            'current_performance': {
                'total_score': 90.0,
                'level': 'A',
                'dept_rank': 1,
                'company_rank': 5,
                'dimension_scores': {
                    'technical': 92.0,
                    'execution': 88.0,
                    'cost_quality': 85.0,
                    'knowledge': 88.0,
                    'collaboration': 95.0
                }
            },
            'comparison': {
                'score_change': 5.0,
                'rank_change': -3  # 上升3名
            },
            'highlights': [],
            'improvements': []
        }

        service = PerformanceFeedbackService(mock_db)
        result = service.generate_feedback_message(engineer_id=1, period_id=2)

        assert '📈' in result  # 得分提升标识
        assert '⬆️' in result  # 排名上升标识


class TestGetDimensionTrend:
    """测试获取五维得分趋势"""

    def test_no_results_returns_empty_trends(self):
        """测试无结果时返回空趋势"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = PerformanceFeedbackService(mock_db)
        result = service.get_dimension_trend(engineer_id=1, periods=6)

        assert result['technical'] == []
        assert result['periods'] == []

    def test_get_trends_with_indicator_scores(self):
        """测试从指标得分获取趋势"""
        mock_db = MagicMock(spec=Session)

        mock_period1 = Mock()
        mock_period1.period_name = "2024Q1"

        mock_result1 = Mock(spec=PerformanceResult)
        mock_result1.indicator_scores = {
            'technical_score': 80,
            'execution_score': 82,
            'cost_quality_score': 78,
            'knowledge_score': 75,
            'collaboration_score': 85
        }
        mock_result1.period = mock_period1

        # 配置查询
        query_results = MagicMock()
        query_results.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_result1]

        query_profile = MagicMock()
        query_profile.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_results, query_profile]

        service = PerformanceFeedbackService(mock_db)
        result = service.get_dimension_trend(engineer_id=1, periods=6)

        assert len(result['technical']) == 1
        assert result['technical'][0] == 80.0
        assert result['periods'][0] == "2024Q1"


class TestIdentifyAbilityChanges:
    """测试识别能力变化"""

    @patch.object(PerformanceFeedbackService, 'get_dimension_trend')
    def test_insufficient_data_returns_empty(self, mock_get_trend):
        """测试数据不足时返回空"""
        mock_db = MagicMock(spec=Session)
        mock_get_trend.return_value = {
            'technical': [80],  # 只有一个周期
            'execution': [82],
            'cost_quality': [78],
            'knowledge': [75],
            'collaboration': [85],
            'periods': ['2024Q1']
        }

        service = PerformanceFeedbackService(mock_db)
        result = service.identify_ability_changes(engineer_id=1)

        assert result == []

    @patch.object(PerformanceFeedbackService, 'get_dimension_trend')
    def test_identify_significant_changes(self, mock_get_trend):
        """测试识别显著变化"""
        mock_db = MagicMock(spec=Session)
        mock_get_trend.return_value = {
            'technical': [70, 72, 75, 80, 85, 90],  # 显著提升
            'execution': [80, 80, 80, 80, 80, 80],  # 稳定
            'cost_quality': [85, 82, 78, 75, 72, 70],  # 显著下降
            'knowledge': [75, 76, 77, 78, 79, 80],  # 轻微提升
            'collaboration': [85, 85, 85, 85, 85, 85],  # 稳定
            'periods': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']
        }

        service = PerformanceFeedbackService(mock_db)
        result = service.identify_ability_changes(engineer_id=1)

        # 应该识别出技术能力提升和成本质量下降
        assert len(result) >= 2
        dim_names = [r['dimension'] for r in result]
        assert 'technical' in dim_names
        assert 'cost_quality' in dim_names


class TestGeneratePersonalizedFeedback:
    """测试生成个性化反馈"""

    @patch.object(PerformanceFeedbackService, 'get_engineer_feedback')
    def test_no_data_returns_feedback_as_is(self, mock_get_feedback):
        """测试无数据时直接返回反馈"""
        mock_db = MagicMock(spec=Session)
        mock_get_feedback.return_value = {'has_data': False}

        query_profile = MagicMock()
        query_profile.filter.return_value.first.return_value = None
        mock_db.query.return_value = query_profile

        service = PerformanceFeedbackService(mock_db)
        result = service.generate_personalized_feedback(engineer_id=1, period_id=1)

        assert result['has_data'] is False

    @patch.object(PerformanceFeedbackService, 'get_engineer_feedback')
    def test_personalized_for_mechanical_engineer(self, mock_get_feedback):
        """测试为机械工程师生成个性化反馈"""
        mock_db = MagicMock(spec=Session)

        mock_profile = Mock(spec=EngineerProfile)
        mock_profile.job_type = 'mechanical'

        mock_get_feedback.return_value = {
            'has_data': True,
            'current_performance': {
                'dimension_scores': {
                    'technical': 85.0,
                    'execution': 80.0,
                    'cost_quality': 75.0,
                    'knowledge': 65.0,  # 低于70，应该有建议
                    'collaboration': 85.0
                }
            }
        }

        query_profile = MagicMock()
        query_profile.filter.return_value.first.return_value = mock_profile
        mock_db.query.return_value = query_profile

        service = PerformanceFeedbackService(mock_db)
        result = service.generate_personalized_feedback(engineer_id=1, period_id=1)

        assert 'personalized_suggestions' in result
        # 应该包含知识沉淀相关的改进建议
        suggestions_text = ' '.join(result['personalized_suggestions'])
        assert '知识沉淀' in suggestions_text

    @patch.object(PerformanceFeedbackService, 'get_engineer_feedback')
    def test_personalized_for_solution_engineer(self, mock_get_feedback):
        """测试为方案工程师生成个性化反馈"""
        mock_db = MagicMock(spec=Session)

        mock_profile = Mock(spec=EngineerProfile)
        mock_profile.job_type = 'solution'

        mock_get_feedback.return_value = {
            'has_data': True,
            'current_performance': {
                'dimension_scores': {
                    'technical': 85.0,
                    'execution': 80.0,
                    'cost_quality': 75.0,
                    'knowledge': 80.0,
                    'collaboration': 85.0
                }
            }
        }

        query_profile = MagicMock()
        query_profile.filter.return_value.first.return_value = mock_profile
        mock_db.query.return_value = query_profile

        service = PerformanceFeedbackService(mock_db)
        result = service.generate_personalized_feedback(engineer_id=1, period_id=1)

        assert 'personalized_suggestions' in result
        # 应该包含方案相关的建议
        suggestions_text = ' '.join(result['personalized_suggestions'])
        assert '方案' in suggestions_text
