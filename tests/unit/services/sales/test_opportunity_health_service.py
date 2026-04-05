# -*- coding: utf-8 -*-
"""
opportunity_health_service 单元测试

测试商机健康度评分服务。
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.opportunity_health_service import (
    OpportunityHealthService,
    HealthLevel,
    HealthDimension,
    DIMENSION_WEIGHTS,
    STAGE_TIME_THRESHOLDS,
)


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return OpportunityHealthService(mock_db)


@pytest.fixture
def mock_opportunity():
    """模拟商机"""
    opp = MagicMock()
    opp.id = 1
    opp.opp_code = "OP202603120001"
    opp.opp_name = "测试商机"
    opp.stage = "QUALIFICATION"
    opp.est_amount = 500000
    opp.probability = 60
    opp.expected_close_date = (datetime.now() + timedelta(days=30)).date()
    opp.project_type = "FCT"
    opp.risk_level = None
    opp.updated_at = datetime.now() - timedelta(days=5)
    opp.created_at = datetime.now() - timedelta(days=20)
    opp.customer_id = 1
    opp.customer = MagicMock()
    opp.customer.customer_name = "测试客户"
    opp.owner = MagicMock()
    opp.owner.real_name = "张三"
    opp.lead = None
    return opp


# ========== 健康等级判定测试 ==========

class TestGetHealthLevel:
    """_get_health_level 测试"""

    def test_excellent_for_high_score(self, service):
        """高分为优秀"""
        assert service._get_health_level(85) == HealthLevel.EXCELLENT
        assert service._get_health_level(100) == HealthLevel.EXCELLENT

    def test_good_for_medium_high_score(self, service):
        """中高分为良好"""
        assert service._get_health_level(70) == HealthLevel.GOOD
        assert service._get_health_level(79) == HealthLevel.GOOD

    def test_warning_for_medium_score(self, service):
        """中分为警告"""
        assert service._get_health_level(50) == HealthLevel.WARNING
        assert service._get_health_level(59) == HealthLevel.WARNING

    def test_critical_for_low_score(self, service):
        """低分为危险"""
        assert service._get_health_level(30) == HealthLevel.CRITICAL
        assert service._get_health_level(0) == HealthLevel.CRITICAL


# ========== 活跃度得分测试 ==========

class TestCalculateActivityScore:
    """_calculate_activity_score 测试"""

    def test_high_score_for_recent_activity(self, service, mock_opportunity):
        """近期活动高分"""
        mock_opportunity.updated_at = datetime.now() - timedelta(days=2)
        score = service._calculate_activity_score(mock_opportunity)
        assert score.score == 100
        assert score.dimension == HealthDimension.ACTIVITY

    def test_medium_score_for_week_ago(self, service, mock_opportunity):
        """一周前活动中等分"""
        mock_opportunity.updated_at = datetime.now() - timedelta(days=6)
        score = service._calculate_activity_score(mock_opportunity)
        assert score.score == 80

    def test_low_score_for_long_inactive(self, service, mock_opportunity):
        """长期不活跃低分"""
        mock_opportunity.updated_at = datetime.now() - timedelta(days=25)
        score = service._calculate_activity_score(mock_opportunity)
        assert score.score == 20
        assert len(score.suggestions) > 0


# ========== 阶段进展得分测试 ==========

class TestCalculateStageScore:
    """_calculate_stage_score 测试"""

    def test_high_score_for_normal_progress(self, service, mock_opportunity):
        """正常进展高分"""
        mock_opportunity.stage = "QUALIFICATION"
        mock_opportunity.updated_at = datetime.now() - timedelta(days=3)
        score = service._calculate_stage_score(mock_opportunity)
        assert score.score >= 80

    def test_warning_for_slow_progress(self, service, mock_opportunity):
        """进展缓慢警告"""
        mock_opportunity.stage = "QUALIFICATION"
        thresholds = STAGE_TIME_THRESHOLDS["QUALIFICATION"]
        mock_opportunity.updated_at = datetime.now() - timedelta(days=thresholds["warning"] + 1)
        score = service._calculate_stage_score(mock_opportunity)
        assert score.score <= 50

    def test_critical_for_stale(self, service, mock_opportunity):
        """停滞危险"""
        mock_opportunity.stage = "QUALIFICATION"
        thresholds = STAGE_TIME_THRESHOLDS["QUALIFICATION"]
        mock_opportunity.updated_at = datetime.now() - timedelta(days=thresholds["critical"] + 1)
        score = service._calculate_stage_score(mock_opportunity)
        assert score.score <= 30


# ========== 信息完整度得分测试 ==========

class TestCalculateCompletenessScore:
    """_calculate_completeness_score 测试"""

    def test_full_score_for_complete_info(self, service, mock_opportunity):
        """完整信息满分"""
        mock_opportunity.customer_id = 1
        mock_opportunity.opp_name = "测试"
        mock_opportunity.est_amount = 100000
        mock_opportunity.expected_close_date = datetime.now().date()
        mock_opportunity.project_type = "FCT"
        mock_opportunity.probability = 50

        score = service._calculate_completeness_score(mock_opportunity)
        assert score.score == 100

    def test_partial_score_for_missing_fields(self, service, mock_opportunity):
        """缺失字段部分分"""
        mock_opportunity.est_amount = None
        mock_opportunity.expected_close_date = None

        score = service._calculate_completeness_score(mock_opportunity)
        assert score.score < 100
        assert len(score.suggestions) > 0


# ========== 客户互动度得分测试 ==========

class TestCalculateEngagementScore:
    """_calculate_engagement_score 测试"""

    def test_higher_score_with_quote(self, service, mock_db, mock_opportunity):
        """有报价加分"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 2

        score = service._calculate_engagement_score(mock_opportunity)
        assert score.score >= 75

    def test_lower_score_without_quote(self, service, mock_db, mock_opportunity):
        """无报价减分"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_opportunity.probability = 20

        score = service._calculate_engagement_score(mock_opportunity)
        assert score.score < 70


# ========== 风险因素得分测试 ==========

class TestCalculateRiskScore:
    """_calculate_risk_score 测试"""

    def test_high_score_no_risk(self, service, mock_opportunity):
        """无风险高分"""
        mock_opportunity.risk_level = None
        mock_opportunity.probability = 60
        mock_opportunity.expected_close_date = (datetime.now() + timedelta(days=30)).date()

        score = service._calculate_risk_score(mock_opportunity)
        assert score.score >= 80

    def test_lower_score_with_high_risk(self, service, mock_opportunity):
        """高风险减分"""
        mock_opportunity.risk_level = "HIGH"

        score = service._calculate_risk_score(mock_opportunity)
        assert score.score <= 75

    def test_lower_score_overdue_close_date(self, service, mock_opportunity):
        """成交日期过期减分"""
        mock_opportunity.expected_close_date = (datetime.now() - timedelta(days=10)).date()

        score = service._calculate_risk_score(mock_opportunity)
        assert score.score <= 70


# ========== 综合健康度测试 ==========

class TestGetOpportunityHealth:
    """get_opportunity_health 测试"""

    def test_returns_health_for_valid_opp(self, service, mock_db, mock_opportunity):
        """有效商机返回健康度"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_opportunity

        # Mock quote count query
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1

        health = service.get_opportunity_health(1)

        assert health is not None
        assert health.opportunity_id == 1
        assert health.total_score > 0
        assert len(health.dimension_scores) == 5

    def test_returns_none_for_invalid_opp(self, service, mock_db):
        """无效商机返回None"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        health = service.get_opportunity_health(999)

        assert health is None


# ========== 汇总统计测试 ==========

class TestGetHealthSummary:
    """get_health_summary 测试"""

    def test_summary_structure(self, service, mock_db):
        """汇总结构正确"""
        with patch.object(service, 'get_user_opportunities_health', return_value=[]):
            summary = service.get_health_summary(user_id=1)

        assert "total_count" in summary
        assert "by_level" in summary
        assert "average_score" in summary
        assert "problem_opportunities" in summary
        assert "excellent" in summary["by_level"]
        assert "critical" in summary["by_level"]

    def test_counts_by_level(self, service, mock_db, mock_opportunity):
        """按等级统计"""
        from app.services.sales.opportunity_health_service import OpportunityHealth, DimensionScore

        mock_health = OpportunityHealth(
            opportunity_id=1,
            opportunity_code="OP001",
            opportunity_name="测试商机",
            customer_name="测试客户",
            stage="QUALIFICATION",
            est_amount=100000,
            total_score=75,
            health_level=HealthLevel.GOOD,
            dimension_scores=[],
            key_issues=[],
            top_suggestions=[],
            last_activity_at=datetime.now(),
            days_in_stage=5,
        )

        with patch.object(service, 'get_user_opportunities_health', return_value=[mock_health]):
            summary = service.get_health_summary(user_id=1)

        assert summary["total_count"] == 1
        assert summary["by_level"]["good"]["count"] == 1
        assert summary["average_score"] == 75
