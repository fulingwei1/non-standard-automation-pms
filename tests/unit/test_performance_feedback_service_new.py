# -*- coding: utf-8 -*-
"""
绩效反馈服务单元测试补充 (F组)

使用 MagicMock 测试 PerformanceFeedbackService 的关键方法：
- get_engineer_feedback
- generate_feedback_message
- get_dimension_trend
- identify_ability_changes
- _get_dimension_name
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.performance_feedback_service import PerformanceFeedbackService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return PerformanceFeedbackService(db)


# ============================================================
# get_engineer_feedback 测试
# ============================================================

class TestGetEngineerFeedback:

    def test_period_not_found(self, service, db):
        """测试考核周期不存在时抛出异常"""
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="考核周期不存在"):
            service.get_engineer_feedback(engineer_id=1, period_id=999)

    def test_no_result_data(self, service, db):
        """测试无绩效数据时返回has_data=False"""
        period = MagicMock(id=1, period_name="2025Q1", start_date=None)
        # period found, but result not found
        db.query.return_value.filter.return_value.first.side_effect = [period, None]
        result = service.get_engineer_feedback(engineer_id=1, period_id=1)
        assert result["has_data"] is False
        assert result["message"] == "绩效数据尚未计算"

    def test_with_result_no_previous(self, service, db):
        """测试有绩效数据但无历史记录"""
        from decimal import Decimal
        period = MagicMock(id=1, period_name="2025Q1", start_date=None, end_date=None)
        perf_result = MagicMock(
            id=1, user_id=1, period_id=1,
            total_score=Decimal("85.0"),
            level="B",
            dept_rank=3, company_rank=10,
            highlights=["按时交付"],
            improvements=["提升沟通效率"],
            indicator_scores={
                "technical_score": 80,
                "execution_score": 85,
                "cost_quality_score": 82,
                "knowledge_score": 78,
                "collaboration_score": 90,
            }
        )
        # period found, result found, previous_result not found
        db.query.return_value.filter.return_value.first.side_effect = [period, perf_result, None]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.first.side_effect = [period, perf_result, None, None]

        result = service.get_engineer_feedback(engineer_id=1, period_id=1)
        assert result["has_data"] is True
        assert result["period_name"] == "2025Q1"
        assert result["current_performance"]["level"] == "B"
        assert result["comparison"] == {}

    def test_with_indicator_scores(self, service, db):
        """测试从indicator_scores获取五维得分"""
        from decimal import Decimal
        period = MagicMock(id=1, period_name="2025Q1", start_date=None)
        perf_result = MagicMock(
            total_score=Decimal("80"),
            level="B", dept_rank=2, company_rank=5,
            highlights=[], improvements=[],
            indicator_scores={
                "technical_score": 75,
                "execution_score": 80,
                "cost_quality_score": 78,
                "knowledge_score": 82,
                "collaboration_score": 85,
            }
        )
        db.query.return_value.filter.return_value.first.side_effect = [period, perf_result, None, None]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = service.get_engineer_feedback(engineer_id=1, period_id=1)
        dim_scores = result["current_performance"]["dimension_scores"]
        assert dim_scores["technical"] == 75.0
        assert dim_scores["collaboration"] == 85.0


# ============================================================
# generate_feedback_message 测试
# ============================================================

class TestGenerateFeedbackMessage:

    def test_no_data_message(self, service):
        """测试无数据时返回提示消息"""
        with patch.object(service, 'get_engineer_feedback', return_value={
            'has_data': False,
            'period_name': '2025Q1',
            'message': '绩效数据尚未计算'
        }):
            msg = service.generate_feedback_message(1, 1)
        assert "2025Q1" in msg
        assert "尚未计算" in msg

    def test_message_includes_scores(self, service):
        """测试生成的消息包含分数信息"""
        with patch.object(service, 'get_engineer_feedback', return_value={
            'has_data': True,
            'period_name': '2025Q1',
            'current_performance': {
                'total_score': 85.0,
                'level': 'B',
                'dept_rank': 3,
                'company_rank': 10,
                'dimension_scores': {
                    'technical': 80.0, 'execution': 85.0,
                    'cost_quality': 82.0, 'knowledge': 78.0,
                    'collaboration': 90.0
                }
            },
            'comparison': {},
            'highlights': ['项目按时完成'],
            'improvements': ['加强文档']
        }):
            msg = service.generate_feedback_message(1, 1)
        assert "2025Q1" in msg
        assert "85.0" in msg
        assert "B" in msg
        assert "项目按时完成" in msg
        assert "加强文档" in msg

    def test_message_with_score_improvement(self, service):
        """测试得分提升时包含积极信息"""
        with patch.object(service, 'get_engineer_feedback', return_value={
            'has_data': True,
            'period_name': '2025Q1',
            'current_performance': {
                'total_score': 90.0,
                'level': 'A',
                'dept_rank': 1,
                'company_rank': 3,
                'dimension_scores': {
                    'technical': 88.0, 'execution': 92.0,
                    'cost_quality': 88.0, 'knowledge': 90.0,
                    'collaboration': 92.0
                }
            },
            'comparison': {
                'score_change': 5.0,
                'rank_change': -2,  # 排名上升
            },
            'highlights': [],
            'improvements': []
        }):
            msg = service.generate_feedback_message(1, 1)
        assert "📈" in msg
        assert "⬆️" in msg


# ============================================================
# _get_dimension_name 测试
# ============================================================

class TestGetDimensionName:

    def test_known_dimensions(self, service):
        """测试已知维度名称"""
        assert service._get_dimension_name("technical") == "技术能力"
        assert service._get_dimension_name("execution") == "项目执行"
        assert service._get_dimension_name("cost_quality") == "成本/质量"
        assert service._get_dimension_name("knowledge") == "知识沉淀"
        assert service._get_dimension_name("collaboration") == "团队协作"
        assert service._get_dimension_name("solution_success") == "方案成功率"

    def test_unknown_dimension(self, service):
        """测试未知维度返回原名"""
        assert service._get_dimension_name("unknown_dim") == "unknown_dim"


# ============================================================
# get_dimension_trend 测试
# ============================================================

class TestGetDimensionTrend:

    def test_no_results(self, service, db):
        """测试无历史数据"""
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = service.get_dimension_trend(1, periods=6)
        assert result["technical"] == []
        assert result["execution"] == []
        assert result["periods"] == []

    def test_with_indicator_scores(self, service, db):
        """测试有indicator_scores时的趋势"""
        r1 = MagicMock(
            indicator_scores={"technical_score": 80, "execution_score": 75, "cost_quality_score": 78,
                              "knowledge_score": 82, "collaboration_score": 85},
            period=MagicMock(period_name="2024Q4", start_date=None)
        )
        r2 = MagicMock(
            indicator_scores={"technical_score": 85, "execution_score": 80, "cost_quality_score": 82,
                              "knowledge_score": 88, "collaboration_score": 88},
            period=MagicMock(period_name="2025Q1", start_date=None)
        )
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [r2, r1]
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_dimension_trend(1, periods=6)
        assert len(result["technical"]) == 2
        assert len(result["periods"]) == 2
        assert result["technical"][0] == 80.0  # reversed order

    def test_without_indicator_scores_uses_defaults(self, service, db):
        """测试无indicator_scores时使用默认值75"""
        r1 = MagicMock(
            indicator_scores=None,
            period=MagicMock(period_name="2024Q4")
        )
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [r1]
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_dimension_trend(1, periods=6)
        assert result["technical"] == [75.0]
        assert result["execution"] == [75.0]


# ============================================================
# identify_ability_changes 测试
# ============================================================

class TestIdentifyAbilityChanges:

    def test_insufficient_data(self, service):
        """测试历史数据不足时返回空列表"""
        with patch.object(service, 'get_dimension_trend', return_value={
            'technical': [80.0], 'execution': [], 'cost_quality': [],
            'knowledge': [], 'collaboration': [], 'periods': []
        }):
            result = service.identify_ability_changes(1, periods=6)
        assert result == []

    def test_improving_trend(self, service):
        """测试上升趋势识别"""
        with patch.object(service, 'get_dimension_trend', return_value={
            'technical': [60.0, 65.0, 70.0, 75.0, 80.0, 85.0],
            'execution': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'cost_quality': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'knowledge': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'collaboration': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'periods': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']
        }):
            result = service.identify_ability_changes(1, periods=6)
        technical_change = next((c for c in result if c['dimension'] == 'technical'), None)
        assert technical_change is not None
        assert technical_change['trend'] == 'improving'

    def test_declining_trend(self, service):
        """测试下降趋势识别"""
        with patch.object(service, 'get_dimension_trend', return_value={
            'technical': [90.0, 85.0, 80.0, 75.0, 70.0, 65.0],
            'execution': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'cost_quality': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'knowledge': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'collaboration': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'periods': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']
        }):
            result = service.identify_ability_changes(1, periods=6)
        technical_change = next((c for c in result if c['dimension'] == 'technical'), None)
        assert technical_change is not None
        assert technical_change['trend'] == 'declining'

    def test_stable_no_change(self, service):
        """测试稳定时不记录变化（变化<5分）"""
        with patch.object(service, 'get_dimension_trend', return_value={
            'technical': [75.0, 76.0, 74.0, 75.0, 76.0, 75.0],
            'execution': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'cost_quality': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'knowledge': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'collaboration': [75.0, 75.0, 75.0, 75.0, 75.0, 75.0],
            'periods': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']
        }):
            result = service.identify_ability_changes(1, periods=6)
        assert result == []
