# -*- coding: utf-8 -*-
"""
KPI采集器单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date, datetime, timedelta

from app.services.strategy.kpi_collector.collectors import (
    collect_project_metrics,
    collect_finance_metrics,
    collect_purchase_metrics,
    collect_hr_metrics,
)


class TestCollectProjectMetrics(unittest.TestCase):
    """测试项目指标采集器"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()

    def test_project_count_no_filter(self):
        """测试项目数量 - 无筛选条件"""
        # Mock query链
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_COUNT")

        self.assertEqual(result, Decimal(10))
        self.db.query.assert_called_once()

    def test_project_count_with_status_filter(self):
        """测试项目数量 - 带状态筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        self.db.query.return_value = mock_query

        filters = {"status": "COMPLETED"}
        result = collect_project_metrics(self.db, "PROJECT_COUNT", filters)

        self.assertEqual(result, Decimal(5))

    def test_project_count_with_year_filter(self):
        """测试项目数量 - 带年份筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 8
        self.db.query.return_value = mock_query

        filters = {"year": 2024}
        result = collect_project_metrics(self.db, "PROJECT_COUNT", filters)

        self.assertEqual(result, Decimal(8))

    def test_project_count_with_health_status(self):
        """测试项目数量 - 带健康状态筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        self.db.query.return_value = mock_query

        filters = {"health_status": "H1"}
        result = collect_project_metrics(self.db, "PROJECT_COUNT", filters)

        self.assertEqual(result, Decimal(3))

    def test_project_completion_rate_with_projects(self):
        """测试项目完成率 - 有项目数据"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        # 第一次count返回总数10, 第二次count返回完成数6
        mock_query.count.side_effect = [10, 6]
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_COMPLETION_RATE")

        self.assertEqual(result, Decimal("60.0"))

    def test_project_completion_rate_zero_projects(self):
        """测试项目完成率 - 零项目"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_COMPLETION_RATE")

        self.assertEqual(result, Decimal(0))

    def test_project_on_time_rate_with_completed_projects(self):
        """测试按时完成率 - 有完成项目"""
        # 创建mock项目对象
        mock_p1 = MagicMock()
        mock_p1.actual_end_date = date(2024, 1, 15)
        mock_p1.planned_end_date = date(2024, 1, 20)  # 按时

        mock_p2 = MagicMock()
        mock_p2.actual_end_date = date(2024, 1, 25)
        mock_p2.planned_end_date = date(2024, 1, 20)  # 延期

        mock_p3 = MagicMock()
        mock_p3.actual_end_date = date(2024, 1, 18)
        mock_p3.planned_end_date = date(2024, 1, 20)  # 按时

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_p1, mock_p2, mock_p3]
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_ON_TIME_RATE")

        # 3个项目中2个按时，66.67%
        expected = Decimal("66.66666666666666666666666667")
        self.assertEqual(result.quantize(Decimal("0.01")), expected.quantize(Decimal("0.01")))

    def test_project_on_time_rate_no_completed_projects(self):
        """测试按时完成率 - 无完成项目"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_ON_TIME_RATE")

        self.assertEqual(result, Decimal(0))

    def test_project_on_time_rate_missing_dates(self):
        """测试按时完成率 - 缺失日期数据"""
        mock_p1 = MagicMock()
        mock_p1.actual_end_date = None  # 缺失actual_end_date
        mock_p1.planned_end_date = date(2024, 1, 20)

        mock_p2 = MagicMock()
        mock_p2.actual_end_date = date(2024, 1, 15)
        mock_p2.planned_end_date = None  # 缺失planned_end_date

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_p1, mock_p2]
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_ON_TIME_RATE")

        # 两个项目都缺失日期，on_time = 0
        self.assertEqual(result, Decimal(0))

    def test_project_health_rate_with_projects(self):
        """测试项目健康率 - 有项目"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        # 第一次count返回总数10, 第二次count返回H1数7
        mock_query.count.side_effect = [10, 7]
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_HEALTH_RATE")

        self.assertEqual(result, Decimal("70.0"))

    def test_project_health_rate_zero_projects(self):
        """测试项目健康率 - 零项目"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_HEALTH_RATE")

        self.assertEqual(result, Decimal(0))

    def test_project_total_value(self):
        """测试项目总金额"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = 1500000
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_TOTAL_VALUE")

        self.assertEqual(result, Decimal("1500000"))

    def test_project_total_value_null(self):
        """测试项目总金额 - 空值"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = None
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_TOTAL_VALUE")

        self.assertEqual(result, Decimal("0"))

    def test_unknown_metric(self):
        """测试未知指标"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "UNKNOWN_METRIC")

        self.assertIsNone(result)


class TestCollectFinanceMetrics(unittest.TestCase):
    """测试财务指标采集器"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()

    def test_contract_total_amount_no_filter(self):
        """测试合同总金额 - 无筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5000000
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "CONTRACT_TOTAL_AMOUNT")

        self.assertEqual(result, Decimal("5000000"))

    def test_contract_total_amount_with_year(self):
        """测试合同总金额 - 带年份筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3000000
        self.db.query.return_value = mock_query

        filters = {"year": 2024}
        result = collect_finance_metrics(self.db, "CONTRACT_TOTAL_AMOUNT", filters)

        self.assertEqual(result, Decimal("3000000"))

    def test_contract_total_amount_with_customer(self):
        """测试合同总金额 - 带客户筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 1200000
        self.db.query.return_value = mock_query

        filters = {"customer_id": 123}
        result = collect_finance_metrics(self.db, "CONTRACT_TOTAL_AMOUNT", filters)

        self.assertEqual(result, Decimal("1200000"))

    def test_contract_total_amount_null(self):
        """测试合同总金额 - 空值"""
        mock_query = MagicMock()
        mock_query.scalar.return_value = None
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "CONTRACT_TOTAL_AMOUNT")

        self.assertEqual(result, Decimal("0"))

    def test_contract_received_amount(self):
        """测试已收款金额"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3500000
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "CONTRACT_RECEIVED_AMOUNT")

        self.assertEqual(result, Decimal("3500000"))

    def test_contract_received_amount_with_filters(self):
        """测试已收款金额 - 带筛选条件"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 500000
        self.db.query.return_value = mock_query

        filters = {"year": 2024, "project_id": 456}
        result = collect_finance_metrics(self.db, "CONTRACT_RECEIVED_AMOUNT", filters)

        self.assertEqual(result, Decimal("500000"))

    def test_project_cost_total(self):
        """测试项目成本总计"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 800000
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "PROJECT_COST_TOTAL")

        self.assertEqual(result, Decimal("800000"))

    def test_project_cost_total_with_filters(self):
        """测试项目成本总计 - 带筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 150000
        self.db.query.return_value = mock_query

        filters = {"year": 2024, "project_id": 789}
        result = collect_finance_metrics(self.db, "PROJECT_COST_TOTAL", filters)

        self.assertEqual(result, Decimal("150000"))

    def test_project_profit_margin_success(self):
        """测试项目利润率 - 正常情况"""
        # Mock项目查询
        mock_project = MagicMock()
        mock_project.id = 123
        mock_project.contract_amount = 1000000

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project

        # Mock成本查询
        mock_cost_query = MagicMock()
        mock_cost_query.filter.return_value = mock_cost_query
        mock_cost_query.scalar.return_value = 700000

        # 第一次query返回项目，第二次返回成本
        self.db.query.side_effect = [mock_project_query, mock_cost_query]

        filters = {"project_id": 123}
        result = collect_finance_metrics(self.db, "PROJECT_PROFIT_MARGIN", filters)

        # (1000000 - 700000) / 1000000 * 100 = 30.0
        self.assertEqual(result, Decimal("30.0"))

    def test_project_profit_margin_no_project_id(self):
        """测试项目利润率 - 缺少project_id"""
        result = collect_finance_metrics(self.db, "PROJECT_PROFIT_MARGIN")

        self.assertIsNone(result)

    def test_project_profit_margin_project_not_found(self):
        """测试项目利润率 - 项目不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.db.query.return_value = mock_query

        filters = {"project_id": 999}
        result = collect_finance_metrics(self.db, "PROJECT_PROFIT_MARGIN", filters)

        self.assertIsNone(result)

    def test_project_profit_margin_no_contract_amount(self):
        """测试项目利润率 - 无合同金额"""
        mock_project = MagicMock()
        mock_project.contract_amount = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        self.db.query.return_value = mock_query

        filters = {"project_id": 123}
        result = collect_finance_metrics(self.db, "PROJECT_PROFIT_MARGIN", filters)

        # 无合同金额时返回Decimal(0)
        self.assertEqual(result, Decimal(0))

    def test_project_profit_margin_zero_contract_amount(self):
        """测试项目利润率 - 合同金额为0"""
        mock_project = MagicMock()
        mock_project.contract_amount = 0

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project

        mock_cost_query = MagicMock()
        mock_cost_query.filter.return_value = mock_cost_query
        mock_cost_query.scalar.return_value = 0

        self.db.query.side_effect = [mock_project_query, mock_cost_query]

        filters = {"project_id": 123}
        result = collect_finance_metrics(self.db, "PROJECT_PROFIT_MARGIN", filters)

        self.assertEqual(result, Decimal(0))

    def test_receivable_overdue_amount(self):
        """测试逾期应收款金额"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 250000
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "RECEIVABLE_OVERDUE_AMOUNT")

        self.assertEqual(result, Decimal("250000"))

    def test_receivable_overdue_amount_with_project_filter(self):
        """测试逾期应收款金额 - 带项目筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 50000
        self.db.query.return_value = mock_query

        filters = {"project_id": 123}
        result = collect_finance_metrics(self.db, "RECEIVABLE_OVERDUE_AMOUNT", filters)

        self.assertEqual(result, Decimal("50000"))

    def test_receivable_overdue_amount_null(self):
        """测试逾期应收款金额 - 空值"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "RECEIVABLE_OVERDUE_AMOUNT")

        self.assertEqual(result, Decimal("0"))

    def test_receivable_overdue_count(self):
        """测试逾期应收款笔数"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        self.db.query.return_value = mock_query

        result = collect_finance_metrics(self.db, "RECEIVABLE_OVERDUE_COUNT")

        self.assertEqual(result, Decimal(15))

    def test_receivable_overdue_count_with_filter(self):
        """测试逾期应收款笔数 - 带筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3
        self.db.query.return_value = mock_query

        filters = {"project_id": 456}
        result = collect_finance_metrics(self.db, "RECEIVABLE_OVERDUE_COUNT", filters)

        self.assertEqual(result, Decimal(3))

    def test_unknown_finance_metric(self):
        """测试未知财务指标"""
        result = collect_finance_metrics(self.db, "UNKNOWN_METRIC")

        self.assertIsNone(result)


class TestCollectPurchaseMetrics(unittest.TestCase):
    """测试采购指标采集器"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()

    def test_po_count_no_filter(self):
        """测试采购订单数量 - 无筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "PO_COUNT")

        self.assertEqual(result, Decimal(50))

    def test_po_count_with_year_filter(self):
        """测试采购订单数量 - 带年份筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 30
        self.db.query.return_value = mock_query

        filters = {"year": 2024}
        result = collect_purchase_metrics(self.db, "PO_COUNT", filters)

        self.assertEqual(result, Decimal(30))

    def test_po_count_with_status_filter(self):
        """测试采购订单数量 - 带状态筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        self.db.query.return_value = mock_query

        filters = {"status": "DELIVERED"}
        result = collect_purchase_metrics(self.db, "PO_COUNT", filters)

        self.assertEqual(result, Decimal(15))

    def test_po_total_amount(self):
        """测试采购总金额"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = 2500000
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "PO_TOTAL_AMOUNT")

        self.assertEqual(result, Decimal("2500000"))

    def test_po_total_amount_null(self):
        """测试采购总金额 - 空值"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = None
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "PO_TOTAL_AMOUNT")

        self.assertEqual(result, Decimal("0"))

    def test_po_on_time_rate_with_delivered_orders(self):
        """测试按时到货率 - 有已到货订单"""
        # 创建mock订单对象
        mock_po1 = MagicMock()
        mock_po1.actual_delivery_date = date(2024, 1, 10)
        mock_po1.expected_delivery_date = date(2024, 1, 15)  # 按时

        mock_po2 = MagicMock()
        mock_po2.actual_delivery_date = date(2024, 1, 20)
        mock_po2.expected_delivery_date = date(2024, 1, 15)  # 延期

        mock_po3 = MagicMock()
        mock_po3.actual_delivery_date = date(2024, 1, 12)
        mock_po3.expected_delivery_date = date(2024, 1, 15)  # 按时

        mock_po4 = MagicMock()
        mock_po4.actual_delivery_date = date(2024, 1, 14)
        mock_po4.expected_delivery_date = date(2024, 1, 15)  # 按时

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_po1, mock_po2, mock_po3, mock_po4]
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "PO_ON_TIME_RATE")

        # 4个订单中3个按时，75%
        self.assertEqual(result, Decimal("75.0"))

    def test_po_on_time_rate_no_delivered_orders(self):
        """测试按时到货率 - 无已到货订单"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "PO_ON_TIME_RATE")

        self.assertEqual(result, Decimal(0))

    def test_po_on_time_rate_missing_dates(self):
        """测试按时到货率 - 缺失日期数据"""
        mock_po1 = MagicMock()
        mock_po1.actual_delivery_date = None
        mock_po1.expected_delivery_date = date(2024, 1, 15)

        mock_po2 = MagicMock()
        mock_po2.actual_delivery_date = date(2024, 1, 10)
        mock_po2.expected_delivery_date = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_po1, mock_po2]
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "PO_ON_TIME_RATE")

        # 两个订单都缺失日期，on_time = 0
        self.assertEqual(result, Decimal(0))

    def test_unknown_purchase_metric(self):
        """测试未知采购指标"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query

        result = collect_purchase_metrics(self.db, "UNKNOWN_METRIC")

        self.assertIsNone(result)


class TestCollectHRMetrics(unittest.TestCase):
    """测试人力资源指标采集器"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()

    def test_employee_count_no_filter(self):
        """测试员工总数 - 无筛选"""
        mock_query = MagicMock()
        mock_query.scalar.return_value = 100
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_COUNT")

        self.assertEqual(result, Decimal(100))

    def test_employee_count_with_department_filter(self):
        """测试员工总数 - 带部门筛选"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 25
        self.db.query.return_value = mock_query

        filters = {"department_id": 10}
        result = collect_hr_metrics(self.db, "EMPLOYEE_COUNT", filters)

        self.assertEqual(result, Decimal(25))

    def test_employee_count_null(self):
        """测试员工总数 - 空值"""
        mock_query = MagicMock()
        mock_query.scalar.return_value = None
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_COUNT")

        self.assertEqual(result, Decimal(0))

    def test_employee_active_count_no_filter(self):
        """测试在职员工数 - 无筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 85
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_ACTIVE_COUNT")

        self.assertEqual(result, Decimal(85))

    def test_employee_active_count_with_department(self):
        """测试在职员工数 - 带部门筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.scalar.return_value = 20
        self.db.query.return_value = mock_query

        filters = {"department_id": 10}
        result = collect_hr_metrics(self.db, "EMPLOYEE_ACTIVE_COUNT", filters)

        self.assertEqual(result, Decimal(20))

    def test_employee_resigned_count_no_filter(self):
        """测试离职员工数 - 无筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_RESIGNED_COUNT")

        self.assertEqual(result, Decimal(15))

    def test_employee_resigned_count_with_year(self):
        """测试离职员工数 - 带年份筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.scalar.return_value = 8
        self.db.query.return_value = mock_query

        filters = {"year": 2024}
        result = collect_hr_metrics(self.db, "EMPLOYEE_RESIGNED_COUNT", filters)

        self.assertEqual(result, Decimal(8))

    def test_employee_turnover_rate_with_employees(self):
        """测试离职率 - 有员工数据"""
        # 第一次query返回总员工数，第二次返回离职员工数
        mock_total_query = MagicMock()
        mock_total_query.scalar.return_value = 100

        mock_resigned_query = MagicMock()
        mock_resigned_query.filter.return_value = mock_resigned_query
        mock_resigned_query.scalar.return_value = 10

        self.db.query.side_effect = [mock_total_query, mock_resigned_query]

        result = collect_hr_metrics(self.db, "EMPLOYEE_TURNOVER_RATE")

        # 10 / 100 * 100 = 10.0
        self.assertEqual(result, Decimal("10.0"))

    def test_employee_turnover_rate_zero_employees(self):
        """测试离职率 - 零员工"""
        mock_query = MagicMock()
        mock_query.scalar.return_value = 0
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_TURNOVER_RATE")

        self.assertEqual(result, Decimal(0))

    def test_employee_turnover_rate_with_department(self):
        """测试离职率 - 带部门筛选"""
        mock_total_query = MagicMock()
        mock_total_query.join.return_value = mock_total_query
        mock_total_query.filter.return_value = mock_total_query
        mock_total_query.scalar.return_value = 50

        mock_resigned_query = MagicMock()
        mock_resigned_query.filter.return_value = mock_resigned_query
        mock_resigned_query.scalar.return_value = 5

        self.db.query.side_effect = [mock_total_query, mock_resigned_query]

        filters = {"department_id": 10}
        result = collect_hr_metrics(self.db, "EMPLOYEE_TURNOVER_RATE", filters)

        # 5 / 50 * 100 = 10.0
        self.assertEqual(result, Decimal("10.0"))

    def test_employee_probation_count(self):
        """测试试用期员工数"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 12
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_PROBATION_COUNT")

        self.assertEqual(result, Decimal(12))

    def test_employee_confirmation_rate_with_data(self):
        """测试转正率 - 有数据"""
        # 第一次query返回已转正数，第二次返回试用期离职数
        mock_confirmed_query = MagicMock()
        mock_confirmed_query.filter.return_value = mock_confirmed_query
        mock_confirmed_query.scalar.return_value = 18

        mock_probation_resigned_query = MagicMock()
        mock_probation_resigned_query.filter.return_value = mock_probation_resigned_query
        mock_probation_resigned_query.scalar.return_value = 2

        self.db.query.side_effect = [mock_confirmed_query, mock_probation_resigned_query]

        result = collect_hr_metrics(self.db, "EMPLOYEE_CONFIRMATION_RATE")

        # 18 / (18 + 2) * 100 = 90.0
        self.assertEqual(result, Decimal("90.0"))

    def test_employee_confirmation_rate_no_data(self):
        """测试转正率 - 无数据（默认100%）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        self.db.query.return_value = mock_query

        result = collect_hr_metrics(self.db, "EMPLOYEE_CONFIRMATION_RATE")

        self.assertEqual(result, Decimal(100))

    def test_employee_confirmation_rate_all_confirmed(self):
        """测试转正率 - 全部转正"""
        mock_confirmed_query = MagicMock()
        mock_confirmed_query.filter.return_value = mock_confirmed_query
        mock_confirmed_query.scalar.return_value = 20

        mock_probation_resigned_query = MagicMock()
        mock_probation_resigned_query.filter.return_value = mock_probation_resigned_query
        mock_probation_resigned_query.scalar.return_value = 0

        self.db.query.side_effect = [mock_confirmed_query, mock_probation_resigned_query]

        result = collect_hr_metrics(self.db, "EMPLOYEE_CONFIRMATION_RATE")

        # 20 / (20 + 0) * 100 = 100.0
        self.assertEqual(result, Decimal("100.0"))

    def test_unknown_hr_metric(self):
        """测试未知HR指标"""
        result = collect_hr_metrics(self.db, "UNKNOWN_METRIC")

        self.assertIsNone(result)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()

    def test_none_filters_parameter(self):
        """测试filters参数为None"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_COUNT", filters=None)

        self.assertEqual(result, Decimal(10))

    def test_empty_filters_dict(self):
        """测试filters参数为空字典"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_COUNT", filters={})

        self.assertEqual(result, Decimal(10))

    def test_multiple_filters(self):
        """测试多个筛选条件"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        self.db.query.return_value = mock_query

        filters = {"status": "COMPLETED", "year": 2024, "health_status": "H1"}
        result = collect_project_metrics(self.db, "PROJECT_COUNT", filters)

        self.assertEqual(result, Decimal(5))

    def test_decimal_precision(self):
        """测试Decimal精度"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [100, 33]  # 33%
        self.db.query.return_value = mock_query

        result = collect_project_metrics(self.db, "PROJECT_COMPLETION_RATE")

        # 33 / 100 * 100 = 33.0
        self.assertEqual(result, Decimal("33.0"))

    def test_aggregation_parameter_ignored(self):
        """测试aggregation参数（当前未使用）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        self.db.query.return_value = mock_query

        result = collect_project_metrics(
            self.db, "PROJECT_COUNT", aggregation="SUM"
        )

        # aggregation参数当前未使用，但不应影响结果
        self.assertEqual(result, Decimal(10))


if __name__ == "__main__":
    unittest.main()
