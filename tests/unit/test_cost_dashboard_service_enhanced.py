# -*- coding: utf-8 -*-
"""
成本仪表盘服务单元测试
测试 CostDashboardService 的所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.cost_dashboard_service import CostDashboardService


class TestCostDashboardService(unittest.TestCase):
    """CostDashboardService 单元测试"""

    def setUp(self):
        """测试前置准备"""
        self.mock_db = MagicMock()
        self.service = CostDashboardService(db=self.mock_db)

    def tearDown(self):
        """测试清理"""
        self.mock_db.reset_mock()

    # ========== get_cost_overview 测试 ==========

    def test_get_cost_overview_success(self):
        """测试获取成本总览 - 正常数据"""
        # Mock 项目总数
        self.mock_db.query.return_value.filter.return_value.count.return_value = 10

        # Mock 预算和成本统计
        mock_stats = Mock()
        mock_stats.total_budget = Decimal("1000000.00")
        mock_stats.total_actual_cost = Decimal("800000.00")
        mock_stats.total_contract_amount = Decimal("1200000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_stats

        # Mock 超支项目数
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.count.side_effect = [10, 3, 5, 2]  # 总数, 超支, 正常, 预警

        # Mock 本月成本
        mock_month_cost_project = Mock()
        mock_month_cost_project.total = Decimal("50000.00")
        mock_month_cost_financial = Mock()
        mock_month_cost_financial.total = Decimal("30000.00")
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_stats,  # 预算统计
            mock_month_cost_project,  # 本月项目成本
            mock_month_cost_financial,  # 本月财务成本
        ]

        result = self.service.get_cost_overview()

        # 验证结果
        self.assertEqual(result["total_projects"], 10)
        self.assertEqual(result["total_budget"], 1000000.00)
        self.assertEqual(result["total_actual_cost"], 800000.00)
        self.assertEqual(result["total_contract_amount"], 1200000.00)
        self.assertEqual(result["budget_execution_rate"], 80.00)
        self.assertEqual(result["cost_overrun_count"], 3)
        self.assertEqual(result["cost_normal_count"], 5)
        self.assertEqual(result["cost_alert_count"], 2)
        self.assertAlmostEqual(result["month_budget"], 83333.33, places=2)
        self.assertEqual(result["month_actual_cost"], 80000.00)

    def test_get_cost_overview_empty_data(self):
        """测试获取成本总览 - 空数据"""
        # Mock 空数据
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        mock_stats = Mock()
        mock_stats.total_budget = None
        mock_stats.total_actual_cost = None
        mock_stats.total_contract_amount = None

        mock_month_cost = Mock()
        mock_month_cost.total = None

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_stats,
            mock_month_cost,
            mock_month_cost,
        ]

        result = self.service.get_cost_overview()

        # 验证零值处理
        self.assertEqual(result["total_projects"], 0)
        self.assertEqual(result["total_budget"], 0.00)
        self.assertEqual(result["total_actual_cost"], 0.00)
        self.assertEqual(result["budget_execution_rate"], 0.00)
        self.assertEqual(result["month_actual_cost"], 0.00)

    def test_get_cost_overview_zero_budget(self):
        """测试获取成本总览 - 预算为零的情况"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5

        mock_stats = Mock()
        mock_stats.total_budget = Decimal("0")
        mock_stats.total_actual_cost = Decimal("10000.00")
        mock_stats.total_contract_amount = Decimal("20000.00")

        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("5000.00")

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_stats,
            mock_month_cost,
            mock_month_cost,
        ]

        result = self.service.get_cost_overview()

        # 验证除零保护
        self.assertEqual(result["budget_execution_rate"], 0.00)
        self.assertEqual(result["month_budget"], 0.00)

    def test_get_cost_overview_high_execution_rate(self):
        """测试获取成本总览 - 高执行率场景"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5

        mock_stats = Mock()
        mock_stats.total_budget = Decimal("1000000.00")
        mock_stats.total_actual_cost = Decimal("1200000.00")  # 超支
        mock_stats.total_contract_amount = Decimal("1500000.00")

        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("100000.00")

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_stats,
            mock_month_cost,
            mock_month_cost,
        ]

        result = self.service.get_cost_overview()

        # 验证超支情况
        self.assertEqual(result["budget_execution_rate"], 120.00)
        self.assertGreater(result["total_actual_cost"], result["total_budget"])

    # ========== get_top_projects 测试 ==========

    def test_get_top_projects_success(self):
        """测试获取TOP项目 - 正常数据"""
        # Mock 项目数据
        mock_projects = []
        for i in range(15):
            project = Mock()
            project.id = i + 1
            project.project_code = f"P{i+1:03d}"
            project.project_name = f"项目{i+1}"
            project.customer_name = f"客户{i+1}"
            project.pm_name = f"PM{i+1}"
            project.budget_amount = Decimal(str((15 - i) * 100000))  # 递减预算
            project.actual_cost = Decimal(str((15 - i) * 90000 + i * 5000))  # 不同成本
            project.contract_amount = Decimal(str((15 - i) * 120000))
            project.stage = "S3"
            project.status = "ACTIVE"
            project.health = "GOOD"
            mock_projects.append(project)

        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_projects

        result = self.service.get_top_projects(limit=5)

        # 验证返回结构
        self.assertIn("top_cost_projects", result)
        self.assertIn("top_overrun_projects", result)
        self.assertIn("top_profit_margin_projects", result)
        self.assertIn("bottom_profit_margin_projects", result)

        # 验证数量限制
        self.assertEqual(len(result["top_cost_projects"]), 5)
        
        # 验证成本排序（应该是降序）
        costs = [p["actual_cost"] for p in result["top_cost_projects"]]
        self.assertEqual(costs, sorted(costs, reverse=True))

    def test_get_top_projects_empty_data(self):
        """测试获取TOP项目 - 无项目数据"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_top_projects()

        # 验证空列表
        self.assertEqual(len(result["top_cost_projects"]), 0)
        self.assertEqual(len(result["top_overrun_projects"]), 0)

    def test_get_top_projects_less_than_limit(self):
        """测试获取TOP项目 - 项目数少于limit"""
        mock_projects = []
        for i in range(3):  # 只有3个项目
            project = Mock()
            project.id = i + 1
            project.project_code = f"P{i+1:03d}"
            project.project_name = f"项目{i+1}"
            project.customer_name = f"客户{i+1}"
            project.pm_name = f"PM{i+1}"
            project.budget_amount = Decimal("100000.00")
            project.actual_cost = Decimal(str(50000 + i * 10000))
            project.contract_amount = Decimal("120000.00")
            project.stage = "S3"
            project.status = "ACTIVE"
            project.health = "GOOD"
            mock_projects.append(project)

        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_projects

        result = self.service.get_top_projects(limit=10)

        # 返回数量应该是实际项目数
        self.assertEqual(len(result["top_cost_projects"]), 3)

    def test_get_top_projects_all_overrun(self):
        """测试获取TOP项目 - 所有项目都超支"""
        mock_projects = []
        for i in range(5):
            project = Mock()
            project.id = i + 1
            project.project_code = f"P{i+1:03d}"
            project.project_name = f"项目{i+1}"
            project.customer_name = f"客户{i+1}"
            project.pm_name = f"PM{i+1}"
            project.budget_amount = Decimal("100000.00")
            project.actual_cost = Decimal(str(100000 + (i + 1) * 10000))  # 都超支
            project.contract_amount = Decimal("120000.00")
            project.stage = "S3"
            project.status = "ACTIVE"
            project.health = "RISK"
            mock_projects.append(project)

        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_projects

        result = self.service.get_top_projects(limit=10)

        # 所有项目都应该在超支列表中
        self.assertEqual(len(result["top_overrun_projects"]), 5)
        
        # 验证超支项目按超支百分比降序排列
        overrun_pcts = [p["cost_variance_pct"] for p in result["top_overrun_projects"]]
        self.assertEqual(overrun_pcts, sorted(overrun_pcts, reverse=True))

    def test_get_top_projects_profit_calculation(self):
        """测试获取TOP项目 - 利润计算正确性"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.customer_name = "测试客户"
        project.pm_name = "测试PM"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("80000.00")
        project.contract_amount = Decimal("120000.00")
        project.stage = "S3"
        project.status = "ACTIVE"
        project.health = "GOOD"

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]

        result = self.service.get_top_projects(limit=1)

        project_data = result["top_cost_projects"][0]
        
        # 验证利润计算
        expected_profit = 120000.00 - 80000.00  # 40000
        expected_margin = (40000 / 120000) * 100  # 33.33%
        
        self.assertEqual(project_data["profit"], expected_profit)
        self.assertAlmostEqual(project_data["profit_margin"], expected_margin, places=2)

    # ========== get_cost_alerts 测试 ==========

    def test_get_cost_alerts_overrun_high(self):
        """测试成本预警 - 严重超支（>20%）"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("125000.00")  # 超支25%

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        # Mock 本月成本查询
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("10000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证高级预警
        self.assertEqual(result["total_alerts"], 1)
        self.assertEqual(result["high_alerts"], 1)
        self.assertEqual(result["alerts"][0]["alert_type"], "overrun")
        self.assertEqual(result["alerts"][0]["alert_level"], "high")
        self.assertIn("严重超支", result["alerts"][0]["message"])

    def test_get_cost_alerts_overrun_medium(self):
        """测试成本预警 - 中度超支（10%-20%）"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("115000.00")  # 超支15%

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("10000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证中级预警
        self.assertEqual(result["medium_alerts"], 1)
        self.assertEqual(result["alerts"][0]["alert_level"], "medium")

    def test_get_cost_alerts_overrun_low(self):
        """测试成本预警 - 轻微超支（<10%）"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("105000.00")  # 超支5%

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("10000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证低级预警
        self.assertEqual(result["low_alerts"], 1)
        self.assertEqual(result["alerts"][0]["alert_level"], "low")
        self.assertIn("轻微超支", result["alerts"][0]["message"])

    def test_get_cost_alerts_budget_critical_high(self):
        """测试成本预警 - 预算告急高级（>95%）"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("96000.00")  # 96%

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("8000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证预算告急高级预警
        self.assertEqual(result["high_alerts"], 1)
        self.assertEqual(result["alerts"][0]["alert_type"], "budget_critical")
        self.assertIn("即将用尽", result["alerts"][0]["message"])

    def test_get_cost_alerts_budget_critical_medium(self):
        """测试成本预警 - 预算告急中级（90%-95%）"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("92000.00")  # 92%

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("7000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证预算告急中级预警
        self.assertEqual(result["medium_alerts"], 1)
        self.assertEqual(result["alerts"][0]["alert_type"], "budget_critical")
        self.assertIn("告急", result["alerts"][0]["message"])

    def test_get_cost_alerts_no_alerts(self):
        """测试成本预警 - 无预警项目"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("50000.00")  # 50%，正常

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("4000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证无预警
        self.assertEqual(result["total_alerts"], 0)
        self.assertEqual(len(result["alerts"]), 0)

    def test_get_cost_alerts_abnormal_cost(self):
        """测试成本预警 - 成本异常波动"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("120000.00")
        project.actual_cost = Decimal("60000.00")  # 平均月成本5000

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        # 本月成本异常高
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("20000.00")  # 是平均的4倍
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证异常预警
        alerts = [a for a in result["alerts"] if a["alert_type"] == "abnormal"]
        self.assertGreater(len(alerts), 0)
        self.assertEqual(alerts[0]["alert_level"], "high")

    def test_get_cost_alerts_sorting(self):
        """测试成本预警 - 排序逻辑"""
        # 创建不同级别的预警项目
        projects = []
        for i in range(3):
            project = Mock()
            project.id = i + 1
            project.project_code = f"P{i+1:03d}"
            project.project_name = f"项目{i+1}"
            project.budget_amount = Decimal("100000.00")
            # 设置不同超支程度
            project.actual_cost = Decimal(str(100000 + (3 - i) * 10000))
            projects.append(project)

        self.mock_db.query.return_value.filter.return_value.all.return_value = projects
        
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("8000.00")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_month_cost

        result = self.service.get_cost_alerts()

        # 验证排序：高级别在前，同级别按偏差率降序
        if len(result["alerts"]) > 1:
            for i in range(len(result["alerts"]) - 1):
                current = result["alerts"][i]
                next_alert = result["alerts"][i + 1]
                level_order = {"high": 0, "medium": 1, "low": 2}
                self.assertLessEqual(
                    level_order[current["alert_level"]],
                    level_order[next_alert["alert_level"]]
                )

    # ========== get_project_cost_dashboard 测试 ==========

    def test_get_project_cost_dashboard_success(self):
        """测试单项目成本仪表盘 - 正常数据"""
        # Mock 项目
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("1000000.00")
        project.actual_cost = Decimal("800000.00")
        project.contract_amount = Decimal("1200000.00")

        self.mock_db.query.return_value.filter.return_value.first.return_value = project

        # Mock 成本分类数据
        cost_breakdown = [("人力", Decimal("400000")), ("材料", Decimal("300000"))]
        financial_breakdown = [("其他", Decimal("100000"))]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.group_by.return_value.all.side_effect = [
            cost_breakdown,
            financial_breakdown,
        ]

        # Mock 月度成本（12个月）
        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("50000.00")
        
        # Mock 收款数据
        mock_received = Mock()
        mock_received.total = Decimal("500000.00")
        mock_invoiced = Mock()
        mock_invoiced.total = Decimal("600000.00")

        # 设置复杂的side_effect序列
        first_calls = [project]  # 第一次：获取项目
        for _ in range(24):  # 12个月 x 2次查询
            first_calls.extend([mock_month_cost, mock_month_cost])
        first_calls.extend([mock_received, mock_invoiced])  # 收款数据
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = first_calls

        result = self.service.get_project_cost_dashboard(project_id=1)

        # 验证基本信息
        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_code"], "P001")
        self.assertEqual(result["budget_amount"], 1000000.00)
        self.assertEqual(result["actual_cost"], 800000.00)
        self.assertEqual(result["variance"], -200000.00)

        # 验证成本结构
        self.assertIn("cost_breakdown", result)
        self.assertIsInstance(result["cost_breakdown"], list)

        # 验证月度数据
        self.assertIn("monthly_costs", result)
        self.assertEqual(len(result["monthly_costs"]), 12)

        # 验证利润数据
        self.assertEqual(result["gross_profit"], 400000.00)
        self.assertAlmostEqual(result["profit_margin"], 33.33, places=2)

    def test_get_project_cost_dashboard_project_not_found(self):
        """测试单项目成本仪表盘 - 项目不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_project_cost_dashboard(project_id=999)

        self.assertIn("不存在", str(context.exception))

    def test_get_project_cost_dashboard_zero_contract(self):
        """测试单项目成本仪表盘 - 合同额为零"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("80000.00")
        project.contract_amount = Decimal("0")  # 合同额为零

        self.mock_db.query.return_value.filter.return_value.first.return_value = project
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        mock_month_cost = Mock()
        mock_month_cost.total = None
        mock_received = Mock()
        mock_received.total = None
        mock_invoiced = Mock()
        mock_invoiced.total = None

        first_calls = [project]
        for _ in range(24):
            first_calls.extend([mock_month_cost, mock_month_cost])
        first_calls.extend([mock_received, mock_invoiced])
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = first_calls

        result = self.service.get_project_cost_dashboard(project_id=1)

        # 验证除零保护
        self.assertEqual(result["profit_margin"], 0.00)

    def test_get_project_cost_dashboard_empty_cost_breakdown(self):
        """测试单项目成本仪表盘 - 无成本分类数据"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("0")
        project.contract_amount = Decimal("120000.00")

        self.mock_db.query.return_value.filter.return_value.first.return_value = project
        
        # 空成本分类
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        mock_month_cost = Mock()
        mock_month_cost.total = None

        first_calls = [project]
        for _ in range(24):
            first_calls.extend([mock_month_cost, mock_month_cost])
        first_calls.extend([Mock(total=None), Mock(total=None)])
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = first_calls

        result = self.service.get_project_cost_dashboard(project_id=1)

        # 验证空成本结构
        self.assertEqual(len(result["cost_breakdown"]), 0)

    def test_get_project_cost_dashboard_cost_trend(self):
        """测试单项目成本仪表盘 - 成本趋势计算"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("1200000.00")
        project.actual_cost = Decimal("600000.00")
        project.contract_amount = Decimal("1500000.00")

        self.mock_db.query.return_value.filter.return_value.first.return_value = project
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("50000.00")

        first_calls = [project]
        for _ in range(24):
            first_calls.extend([mock_month_cost, mock_month_cost])
        first_calls.extend([Mock(total=None), Mock(total=None)])
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = first_calls

        result = self.service.get_project_cost_dashboard(project_id=1)

        # 验证成本趋势
        self.assertIn("cost_trend", result)
        self.assertEqual(len(result["cost_trend"]), 12)
        
        # 验证累计成本递增
        cumulative_costs = [t["cumulative_cost"] for t in result["cost_trend"]]
        for i in range(1, len(cumulative_costs)):
            self.assertGreaterEqual(cumulative_costs[i], cumulative_costs[i-1])

    def test_get_project_cost_dashboard_negative_profit(self):
        """测试单项目成本仪表盘 - 负利润场景"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("150000.00")  # 成本高于合同额
        project.contract_amount = Decimal("120000.00")

        self.mock_db.query.return_value.filter.return_value.first.return_value = project
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        mock_month_cost = Mock()
        mock_month_cost.total = None

        first_calls = [project]
        for _ in range(24):
            first_calls.extend([mock_month_cost, mock_month_cost])
        first_calls.extend([Mock(total=None), Mock(total=None)])
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = first_calls

        result = self.service.get_project_cost_dashboard(project_id=1)

        # 验证负利润
        self.assertEqual(result["gross_profit"], -30000.00)
        self.assertLess(result["profit_margin"], 0)

    def test_get_project_cost_dashboard_cost_type_merge(self):
        """测试单项目成本仪表盘 - 成本类型合并"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000.00")
        project.actual_cost = Decimal("80000.00")
        project.contract_amount = Decimal("120000.00")

        self.mock_db.query.return_value.filter.return_value.first.return_value = project

        # 两个数据源有相同类型
        cost_breakdown = [("人力", Decimal("30000")), ("材料", Decimal("20000"))]
        financial_breakdown = [("人力", Decimal("20000")), ("其他", Decimal("10000"))]
        
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.side_effect = [
            cost_breakdown,
            financial_breakdown,
        ]

        mock_month_cost = Mock()
        mock_month_cost.total = None

        first_calls = [project]
        for _ in range(24):
            first_calls.extend([mock_month_cost, mock_month_cost])
        first_calls.extend([Mock(total=None), Mock(total=None)])
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = first_calls

        result = self.service.get_project_cost_dashboard(project_id=1)

        # 验证同类型合并
        breakdown = result["cost_breakdown"]
        labor_items = [b for b in breakdown if b["category"] == "人力"]
        
        if labor_items:
            # 人力成本应该是 30000 + 20000 = 50000
            self.assertEqual(labor_items[0]["amount"], 50000.00)

    # ========== 边界条件和异常测试 ==========

    def test_service_initialization(self):
        """测试服务初始化"""
        db = MagicMock()
        service = CostDashboardService(db=db)
        self.assertEqual(service.db, db)

    def test_decimal_to_float_conversion(self):
        """测试 Decimal 到 float 的转换"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 1

        mock_stats = Mock()
        mock_stats.total_budget = Decimal("123456.789")
        mock_stats.total_actual_cost = Decimal("98765.432")
        mock_stats.total_contract_amount = Decimal("150000.00")

        mock_month_cost = Mock()
        mock_month_cost.total = Decimal("12345.67")

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_stats,
            mock_month_cost,
            mock_month_cost,
        ]

        result = self.service.get_cost_overview()

        # 验证转换和精度
        self.assertIsInstance(result["total_budget"], float)
        self.assertEqual(result["total_budget"], 123456.79)  # 四舍五入到2位
        self.assertEqual(result["total_actual_cost"], 98765.43)

    def test_none_values_handling(self):
        """测试 None 值处理"""
        project = Mock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = None
        project.actual_cost = None
        project.contract_amount = None

        self.mock_db.query.return_value.filter.return_value.all.return_value = [project]

        result = self.service.get_top_projects()

        # 验证 None 被转换为 0
        if result["top_cost_projects"]:
            project_data = result["top_cost_projects"][0]
            self.assertEqual(project_data["budget_amount"], 0.00)
            self.assertEqual(project_data["actual_cost"], 0.00)


if __name__ == "__main__":
    unittest.main()
