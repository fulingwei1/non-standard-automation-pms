# -*- coding: utf-8 -*-
"""
recommendation_service 单元测试

测试销售智能推荐服务。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.engines.base import (
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)
from app.services.sales.recommendation_service import SalesRecommendationService


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_engines():
    """模拟所有推荐引擎"""
    with patch("app.services.sales.recommendation_service.FollowUpEngine") as follow_up, \
         patch("app.services.sales.recommendation_service.PricingEngine") as pricing, \
         patch("app.services.sales.recommendation_service.RelationshipEngine") as relationship, \
         patch("app.services.sales.recommendation_service.CrossSellEngine") as cross_sell, \
         patch("app.services.sales.recommendation_service.RiskEngine") as risk:

        # 默认返回空列表
        follow_up.return_value.get_recommendations.return_value = []
        pricing.return_value.get_recommendations.return_value = []
        relationship.return_value.get_recommendations.return_value = []
        cross_sell.return_value.get_recommendations.return_value = []
        risk.return_value.get_recommendations.return_value = []

        yield {
            "follow_up": follow_up,
            "pricing": pricing,
            "relationship": relationship,
            "cross_sell": cross_sell,
            "risk": risk,
        }


@pytest.fixture
def service(mock_db, mock_engines):
    """创建带有模拟引擎的服务实例"""
    return SalesRecommendationService(mock_db)


@pytest.fixture
def sample_recommendations():
    """示例推荐列表"""
    return [
        Recommendation(
            type=RecommendationType.FOLLOW_UP,
            priority=RecommendationPriority.HIGH,
            title="跟进客户A",
            description="客户近期有采购计划",
            action="安排拜访",
            entity_type="opportunity",
            entity_id=1,
            confidence=0.9,
        ),
        Recommendation(
            type=RecommendationType.PRICING,
            priority=RecommendationPriority.MEDIUM,
            title="优化报价B",
            description="报价利润率偏低",
            action="调整定价",
            entity_type="quote",
            entity_id=2,
            confidence=0.8,
        ),
        Recommendation(
            type=RecommendationType.RISK,
            priority=RecommendationPriority.CRITICAL,
            title="合同即将到期",
            description="C公司合同将在30天内到期",
            action="启动续约流程",
            entity_type="contract",
            entity_id=3,
            confidence=0.95,
        ),
    ]


# ========== __init__ 测试 ==========

class TestInit:
    """__init__ 测试"""

    def test_creates_all_engines(self, mock_db, mock_engines):
        """初始化时创建所有引擎"""
        service = SalesRecommendationService(mock_db)

        mock_engines["follow_up"].assert_called_once_with(mock_db)
        mock_engines["pricing"].assert_called_once_with(mock_db)
        mock_engines["relationship"].assert_called_once_with(mock_db)
        mock_engines["cross_sell"].assert_called_once_with(mock_db)
        mock_engines["risk"].assert_called_once_with(mock_db)


# ========== get_recommendations 测试 ==========

class TestGetRecommendations:
    """get_recommendations 测试"""

    def test_returns_empty_when_no_recommendations(self, service):
        """无推荐时返回空结果"""
        result = service.get_recommendations(user_id=1)

        assert result.user_id == 1
        assert len(result.recommendations) == 0
        assert result.summary["total_count"] == 0

    def test_calls_all_engines_by_default(self, mock_db, mock_engines):
        """默认调用所有引擎"""
        service = SalesRecommendationService(mock_db)
        service.get_recommendations(user_id=1)

        mock_engines["follow_up"].return_value.get_recommendations.assert_called_once_with(1)
        mock_engines["pricing"].return_value.get_recommendations.assert_called_once_with(1)
        mock_engines["relationship"].return_value.get_recommendations.assert_called_once_with(1)
        mock_engines["cross_sell"].return_value.get_recommendations.assert_called_once_with(1)
        mock_engines["risk"].return_value.get_recommendations.assert_called_once_with(1)

    def test_filters_by_types(self, mock_db, mock_engines):
        """按类型过滤只调用相关引擎"""
        service = SalesRecommendationService(mock_db)
        service.get_recommendations(
            user_id=1,
            types=[RecommendationType.FOLLOW_UP, RecommendationType.RISK]
        )

        # 只应调用 follow_up 和 risk 引擎
        mock_engines["follow_up"].return_value.get_recommendations.assert_called_once()
        mock_engines["risk"].return_value.get_recommendations.assert_called_once()

        # 其他引擎不应被调用
        mock_engines["pricing"].return_value.get_recommendations.assert_not_called()
        mock_engines["relationship"].return_value.get_recommendations.assert_not_called()
        mock_engines["cross_sell"].return_value.get_recommendations.assert_not_called()

    def test_sorts_by_priority_and_confidence(self, mock_db, mock_engines, sample_recommendations):
        """按优先级和置信度排序"""
        # 设置引擎返回推荐
        mock_engines["follow_up"].return_value.get_recommendations.return_value = [sample_recommendations[0]]
        mock_engines["pricing"].return_value.get_recommendations.return_value = [sample_recommendations[1]]
        mock_engines["risk"].return_value.get_recommendations.return_value = [sample_recommendations[2]]

        service = SalesRecommendationService(mock_db)
        result = service.get_recommendations(user_id=1)

        # CRITICAL 应该排在最前面
        assert result.recommendations[0].priority == RecommendationPriority.CRITICAL
        assert result.recommendations[1].priority == RecommendationPriority.HIGH
        assert result.recommendations[2].priority == RecommendationPriority.MEDIUM

    def test_respects_limit(self, mock_db, mock_engines):
        """限制返回数量"""
        # 创建很多推荐
        many_recommendations = [
            Recommendation(
                type=RecommendationType.FOLLOW_UP,
                priority=RecommendationPriority.MEDIUM,
                title=f"推荐{i}",
                description=f"描述{i}",
                action="action",
                entity_type="opportunity",
                entity_id=i,
                confidence=0.5,
            )
            for i in range(30)
        ]
        mock_engines["follow_up"].return_value.get_recommendations.return_value = many_recommendations

        service = SalesRecommendationService(mock_db)
        result = service.get_recommendations(user_id=1, limit=10)

        assert len(result.recommendations) == 10

    def test_includes_generated_at_timestamp(self, service):
        """结果包含生成时间"""
        before = datetime.now()
        result = service.get_recommendations(user_id=1)
        after = datetime.now()

        assert before <= result.generated_at <= after


# ========== _generate_summary 测试 ==========

class TestGenerateSummary:
    """_generate_summary 测试"""

    def test_counts_by_type(self, service, sample_recommendations):
        """按类型统计"""
        summary = service._generate_summary(sample_recommendations)

        assert summary["by_type"]["follow_up"] == 1
        assert summary["by_type"]["pricing"] == 1
        assert summary["by_type"]["risk"] == 1

    def test_counts_by_priority(self, service, sample_recommendations):
        """按优先级统计"""
        summary = service._generate_summary(sample_recommendations)

        assert summary["by_priority"]["critical"] == 1
        assert summary["by_priority"]["high"] == 1
        assert summary["by_priority"]["medium"] == 1

    def test_counts_critical_and_high(self, service, sample_recommendations):
        """统计紧急和高优先级数量"""
        summary = service._generate_summary(sample_recommendations)

        assert summary["critical_count"] == 1
        assert summary["high_count"] == 1

    def test_empty_recommendations(self, service):
        """空推荐列表"""
        summary = service._generate_summary([])

        assert summary["total_count"] == 0
        assert summary["by_type"] == {}
        assert summary["by_priority"] == {}
        assert summary["critical_count"] == 0
        assert summary["high_count"] == 0

    def test_total_count(self, service, sample_recommendations):
        """总数统计"""
        summary = service._generate_summary(sample_recommendations)
        assert summary["total_count"] == 3


# ========== get_opportunity_recommendations 测试 ==========

class TestGetOpportunityRecommendations:
    """get_opportunity_recommendations 测试"""

    def test_returns_empty_for_nonexistent_opportunity(self, service, mock_db):
        """不存在的商机返回空列表"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = service.get_opportunity_recommendations(opportunity_id=999)

        assert result == []

    def test_discovery_stage_recommendations(self, service, mock_db):
        """DISCOVERY阶段推荐"""
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.stage = "DISCOVERY"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opp

        result = service.get_opportunity_recommendations(opportunity_id=1)

        assert len(result) == 3  # DISCOVERY 阶段有3个推荐
        titles = [r.title for r in result]
        assert "确认客户痛点" in titles
        assert "识别决策链" in titles
        assert "评估预算" in titles

    def test_qualification_stage_recommendations(self, service, mock_db):
        """QUALIFICATION阶段推荐"""
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.stage = "QUALIFICATION"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opp

        result = service.get_opportunity_recommendations(opportunity_id=1)

        assert len(result) == 3
        titles = [r.title for r in result]
        assert "验证技术可行性" in titles
        assert "竞争分析" in titles
        assert "建立高层关系" in titles

    def test_proposal_stage_recommendations(self, service, mock_db):
        """PROPOSAL阶段推荐"""
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.stage = "PROPOSAL"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opp

        result = service.get_opportunity_recommendations(opportunity_id=1)

        assert len(result) == 3
        titles = [r.title for r in result]
        assert "定制化方案" in titles

    def test_negotiation_stage_recommendations(self, service, mock_db):
        """NEGOTIATION阶段推荐"""
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.stage = "NEGOTIATION"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opp

        result = service.get_opportunity_recommendations(opportunity_id=1)

        assert len(result) == 3
        titles = [r.title for r in result]
        assert "灵活谈判" in titles
        assert "处理异议" in titles
        assert "推动签约" in titles

    def test_unknown_stage_returns_empty(self, service, mock_db):
        """未知阶段返回空列表"""
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.stage = "UNKNOWN_STAGE"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opp

        result = service.get_opportunity_recommendations(opportunity_id=1)

        assert result == []

    def test_recommendations_include_entity_info(self, service, mock_db):
        """推荐包含实体信息"""
        mock_opp = MagicMock()
        mock_opp.id = 42
        mock_opp.stage = "DISCOVERY"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opp

        result = service.get_opportunity_recommendations(opportunity_id=42)

        for rec in result:
            assert rec.entity_type == "opportunity"
            assert rec.entity_id == 42


# ========== 优先级排序测试 ==========

class TestPrioritySorting:
    """优先级排序测试"""

    def test_critical_before_high(self, mock_db, mock_engines):
        """CRITICAL优先于HIGH"""
        critical_rec = Recommendation(
            type=RecommendationType.RISK,
            priority=RecommendationPriority.CRITICAL,
            title="紧急",
            description="",
            action="",
            entity_type="contract",
            entity_id=1,
            confidence=0.5,
        )
        high_rec = Recommendation(
            type=RecommendationType.FOLLOW_UP,
            priority=RecommendationPriority.HIGH,
            title="高优先",
            description="",
            action="",
            entity_type="opportunity",
            entity_id=2,
            confidence=0.9,  # 更高置信度但优先级低
        )

        mock_engines["risk"].return_value.get_recommendations.return_value = [critical_rec]
        mock_engines["follow_up"].return_value.get_recommendations.return_value = [high_rec]

        service = SalesRecommendationService(mock_db)
        result = service.get_recommendations(user_id=1)

        assert result.recommendations[0].priority == RecommendationPriority.CRITICAL
        assert result.recommendations[1].priority == RecommendationPriority.HIGH

    def test_same_priority_sorted_by_confidence(self, mock_db, mock_engines):
        """相同优先级按置信度排序"""
        rec1 = Recommendation(
            type=RecommendationType.FOLLOW_UP,
            priority=RecommendationPriority.HIGH,
            title="推荐1",
            description="",
            action="",
            entity_type="opportunity",
            entity_id=1,
            confidence=0.7,
        )
        rec2 = Recommendation(
            type=RecommendationType.FOLLOW_UP,
            priority=RecommendationPriority.HIGH,
            title="推荐2",
            description="",
            action="",
            entity_type="opportunity",
            entity_id=2,
            confidence=0.9,
        )

        mock_engines["follow_up"].return_value.get_recommendations.return_value = [rec1, rec2]

        service = SalesRecommendationService(mock_db)
        result = service.get_recommendations(user_id=1)

        # 置信度高的应该在前
        assert result.recommendations[0].confidence == 0.9
        assert result.recommendations[1].confidence == 0.7
