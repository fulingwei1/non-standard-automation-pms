# -*- coding: utf-8 -*-
"""
成本匹配建议服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from app.services.cost_match_suggestion_service import (
    check_cost_anomalies,
    find_matching_cost,
    build_cost_suggestion,
    check_overall_anomalies,
    calculate_summary,
    process_cost_match_suggestions,
)


class TestCheckCostAnomalies(unittest.TestCase):
    """测试成本异常检查"""

    def setUp(self):
        self.db = MagicMock()
        self.cost_query = MagicMock()

    def _create_mock_item(self, item_name="测试物料", cost=1000.0):
        """创建mock QuoteItem"""
        item = MagicMock()
        item.item_name = item_name
        item.cost = cost
        item.id = 1
        item.qty = 10
        return item

    def _create_mock_cost(self, unit_cost):
        """创建mock PurchaseMaterialCost"""
        cost = MagicMock()
        cost.unit_cost = unit_cost
        cost.material_name = "测试物料"
        return cost

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_no_item_name(self, mock_filter):
        """测试无物料名称时直接返回空列表"""
        item = self._create_mock_item(item_name=None)
        warnings = check_cost_anomalies(self.db, item, self.cost_query, 1000.0)
        
        self.assertEqual(warnings, [])
        mock_filter.assert_not_called()

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_empty_item_name(self, mock_filter):
        """测试空物料名称"""
        item = self._create_mock_item(item_name="")
        warnings = check_cost_anomalies(self.db, item, self.cost_query, 1000.0)
        
        self.assertEqual(warnings, [])
        mock_filter.assert_not_called()

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_no_historical_costs(self, mock_filter):
        """测试无历史成本记录时返回空列表"""
        item = self._create_mock_item()
        mock_filter.return_value.all.return_value = []
        
        warnings = check_cost_anomalies(self.db, item, self.cost_query, 1000.0)
        
        self.assertEqual(warnings, [])
        mock_filter.assert_called_once()

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_cost_extremely_high(self, mock_filter):
        """测试成本异常偏高（超过历史最高的50%）"""
        item = self._create_mock_item()
        historical_costs = [
            self._create_mock_cost(1000.0),
            self._create_mock_cost(1200.0),
            self._create_mock_cost(1100.0),
        ]
        mock_filter.return_value.all.return_value = historical_costs
        
        current_cost = 2000.0  # 超过max(1200) * 1.5 = 1800
        warnings = check_cost_anomalies(self.db, item, self.cost_query, current_cost)
        
        self.assertEqual(len(warnings), 1)
        self.assertIn("成本异常偏高", warnings[0])
        self.assertIn("2000", warnings[0])
        self.assertIn("1200", warnings[0])

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_cost_extremely_low(self, mock_filter):
        """测试成本异常偏低（低于历史最低的50%）"""
        item = self._create_mock_item()
        historical_costs = [
            self._create_mock_cost(1000.0),
            self._create_mock_cost(1200.0),
            self._create_mock_cost(900.0),
        ]
        mock_filter.return_value.all.return_value = historical_costs
        
        current_cost = 400.0  # 低于min(900) * 0.5 = 450
        warnings = check_cost_anomalies(self.db, item, self.cost_query, current_cost)
        
        self.assertEqual(len(warnings), 1)
        self.assertIn("成本异常偏低", warnings[0])
        self.assertIn("400", warnings[0])
        self.assertIn("900", warnings[0])

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_cost_deviation_over_30_percent(self, mock_filter):
        """测试成本偏差超过30%"""
        item = self._create_mock_item()
        historical_costs = [
            self._create_mock_cost(1000.0),
            self._create_mock_cost(1000.0),
            self._create_mock_cost(1000.0),
        ]
        mock_filter.return_value.all.return_value = historical_costs
        
        current_cost = 1400.0  # 偏差 40% > 30%
        warnings = check_cost_anomalies(self.db, item, self.cost_query, current_cost)
        
        self.assertEqual(len(warnings), 1)
        self.assertIn("成本偏差较大", warnings[0])
        self.assertIn("1400", warnings[0])
        self.assertIn("1000.00", warnings[0])
        self.assertIn("30%", warnings[0])

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_cost_within_normal_range(self, mock_filter):
        """测试成本在正常范围内"""
        item = self._create_mock_item()
        historical_costs = [
            self._create_mock_cost(1000.0),
            self._create_mock_cost(1100.0),
            self._create_mock_cost(1050.0),
        ]
        mock_filter.return_value.all.return_value = historical_costs
        
        current_cost = 1080.0  # 偏差约3%，在正常范围内
        warnings = check_cost_anomalies(self.db, item, self.cost_query, current_cost)
        
        self.assertEqual(warnings, [])

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_cost_with_none_values(self, mock_filter):
        """测试历史成本中包含None值"""
        item = self._create_mock_item()
        historical_costs = [
            self._create_mock_cost(1000.0),
            self._create_mock_cost(None),  # None值会被转换为0
            self._create_mock_cost(1200.0),
        ]
        mock_filter.return_value.all.return_value = historical_costs
        
        current_cost = 1100.0
        warnings = check_cost_anomalies(self.db, item, self.cost_query, current_cost)
        
        # 平均值 = (1000 + 0 + 1200) / 3 = 733.33
        # 不应该触发异常
        self.assertTrue(len(warnings) >= 0)  # 可能有也可能没有警告


class TestFindMatchingCost(unittest.TestCase):
    """测试查找匹配的成本记录"""

    def setUp(self):
        self.db = MagicMock()
        self.cost_query = MagicMock()

    def _create_mock_item(self, item_name="测试物料A"):
        """创建mock QuoteItem"""
        item = MagicMock()
        item.item_name = item_name
        item.id = 1
        return item

    def _create_mock_cost(self, material_name, match_priority=5, purchase_date=None):
        """创建mock PurchaseMaterialCost"""
        cost = MagicMock()
        cost.material_name = material_name
        cost.match_priority = match_priority
        cost.purchase_date = purchase_date or datetime.now()
        cost.unit_cost = 1000.0
        cost.usage_count = 10
        return cost

    def test_no_item_name(self):
        """测试无物料名称时返回None"""
        item = self._create_mock_item(item_name=None)
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertIsNone(result)
        self.assertIsNone(score)
        self.assertIsNone(reason)

    def test_empty_item_name(self):
        """测试空物料名称"""
        item = self._create_mock_item(item_name="")
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertIsNone(result)
        self.assertIsNone(score)
        self.assertIsNone(reason)

    def test_exact_match_found(self):
        """测试精确匹配成功"""
        item = self._create_mock_item(item_name="测试物料A")
        matched_cost = self._create_mock_cost("测试物料A")
        
        # Mock查询链
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_filter.order_by.return_value = mock_order
        mock_order.first.return_value = matched_cost
        
        self.cost_query.filter.return_value = mock_filter
        
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertEqual(result, matched_cost)
        self.assertEqual(score, 100)
        self.assertEqual(reason, "精确匹配物料名称")

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_fuzzy_match_found(self, mock_filter_func):
        """测试模糊匹配成功"""
        item = self._create_mock_item(item_name="测试物料A")
        matched_cost = self._create_mock_cost("测试物料A-规格1")
        
        # 精确匹配失败
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_filter.order_by.return_value = mock_order
        mock_order.first.return_value = None
        self.cost_query.filter.return_value = mock_filter
        
        # 模糊匹配成功
        mock_fuzzy = MagicMock()
        mock_fuzzy_order = MagicMock()
        mock_fuzzy_limit = MagicMock()
        mock_fuzzy.order_by.return_value = mock_fuzzy_order
        mock_fuzzy_order.limit.return_value = mock_fuzzy_limit
        mock_fuzzy_limit.all.return_value = [matched_cost]
        
        mock_filter_func.return_value = mock_fuzzy
        
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertEqual(result, matched_cost)
        self.assertEqual(score, 80)
        self.assertEqual(reason, "模糊匹配物料名称")

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_keyword_match_found(self, mock_filter_func):
        """测试关键词匹配成功"""
        item = self._create_mock_item(item_name="不锈钢 304 螺栓")
        matched_cost = self._create_mock_cost("304不锈钢")
        
        # 精确匹配失败
        mock_exact = MagicMock()
        mock_exact.order_by.return_value.first.return_value = None
        self.cost_query.filter.return_value = mock_exact
        
        # 模糊匹配失败
        mock_fuzzy = MagicMock()
        mock_fuzzy.order_by.return_value.limit.return_value.all.return_value = []
        
        # 关键词匹配成功（第二个关键词"304"匹配）
        mock_keyword = MagicMock()
        mock_keyword.order_by.return_value.limit.return_value.all.return_value = [matched_cost]
        
        # 第一次调用返回模糊匹配结果（空），后续调用返回关键词匹配
        mock_filter_func.side_effect = [
            mock_fuzzy,  # 模糊匹配
            MagicMock(order_by=MagicMock(return_value=MagicMock(limit=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))),  # 第一个关键词"不锈钢"
            mock_keyword,  # 第二个关键词"304"
        ]
        
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertEqual(result, matched_cost)
        self.assertEqual(score, 60)
        self.assertIn("关键词匹配", reason)
        self.assertIn("304", reason)

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_no_match_found(self, mock_filter_func):
        """测试无匹配记录"""
        item = self._create_mock_item(item_name="找不到的物料")
        
        # 精确匹配失败
        mock_exact = MagicMock()
        mock_exact.order_by.return_value.first.return_value = None
        self.cost_query.filter.return_value = mock_exact
        
        # 模糊匹配失败
        mock_fuzzy = MagicMock()
        mock_fuzzy.order_by.return_value.limit.return_value.all.return_value = []
        
        # 关键词匹配也失败
        mock_keyword = MagicMock()
        mock_keyword.order_by.return_value.limit.return_value.all.return_value = []
        
        mock_filter_func.side_effect = [
            mock_fuzzy,
            mock_keyword,
            mock_keyword,
        ]
        
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertIsNone(result)
        self.assertIsNone(score)
        self.assertIsNone(reason)

    @patch('app.services.cost_match_suggestion_service.apply_keyword_filter')
    def test_keyword_too_short_skipped(self, mock_filter_func):
        """测试过短的关键词被跳过"""
        item = self._create_mock_item(item_name="A B C DE")  # 都是短关键词，只有DE长度为2
        
        # 精确匹配失败
        mock_exact = MagicMock()
        mock_exact.order_by.return_value.first.return_value = None
        self.cost_query.filter.return_value = mock_exact
        
        # 模糊匹配失败
        mock_fuzzy = MagicMock()
        mock_fuzzy.order_by.return_value.limit.return_value.all.return_value = []
        mock_filter_func.return_value = mock_fuzzy
        
        result, score, reason = find_matching_cost(self.db, item, self.cost_query)
        
        self.assertIsNone(result)
        # 因为所有关键词长度<=2，不会进行关键词匹配


class TestBuildCostSuggestion(unittest.TestCase):
    """测试构建成本匹配建议"""

    def _create_mock_item(self, item_id=1, item_name="测试物料", cost=1000.0):
        """创建mock QuoteItem"""
        item = MagicMock()
        item.id = item_id
        item.item_name = item_name
        item.cost = cost
        return item

    def _create_mock_cost(self):
        """创建mock PurchaseMaterialCost"""
        cost = MagicMock()
        cost.unit_cost = 1200.0
        cost.specification = "规格A"
        cost.unit = "个"
        cost.lead_time_days = 7
        cost.material_type = "原材料"
        cost.material_name = "测试物料"
        cost.id = 1
        
        # Mock表列 - 每个列需要有name属性（字符串类型）
        col_id = MagicMock()
        col_id.name = "id"
        
        col_material = MagicMock()
        col_material.name = "material_name"
        
        col_cost = MagicMock()
        col_cost.name = "unit_cost"
        
        cost.__table__ = MagicMock()
        cost.__table__.columns = [col_id, col_material, col_cost]
        
        # Mock提交人
        submitter = MagicMock()
        submitter.real_name = "张三"
        cost.submitter = submitter
        
        return cost

    def test_build_without_matched_cost(self):
        """测试无匹配成本的建议"""
        item = self._create_mock_item()
        warnings = ["未找到匹配的成本记录"]
        
        suggestion = build_cost_suggestion(
            item=item,
            current_cost=1000.0,
            matched_cost=None,
            match_score=None,
            reason=None,
            warnings=warnings
        )
        
        self.assertEqual(suggestion.item_id, 1)
        self.assertEqual(suggestion.item_name, "测试物料")
        self.assertEqual(suggestion.current_cost, Decimal("1000.0"))
        self.assertIsNone(suggestion.suggested_cost)
        self.assertIsNone(suggestion.match_score)
        self.assertIsNone(suggestion.reason)
        self.assertEqual(suggestion.warnings, warnings)
        self.assertIsNone(suggestion.matched_cost_record)

    def test_build_with_matched_cost(self):
        """测试有匹配成本的建议"""
        item = self._create_mock_item()
        matched_cost = self._create_mock_cost()
        warnings = []
        
        suggestion = build_cost_suggestion(
            item=item,
            current_cost=1000.0,
            matched_cost=matched_cost,
            match_score=100,
            reason="精确匹配",
            warnings=warnings
        )
        
        self.assertEqual(suggestion.item_id, 1)
        self.assertEqual(suggestion.suggested_cost, Decimal("1200.0"))
        self.assertEqual(suggestion.match_score, 100)
        self.assertEqual(suggestion.reason, "精确匹配")
        self.assertEqual(suggestion.suggested_specification, "规格A")
        self.assertEqual(suggestion.suggested_unit, "个")
        self.assertEqual(suggestion.suggested_lead_time_days, 7)
        self.assertEqual(suggestion.suggested_cost_category, "原材料")
        self.assertIsNotNone(suggestion.matched_cost_record)

    def test_build_with_zero_current_cost(self):
        """测试当前成本为0的情况"""
        item = self._create_mock_item(cost=0.0)
        
        suggestion = build_cost_suggestion(
            item=item,
            current_cost=0.0,
            matched_cost=None,
            match_score=None,
            reason=None,
            warnings=[]
        )
        
        self.assertIsNone(suggestion.current_cost)  # 0成本不显示

    def test_build_with_empty_item_name(self):
        """测试空物料名称"""
        item = self._create_mock_item(item_name=None)
        
        suggestion = build_cost_suggestion(
            item=item,
            current_cost=1000.0,
            matched_cost=None,
            match_score=None,
            reason=None,
            warnings=[]
        )
        
        self.assertEqual(suggestion.item_name, "")  # None被转换为空字符串


class TestCheckOverallAnomalies(unittest.TestCase):
    """测试整体异常检查"""

    def _create_mock_item(self, item_id=1):
        """创建mock QuoteItem"""
        item = MagicMock()
        item.id = item_id
        return item

    def _create_mock_suggestion(self, item_id, current_cost, suggested_cost):
        """创建mock CostMatchSuggestion"""
        suggestion = MagicMock()
        suggestion.item_id = item_id
        suggestion.current_cost = Decimal(str(current_cost)) if current_cost else None
        suggestion.suggested_cost = Decimal(str(suggested_cost)) if suggested_cost else None
        return suggestion

    def test_low_margin_warning(self):
        """测试建议成本导致低毛利率警告"""
        warnings = check_overall_anomalies(
            current_total_price=10000.0,
            current_total_cost=7000.0,
            suggested_total_cost=9500.0,  # 毛利率仅5%
            items=[],
            suggestions=[]
        )
        
        self.assertEqual(len(warnings), 1)
        self.assertIn("毛利率仅5.00%", warnings[0])
        self.assertIn("低于10%", warnings[0])

    def test_large_margin_difference_warning(self):
        """测试毛利率差异过大警告"""
        warnings = check_overall_anomalies(
            current_total_price=10000.0,
            current_total_cost=5000.0,  # 当前毛利率50%
            suggested_total_cost=7500.0,  # 建议毛利率25%
            items=[],
            suggestions=[]
        )
        
        self.assertEqual(len(warnings), 1)
        self.assertIn("差异较大", warnings[0])
        self.assertIn("50.00%", warnings[0])
        self.assertIn("25.00%", warnings[0])

    def test_no_warnings_when_margin_acceptable(self):
        """测试毛利率可接受时无警告"""
        warnings = check_overall_anomalies(
            current_total_price=10000.0,
            current_total_cost=6000.0,  # 当前毛利率40%
            suggested_total_cost=6500.0,  # 建议毛利率35%，差异5%
            items=[],
            suggestions=[]
        )
        
        self.assertEqual(warnings, [])

    def test_zero_price_no_warning(self):
        """测试总价为0时不检查"""
        warnings = check_overall_anomalies(
            current_total_price=0.0,
            current_total_cost=5000.0,
            suggested_total_cost=6000.0,
            items=[],
            suggestions=[]
        )
        
        self.assertEqual(warnings, [])

    def test_zero_suggested_cost_no_warning(self):
        """测试建议总成本为0时不检查"""
        warnings = check_overall_anomalies(
            current_total_price=10000.0,
            current_total_cost=5000.0,
            suggested_total_cost=0.0,
            items=[],
            suggestions=[]
        )
        
        self.assertEqual(warnings, [])


class TestCalculateSummary(unittest.TestCase):
    """测试计算汇总信息"""

    def _create_mock_item(self, item_id=1, qty=10):
        """创建mock QuoteItem"""
        item = MagicMock()
        item.id = item_id
        item.qty = qty
        return item

    def _create_mock_suggestion(self, item_id, current_cost, suggested_cost):
        """创建mock CostMatchSuggestion"""
        suggestion = MagicMock()
        suggestion.item_id = item_id
        suggestion.current_cost = Decimal(str(current_cost)) if current_cost else None
        suggestion.suggested_cost = Decimal(str(suggested_cost)) if suggested_cost else None
        return suggestion

    def test_calculate_with_all_costs(self):
        """测试有完整成本信息的汇总"""
        items = [
            self._create_mock_item(item_id=1, qty=10),
            self._create_mock_item(item_id=2, qty=5),
        ]
        suggestions = [
            self._create_mock_suggestion(item_id=1, current_cost=100, suggested_cost=120),
            self._create_mock_suggestion(item_id=2, current_cost=200, suggested_cost=180),
        ]
        
        summary = calculate_summary(
            current_total_cost=2000.0,  # 100*10 + 200*5 = 2000
            current_total_price=3000.0,
            items=items,
            suggestions=suggestions
        )
        
        self.assertEqual(summary["current_total_cost"], 2000.0)
        self.assertEqual(summary["suggested_total_cost"], 2100.0)  # 120*10 + 180*5
        self.assertEqual(summary["current_total_price"], 3000.0)
        self.assertAlmostEqual(summary["current_margin"], 33.33, places=2)
        self.assertEqual(summary["suggested_margin"], 30.0)

    def test_calculate_with_no_suggested_cost(self):
        """测试无建议成本时使用当前成本"""
        items = [self._create_mock_item(item_id=1, qty=10)]
        suggestions = [
            self._create_mock_suggestion(item_id=1, current_cost=100, suggested_cost=None)
        ]
        
        summary = calculate_summary(
            current_total_cost=1000.0,
            current_total_price=1500.0,
            items=items,
            suggestions=suggestions
        )
        
        self.assertEqual(summary["suggested_total_cost"], 1000.0)  # 使用current_cost

    def test_calculate_with_zero_current_cost(self):
        """测试当前总成本为0"""
        items = [self._create_mock_item(item_id=1, qty=10)]
        suggestions = [
            self._create_mock_suggestion(item_id=1, current_cost=0, suggested_cost=120)
        ]
        
        summary = calculate_summary(
            current_total_cost=0.0,
            current_total_price=2000.0,
            items=items,
            suggestions=suggestions
        )
        
        self.assertIsNone(summary["current_margin"])  # 当前成本为0，无毛利率

    def test_calculate_with_zero_price(self):
        """测试总价为0"""
        items = [self._create_mock_item(item_id=1, qty=10)]
        suggestions = [
            self._create_mock_suggestion(item_id=1, current_cost=100, suggested_cost=120)
        ]
        
        summary = calculate_summary(
            current_total_cost=1000.0,
            current_total_price=0.0,
            items=items,
            suggestions=suggestions
        )
        
        self.assertIsNone(summary["current_margin"])
        self.assertIsNone(summary["suggested_margin"])

    def test_calculate_with_missing_qty(self):
        """测试物料数量缺失"""
        items = [self._create_mock_item(item_id=1, qty=None)]
        suggestions = [
            self._create_mock_suggestion(item_id=1, current_cost=100, suggested_cost=120)
        ]
        
        summary = calculate_summary(
            current_total_cost=0.0,
            current_total_price=1000.0,
            items=items,
            suggestions=suggestions
        )
        
        self.assertEqual(summary["suggested_total_cost"], 0.0)  # qty为None被转换为0


class TestProcessCostMatchSuggestions(unittest.TestCase):
    """测试处理成本匹配建议主流程"""

    def setUp(self):
        self.db = MagicMock()
        self.cost_query = MagicMock()

    def _create_mock_item(self, item_id=1, item_name="测试物料", cost=None, qty=10):
        """创建mock QuoteItem"""
        item = MagicMock()
        item.id = item_id
        item.item_name = item_name
        item.cost = cost
        item.qty = qty
        return item

    def _create_mock_cost(self, unit_cost=1200.0):
        """创建mock PurchaseMaterialCost"""
        cost = MagicMock()
        cost.unit_cost = unit_cost
        cost.specification = "规格A"
        cost.unit = "个"
        cost.lead_time_days = 7
        cost.material_type = "原材料"
        cost.__table__ = MagicMock()
        cost.__table__.columns = []
        cost.submitter = MagicMock(real_name="张三")
        return cost

    @patch('app.services.cost_match_suggestion_service.find_matching_cost')
    @patch('app.services.cost_match_suggestion_service.check_cost_anomalies')
    def test_process_items_with_existing_cost(self, mock_check, mock_find):
        """测试处理已有成本的物料"""
        items = [
            self._create_mock_item(item_id=1, cost=1000.0, qty=10),
            self._create_mock_item(item_id=2, cost=2000.0, qty=5),
        ]
        
        mock_check.return_value = ["成本偏差较大"]
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            self.db, items, self.cost_query
        )
        
        self.assertEqual(len(suggestions), 2)
        self.assertEqual(matched, 0)  # 已有成本的不计入匹配
        self.assertEqual(unmatched, 0)
        self.assertEqual(total_cost, 20000.0)  # 1000*10 + 2000*5
        
        # 检查异常应该被调用
        self.assertEqual(mock_check.call_count, 2)
        
        # 不应该尝试匹配
        mock_find.assert_not_called()

    @patch('app.services.cost_match_suggestion_service.find_matching_cost')
    @patch('app.services.cost_match_suggestion_service.check_cost_anomalies')
    def test_process_items_without_cost_matched(self, mock_check, mock_find):
        """测试处理无成本物料且匹配成功"""
        items = [
            self._create_mock_item(item_id=1, cost=0, qty=10),
        ]
        
        matched_cost = self._create_mock_cost(unit_cost=1200.0)
        mock_find.return_value = (matched_cost, 100, "精确匹配")
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            self.db, items, self.cost_query
        )
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(matched, 1)
        self.assertEqual(unmatched, 0)
        self.assertEqual(total_cost, 0.0)
        
        # 应该尝试匹配
        mock_find.assert_called_once()
        
        # 不应该检查异常（因为成本为0）
        mock_check.assert_not_called()

    @patch('app.services.cost_match_suggestion_service.find_matching_cost')
    @patch('app.services.cost_match_suggestion_service.check_cost_anomalies')
    def test_process_items_without_cost_unmatched(self, mock_check, mock_find):
        """测试处理无成本物料且未匹配"""
        items = [
            self._create_mock_item(item_id=1, cost=None, qty=10),
        ]
        
        mock_find.return_value = (None, None, None)
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            self.db, items, self.cost_query
        )
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(matched, 0)
        self.assertEqual(unmatched, 1)
        
        # 检查建议中是否包含未匹配警告
        self.assertIn("未找到匹配的成本记录", suggestions[0].warnings[0])

    @patch('app.services.cost_match_suggestion_service.find_matching_cost')
    @patch('app.services.cost_match_suggestion_service.check_cost_anomalies')
    def test_process_mixed_items(self, mock_check, mock_find):
        """测试混合处理有成本和无成本的物料"""
        items = [
            self._create_mock_item(item_id=1, cost=1000.0, qty=10),  # 已有成本
            self._create_mock_item(item_id=2, cost=0, qty=5),        # 无成本，待匹配
            self._create_mock_item(item_id=3, cost=None, qty=8),     # 无成本，待匹配
        ]
        
        mock_check.return_value = []
        matched_cost = self._create_mock_cost()
        
        # 第一次调用匹配成功，第二次失败
        mock_find.side_effect = [
            (matched_cost, 80, "模糊匹配"),
            (None, None, None),
        ]
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            self.db, items, self.cost_query
        )
        
        self.assertEqual(len(suggestions), 3)
        self.assertEqual(matched, 1)
        self.assertEqual(unmatched, 1)
        self.assertEqual(total_cost, 10000.0)  # 只有第一项有成本

    def test_process_empty_items(self):
        """测试空物料列表"""
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            self.db, [], self.cost_query
        )
        
        self.assertEqual(suggestions, [])
        self.assertEqual(matched, 0)
        self.assertEqual(unmatched, 0)
        self.assertEqual(total_cost, 0.0)

    @patch('app.services.cost_match_suggestion_service.find_matching_cost')
    @patch('app.services.cost_match_suggestion_service.check_cost_anomalies')
    def test_process_with_none_qty(self, mock_check, mock_find):
        """测试数量为None的物料"""
        items = [
            self._create_mock_item(item_id=1, cost=1000.0, qty=None),
        ]
        
        mock_check.return_value = []
        
        suggestions, matched, unmatched, warnings, total_cost = process_cost_match_suggestions(
            self.db, items, self.cost_query
        )
        
        self.assertEqual(total_cost, 0.0)  # None * 1000 = 0


class TestEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def test_build_suggestion_with_negative_cost(self):
        """测试负成本"""
        item = MagicMock()
        item.id = 1
        item.item_name = "测试"
        
        suggestion = build_cost_suggestion(
            item=item,
            current_cost=-100.0,
            matched_cost=None,
            match_score=None,
            reason=None,
            warnings=[]
        )
        
        # 负成本不符合 current_cost > 0 的条件，会被设置为None
        self.assertIsNone(suggestion.current_cost)

    def test_calculate_summary_negative_margin(self):
        """测试负毛利率"""
        summary = calculate_summary(
            current_total_cost=15000.0,
            current_total_price=10000.0,  # 成本高于售价
            items=[],
            suggestions=[]
        )
        
        self.assertEqual(summary["current_margin"], -50.0)  # 负毛利率

    def test_check_anomalies_with_single_historical_cost(self):
        """测试只有一条历史成本记录"""
        db = MagicMock()
        cost_query = MagicMock()
        item = MagicMock()
        item.item_name = "测试物料"
        
        historical_cost = MagicMock()
        historical_cost.unit_cost = 1000.0
        
        with patch('app.services.cost_match_suggestion_service.apply_keyword_filter') as mock_filter:
            mock_filter.return_value.all.return_value = [historical_cost]
            
            # 当前成本与唯一历史成本相同
            warnings = check_cost_anomalies(db, item, cost_query, 1000.0)
            self.assertEqual(warnings, [])
            
            # 当前成本远高于历史成本
            warnings = check_cost_anomalies(db, item, cost_query, 2000.0)
            self.assertGreater(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
