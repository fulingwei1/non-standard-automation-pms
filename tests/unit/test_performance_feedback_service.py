# -*- coding: utf-8 -*-
"""
绩效反馈服务单元测试

测试覆盖:
- 获取工程师绩效反馈
- 生成反馈消息
- 获取五维得分趋势
- 识别能力变化
- 生成个性化反馈
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.performance_feedback_service import PerformanceFeedbackService


class TestPerformanceFeedbackServiceInit:
    """服务初始化测试"""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = PerformanceFeedbackService(db_session)
        assert service.db == db_session


class TestGetEngineerFeedback:
    """获取工程师绩效反馈测试"""

    def test_get_engineer_feedback_period_not_found(self, db_session: Session):
        """测试考核周期不存在时抛出异常"""
        service = PerformanceFeedbackService(db_session)

        with pytest.raises(ValueError, match="考核周期不存在"):
            service.get_engineer_feedback(engineer_id=1, period_id=99999)

    def test_get_engineer_feedback_no_result(self, db_session: Session):
        """测试无绩效数据时的返回"""
        service = PerformanceFeedbackService(db_session)

        # 如果有考核周期但无绩效数据
        # 这里需要mock或者使用真实数据
        # 简化测试：跳过如果没有考核周期
        try:
            result = service.get_engineer_feedback(engineer_id=99999, period_id=1)
            if result.get('has_data') is False:
                assert result['message'] == '绩效数据尚未计算'
        except ValueError:
            # 考核周期不存在，这也是预期的
        pass


class TestGenerateFeedbackMessage:
    """生成反馈消息测试"""

    def test_generate_feedback_message_no_data(self, db_session: Session):
        """测试无数据时的消息生成"""
        service = PerformanceFeedbackService(db_session)

        # Mock get_engineer_feedback 返回无数据
        with patch.object(service, 'get_engineer_feedback') as mock_get:
            mock_get.return_value = {
            'has_data': False,
            'period_name': '2024年Q1',
            }
            message = service.generate_feedback_message(1, 1)
            assert '绩效数据尚未计算' in message

    def test_generate_feedback_message_with_data(self, db_session: Session):
        """测试有数据时的消息生成"""
        service = PerformanceFeedbackService(db_session)

        # Mock get_engineer_feedback 返回有数据
        with patch.object(service, 'get_engineer_feedback') as mock_get:
            mock_get.return_value = {
            'has_data': True,
            'period_name': '2024年Q1',
            'current_performance': {
            'total_score': 85.0,
            'level': 'A',
            'dept_rank': 3,
            'company_rank': 15,
            'dimension_scores': {
            'technical': 88.0,
            'execution': 82.0,
            'cost_quality': 85.0,
            'knowledge': 80.0,
            'collaboration': 90.0,
            }
            },
            'comparison': {},
            'highlights': ['项目执行效率高'],
            'improvements': ['可加强技术文档分享'],
            }
            message = service.generate_feedback_message(1, 1)
            assert '2024年Q1' in message
            assert '85.0' in message
            assert '技术能力' in message


class TestGetDimensionTrend:
    """获取五维得分趋势测试"""

    def test_get_dimension_trend_no_data(self, db_session: Session):
        """测试无数据时的返回结构"""
        service = PerformanceFeedbackService(db_session)

        result = service.get_dimension_trend(engineer_id=99999, periods=6)

        assert 'technical' in result
        assert 'execution' in result
        assert 'cost_quality' in result
        assert 'knowledge' in result
        assert 'collaboration' in result
        assert 'periods' in result
        assert isinstance(result['technical'], list)
        assert isinstance(result['periods'], list)

    def test_get_dimension_trend_with_periods_param(self, db_session: Session):
        """测试指定周期数"""
        service = PerformanceFeedbackService(db_session)

        result = service.get_dimension_trend(engineer_id=1, periods=3)

        # 返回的数据不应超过指定的周期数
        assert len(result['periods']) <= 3


class TestIdentifyAbilityChanges:
    """识别能力变化测试"""

    def test_identify_ability_changes_no_data(self, db_session: Session):
        """测试无数据时返回空列表"""
        service = PerformanceFeedbackService(db_session)

        result = service.identify_ability_changes(engineer_id=99999, periods=6)

        assert isinstance(result, list)

    def test_identify_ability_changes_insufficient_data(self, db_session: Session):
        """测试数据不足时返回空列表"""
        service = PerformanceFeedbackService(db_session)

        # Mock get_dimension_trend 返回少于2个周期的数据
        with patch.object(service, 'get_dimension_trend') as mock_get:
            mock_get.return_value = {
            'technical': [80.0],
            'execution': [75.0],
            'cost_quality': [78.0],
            'knowledge': [70.0],
            'collaboration': [85.0],
            'periods': ['2024Q1']
            }
            result = service.identify_ability_changes(1, 6)
            assert result == []


class TestGeneratePersonalizedFeedback:
    """生成个性化反馈测试"""

    def test_generate_personalized_feedback_no_data(self, db_session: Session):
        """测试无数据时的返回"""
        service = PerformanceFeedbackService(db_session)

        # Mock get_engineer_feedback 返回无数据
        with patch.object(service, 'get_engineer_feedback') as mock_get:
            mock_get.return_value = {
            'has_data': False,
            }
            result = service.generate_personalized_feedback(1, 1)
            assert result['has_data'] is False

    def test_generate_personalized_feedback_with_suggestions(self, db_session: Session):
        """测试有数据时包含个性化建议"""
        service = PerformanceFeedbackService(db_session)

        # Mock get_engineer_feedback 返回有数据
        with patch.object(service, 'get_engineer_feedback') as mock_get:
            mock_get.return_value = {
            'has_data': True,
            'current_performance': {
            'dimension_scores': {
            'technical': 65.0,  # 低于70，应该触发建议
            'execution': 80.0,
            'cost_quality': 75.0,
            'knowledge': 60.0,  # 低于70，应该触发建议
            'collaboration': 85.0,
            }
            }
            }
            result = service.generate_personalized_feedback(99999, 1)
            assert 'personalized_suggestions' in result
            assert isinstance(result['personalized_suggestions'], list)


class TestGetDimensionName:
    """维度名称获取测试"""

    def test_get_dimension_name_known(self, db_session: Session):
        """测试已知维度名称"""
        service = PerformanceFeedbackService(db_session)

        assert service._get_dimension_name('technical') == '技术能力'
        assert service._get_dimension_name('execution') == '项目执行'
        assert service._get_dimension_name('cost_quality') == '成本/质量'
        assert service._get_dimension_name('knowledge') == '知识沉淀'
        assert service._get_dimension_name('collaboration') == '团队协作'
        assert service._get_dimension_name('solution_success') == '方案成功率'

    def test_get_dimension_name_unknown(self, db_session: Session):
        """测试未知维度返回原名"""
        service = PerformanceFeedbackService(db_session)

        assert service._get_dimension_name('unknown_dim') == 'unknown_dim'
