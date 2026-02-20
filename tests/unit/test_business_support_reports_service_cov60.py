# -*- coding: utf-8 -*-
"""
商务支持报表服务单元测试
测试覆盖率目标：60%+
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.business_support_reports import BusinessSupportReportsService


class TestBusinessSupportReportsService(unittest.TestCase):
    """商务支持报表服务测试类"""

    def setUp(self):
        """测试初始化"""
        self.mock_db = MagicMock()
        self.service = BusinessSupportReportsService(self.mock_db)

    def tearDown(self):
        """测试清理"""
        self.mock_db = None
        self.service = None

    # ========== 测试1: 周字符串解析 ==========

    def test_parse_week_string(self):
        """测试解析周字符串"""
        year, week_num, week_start, week_end = self.service.parse_week_string(
            "2024-W10"
        )

        self.assertEqual(year, 2024)
        self.assertEqual(week_num, 10)
        self.assertIsInstance(week_start, date)
        self.assertIsInstance(week_end, date)
        self.assertEqual((week_end - week_start).days, 6)

    # ========== 测试2: 获取当前周范围 ==========

    def test_get_current_week_range(self):
        """测试获取当前周范围"""
        year, week_num, week_start, week_end = self.service.get_current_week_range()

        self.assertIsInstance(year, int)
        self.assertIsInstance(week_num, int)
        self.assertIsInstance(week_start, date)
        self.assertIsInstance(week_end, date)
        self.assertEqual((week_end - week_start).days, 6)
        self.assertGreater(year, 2020)

    # ========== 测试3: 计算合同统计 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.Contract")
    def test_calculate_contract_stats(self, mock_contract_class):
        """测试计算合同统计"""
        # Mock查询结果
        mock_contract1 = MagicMock()
        mock_contract1.contract_amount = Decimal("100000")

        mock_contract2 = MagicMock()
        mock_contract2.contract_amount = Decimal("200000")

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            mock_contract1,
            mock_contract2,
        ]
        mock_query.filter.return_value.count.side_effect = [5, 3]

        self.mock_db.query.return_value = mock_query

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.calculate_contract_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["new_amount"], Decimal("300000"))
        self.assertEqual(result["active_count"], 5)
        self.assertEqual(result["completed_count"], 3)

    # ========== 测试4: 计算订单统计 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.SalesOrder")
    def test_calculate_order_stats(self, mock_order_class):
        """测试计算订单统计"""
        # Mock订单
        mock_order1 = MagicMock()
        mock_order1.order_amount = Decimal("50000")

        mock_order2 = MagicMock()
        mock_order2.order_amount = Decimal("75000")

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_order1, mock_order2]

        self.mock_db.query.return_value = mock_query

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.calculate_order_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["new_amount"], Decimal("125000"))

    # ========== 测试5: 计算回款统计 ==========

    def test_calculate_receipt_stats(self):
        """测试计算回款统计"""
        # Mock SQL执行结果
        mock_execute = self.mock_db.execute
        mock_execute.return_value.fetchone.side_effect = [
            (Decimal("100000"),),  # planned
            (Decimal("80000"),),  # actual
            (Decimal("20000"),),  # overdue
        ]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.calculate_receipt_stats(start_date, end_date)

        self.assertEqual(result["planned"], Decimal("100000"))
        self.assertEqual(result["actual"], Decimal("80000"))
        self.assertEqual(result["rate"], Decimal("80"))
        self.assertEqual(result["overdue"], Decimal("20000"))

    # ========== 测试6: 计算开票统计 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.Invoice")
    def test_calculate_invoice_stats(self, mock_invoice_class):
        """测试计算开票统计"""
        # Mock发票
        mock_invoice1 = MagicMock()
        mock_invoice1.invoice_amount = Decimal("30000")

        mock_invoice2 = MagicMock()
        mock_invoice2.invoice_amount = Decimal("40000")

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [
            mock_invoice1,
            mock_invoice2,
        ]

        self.mock_db.query.return_value = mock_query

        # Mock total_needed查询
        self.mock_db.execute.return_value.fetchone.return_value = (10,)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.calculate_invoice_stats(start_date, end_date)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["amount"], Decimal("70000"))
        self.assertEqual(result["rate"], Decimal("20"))  # 2/10 * 100

    # ========== 测试7: 计算投标统计 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.BiddingProject")
    def test_calculate_bidding_stats(self, mock_bidding_class):
        """测试计算投标统计"""
        mock_query = MagicMock()
        mock_query.filter.return_value.count.side_effect = [5, 3, 20]

        self.mock_db.query.return_value = mock_query

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.calculate_bidding_stats(start_date, end_date)

        self.assertEqual(result["new_count"], 5)
        self.assertEqual(result["won_count"], 3)
        self.assertEqual(result["win_rate"], Decimal("15"))  # 3/20 * 100

    # ========== 测试8: 获取日报数据 - 基础场景 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.BiddingProject")
    @patch("app.services.business_support_reports.business_support_reports_service.Invoice")
    @patch("app.services.business_support_reports.business_support_reports_service.SalesOrder")
    @patch("app.services.business_support_reports.business_support_reports_service.Contract")
    def test_get_daily_report_basic(
        self,
        mock_contract_class,
        mock_order_class,
        mock_invoice_class,
        mock_bidding_class,
    ):
        """测试获取日报数据 - 基础场景"""
        # Mock合同查询
        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_contract]
        mock_query.filter.return_value.count.side_effect = [5, 3, 2, 1, 10]

        self.mock_db.query.return_value = mock_query

        # Mock SQL执行结果
        self.mock_db.execute.return_value.fetchone.side_effect = [
            (Decimal("50000"),),  # planned_receipt
            (Decimal("40000"),),  # actual_receipt
            (Decimal("10000"),),  # overdue
            (5,),  # total_needed
        ]

        result = self.service.get_daily_report("2024-01-15")

        self.assertEqual(result["report_type"], "daily")
        self.assertEqual(result["report_date"], "2024-01-15")
        self.assertIn("new_contracts_count", result)
        self.assertIn("new_orders_count", result)
        self.assertIn("invoices_count", result)
        self.assertIn("new_bidding_count", result)

    # ========== 测试9: 获取日报数据 - 使用今天日期 ==========

    @patch("app.services.business_support_reports.business_support_reports_service.BiddingProject")
    @patch("app.services.business_support_reports.business_support_reports_service.Invoice")
    @patch("app.services.business_support_reports.business_support_reports_service.SalesOrder")
    @patch("app.services.business_support_reports.business_support_reports_service.Contract")
    def test_get_daily_report_today(
        self,
        mock_contract_class,
        mock_order_class,
        mock_invoice_class,
        mock_bidding_class,
    ):
        """测试获取日报数据 - 使用今天日期"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_query.filter.return_value.count.side_effect = [0, 0, 0, 0, 0]

        self.mock_db.query.return_value = mock_query

        self.mock_db.execute.return_value.fetchone.side_effect = [
            (Decimal("0"),),
            (Decimal("0"),),
            (Decimal("0"),),
            (0,),
        ]

        result = self.service.get_daily_report(None)

        self.assertEqual(result["report_type"], "daily")
        self.assertEqual(result["report_date"], date.today().strftime("%Y-%m-%d"))

    # ========== 测试10: 获取周报数据 - 指定周 ==========

    def test_get_weekly_report_with_week(self):
        """测试获取周报数据 - 指定周"""
        with patch.object(
            self.service, "calculate_contract_stats"
        ) as mock_contract, patch.object(
            self.service, "calculate_order_stats"
        ) as mock_order, patch.object(
            self.service, "calculate_receipt_stats"
        ) as mock_receipt, patch.object(
            self.service, "calculate_invoice_stats"
        ) as mock_invoice, patch.object(
            self.service, "calculate_bidding_stats"
        ) as mock_bidding:

            mock_contract.return_value = {
                "new_count": 5,
                "new_amount": Decimal("500000"),
                "active_count": 10,
                "completed_count": 3,
            }
            mock_order.return_value = {
                "new_count": 8,
                "new_amount": Decimal("400000"),
            }
            mock_receipt.return_value = {
                "planned": Decimal("300000"),
                "actual": Decimal("250000"),
                "rate": Decimal("83.33"),
                "overdue": Decimal("50000"),
            }
            mock_invoice.return_value = {
                "count": 6,
                "amount": Decimal("200000"),
                "rate": Decimal("75"),
            }
            mock_bidding.return_value = {
                "new_count": 4,
                "won_count": 2,
                "win_rate": Decimal("50"),
            }

            result = self.service.get_weekly_report("2024-W10")

            self.assertEqual(result["report_type"], "weekly")
            self.assertEqual(result["report_date"], "2024-W10")
            self.assertEqual(result["new_contracts_count"], 5)
            self.assertEqual(result["new_orders_count"], 8)
            self.assertEqual(result["invoices_count"], 6)

    # ========== 测试11: 获取周报数据 - 当前周 ==========

    def test_get_weekly_report_current_week(self):
        """测试获取周报数据 - 当前周"""
        with patch.object(
            self.service, "calculate_contract_stats"
        ) as mock_contract, patch.object(
            self.service, "calculate_order_stats"
        ) as mock_order, patch.object(
            self.service, "calculate_receipt_stats"
        ) as mock_receipt, patch.object(
            self.service, "calculate_invoice_stats"
        ) as mock_invoice, patch.object(
            self.service, "calculate_bidding_stats"
        ) as mock_bidding:

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

            result = self.service.get_weekly_report(None)

            self.assertEqual(result["report_type"], "weekly")
            self.assertIn("-W", result["report_date"])

    # ========== 测试12: 回款统计 - 零除问题 ==========

    def test_calculate_receipt_stats_zero_division(self):
        """测试回款统计 - 处理零除问题"""
        # Mock SQL执行结果 - planned为0
        mock_execute = self.mock_db.execute
        mock_execute.return_value.fetchone.side_effect = [
            (Decimal("0"),),  # planned = 0
            (Decimal("0"),),  # actual
            (Decimal("0"),),  # overdue
        ]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.calculate_receipt_stats(start_date, end_date)

        # 应该返回0而不是抛出异常
        self.assertEqual(result["rate"], Decimal("0"))


if __name__ == "__main__":
    unittest.main()
