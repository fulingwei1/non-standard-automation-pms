# -*- coding: utf-8 -*-
"""
推荐引擎基础类型测试
"""

import pytest

from app.services.sales.engines.base import (
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)


class TestRecommendationType:
    """RecommendationType 枚举测试"""

    def test_all_types_exist(self):
        assert RecommendationType.FOLLOW_UP.value == "follow_up"
        assert RecommendationType.PRICING.value == "pricing"
        assert RecommendationType.RELATIONSHIP.value == "relationship"
        assert RecommendationType.CROSS_SELL.value == "cross_sell"
        assert RecommendationType.RISK.value == "risk"


class TestRecommendationPriority:
    """RecommendationPriority 枚举测试"""

    def test_all_priorities_exist(self):
        assert RecommendationPriority.CRITICAL.value == "critical"
        assert RecommendationPriority.HIGH.value == "high"
        assert RecommendationPriority.MEDIUM.value == "medium"
        assert RecommendationPriority.LOW.value == "low"


class TestRecommendation:
    """Recommendation 数据类测试"""

    def test_create_recommendation(self):
        rec = Recommendation(
            type=RecommendationType.RISK,
            priority=RecommendationPriority.HIGH,
            title="测试标题",
            description="测试描述",
            action="测试操作",
            entity_type="contract",
            entity_id=123,
            confidence=0.95,
            expected_impact="测试影响",
        )

        assert rec.type == RecommendationType.RISK
        assert rec.priority == RecommendationPriority.HIGH
        assert rec.title == "测试标题"
        assert rec.entity_id == 123
        assert rec.confidence == 0.95

    def test_recommendation_with_data(self):
        rec = Recommendation(
            type=RecommendationType.FOLLOW_UP,
            priority=RecommendationPriority.MEDIUM,
            title="跟进提醒",
            description="商机需要跟进",
            action="联系客户",
            entity_type="opportunity",
            entity_id=456,
            confidence=0.8,
            expected_impact="提高转化率",
            data={"days_since_update": 14, "amount": 100000},
        )

        assert rec.data["days_since_update"] == 14
        assert rec.data["amount"] == 100000

    def test_recommendation_optional_data(self):
        rec = Recommendation(
            type=RecommendationType.PRICING,
            priority=RecommendationPriority.LOW,
            title="定价建议",
            description="毛利率可优化",
            action="调整报价",
            entity_type="quote",
            entity_id=789,
            confidence=0.6,
            expected_impact="提高利润",
        )

        # data 字段默认为空字典
        assert rec.data == {}
