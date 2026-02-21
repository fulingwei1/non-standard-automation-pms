# -*- coding: utf-8 -*-
"""
商务支持报表服务单元测试

目标：
1. 只mock外部依赖（db.query, db.execute等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.services.business_support_reports.business_support_reports_service import (
    BusinessSupportReportsService,
)


class TestBusinessSupportReportsService(unittest.TestCase):
    """测试商务支持报表服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = BusinessSupportReportsService(self.db)

    # ========== 日期解析辅助方法测试 ==========

    def test_parse_week_string_normal(self):
        """测试解析正常的周字符串"""
        year, week_num, week_start, week_end = self.service.parse_week_string("2024-W01")
        self.assertEqual(year, 2024)
        self.assertEqual(week_num, 1)
        self.assertIsInstance(week_start, date)
        self.assertIsInstance(week_end, date)
        self.assertEqual((week_end - week_start).days, 6)

    def test_parse_week_string_mid_year(self):
        """测试解析年中的周"""
        year, week_num, week_start, week_end = self.service.parse_week_string("2024-W26")
        self.assertEqual(year, 2024)
        self.assertEqual(week_num, 26)
        self.assertEqual((week_end - week_start).days, 6)

    def test_get_current_week_range(self):
        """测试获取当前周范围"""
        year, week_num, week_start, week_end = self.service.get_current_week_range()
        today = date.today()
        self.assertEqual(year, today.year)
        self.assertIsInstance(week_num, int)
        self.assertGreater(week_num, 0)
        self.assertLessEqual(week_num, 53)
        self.assertEqual((week_end - week_start).days, 6)
        # 验证今天在这个周范围内
        self.assertGreaterEqual(today, week_start)
        self.assertLessEqual(today, week_end)

    # ========== calculate_contract_stats() 测试 ==========

    def test_calculate_contract_stats_with_contracts(self):
        """测试有合同的情况"""
        # Mock新签合同
        mock_contract1 = Mock()
        mock_contract1.contract_amount = Decimal("50000")
        mock_contract2 = Mock()
        mock_contract2.contract_amount = Decimal("30000")

        # Mock filter().all() 链
        filter_mock1 = MagicMock()
        filter_mock1.all.return_value = [mock_contract1, mock_contract2]
        
        new_contracts_query = MagicMock()
        new_contracts_query.filter.return_value = filter_mock1

        # Mock活跃合同 filter().count()
        filter_mock2 = MagicMock()
        filter_mock2.count.return_value = 15
        
        active_query = MagicMock()
        active_query.filter.return_value = filter_mock2

        # Mock完成合同 filter().count()
        filter_mock3 = MagicMock()
        filter_mock3.count.return_value = 8
        
        completed_query = MagicMock()
        completed_query.filter.return_value = filter_mock3

        self.db.query.side_effect = [
            new_contracts_query,
            active_query,
            completed_query,
        ]

        result = self.service.calculate_contract_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["new_amount"], Decimal("80000"))
        self.assertEqual(result["active_count"], 15)
        self.assertEqual(result["completed_count"], 8)

    def test_calculate_contract_stats_no_contracts(self):
        """测试没有合同的情况"""
        # Mock返回空列表
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        active_query = MagicMock()
        active_query.filter.return_value.count.return_value = 0

        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 0

        self.db.query.side_effect = [mock_query, active_query, completed_query]

        result = self.service.calculate_contract_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["new_count"], 0)
        self.assertEqual(result["new_amount"], Decimal("0"))
        self.assertEqual(result["active_count"], 0)
        self.assertEqual(result["completed_count"], 0)

    def test_calculate_contract_stats_null_amount(self):
        """测试合同金额为None的情况"""
        mock_contract = Mock()
        mock_contract.contract_amount = None

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_contract
        ]

        active_query = MagicMock()
        active_query.filter.return_value.count.return_value = 0

        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 0

        self.db.query.side_effect = [mock_query, active_query, completed_query]

        result = self.service.calculate_contract_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["new_amount"], Decimal("0"))

    # ========== calculate_order_stats() 测试 ==========

    def test_calculate_order_stats_with_orders(self):
        """测试有订单的情况"""
        mock_order1 = Mock()
        mock_order1.order_amount = Decimal("10000")
        mock_order2 = Mock()
        mock_order2.order_amount = Decimal("20000")

        # Mock filter().all() 链
        filter_mock = MagicMock()
        filter_mock.all.return_value = [mock_order1, mock_order2]
        
        query_mock = MagicMock()
        query_mock.filter.return_value = filter_mock

        self.db.query.return_value = query_mock

        result = self.service.calculate_order_stats(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["new_amount"], Decimal("30000"))

    def test_calculate_order_stats_no_orders(self):
        """测试没有订单的情况"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        result = self.service.calculate_order_stats(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(result["new_count"], 0)
        self.assertEqual(result["new_amount"], Decimal("0"))

    def test_calculate_order_stats_null_amount(self):
        """测试订单金额为None"""
        mock_order = Mock()
        mock_order.order_amount = None

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [mock_order]

        self.db.query.return_value = mock_query

        result = self.service.calculate_order_stats(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(result["new_amount"], Decimal("0"))

    # ========== calculate_receipt_stats() 测试 ==========

    def test_calculate_receipt_stats_normal(self):
        """测试正常回款统计"""
        # Mock计划回款
        planned_result = Mock()
        planned_result.fetchone.return_value = (Decimal("100000"),)

        # Mock实际回款
        actual_result = Mock()
        actual_result.fetchone.return_value = (Decimal("80000"),)

        # Mock逾期回款
        overdue_result = Mock()
        overdue_result.fetchone.return_value = (Decimal("15000"),)

        self.db.execute.side_effect = [
            planned_result,
            actual_result,
            overdue_result,
        ]

        result = self.service.calculate_receipt_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["planned"], Decimal("100000"))
        self.assertEqual(result["actual"], Decimal("80000"))
        self.assertEqual(result["rate"], Decimal("80"))  # 80/100 * 100 = 80
        self.assertEqual(result["overdue"], Decimal("15000"))

    def test_calculate_receipt_stats_zero_planned(self):
        """测试计划回款为0的情况"""
        planned_result = Mock()
        planned_result.fetchone.return_value = (Decimal("0"),)

        actual_result = Mock()
        actual_result.fetchone.return_value = (Decimal("0"),)

        overdue_result = Mock()
        overdue_result.fetchone.return_value = (Decimal("0"),)

        self.db.execute.side_effect = [planned_result, actual_result, overdue_result]

        result = self.service.calculate_receipt_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["rate"], Decimal("0"))

    def test_calculate_receipt_stats_null_values(self):
        """测试返回None的情况"""
        planned_result = Mock()
        planned_result.fetchone.return_value = (None,)

        actual_result = Mock()
        actual_result.fetchone.return_value = (None,)

        overdue_result = Mock()
        overdue_result.fetchone.return_value = (None,)

        self.db.execute.side_effect = [planned_result, actual_result, overdue_result]

        result = self.service.calculate_receipt_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["planned"], Decimal("0"))
        self.assertEqual(result["actual"], Decimal("0"))
        self.assertEqual(result["overdue"], Decimal("0"))

    def test_calculate_receipt_stats_no_result(self):
        """测试没有结果的情况"""
        planned_result = Mock()
        planned_result.fetchone.return_value = None

        actual_result = Mock()
        actual_result.fetchone.return_value = None

        overdue_result = Mock()
        overdue_result.fetchone.return_value = None

        self.db.execute.side_effect = [planned_result, actual_result, overdue_result]

        result = self.service.calculate_receipt_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["planned"], Decimal("0"))
        self.assertEqual(result["actual"], Decimal("0"))
        self.assertEqual(result["overdue"], Decimal("0"))

    # ========== calculate_invoice_stats() 测试 ==========

    def test_calculate_invoice_stats_normal(self):
        """测试正常开票统计"""
        # Mock开票记录
        mock_invoice1 = Mock()
        mock_invoice1.invoice_amount = Decimal("50000")
        mock_invoice2 = Mock()
        mock_invoice2.invoice_amount = Decimal("30000")

        # Mock filter().all() 链
        filter_mock = MagicMock()
        filter_mock.all.return_value = [mock_invoice1, mock_invoice2]
        
        query_mock = MagicMock()
        query_mock.filter.return_value = filter_mock

        self.db.query.return_value = query_mock

        # Mock需要开票总数
        total_result = Mock()
        total_result.fetchone.return_value = (10,)

        self.db.execute.return_value = total_result

        result = self.service.calculate_invoice_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["amount"], Decimal("80000"))
        self.assertEqual(result["rate"], Decimal("20"))  # 2/10 * 100 = 20

    def test_calculate_invoice_stats_no_invoices(self):
        """测试没有开票的情况"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        total_result = Mock()
        total_result.fetchone.return_value = (0,)

        self.db.execute.return_value = total_result

        result = self.service.calculate_invoice_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["amount"], Decimal("0"))
        self.assertEqual(result["rate"], Decimal("0"))

    def test_calculate_invoice_stats_null_amount(self):
        """测试开票金额为None"""
        mock_invoice = Mock()
        mock_invoice.invoice_amount = None

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_invoice
        ]

        self.db.query.return_value = mock_query

        total_result = Mock()
        total_result.fetchone.return_value = (1,)

        self.db.execute.return_value = total_result

        result = self.service.calculate_invoice_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["amount"], Decimal("0"))

    def test_calculate_invoice_stats_no_total_needed(self):
        """测试需要开票总数为None"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        total_result = Mock()
        total_result.fetchone.return_value = None

        self.db.execute.return_value = total_result

        result = self.service.calculate_invoice_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["rate"], Decimal("0"))

    # ========== calculate_bidding_stats() 测试 ==========

    def test_calculate_bidding_stats_normal(self):
        """测试正常投标统计"""
        # Mock新增投标 filter().count()
        new_filter = MagicMock()
        new_filter.count.return_value = 5
        new_query = MagicMock()
        new_query.filter.return_value = new_filter

        # Mock中标 filter().count()
        won_filter = MagicMock()
        won_filter.count.return_value = 2
        won_query = MagicMock()
        won_query.filter.return_value = won_filter

        # Mock总数 count()
        total_query = MagicMock()
        total_query.count.return_value = 20

        self.db.query.side_effect = [
            new_query,
            won_query,
            total_query,
        ]

        result = self.service.calculate_bidding_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["new_count"], 5)
        self.assertEqual(result["won_count"], 2)
        self.assertEqual(result["win_rate"], Decimal("10"))  # 2/20 * 100 = 10

    def test_calculate_bidding_stats_zero_total(self):
        """测试总投标数为0"""
        new_query = MagicMock()
        new_query.filter.return_value.filter.return_value.count.return_value = 0

        won_query = MagicMock()
        won_query.filter.return_value.filter.return_value.filter.return_value.count.return_value = 0

        total_query = MagicMock()
        total_query.count.return_value = 0

        self.db.query.side_effect = [new_query, won_query, total_query]

        result = self.service.calculate_bidding_stats(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["win_rate"], Decimal("0"))

    # ========== get_daily_report() 测试 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_daily_report_with_date(self, mock_date_class):
        """测试指定日期的日报"""
        # Mock合同查询 - 新签合同 filter().all()
        mock_contract = Mock()
        mock_contract.contract_amount = Decimal("50000")

        new_contracts_filter = MagicMock()
        new_contracts_filter.all.return_value = [mock_contract]
        new_contracts_query = MagicMock()
        new_contracts_query.filter.return_value = new_contracts_filter

        # 活跃合同 filter().count()
        active_filter = MagicMock()
        active_filter.count.return_value = 10
        active_query = MagicMock()
        active_query.filter.return_value = active_filter

        # 完成合同 filter().count()
        completed_filter = MagicMock()
        completed_filter.count.return_value = 5
        completed_query = MagicMock()
        completed_query.filter.return_value = completed_filter

        # Mock订单查询 filter().all()
        mock_order = Mock()
        mock_order.order_amount = Decimal("20000")

        orders_filter = MagicMock()
        orders_filter.all.return_value = [mock_order]
        orders_query = MagicMock()
        orders_query.filter.return_value = orders_filter

        # Mock开票查询 filter().all()
        mock_invoice = Mock()
        mock_invoice.invoice_amount = Decimal("30000")

        invoices_filter = MagicMock()
        invoices_filter.all.return_value = [mock_invoice]
        invoices_query = MagicMock()
        invoices_query.filter.return_value = invoices_filter

        # Mock投标查询 filter().count()
        new_bidding_filter = MagicMock()
        new_bidding_filter.count.return_value = 3
        new_bidding_query = MagicMock()
        new_bidding_query.filter.return_value = new_bidding_filter

        won_bidding_filter = MagicMock()
        won_bidding_filter.count.return_value = 1
        won_bidding_query = MagicMock()
        won_bidding_query.filter.return_value = won_bidding_filter

        total_bidding_query = MagicMock()
        total_bidding_query.count.return_value = 30

        self.db.query.side_effect = [
            new_contracts_query,  # 新签合同
            active_query,  # 活跃合同
            completed_query,  # 完成合同
            orders_query,  # 新订单
            invoices_query,  # 开票
            new_bidding_query,  # 新投标
            won_bidding_query,  # 中标
            total_bidding_query,  # 总投标
        ]

        # Mock SQL执行结果（回款）
        planned_receipt = Mock()
        planned_receipt.fetchone.return_value = (Decimal("100000"),)

        actual_receipt = Mock()
        actual_receipt.fetchone.return_value = (Decimal("80000"),)

        overdue_receipt = Mock()
        overdue_receipt.fetchone.return_value = (Decimal("10000"),)

        # Mock开票需求总数
        total_invoice_needed = Mock()
        total_invoice_needed.fetchone.return_value = (10,)

        self.db.execute.side_effect = [
            planned_receipt,
            actual_receipt,
            overdue_receipt,
            total_invoice_needed,
        ]

        result = self.service.get_daily_report("2024-01-15")

        self.assertEqual(result["report_date"], "2024-01-15")
        self.assertEqual(result["report_type"], "daily")
        self.assertEqual(result["new_contracts_count"], 1)
        self.assertEqual(result["new_contracts_amount"], Decimal("50000"))
        self.assertEqual(result["active_contracts_count"], 10)
        self.assertEqual(result["completed_contracts_count"], 5)
        self.assertEqual(result["new_orders_count"], 1)
        self.assertEqual(result["new_orders_amount"], Decimal("20000"))
        self.assertEqual(result["planned_receipt_amount"], Decimal("100000"))
        self.assertEqual(result["actual_receipt_amount"], Decimal("80000"))
        self.assertEqual(result["receipt_completion_rate"], Decimal("80"))
        self.assertEqual(result["overdue_amount"], Decimal("10000"))
        self.assertEqual(result["invoices_count"], 1)
        self.assertEqual(result["invoices_amount"], Decimal("30000"))
        self.assertEqual(result["invoice_rate"], Decimal("10"))  # 1/10 * 100
        self.assertEqual(result["new_bidding_count"], 3)
        self.assertEqual(result["won_bidding_count"], 1)
        self.assertAlmostEqual(
            float(result["bidding_win_rate"]), 3.33, places=2
        )  # 1/30*100

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_daily_report_no_date(self, mock_date_class):
        """测试不指定日期（使用今天）"""
        # Mock date.today()
        mock_today = date(2024, 2, 21)
        mock_date_class.today.return_value = mock_today

        # Mock所有查询为空
        empty_query = MagicMock()
        empty_query.filter.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []
        empty_query.filter.return_value.count.return_value = 0
        empty_query.filter.return_value.filter.return_value.count.return_value = 0
        empty_query.count.return_value = 0

        self.db.query.return_value = empty_query

        # Mock SQL返回0
        empty_result = Mock()
        empty_result.fetchone.return_value = (0,)

        self.db.execute.return_value = empty_result

        result = self.service.get_daily_report()

        self.assertEqual(result["report_date"], "2024-02-21")
        self.assertEqual(result["report_type"], "daily")
        self.assertEqual(result["new_contracts_count"], 0)

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_daily_report_zero_planned_receipt(self, mock_date_class):
        """测试计划回款为0的情况"""
        # Mock所有查询为空
        empty_query = MagicMock()
        empty_query.filter.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []
        empty_query.filter.return_value.count.return_value = 0
        empty_query.filter.return_value.filter.return_value.count.return_value = 0
        empty_query.count.return_value = 0

        self.db.query.return_value = empty_query

        # Mock回款为0
        zero_result = Mock()
        zero_result.fetchone.return_value = (0,)

        self.db.execute.return_value = zero_result

        result = self.service.get_daily_report("2024-01-15")

        self.assertEqual(result["receipt_completion_rate"], Decimal("0"))

    # ========== get_weekly_report() 测试 ==========

    @patch.object(BusinessSupportReportsService, "calculate_contract_stats")
    @patch.object(BusinessSupportReportsService, "calculate_order_stats")
    @patch.object(BusinessSupportReportsService, "calculate_receipt_stats")
    @patch.object(BusinessSupportReportsService, "calculate_invoice_stats")
    @patch.object(BusinessSupportReportsService, "calculate_bidding_stats")
    def test_get_weekly_report_with_week(
        self,
        mock_bidding,
        mock_invoice,
        mock_receipt,
        mock_order,
        mock_contract,
    ):
        """测试指定周的周报"""
        # Mock各统计方法返回值
        mock_contract.return_value = {
            "new_count": 5,
            "new_amount": Decimal("250000"),
            "active_count": 20,
            "completed_count": 10,
        }

        mock_order.return_value = {
            "new_count": 8,
            "new_amount": Decimal("160000"),
        }

        mock_receipt.return_value = {
            "planned": Decimal("500000"),
            "actual": Decimal("400000"),
            "rate": Decimal("80"),
            "overdue": Decimal("50000"),
        }

        mock_invoice.return_value = {
            "count": 12,
            "amount": Decimal("360000"),
            "rate": Decimal("60"),
        }

        mock_bidding.return_value = {
            "new_count": 10,
            "won_count": 3,
            "win_rate": Decimal("15"),
        }

        result = self.service.get_weekly_report("2024-W03")

        self.assertEqual(result["report_date"], "2024-W03")
        self.assertEqual(result["report_type"], "weekly")
        self.assertEqual(result["new_contracts_count"], 5)
        self.assertEqual(result["new_contracts_amount"], Decimal("250000"))
        self.assertEqual(result["active_contracts_count"], 20)
        self.assertEqual(result["completed_contracts_count"], 10)
        self.assertEqual(result["new_orders_count"], 8)
        self.assertEqual(result["new_orders_amount"], Decimal("160000"))
        self.assertEqual(result["planned_receipt_amount"], Decimal("500000"))
        self.assertEqual(result["actual_receipt_amount"], Decimal("400000"))
        self.assertEqual(result["receipt_completion_rate"], Decimal("80"))
        self.assertEqual(result["overdue_amount"], Decimal("50000"))
        self.assertEqual(result["invoices_count"], 12)
        self.assertEqual(result["invoices_amount"], Decimal("360000"))
        self.assertEqual(result["invoice_rate"], Decimal("60"))
        self.assertEqual(result["new_bidding_count"], 10)
        self.assertEqual(result["won_bidding_count"], 3)
        self.assertEqual(result["bidding_win_rate"], Decimal("15"))

        # 验证调用了辅助方法
        mock_contract.assert_called_once()
        mock_order.assert_called_once()
        mock_receipt.assert_called_once()
        mock_invoice.assert_called_once()
        mock_bidding.assert_called_once()

    @patch.object(BusinessSupportReportsService, "get_current_week_range")
    @patch.object(BusinessSupportReportsService, "calculate_contract_stats")
    @patch.object(BusinessSupportReportsService, "calculate_order_stats")
    @patch.object(BusinessSupportReportsService, "calculate_receipt_stats")
    @patch.object(BusinessSupportReportsService, "calculate_invoice_stats")
    @patch.object(BusinessSupportReportsService, "calculate_bidding_stats")
    def test_get_weekly_report_no_week(
        self,
        mock_bidding,
        mock_invoice,
        mock_receipt,
        mock_order,
        mock_contract,
        mock_current_week,
    ):
        """测试不指定周（使用当前周）"""
        # Mock当前周
        mock_current_week.return_value = (
            2024,
            8,
            date(2024, 2, 19),
            date(2024, 2, 25),
        )

        # Mock统计方法返回空数据
        mock_contract.return_value = {
            "new_count": 0,
            "new_amount": Decimal("0"),
            "active_count": 0,
            "completed_count": 0,
        }

        mock_order.return_value = {
            "new_count": 0,
            "new_amount": Decimal("0"),
        }

        mock_receipt.return_value = {
            "planned": Decimal("0"),
            "actual": Decimal("0"),
            "rate": Decimal("0"),
            "overdue": Decimal("0"),
        }

        mock_invoice.return_value = {
            "count": 0,
            "amount": Decimal("0"),
            "rate": Decimal("0"),
        }

        mock_bidding.return_value = {
            "new_count": 0,
            "won_count": 0,
            "win_rate": Decimal("0"),
        }

        result = self.service.get_weekly_report()

        self.assertEqual(result["report_date"], "2024-W08")
        self.assertEqual(result["report_type"], "weekly")

        # 验证调用了get_current_week_range
        mock_current_week.assert_called_once()


if __name__ == "__main__":
    unittest.main()
