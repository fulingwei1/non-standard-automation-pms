# -*- coding: utf-8 -*-
"""
QuotesService 单元测试 - 销售模块核心服务
覆盖：报价列表查询、创建报价、编号生成、类型推断、优先级推断
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.sales.quotes_service import QuotesService
from app.models.sales import Quote
from app.models.user import User


def _make_mock_quote(
    quote_id=1,
    quote_code="QT202504050001",
    customer_id=1,
    customer_name="测试客户",
    owner_id=1,
    owner_name="测试销售",
    status="DRAFT",
    valid_until=None,
    opportunity_id=1,
    opportunity_title="测试商机",
    created_at=None,
    updated_at=None,
):
    """创建模拟报价对象"""
    quote = MagicMock(spec=Quote)
    quote.id = quote_id
    quote.quote_code = quote_code
    quote.customer_id = customer_id
    quote.owner_id = owner_id
    quote.status = status
    quote.valid_until = valid_until
    quote.opportunity_id = opportunity_id

    # Mock 关联对象
    quote.customer = MagicMock()
    quote.customer.customer_name = customer_name

    quote.owner = MagicMock()
    quote.owner.real_name = owner_name

    quote.opportunity = MagicMock()
    quote.opportunity.opp_name = opportunity_title

    quote.current_version = None
    quote.versions = []

    quote.created_at = created_at or datetime.now()
    quote.updated_at = updated_at or datetime.now()

    return quote


def _make_mock_user(user_id=1, real_name="测试用户"):
    """创建模拟用户对象"""
    user = MagicMock(spec=User)
    user.id = user_id
    user.real_name = real_name
    return user


class TestQuotesService(unittest.TestCase):
    """QuotesService 测试类"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = QuotesService(self.db)

    def _setup_query_results(self, quotes=None, total=0):
        """设置查询结果"""
        query = MagicMock()
        self.db.query.return_value = query

        # 链式调用模拟
        mock_query = MagicMock()
        query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = quotes or []
        mock_query.count.return_value = total
        mock_query.order_by.return_value = mock_query

        return mock_query

    def test_get_quotes_returns_paginated_response(self):
        """测试获取报价列表返回分页响应"""
        quotes = [_make_mock_quote(quote_id=i) for i in range(1, 6)]
        self._setup_query_results(quotes=quotes, total=5)

        result = self.svc.get_quotes(page=1, page_size=10)

        self.assertEqual(result.total, 5)
        self.assertEqual(result.page, 1)
        self.assertEqual(result.page_size, 10)

    def test_get_quotes_with_keyword_filter(self):
        """测试带关键字搜索的报价列表"""
        self._setup_query_results(quotes=[], total=0)

        result = self.svc.get_quotes(keyword="测试")

        # 验证 filter 方法被调用
        self.db.query.return_value.options.return_value.filter.assert_called()

    def test_get_quotes_with_status_filter(self):
        """测试带状态筛选的报价列表"""
        self._setup_query_results(quotes=[], total=0)

        result = self.svc.get_quotes(status="DRAFT")

        # 验证 filter 方法被调用
        self.db.query.return_value.options.return_value.filter.assert_called()

    def test_get_quotes_with_customer_filter(self):
        """测试带客户筛选的报价列表"""
        self._setup_query_results(quotes=[], total=0)

        result = self.svc.get_quotes(customer_id=1)

        # 验证 filter 方法被调用
        self.db.query.return_value.options.return_value.filter.assert_called()

    def test_get_quotes_with_date_range(self):
        """测试带日期范围筛选的报价列表"""
        self._setup_query_results(quotes=[], total=0)

        result = self.svc.get_quotes(
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )

        # 验证 filter 方法被调用
        self.db.query.return_value.options.return_value.filter.assert_called()


class TestQuotesServiceCreate(unittest.TestCase):
    """QuotesService 创建测试类"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = QuotesService(self.db)

    def test_create_quote_invocates_service(self):
        """测试创建报价调用服务方法"""
        # 这个测试只验证方法存在和可调用
        self.assertTrue(hasattr(self.svc, 'create_quote'))
        self.assertTrue(callable(self.svc.create_quote))


class TestGenerateQuoteNumber(unittest.TestCase):
    """报价编号生成测试类"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = QuotesService(self.db)

    def _setup_query_results(self, count=0):
        """设置查询计数结果"""
        query = MagicMock()
        self.db.query.return_value = query
        query.filter.return_value = query
        query.count.return_value = count

    def test_generate_quote_number_first_of_day(self):
        """测试当天第一个报价编号"""
        self._setup_query_results(count=0)

        quote_number = self.svc._generate_quote_number()

        # 应该是 QT + 日期 + 0001
        self.assertTrue(quote_number.startswith("QT"))
        self.assertTrue(quote_number.endswith("0001"))

    def test_generate_quote_number_increments(self):
        """测试报价编号递增"""
        self._setup_query_results(count=5)

        quote_number = self.svc._generate_quote_number()

        # 应该是 QT + 日期 + 0006
        self.assertTrue(quote_number.startswith("QT"))
        self.assertTrue(quote_number.endswith("0006"))


class TestInferQuoteType(unittest.TestCase):
    """报价类型推断测试类"""

    def test_infer_quote_type_service(self):
        """测试推断服务类型报价"""
        result = QuotesService._infer_quote_type("维保服务报价")
        self.assertEqual(result, "SERVICE")

    def test_infer_quote_type_service_lowercase(self):
        """测试推断服务类型报价（小写）"""
        result = QuotesService._infer_quote_type("maintenance service")
        self.assertEqual(result, "SERVICE")

    def test_infer_quote_type_standard(self):
        """测试推断标准类型报价"""
        result = QuotesService._infer_quote_type("标准件报价")
        self.assertEqual(result, "STANDARD")

    def test_infer_quote_type_project(self):
        """测试推断项目类型报价"""
        result = QuotesService._infer_quote_type("自动化产线项目")
        self.assertEqual(result, "PROJECT")

    def test_infer_quote_type_default(self):
        """测试默认类型报价"""
        result = QuotesService._infer_quote_type("其他报价")
        self.assertEqual(result, "CUSTOM")


class TestInferPriority(unittest.TestCase):
    """优先级推断测试类"""

    def test_infer_priority_rejected(self):
        """测试已拒绝状态返回低优先级"""
        result = QuotesService._infer_priority("REJECTED", None)
        self.assertEqual(result, "LOW")

    def test_infer_priority_expired(self):
        """测试过期状态返回低优先级"""
        result = QuotesService._infer_priority("EXPIRED", None)
        self.assertEqual(result, "LOW")

    def test_infer_priority_in_review(self):
        """测试审核中状态返回高优先级"""
        result = QuotesService._infer_priority("IN_REVIEW", None)
        self.assertEqual(result, "HIGH")

    def test_infer_priority_submitted(self):
        """测试已提交状态返回高优先级"""
        result = QuotesService._infer_priority("SUBMITTED", None)
        self.assertEqual(result, "HIGH")

    def test_infer_priority_urgent_within_week(self):
        """测试7天内过期返回紧急优先级"""
        future_date = date.today() + timedelta(days=5)
        result = QuotesService._infer_priority("DRAFT", future_date)
        self.assertEqual(result, "URGENT")

    def test_infer_priority_medium_normal(self):
        """测试正常状态返回中等优先级"""
        future_date = date.today() + timedelta(days=30)
        result = QuotesService._infer_priority("DRAFT", future_date)
        self.assertEqual(result, "MEDIUM")


class TestPickDisplayVersion(unittest.TestCase):
    """选择显示版本测试类"""

    def test_pick_current_version(self):
        """测试优先选择当前版本"""
        quote = MagicMock()
        quote.current_version = MagicMock(id=1)
        quote.versions = []

        result = QuotesService._pick_display_version(quote)
        self.assertEqual(result.id, 1)

    def test_pick_latest_version(self):
        """测试无当前版本时选择最新版本"""
        quote = MagicMock()
        quote.current_version = None
        quote.versions = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3),
        ]

        result = QuotesService._pick_display_version(quote)
        self.assertEqual(result.id, 3)

    def test_pick_none_when_no_versions(self):
        """测试无版本时返回None"""
        quote = MagicMock()
        quote.current_version = None
        quote.versions = []

        result = QuotesService._pick_display_version(quote)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()