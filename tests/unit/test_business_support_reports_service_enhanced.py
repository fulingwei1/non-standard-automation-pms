# -*- coding: utf-8 -*-
"""
商务支持报表服务增强测试
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, Mock, PropertyMock

from app.services.business_support_reports.business_support_reports_service import (
    BusinessSupportReportsService,
)


class TestBusinessSupportReportsService(unittest.TestCase):
    """商务支持报表服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = BusinessSupportReportsService(db=self.mock_db)

    def tearDown(self):
        """测试后清理"""
        self.mock_db.reset_mock()

    # ========== 日期解析辅助方法测试 ==========

    def test_parse_week_string_normal(self):
        """测试正常解析周字符串"""
        year, week_num, week_start, week_end = self.service.parse_week_string("2024-W10")
        self.assertEqual(year, 2024)
        self.assertEqual(week_num, 10)
        self.assertIsInstance(week_start, date)
        self.assertIsInstance(week_end, date)
        self.assertEqual((week_end - week_start).days, 6)

    def test_parse_week_string_year_start(self):
        """测试解析年初周字符串"""
        year, week_num, week_start, week_end = self.service.parse_week_string("2024-W01")
        self.assertEqual(year, 2024)
        self.assertEqual(week_num, 1)
        self.assertEqual((week_end - week_start).days, 6)

    def test_parse_week_string_year_end(self):
        """测试解析年末周字符串"""
        year, week_num, week_start, week_end = self.service.parse_week_string("2024-W52")
        self.assertEqual(year, 2024)
        self.assertEqual(week_num, 52)

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_current_week_range(self, mock_date_class):
        """测试获取当前周范围"""
        mock_date_class.today.return_value = date(2024, 3, 15)  # 周五
        year, week_num, week_start, week_end = self.service.get_current_week_range()
        
        self.assertEqual(year, 2024)
        self.assertIsInstance(week_num, int)
        self.assertEqual(week_start.weekday(), 0)  # 周一
        self.assertEqual((week_end - week_start).days, 6)

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_current_week_range_monday(self, mock_date_class):
        """测试周一获取当前周范围"""
        mock_date_class.today.return_value = date(2024, 3, 11)  # 周一
        year, week_num, week_start, week_end = self.service.get_current_week_range()
        
        self.assertEqual(week_start, date(2024, 3, 11))
        self.assertEqual(week_end, date(2024, 3, 17))

    # ========== 合同统计测试 ==========

    def test_calculate_contract_stats_with_data(self):
        """测试有数据的合同统计"""
        mock_contract1 = MagicMock()
        mock_contract1.contract_amount = Decimal("100000")
        mock_contract2 = MagicMock()
        mock_contract2.contract_amount = Decimal("200000")

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [mock_contract1, mock_contract2]
        
        # Mock count() calls
        mock_filter.count.side_effect = [5, 3]  # active_count, completed_count

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_contract_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["new_amount"], Decimal("300000"))
        self.assertEqual(result["active_count"], 5)
        self.assertEqual(result["completed_count"], 3)

    def test_calculate_contract_stats_no_data(self):
        """测试无数据的合同统计"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []
        mock_filter.count.side_effect = [0, 0]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_contract_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 0)
        self.assertEqual(result["new_amount"], Decimal("0"))

    def test_calculate_contract_stats_with_none_amount(self):
        """测试合同金额为None的情况"""
        mock_contract = MagicMock()
        mock_contract.contract_amount = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [mock_contract]
        mock_filter.count.side_effect = [1, 0]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_contract_stats(start_date, end_date)

        self.assertEqual(result["new_amount"], Decimal("0"))

    # ========== 订单统计测试 ==========

    def test_calculate_order_stats_with_data(self):
        """测试有数据的订单统计"""
        mock_order1 = MagicMock()
        mock_order1.order_amount = Decimal("50000")
        mock_order2 = MagicMock()
        mock_order2.order_amount = Decimal("75000")

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [mock_order1, mock_order2]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_order_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["new_amount"], Decimal("125000"))

    def test_calculate_order_stats_no_data(self):
        """测试无数据的订单统计"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_order_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 0)
        self.assertEqual(result["new_amount"], Decimal("0"))

    def test_calculate_order_stats_with_none_amount(self):
        """测试订单金额为None的情况"""
        mock_order = MagicMock()
        mock_order.order_amount = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [mock_order]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_order_stats(start_date, end_date)

        self.assertEqual(result["new_amount"], Decimal("0"))

    # ========== 回款统计测试 ==========

    def test_calculate_receipt_stats_with_data(self):
        """测试有数据的回款统计"""
        # Mock planned
        mock_planned = MagicMock()
        mock_planned.__getitem__.return_value = 100000
        
        # Mock actual
        mock_actual = MagicMock()
        mock_actual.__getitem__.return_value = 80000
        
        # Mock overdue
        mock_overdue = MagicMock()
        mock_overdue.__getitem__.return_value = 20000

        self.mock_db.execute.return_value.fetchone.side_effect = [
            mock_planned,
            mock_actual,
            mock_overdue,
        ]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_receipt_stats(start_date, end_date)

        self.assertEqual(result["planned"], Decimal("100000"))
        self.assertEqual(result["actual"], Decimal("80000"))
        self.assertEqual(result["rate"], Decimal("80"))
        self.assertEqual(result["overdue"], Decimal("20000"))

    def test_calculate_receipt_stats_no_data(self):
        """测试无数据的回款统计"""
        mock_result = MagicMock()
        mock_result.__getitem__.return_value = None
        
        self.mock_db.execute.return_value.fetchone.side_effect = [
            mock_result,
            mock_result,
            mock_result,
        ]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_receipt_stats(start_date, end_date)

        self.assertEqual(result["planned"], Decimal("0"))
        self.assertEqual(result["actual"], Decimal("0"))
        self.assertEqual(result["rate"], Decimal("0"))

    def test_calculate_receipt_stats_zero_planned(self):
        """测试计划回款为0的情况"""
        mock_planned = MagicMock()
        mock_planned.__getitem__.return_value = 0
        
        mock_actual = MagicMock()
        mock_actual.__getitem__.return_value = 0
        
        mock_overdue = MagicMock()
        mock_overdue.__getitem__.return_value = 0

        self.mock_db.execute.return_value.fetchone.side_effect = [
            mock_planned,
            mock_actual,
            mock_overdue,
        ]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_receipt_stats(start_date, end_date)

        self.assertEqual(result["rate"], Decimal("0"))  # 避免除零

    # ========== 开票统计测试 ==========

    def test_calculate_invoice_stats_with_data(self):
        """测试有数据的开票统计"""
        mock_invoice1 = MagicMock()
        mock_invoice1.invoice_amount = Decimal("30000")
        mock_invoice2 = MagicMock()
        mock_invoice2.invoice_amount = Decimal("40000")

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [mock_invoice1, mock_invoice2]

        mock_total_needed = MagicMock()
        mock_total_needed.__getitem__.return_value = 10
        self.mock_db.execute.return_value.fetchone.return_value = mock_total_needed

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_invoice_stats(start_date, end_date)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["amount"], Decimal("70000"))
        self.assertEqual(result["rate"], Decimal("20"))  # 2/10 * 100

    def test_calculate_invoice_stats_no_data(self):
        """测试无数据的开票统计"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []

        mock_total_needed = MagicMock()
        mock_total_needed.__getitem__.return_value = 0
        self.mock_db.execute.return_value.fetchone.return_value = mock_total_needed

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_invoice_stats(start_date, end_date)

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["rate"], Decimal("0"))

    def test_calculate_invoice_stats_with_none_amount(self):
        """测试发票金额为None的情况"""
        mock_invoice = MagicMock()
        mock_invoice.invoice_amount = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [mock_invoice]

        mock_total_needed = MagicMock()
        mock_total_needed.__getitem__.return_value = 5
        self.mock_db.execute.return_value.fetchone.return_value = mock_total_needed

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_invoice_stats(start_date, end_date)

        self.assertEqual(result["amount"], Decimal("0"))

    # ========== 投标统计测试 ==========

    def test_calculate_bidding_stats_with_data(self):
        """测试有数据的投标统计"""
        # Mock the first query for new_bidding
        mock_query1 = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter1.count.return_value = 5
        mock_query1.filter.return_value = mock_filter1
        
        # Mock the second query for won_bidding
        mock_query2 = MagicMock()
        mock_filter2 = MagicMock()
        mock_filter2.count.return_value = 3
        mock_query2.filter.return_value = mock_filter2
        
        # Mock the third query for total
        mock_query3 = MagicMock()
        mock_query3.count.return_value = 10
        
        self.mock_db.query.side_effect = [mock_query1, mock_query2, mock_query3]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_bidding_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 5)
        self.assertEqual(result["won_count"], 3)
        self.assertEqual(result["win_rate"], Decimal("30"))  # 3/10 * 100

    def test_calculate_bidding_stats_no_data(self):
        """测试无数据的投标统计"""
        # Mock the first query for new_bidding
        mock_query1 = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter1.count.return_value = 0
        mock_query1.filter.return_value = mock_filter1
        
        # Mock the second query for won_bidding
        mock_query2 = MagicMock()
        mock_filter2 = MagicMock()
        mock_filter2.count.return_value = 0
        mock_query2.filter.return_value = mock_filter2
        
        # Mock the third query for total
        mock_query3 = MagicMock()
        mock_query3.count.return_value = 0
        
        self.mock_db.query.side_effect = [mock_query1, mock_query2, mock_query3]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_bidding_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 0)
        self.assertEqual(result["won_count"], 0)
        self.assertEqual(result["win_rate"], Decimal("0"))

    def test_calculate_bidding_stats_zero_total(self):
        """测试总投标数为0的情况"""
        # Mock the first query for new_bidding
        mock_query1 = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter1.count.return_value = 2
        mock_query1.filter.return_value = mock_filter1
        
        # Mock the second query for won_bidding
        mock_query2 = MagicMock()
        mock_filter2 = MagicMock()
        mock_filter2.count.return_value = 1
        mock_query2.filter.return_value = mock_filter2
        
        # Mock the third query for total
        mock_query3 = MagicMock()
        mock_query3.count.return_value = 0
        
        self.mock_db.query.side_effect = [mock_query1, mock_query2, mock_query3]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.calculate_bidding_stats(start_date, end_date)

        self.assertEqual(result["win_rate"], Decimal("0"))  # 避免除零

    # ========== 日报测试 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_daily_report_with_date(self, mock_date_class):
        """测试指定日期的日报"""
        # Mock all database queries
        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")
        
        mock_order = MagicMock()
        mock_order.order_amount = Decimal("50000")
        
        mock_invoice = MagicMock()
        mock_invoice.invoice_amount = Decimal("30000")

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.side_effect = [
            [mock_contract],  # new_contracts
            [mock_order],     # new_orders
            [mock_invoice],   # invoices
        ]
        mock_filter.count.side_effect = [
            2,  # active_contracts
            1,  # completed_contracts
            3,  # new_bidding
            2,  # won_bidding
            10, # total_bidding
        ]

        # Mock execute for receipt and invoice stats
        mock_execute_result = self.mock_db.execute.return_value
        mock_result1 = MagicMock()
        mock_result1.__getitem__.return_value = 100000
        mock_result2 = MagicMock()
        mock_result2.__getitem__.return_value = 80000
        mock_result3 = MagicMock()
        mock_result3.__getitem__.return_value = 20000
        mock_result4 = MagicMock()
        mock_result4.__getitem__.return_value = 5
        
        mock_execute_result.fetchone.side_effect = [
            mock_result1,  # planned_receipt
            mock_result2,  # actual_receipt
            mock_result3,  # overdue
            mock_result4,  # total_needed for invoice_rate
        ]

        result = self.service.get_daily_report("2024-01-15")

        self.assertEqual(result["report_date"], "2024-01-15")
        self.assertEqual(result["report_type"], "daily")
        self.assertEqual(result["new_contracts_count"], 1)
        self.assertEqual(result["new_contracts_amount"], Decimal("100000"))
        self.assertEqual(result["new_orders_count"], 1)
        self.assertEqual(result["invoices_count"], 1)

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_daily_report_default_today(self, mock_date_class):
        """测试默认使用今天日期的日报"""
        mock_date_class.today.return_value = date(2024, 1, 20)

        # Mock all queries to return empty
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.side_effect = [[], [], []]
        mock_filter.count.side_effect = [0, 0, 0, 0, 0]

        # Mock execute
        mock_execute_result = self.mock_db.execute.return_value
        mock_result = MagicMock()
        mock_result.__getitem__.return_value = 0
        mock_execute_result.fetchone.side_effect = [
            mock_result, mock_result, mock_result, mock_result
        ]

        result = self.service.get_daily_report()

        self.assertEqual(result["report_date"], "2024-01-20")
        self.assertEqual(result["report_type"], "daily")

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_daily_report_with_none_amounts(self, mock_date_class):
        """测试日报中金额为None的情况"""
        mock_contract = MagicMock()
        mock_contract.contract_amount = None
        
        mock_order = MagicMock()
        mock_order.order_amount = None
        
        mock_invoice = MagicMock()
        mock_invoice.invoice_amount = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.side_effect = [
            [mock_contract],
            [mock_order],
            [mock_invoice],
        ]
        mock_filter.count.side_effect = [0, 0, 0, 0, 0]

        # Mock execute
        mock_execute_result = self.mock_db.execute.return_value
        mock_result = MagicMock()
        mock_result.__getitem__.return_value = None
        mock_execute_result.fetchone.side_effect = [
            mock_result, mock_result, mock_result, mock_result
        ]

        result = self.service.get_daily_report("2024-01-15")

        self.assertEqual(result["new_contracts_amount"], Decimal("0"))
        self.assertEqual(result["new_orders_amount"], Decimal("0"))
        self.assertEqual(result["invoices_amount"], Decimal("0"))

    # ========== 周报测试 ==========

    def test_get_weekly_report_with_week_string(self):
        """测试指定周的周报"""
        # Mock calculate methods
        with patch.object(
            self.service, "calculate_contract_stats"
        ) as mock_contract_stats, \
             patch.object(
                 self.service, "calculate_order_stats"
             ) as mock_order_stats, \
             patch.object(
                 self.service, "calculate_receipt_stats"
             ) as mock_receipt_stats, \
             patch.object(
                 self.service, "calculate_invoice_stats"
             ) as mock_invoice_stats, \
             patch.object(
                 self.service, "calculate_bidding_stats"
             ) as mock_bidding_stats:

            mock_contract_stats.return_value = {
                "new_count": 5,
                "new_amount": Decimal("500000"),
                "active_count": 10,
                "completed_count": 3,
            }
            mock_order_stats.return_value = {
                "new_count": 8,
                "new_amount": Decimal("300000"),
            }
            mock_receipt_stats.return_value = {
                "planned": Decimal("400000"),
                "actual": Decimal("350000"),
                "rate": Decimal("87.5"),
                "overdue": Decimal("50000"),
            }
            mock_invoice_stats.return_value = {
                "count": 6,
                "amount": Decimal("200000"),
                "rate": Decimal("60"),
            }
            mock_bidding_stats.return_value = {
                "new_count": 10,
                "won_count": 4,
                "win_rate": Decimal("40"),
            }

            result = self.service.get_weekly_report("2024-W10")

            self.assertEqual(result["report_date"], "2024-W10")
            self.assertEqual(result["report_type"], "weekly")
            self.assertEqual(result["new_contracts_count"], 5)
            self.assertEqual(result["new_contracts_amount"], Decimal("500000"))
            self.assertEqual(result["new_orders_count"], 8)
            self.assertEqual(result["receipt_completion_rate"], Decimal("87.5"))

    @patch("app.services.business_support_reports.business_support_reports_service.date")
    def test_get_weekly_report_default_current_week(self, mock_date_class):
        """测试默认使用当前周的周报"""
        mock_date_class.today.return_value = date(2024, 3, 15)

        # Mock calculate methods
        with patch.object(
            self.service, "calculate_contract_stats"
        ) as mock_contract_stats, \
             patch.object(
                 self.service, "calculate_order_stats"
             ) as mock_order_stats, \
             patch.object(
                 self.service, "calculate_receipt_stats"
             ) as mock_receipt_stats, \
             patch.object(
                 self.service, "calculate_invoice_stats"
             ) as mock_invoice_stats, \
             patch.object(
                 self.service, "calculate_bidding_stats"
             ) as mock_bidding_stats:

            mock_contract_stats.return_value = {
                "new_count": 0,
                "new_amount": Decimal("0"),
                "active_count": 0,
                "completed_count": 0,
            }
            mock_order_stats.return_value = {
                "new_count": 0,
                "new_amount": Decimal("0"),
            }
            mock_receipt_stats.return_value = {
                "planned": Decimal("0"),
                "actual": Decimal("0"),
                "rate": Decimal("0"),
                "overdue": Decimal("0"),
            }
            mock_invoice_stats.return_value = {
                "count": 0,
                "amount": Decimal("0"),
                "rate": Decimal("0"),
            }
            mock_bidding_stats.return_value = {
                "new_count": 0,
                "won_count": 0,
                "win_rate": Decimal("0"),
            }

            result = self.service.get_weekly_report()

            self.assertEqual(result["report_type"], "weekly")
            self.assertIn("2024-W", result["report_date"])

    def test_get_weekly_report_year_start_week(self):
        """测试年初第一周的周报"""
        with patch.object(
            self.service, "calculate_contract_stats"
        ) as mock_contract_stats, \
             patch.object(
                 self.service, "calculate_order_stats"
             ) as mock_order_stats, \
             patch.object(
                 self.service, "calculate_receipt_stats"
             ) as mock_receipt_stats, \
             patch.object(
                 self.service, "calculate_invoice_stats"
             ) as mock_invoice_stats, \
             patch.object(
                 self.service, "calculate_bidding_stats"
             ) as mock_bidding_stats:

            # Setup all mock returns
            mock_contract_stats.return_value = {
                "new_count": 1,
                "new_amount": Decimal("100000"),
                "active_count": 1,
                "completed_count": 0,
            }
            mock_order_stats.return_value = {
                "new_count": 1,
                "new_amount": Decimal("50000"),
            }
            mock_receipt_stats.return_value = {
                "planned": Decimal("100000"),
                "actual": Decimal("100000"),
                "rate": Decimal("100"),
                "overdue": Decimal("0"),
            }
            mock_invoice_stats.return_value = {
                "count": 1,
                "amount": Decimal("50000"),
                "rate": Decimal("100"),
            }
            mock_bidding_stats.return_value = {
                "new_count": 2,
                "won_count": 1,
                "win_rate": Decimal("50"),
            }

            result = self.service.get_weekly_report("2024-W01")

            self.assertEqual(result["report_date"], "2024-W01")


if __name__ == "__main__":
    unittest.main()
