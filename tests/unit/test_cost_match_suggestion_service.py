# -*- coding: utf-8 -*-
"""
Tests for cost_match_suggestion_service service
Covers: app/services/cost_match_suggestion_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 84 lines
Batch: 3
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_match_suggestion_service import (
    check_cost_anomalies,
    find_matching_cost,
    build_cost_suggestion,
    check_overall_anomalies,
    calculate_summary,
    process_cost_match_suggestions
)
from app.models.sales import QuoteItem
from app.models.material import PurchaseMaterialCost
from app.schemas.sales import CostMatchSuggestion


@pytest.fixture
def test_quote_item():
    """创建测试报价项"""
    item = QuoteItem(
        item_name="测试物料",
        qty=10,
        cost=Decimal("100.00")
    )
    return item


@pytest.fixture
def test_cost_query(db_session):
    """创建测试成本查询"""
    from sqlalchemy.orm import Query
    query = db_session.query(PurchaseMaterialCost)
    return query


class TestCostMatchSuggestionService:
    """Test suite for cost_match_suggestion_service."""

    def test_check_cost_anomalies_no_item_name(self, db_session, test_cost_query):
        """测试检查成本异常 - 无物料名称"""
        item = QuoteItem(item_name=None)
        
        result = check_cost_anomalies(db_session, item, test_cost_query, 100.0)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_check_cost_anomalies_no_history(self, db_session, test_cost_query, test_quote_item):
        """测试检查成本异常 - 无历史数据"""
        result = check_cost_anomalies(db_session, test_quote_item, test_cost_query, 100.0)
        
        assert isinstance(result, list)

    def test_check_cost_anomalies_high_cost(self, db_session, test_cost_query, test_quote_item):
        """测试检查成本异常 - 成本偏高"""
        # 创建历史成本记录
        historical_cost = PurchaseMaterialCost(
            material_name="测试物料",
            unit_cost=Decimal("50.00")
        )
        db_session.add(historical_cost)
        db_session.commit()
        
        # 当前成本是历史最高成本的2倍（超过1.5倍阈值）
        result = check_cost_anomalies(db_session, test_quote_item, test_cost_query, 150.0)
        
        assert isinstance(result, list)
        # 应该检测到异常

    def test_find_matching_cost_no_item_name(self, db_session, test_cost_query):
        """测试查找匹配成本 - 无物料名称"""
        item = QuoteItem(item_name=None)
        
        matched, score, reason = find_matching_cost(db_session, item, test_cost_query)
        
        assert matched is None
        assert score is None
        assert reason is None

    def test_find_matching_cost_exact_match(self, db_session, test_cost_query, test_quote_item):
        """测试查找匹配成本 - 精确匹配"""
        # 创建精确匹配的成本记录
        cost = PurchaseMaterialCost(
            material_name="测试物料",
            unit_cost=Decimal("100.00"),
            match_priority=100
        )
        db_session.add(cost)
        db_session.commit()
        
        matched, score, reason = find_matching_cost(db_session, test_quote_item, test_cost_query)
        
        assert matched is not None
        assert score == 100
        assert "精确匹配" in reason

    def test_find_matching_cost_fuzzy_match(self, db_session, test_cost_query):
        """测试查找匹配成本 - 模糊匹配"""
        item = QuoteItem(item_name="测试物料A")
        
        # 创建模糊匹配的成本记录
        cost = PurchaseMaterialCost(
            material_name="测试物料A型",
            unit_cost=Decimal("100.00")
        )
        db_session.add(cost)
        db_session.commit()
        
        matched, score, reason = find_matching_cost(db_session, item, test_cost_query)
        
        assert matched is not None
        assert score == 80
        assert "模糊匹配" in reason

    def test_build_cost_suggestion_with_match(self, test_quote_item):
        """测试构建成本建议 - 有匹配"""
        matched_cost = MagicMock()
        matched_cost.unit_cost = Decimal("90.00")
        matched_cost.specification = "规格A"
        matched_cost.unit = "个"
        matched_cost.lead_time_days = 7
        matched_cost.material_type = "标准件"
        matched_cost.submitter = None
        
        suggestion = build_cost_suggestion(
            test_quote_item,
            current_cost=100.0,
            matched_cost=matched_cost,
            match_score=100,
            reason="精确匹配",
            warnings=[]
        )
        
        assert suggestion is not None
        assert suggestion.current_cost == Decimal("100.00")
        assert suggestion.suggested_cost == Decimal("90.00")
        assert suggestion.match_score == 100

    def test_build_cost_suggestion_no_match(self, test_quote_item):
        """测试构建成本建议 - 无匹配"""
        suggestion = build_cost_suggestion(
            test_quote_item,
            current_cost=100.0,
            matched_cost=None,
            match_score=None,
            reason=None,
            warnings=["未找到匹配"]
        )
        
        assert suggestion is not None
        assert suggestion.suggested_cost is None
        assert len(suggestion.warnings) > 0

    def test_check_overall_anomalies_low_margin(self):
        """测试整体异常检查 - 毛利率低"""
        items = []
        suggestions = []
        
        warnings = check_overall_anomalies(
            current_total_price=1000.0,
            current_total_cost=950.0,
            suggested_total_cost=960.0,
            items=items,
            suggestions=suggestions
        )
        
        assert isinstance(warnings, list)

    def test_check_overall_anomalies_zero_price(self):
        """测试整体异常检查 - 价格为0"""
        warnings = check_overall_anomalies(
            current_total_price=0.0,
            current_total_cost=100.0,
            suggested_total_cost=90.0,
            items=[],
            suggestions=[]
        )
        
        assert isinstance(warnings, list)
        assert len(warnings) == 0

    def test_calculate_summary_success(self):
        """测试计算汇总 - 成功场景"""
        items = [
            QuoteItem(id=1, qty=10, cost=Decimal("100.00"))
        ]
        suggestions = [
            CostMatchSuggestion(
                item_id=1,
                item_name="物料1",
                current_cost=Decimal("100.00"),
                suggested_cost=Decimal("90.00")
            )
        ]
        
        result = calculate_summary(
            current_total_cost=1000.0,
            current_total_price=1200.0,
            items=items,
            suggestions=suggestions
        )
        
        assert result is not None
        assert 'current_total_cost' in result
        assert 'suggested_total_cost' in result
        assert 'current_margin' in result
        assert 'suggested_margin' in result

    def test_calculate_summary_zero_cost(self):
        """测试计算汇总 - 成本为0"""
        result = calculate_summary(
            current_total_cost=0.0,
            current_total_price=1000.0,
            items=[],
            suggestions=[]
        )
        
        assert result is not None
        assert result['current_total_cost'] == 0.0

    def test_process_cost_match_suggestions_success(self, db_session, test_cost_query):
        """测试处理成本匹配建议 - 成功场景"""
        items = [
            QuoteItem(
                id=1,
                item_name="测试物料",
                qty=10,
                cost=Decimal("100.00")
            )
        ]
        
        suggestions, matched_count, unmatched_count, warnings, total_cost = process_cost_match_suggestions(
            db_session,
            items,
            test_cost_query
        )
        
        assert isinstance(suggestions, list)
        assert isinstance(matched_count, int)
        assert isinstance(unmatched_count, int)
        assert isinstance(warnings, list)
        assert isinstance(total_cost, float)

    def test_process_cost_match_suggestions_empty_items(self, db_session, test_cost_query):
        """测试处理成本匹配建议 - 空列表"""
        suggestions, matched_count, unmatched_count, warnings, total_cost = process_cost_match_suggestions(
            db_session,
            [],
            test_cost_query
        )
        
        assert len(suggestions) == 0
        assert matched_count == 0
        assert unmatched_count == 0
        assert total_cost == 0.0
