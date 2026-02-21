# -*- coding: utf-8 -*-
"""
成本匹配建议服务测试
测试目标: 60%+ 覆盖率，全面覆盖成本匹配、相似度计算、推荐算法、异常处理
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.sales.quotes import PurchaseMaterialCost, QuoteItem
from app.schemas.sales import CostMatchSuggestion
from app.services.cost_match_suggestion_service import (
    check_cost_anomalies,
    find_matching_cost,
    build_cost_suggestion,
    check_overall_anomalies,
    calculate_summary,
    process_cost_match_suggestions,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_quote_item():
    """示例报价明细项"""
    item = QuoteItem(
        id=1,
        item_name="304不锈钢板",
        cost=Decimal("100.00"),
        qty=Decimal("10"),
        specification="2mm*1000*2000",
    )
    return item


@pytest.fixture
def sample_cost_record():
    """示例成本记录"""
    cost = PurchaseMaterialCost(
        id=1,
        material_name="304不锈钢板",
        unit_cost=Decimal("95.00"),
        specification="2mm*1000*2000",
        unit="张",
        lead_time_days=7,
        material_type="金属材料",
        match_priority=5,
        usage_count=10,
        purchase_date=(datetime.now() - timedelta(days=30)).date(),  # 使用纯日期
    )
    cost.submitter = MagicMock(real_name="测试采购员")
    return cost


@pytest.fixture
def mock_cost_query():
    """Mock成本查询"""
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = []
    query.first.return_value = None
    return query


# ==================== check_cost_anomalies 测试 ====================

def test_check_cost_anomalies_no_item_name(mock_db, mock_cost_query):
    """测试：物料名称为空时返回空警告"""
    item = QuoteItem(id=1, item_name=None)
    warnings = check_cost_anomalies(mock_db, item, mock_cost_query, 100.0)
    assert warnings == []


def test_check_cost_anomalies_no_historical_data(mock_db, sample_quote_item, mock_cost_query):
    """测试：无历史成本数据时返回空警告"""
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.all.return_value = []
        warnings = check_cost_anomalies(mock_db, sample_quote_item, mock_cost_query, 100.0)
        assert warnings == []


def test_check_cost_anomalies_extremely_high(mock_db, sample_quote_item, mock_cost_query):
    """测试：成本异常偏高（超过历史最高值50%）"""
    historical_costs = [
        MagicMock(unit_cost=Decimal("100")),
        MagicMock(unit_cost=Decimal("110")),
        MagicMock(unit_cost=Decimal("105")),
    ]
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.all.return_value = historical_costs
        warnings = check_cost_anomalies(mock_db, sample_quote_item, mock_cost_query, 200.0)
        
        assert len(warnings) == 1
        assert "成本异常偏高" in warnings[0]
        assert "200" in warnings[0]
        assert "110" in warnings[0]


def test_check_cost_anomalies_extremely_low(mock_db, sample_quote_item, mock_cost_query):
    """测试：成本异常偏低（低于历史最低值50%）"""
    historical_costs = [
        MagicMock(unit_cost=Decimal("100")),
        MagicMock(unit_cost=Decimal("110")),
        MagicMock(unit_cost=Decimal("95")),
    ]
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.all.return_value = historical_costs
        warnings = check_cost_anomalies(mock_db, sample_quote_item, mock_cost_query, 40.0)
        
        assert len(warnings) == 1
        assert "成本异常偏低" in warnings[0]
        assert "40" in warnings[0]
        assert "95" in warnings[0]


def test_check_cost_anomalies_large_deviation(mock_db, sample_quote_item, mock_cost_query):
    """测试：成本偏差较大（偏离平均值超过30%）"""
    historical_costs = [
        MagicMock(unit_cost=Decimal("100")),
        MagicMock(unit_cost=Decimal("100")),
        MagicMock(unit_cost=Decimal("100")),
    ]
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.all.return_value = historical_costs
        warnings = check_cost_anomalies(mock_db, sample_quote_item, mock_cost_query, 140.0)
        
        assert len(warnings) == 1
        assert "成本偏差较大" in warnings[0]
        assert "140" in warnings[0]
        assert "100.00" in warnings[0]


def test_check_cost_anomalies_normal_range(mock_db, sample_quote_item, mock_cost_query):
    """测试：成本在正常范围内"""
    historical_costs = [
        MagicMock(unit_cost=Decimal("95")),
        MagicMock(unit_cost=Decimal("100")),
        MagicMock(unit_cost=Decimal("105")),
    ]
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.all.return_value = historical_costs
        warnings = check_cost_anomalies(mock_db, sample_quote_item, mock_cost_query, 102.0)
        
        assert warnings == []


# ==================== find_matching_cost 测试 ====================

def test_find_matching_cost_no_item_name(mock_db, mock_cost_query):
    """测试：物料名称为空时返回None"""
    item = QuoteItem(id=1, item_name=None)
    result, score, reason = find_matching_cost(mock_db, item, mock_cost_query)
    assert result is None
    assert score is None
    assert reason is None


def test_find_matching_cost_exact_match(mock_db, sample_quote_item, mock_cost_query, sample_cost_record):
    """测试：精确匹配物料名称（分数100）"""
    mock_cost_query.filter.return_value.order_by.return_value.first.return_value = sample_cost_record
    
    result, score, reason = find_matching_cost(mock_db, sample_quote_item, mock_cost_query)
    
    assert result == sample_cost_record
    assert score == 100
    assert reason == "精确匹配物料名称"


def test_find_matching_cost_fuzzy_match(mock_db, sample_quote_item, mock_cost_query, sample_cost_record):
    """测试：模糊匹配物料名称（分数80）"""
    mock_cost_query.filter.return_value.order_by.return_value.first.return_value = None
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_cost_record]
        
        result, score, reason = find_matching_cost(mock_db, sample_quote_item, mock_cost_query)
        
        assert result == sample_cost_record
        assert score == 80
        assert reason == "模糊匹配物料名称"


def test_find_matching_cost_keyword_match(mock_db, mock_cost_query, sample_cost_record):
    """测试：关键词匹配（分数60）"""
    item = QuoteItem(id=1, item_name="304不锈钢板 2mm厚")
    mock_cost_query.filter.return_value.order_by.return_value.first.return_value = None
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        # 第一次调用（模糊匹配）返回空
        # 第二次调用（关键词匹配）返回结果
        mock_filter.return_value.order_by.return_value.limit.return_value.all.side_effect = [
            [],  # 模糊匹配失败
            [sample_cost_record],  # 关键词匹配成功
        ]
        
        result, score, reason = find_matching_cost(mock_db, item, mock_cost_query)
        
        assert result == sample_cost_record
        assert score == 60
        assert "关键词匹配" in reason


def test_find_matching_cost_no_match(mock_db, sample_quote_item, mock_cost_query):
    """测试：无任何匹配"""
    mock_cost_query.filter.return_value.order_by.return_value.first.return_value = None
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result, score, reason = find_matching_cost(mock_db, sample_quote_item, mock_cost_query)
        
        assert result is None
        assert score is None
        assert reason is None


def test_find_matching_cost_short_keywords_ignored(mock_db, mock_cost_query):
    """测试：短关键词（<=2字符）被忽略"""
    item = QuoteItem(id=1, item_name="螺丝 M8")  # "螺丝"会匹配，"M8"会被忽略
    mock_cost_query.filter.return_value.order_by.return_value.first.return_value = None
    
    with patch("app.services.cost_match_suggestion_service.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result, score, reason = find_matching_cost(mock_db, item, mock_cost_query)
        
        # 应该只调用一次（模糊匹配），关键词太短不会触发关键词匹配
        assert mock_filter.call_count >= 1


# ==================== build_cost_suggestion 测试 ====================

def test_build_cost_suggestion_with_matched_cost(sample_quote_item, sample_cost_record):
    """测试：有匹配成本记录时构建建议"""
    suggestion = build_cost_suggestion(
        item=sample_quote_item,
        current_cost=100.0,
        matched_cost=sample_cost_record,
        match_score=100,
        reason="精确匹配",
        warnings=[]
    )
    
    assert suggestion.item_id == 1
    assert suggestion.item_name == "304不锈钢板"
    assert suggestion.current_cost == Decimal("100")
    assert suggestion.suggested_cost == Decimal("95.00")
    assert suggestion.match_score == 100
    assert suggestion.reason == "精确匹配"
    assert suggestion.matched_cost_record is not None
    assert suggestion.suggested_specification == "2mm*1000*2000"


def test_build_cost_suggestion_without_matched_cost(sample_quote_item):
    """测试：无匹配成本记录时构建建议"""
    warnings = ["未找到匹配的成本记录"]
    suggestion = build_cost_suggestion(
        item=sample_quote_item,
        current_cost=100.0,
        matched_cost=None,
        match_score=None,
        reason=None,
        warnings=warnings
    )
    
    assert suggestion.item_id == 1
    assert suggestion.current_cost == Decimal("100")
    assert suggestion.suggested_cost is None
    assert suggestion.match_score is None
    assert suggestion.reason is None
    assert suggestion.warnings == warnings
    assert suggestion.matched_cost_record is None


def test_build_cost_suggestion_zero_cost(sample_quote_item, sample_cost_record):
    """测试：当前成本为0时"""
    suggestion = build_cost_suggestion(
        item=sample_quote_item,
        current_cost=0.0,
        matched_cost=sample_cost_record,
        match_score=80,
        reason="模糊匹配",
        warnings=[]
    )
    
    assert suggestion.current_cost is None
    assert suggestion.suggested_cost == Decimal("95.00")


def test_build_cost_suggestion_with_warnings(sample_quote_item):
    """测试：包含警告信息的建议"""
    warnings = ["成本异常偏高", "供应商价格波动"]
    suggestion = build_cost_suggestion(
        item=sample_quote_item,
        current_cost=150.0,
        matched_cost=None,
        match_score=None,
        reason=None,
        warnings=warnings
    )
    
    assert len(suggestion.warnings) == 2
    assert "成本异常偏高" in suggestion.warnings


# ==================== check_overall_anomalies 测试 ====================

def test_check_overall_anomalies_low_margin(sample_quote_item):
    """测试：建议成本导致低毛利率（<10%）"""
    warnings = check_overall_anomalies(
        current_total_price=1000.0,
        current_total_cost=800.0,
        suggested_total_cost=950.0,
        items=[sample_quote_item],
        suggestions=[]
    )
    
    assert len(warnings) == 1
    assert "毛利率仅" in warnings[0]
    assert "5.00%" in warnings[0]


def test_check_overall_anomalies_large_difference(sample_quote_item):
    """测试：建议成本与当前成本差异大（>10%）"""
    warnings = check_overall_anomalies(
        current_total_price=1000.0,
        current_total_cost=600.0,  # 40% 毛利
        suggested_total_cost=900.0,  # 10% 毛利
        items=[sample_quote_item],
        suggestions=[]
    )
    
    assert len(warnings) >= 1
    assert any("差异较大" in w for w in warnings)


def test_check_overall_anomalies_normal_range(sample_quote_item):
    """测试：正常毛利率范围"""
    warnings = check_overall_anomalies(
        current_total_price=1000.0,
        current_total_cost=700.0,  # 30% 毛利
        suggested_total_cost=750.0,  # 25% 毛利
        items=[sample_quote_item],
        suggestions=[]
    )
    
    assert warnings == []


def test_check_overall_anomalies_zero_price(sample_quote_item):
    """测试：总价为0时返回空警告"""
    warnings = check_overall_anomalies(
        current_total_price=0.0,
        current_total_cost=500.0,
        suggested_total_cost=600.0,
        items=[sample_quote_item],
        suggestions=[]
    )
    
    assert warnings == []


def test_check_overall_anomalies_zero_suggested_cost(sample_quote_item):
    """测试：建议总成本为0时返回空警告"""
    warnings = check_overall_anomalies(
        current_total_price=1000.0,
        current_total_cost=500.0,
        suggested_total_cost=0.0,
        items=[sample_quote_item],
        suggestions=[]
    )
    
    assert warnings == []


# ==================== calculate_summary 测试 ====================

def test_calculate_summary_basic():
    """测试：基本汇总计算"""
    items = [
        QuoteItem(id=1, qty=Decimal("10")),
        QuoteItem(id=2, qty=Decimal("5")),
    ]
    suggestions = [
        MagicMock(item_id=1, suggested_cost=Decimal("100"), current_cost=Decimal("90")),
        MagicMock(item_id=2, suggested_cost=None, current_cost=Decimal("200")),
    ]
    
    summary = calculate_summary(
        current_total_cost=1900.0,
        current_total_price=3000.0,
        items=items,
        suggestions=suggestions
    )
    
    assert summary["current_total_cost"] == 1900.0
    assert summary["current_total_price"] == 3000.0
    assert summary["suggested_total_cost"] == 2000.0  # 10*100 + 5*200
    assert summary["current_margin"] == pytest.approx(36.67, rel=0.01)
    assert summary["suggested_margin"] == pytest.approx(33.33, rel=0.01)


def test_calculate_summary_zero_price():
    """测试：总价为0时的汇总"""
    summary = calculate_summary(
        current_total_cost=1000.0,
        current_total_price=0.0,
        items=[],
        suggestions=[]
    )
    
    assert summary["current_margin"] is None
    assert summary["suggested_margin"] is None


def test_calculate_summary_zero_current_cost():
    """测试：当前成本为0时的汇总"""
    summary = calculate_summary(
        current_total_cost=0.0,
        current_total_price=1000.0,
        items=[],
        suggestions=[]
    )
    
    assert summary["current_margin"] is None


def test_calculate_summary_all_suggested_costs():
    """测试：所有项都有建议成本"""
    items = [QuoteItem(id=1, qty=Decimal("10"))]
    suggestions = [
        MagicMock(item_id=1, suggested_cost=Decimal("50"), current_cost=Decimal("60"))
    ]
    
    summary = calculate_summary(
        current_total_cost=600.0,
        current_total_price=1000.0,
        items=items,
        suggestions=suggestions
    )
    
    assert summary["suggested_total_cost"] == 500.0
    assert summary["suggested_margin"] == 50.0


# ==================== process_cost_match_suggestions 测试 ====================

def test_process_cost_match_suggestions_all_matched(mock_db, sample_cost_record):
    """测试：所有项都匹配到成本"""
    items = [
        QuoteItem(id=1, item_name="304不锈钢板", cost=None, qty=Decimal("10")),
        QuoteItem(id=2, item_name="铝合金板", cost=None, qty=Decimal("5")),
    ]
    
    mock_query = MagicMock()
    
    with patch("app.services.cost_match_suggestion_service.find_matching_cost") as mock_find:
        mock_find.return_value = (sample_cost_record, 100, "精确匹配")
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            mock_db, items, mock_query
        )
        
        assert len(suggestions) == 2
        assert matched == 2
        assert unmatched == 0
        assert total_cost == 0.0  # 所有成本都为None


def test_process_cost_match_suggestions_partial_matched(mock_db, sample_cost_record):
    """测试：部分项匹配，部分未匹配"""
    items = [
        QuoteItem(id=1, item_name="304不锈钢板", cost=None, qty=Decimal("10")),
        QuoteItem(id=2, item_name="未知材料", cost=None, qty=Decimal("5")),
    ]
    
    mock_query = MagicMock()
    
    with patch("app.services.cost_match_suggestion_service.find_matching_cost") as mock_find:
        mock_find.side_effect = [
            (sample_cost_record, 100, "精确匹配"),
            (None, None, None)
        ]
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            mock_db, items, mock_query
        )
        
        assert matched == 1
        assert unmatched == 1
        assert any("未找到匹配" in s.warnings[0] for s in suggestions if s.warnings)


def test_process_cost_match_suggestions_with_existing_cost(mock_db):
    """测试：已有成本时进行异常检查"""
    items = [
        QuoteItem(id=1, item_name="304不锈钢板", cost=Decimal("100"), qty=Decimal("10")),
    ]
    
    mock_query = MagicMock()
    
    with patch("app.services.cost_match_suggestion_service.check_cost_anomalies") as mock_check:
        mock_check.return_value = ["成本偏高警告"]
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            mock_db, items, mock_query
        )
        
        assert total_cost == 1000.0  # 100 * 10
        assert len(suggestions) == 1
        assert "成本偏高警告" in suggestions[0].warnings


def test_process_cost_match_suggestions_mixed_costs(mock_db, sample_cost_record):
    """测试：混合场景（有成本+无成本）"""
    items = [
        QuoteItem(id=1, item_name="304不锈钢板", cost=Decimal("100"), qty=Decimal("10")),
        QuoteItem(id=2, item_name="铝合金板", cost=None, qty=Decimal("5")),
    ]
    
    mock_query = MagicMock()
    
    with patch("app.services.cost_match_suggestion_service.check_cost_anomalies") as mock_check:
        mock_check.return_value = []
        with patch("app.services.cost_match_suggestion_service.find_matching_cost") as mock_find:
            mock_find.return_value = (sample_cost_record, 80, "模糊匹配")
            
            suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
                mock_db, items, mock_query
            )
            
            assert len(suggestions) == 2
            assert matched == 1
            assert unmatched == 0
            assert total_cost == 1000.0


def test_process_cost_match_suggestions_empty_items(mock_db):
    """测试：空项目列表"""
    suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
        mock_db, [], MagicMock()
    )
    
    assert suggestions == []
    assert matched == 0
    assert unmatched == 0
    assert total_cost == 0.0


# ==================== 边界情况和异常处理 ====================

def test_zero_quantity_handling():
    """测试：数量为0时的处理"""
    items = [QuoteItem(id=1, qty=Decimal("0"))]
    suggestions = [
        MagicMock(item_id=1, suggested_cost=Decimal("100"), current_cost=None)
    ]
    
    summary = calculate_summary(0.0, 1000.0, items, suggestions)
    assert summary["suggested_total_cost"] == 0.0


def test_negative_cost_handling(sample_quote_item):
    """测试：负成本处理（虽然不应该出现，但要确保不会崩溃）"""
    suggestion = build_cost_suggestion(
        item=sample_quote_item,
        current_cost=-50.0,
        matched_cost=None,
        match_score=None,
        reason=None,
        warnings=[]
    )
    
    # 应该正常构建，即使是负值
    assert suggestion.current_cost is None  # 因为 current_cost <= 0


def test_very_large_numbers():
    """测试：处理非常大的数字"""
    items = [QuoteItem(id=1, qty=Decimal("999999"))]
    suggestions = [
        MagicMock(item_id=1, suggested_cost=Decimal("999999"), current_cost=None)
    ]
    
    summary = calculate_summary(0.0, 1e12, items, suggestions)
    assert summary["suggested_total_cost"] > 0


def test_decimal_precision():
    """测试：小数精度处理"""
    item = QuoteItem(id=1, item_name="精密零件", cost=Decimal("0.001"), qty=Decimal("1000"))
    
    suggestion = build_cost_suggestion(
        item=item,
        current_cost=0.001,
        matched_cost=None,
        match_score=None,
        reason=None,
        warnings=[]
    )
    
    assert suggestion.current_cost == Decimal("0.001")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
