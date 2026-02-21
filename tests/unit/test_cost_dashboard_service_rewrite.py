# -*- coding: utf-8 -*-
"""
成本仪表盘服务单元测试 - 重写版本

目标：
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query等数据库操作）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta
from app.services.cost_dashboard_service import CostDashboardService


class TestCostDashboardServiceCostOverview(unittest.TestCase):
    """测试 get_cost_overview() 方法"""

    def setUp(self):
        """准备测试环境"""
        self.mock_db = MagicMock()
        self.service = CostDashboardService(self.mock_db)

    def test_get_cost_overview_basic(self):
        """测试基本的成本总览"""
        # Mock 项目数量查询
        mock_count_query = MagicMock()
        mock_count_query.filter.return_value.count.return_value = 10
        
        # Mock 预算成本统计查询
        mock_stats_query = MagicMock()
        mock_stats_result = MagicMock()
        mock_stats_result.total_budget = 1000000
        mock_stats_result.total_actual_cost = 750000
        mock_stats_result.total_contract_amount = 1200000
        mock_stats_query.filter.return_value.first.return_value = mock_stats_result
        
        # Mock 超支项目查询
        mock_overrun_query = MagicMock()
        mock_overrun_query.filter.return_value.count.return_value = 2
        
        # Mock 正常项目查询
        mock_normal_query = MagicMock()
        mock_normal_query.filter.return_value.count.return_value = 6
        
        # Mock 预警项目查询
        mock_alert_query = MagicMock()
        mock_alert_query.filter.return_value.count.return_value = 2
        
        # Mock 本月成本查询（ProjectCost）
        mock_month_cost_project = MagicMock()
        mock_month_cost_project.total = 80000
        mock_month_project_query = MagicMock()
        mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
        
        # Mock 本月成本查询（FinancialProjectCost）
        mock_month_cost_financial = MagicMock()
        mock_month_cost_financial.total = 20000
        mock_month_financial_query = MagicMock()
        mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
        
        # 设置db.query的返回值序列
        self.mock_db.query.side_effect = [
            mock_count_query,  # 项目数量
            mock_stats_query,  # 预算成本统计
            mock_overrun_query,  # 超支项目
            mock_normal_query,  # 正常项目
            mock_alert_query,  # 预警项目
            mock_month_project_query,  # 本月ProjectCost
            mock_month_financial_query,  # 本月FinancialProjectCost
        ]
        
        # 执行
        result = self.service.get_cost_overview()
        
        # 验证
        self.assertEqual(result["total_projects"], 10)
        self.assertEqual(result["total_budget"], 1000000.0)
        self.assertEqual(result["total_actual_cost"], 750000.0)
        self.assertEqual(result["total_contract_amount"], 1200000.0)
        self.assertEqual(result["budget_execution_rate"], 75.0)  # 750000/1000000*100
        self.assertEqual(result["cost_overrun_count"], 2)
        self.assertEqual(result["cost_normal_count"], 6)
        self.assertEqual(result["cost_alert_count"], 2)
        self.assertEqual(result["month_budget"], round(1000000 / 12, 2))
        self.assertEqual(result["month_actual_cost"], 100000.0)  # 80000 + 20000

    def test_get_cost_overview_zero_budget(self):
        """测试预算为0的情况"""
        # Mock 项目数量查询
        mock_count_query = MagicMock()
        mock_count_query.filter.return_value.count.return_value = 5
        
        # Mock 预算成本统计查询（预算为0）
        mock_stats_query = MagicMock()
        mock_stats_result = MagicMock()
        mock_stats_result.total_budget = 0
        mock_stats_result.total_actual_cost = 0
        mock_stats_result.total_contract_amount = 0
        mock_stats_query.filter.return_value.first.return_value = mock_stats_result
        
        # Mock 其他查询
        mock_overrun_query = MagicMock()
        mock_overrun_query.filter.return_value.count.return_value = 0
        
        mock_normal_query = MagicMock()
        mock_normal_query.filter.return_value.count.return_value = 0
        
        mock_alert_query = MagicMock()
        mock_alert_query.filter.return_value.count.return_value = 0
        
        mock_month_cost_project = MagicMock()
        mock_month_cost_project.total = None
        mock_month_project_query = MagicMock()
        mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
        
        mock_month_cost_financial = MagicMock()
        mock_month_cost_financial.total = None
        mock_month_financial_query = MagicMock()
        mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
        
        self.mock_db.query.side_effect = [
            mock_count_query,
            mock_stats_query,
            mock_overrun_query,
            mock_normal_query,
            mock_alert_query,
            mock_month_project_query,
            mock_month_financial_query,
        ]
        
        # 执行
        result = self.service.get_cost_overview()
        
        # 验证：预算为0时，执行率应为0
        self.assertEqual(result["budget_execution_rate"], 0.0)
        self.assertEqual(result["month_budget"], 0.0)
        self.assertEqual(result["month_variance_pct"], 0.0)

    def test_get_cost_overview_null_values(self):
        """测试NULL值处理"""
        mock_count_query = MagicMock()
        mock_count_query.filter.return_value.count.return_value = 3
        
        mock_stats_query = MagicMock()
        mock_stats_result = MagicMock()
        mock_stats_result.total_budget = None
        mock_stats_result.total_actual_cost = None
        mock_stats_result.total_contract_amount = None
        mock_stats_query.filter.return_value.first.return_value = mock_stats_result
        
        mock_overrun_query = MagicMock()
        mock_overrun_query.filter.return_value.count.return_value = 0
        
        mock_normal_query = MagicMock()
        mock_normal_query.filter.return_value.count.return_value = 0
        
        mock_alert_query = MagicMock()
        mock_alert_query.filter.return_value.count.return_value = 0
        
        mock_month_cost_project = MagicMock()
        mock_month_cost_project.total = None
        mock_month_project_query = MagicMock()
        mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
        
        mock_month_cost_financial = MagicMock()
        mock_month_cost_financial.total = None
        mock_month_financial_query = MagicMock()
        mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
        
        self.mock_db.query.side_effect = [
            mock_count_query,
            mock_stats_query,
            mock_overrun_query,
            mock_normal_query,
            mock_alert_query,
            mock_month_project_query,
            mock_month_financial_query,
        ]
        
        result = self.service.get_cost_overview()
        
        # NULL值应转为0
        self.assertEqual(result["total_budget"], 0.0)
        self.assertEqual(result["total_actual_cost"], 0.0)
        self.assertEqual(result["month_actual_cost"], 0.0)


class TestCostDashboardServiceTopProjects(unittest.TestCase):
    """测试 get_top_projects() 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = CostDashboardService(self.mock_db)

    def _create_mock_project(self, project_id, code, name, budget, actual, contract):
        """创建mock项目对象"""
        project = MagicMock()
        project.id = project_id
        project.project_code = code
        project.project_name = name
        project.customer_name = "客户A"
        project.pm_name = "PM张三"
        project.budget_amount = budget
        project.actual_cost = actual
        project.contract_amount = contract
        project.stage = "S3"
        project.status = "ACTIVE"
        project.health = "GREEN"
        return project

    def test_get_top_projects_basic(self):
        """测试基本的TOP项目统计"""
        # 创建mock项目数据
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 120000, 150000),  # 超支20%
            self._create_mock_project(2, "P002", "项目B", 200000, 180000, 250000),  # 正常，高利润率
            self._create_mock_project(3, "P003", "项目C", 150000, 140000, 160000),  # 正常，低利润率
            self._create_mock_project(4, "P004", "项目D", 80000, 95000, 100000),   # 超支18.75%
            self._create_mock_project(5, "P005", "项目E", 120000, 110000, 140000),  # 正常
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query
        
        # 执行
        result = self.service.get_top_projects(limit=3)
        
        # 验证 top_cost_projects（按actual_cost降序）
        self.assertEqual(len(result["top_cost_projects"]), 3)
        self.assertEqual(result["top_cost_projects"][0]["project_code"], "P002")  # 180000
        self.assertEqual(result["top_cost_projects"][1]["project_code"], "P003")  # 140000
        self.assertEqual(result["top_cost_projects"][2]["project_code"], "P001")  # 120000
        
        # 验证 top_overrun_projects（超支率降序）
        self.assertEqual(len(result["top_overrun_projects"]), 2)  # 只有2个超支项目
        self.assertEqual(result["top_overrun_projects"][0]["project_code"], "P001")  # 20%超支
        self.assertEqual(result["top_overrun_projects"][1]["project_code"], "P004")  # 18.75%超支
        
        # 验证 top_profit_margin_projects（利润率降序）
        self.assertEqual(len(result["top_profit_margin_projects"]), 3)
        # P002: (250000-180000)/250000 = 28%
        # P005: (140000-110000)/140000 = 21.43%
        # P003: (160000-140000)/160000 = 12.5%
        self.assertEqual(result["top_profit_margin_projects"][0]["project_code"], "P002")
        
        # 验证利润率计算
        p002 = next(p for p in result["top_profit_margin_projects"] if p["project_code"] == "P002")
        self.assertEqual(p002["profit"], 70000.0)  # 250000-180000
        self.assertEqual(p002["profit_margin"], 28.0)

    def test_get_top_projects_empty(self):
        """测试无项目的情况"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_top_projects(limit=10)
        
        self.assertEqual(len(result["top_cost_projects"]), 0)
        self.assertEqual(len(result["top_overrun_projects"]), 0)
        self.assertEqual(len(result["top_profit_margin_projects"]), 0)
        self.assertEqual(len(result["bottom_profit_margin_projects"]), 0)

    def test_get_top_projects_custom_limit(self):
        """测试自定义limit"""
        projects = [
            self._create_mock_project(i, f"P{i:03d}", f"项目{i}", 100000, 90000, 120000)
            for i in range(1, 21)  # 20个项目
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_top_projects(limit=5)
        
        # 验证每个列表的长度都是5
        self.assertEqual(len(result["top_cost_projects"]), 5)
        self.assertEqual(len(result["top_profit_margin_projects"]), 5)
        self.assertEqual(len(result["bottom_profit_margin_projects"]), 5)

    def test_get_top_projects_zero_contract_amount(self):
        """测试合同金额为0的情况（避免除零错误）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 80000, 0),  # 合同金额为0
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_top_projects(limit=10)
        
        # 验证利润率为0（不抛异常）
        project_data = result["top_profit_margin_projects"][0]
        self.assertEqual(project_data["profit_margin"], 0.0)


class TestCostDashboardServiceCostAlerts(unittest.TestCase):
    """测试 get_cost_alerts() 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = CostDashboardService(self.mock_db)

    def _create_mock_project(self, project_id, code, name, budget, actual):
        """创建mock项目对象"""
        project = MagicMock()
        project.id = project_id
        project.project_code = code
        project.project_name = name
        project.budget_amount = budget
        project.actual_cost = actual
        project.stage = "S3"
        return project

    def test_get_cost_alerts_overrun_high(self):
        """测试严重超支预警（>20%）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 125000),  # 超支25%
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        # Mock 本月成本查询（用于异常波动检测）
        mock_month_cost = MagicMock()
        mock_month_cost.total = None
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,  # 项目查询
            mock_month_query,     # 本月成本查询
        ]
        
        result = self.service.get_cost_alerts()
        
        self.assertEqual(result["total_alerts"], 1)
        self.assertEqual(result["high_alerts"], 1)
        self.assertEqual(result["medium_alerts"], 0)
        
        alert = result["alerts"][0]
        self.assertEqual(alert["alert_type"], "overrun")
        self.assertEqual(alert["alert_level"], "high")
        self.assertIn("严重超支", alert["message"])

    def test_get_cost_alerts_overrun_medium(self):
        """测试中度超支预警（10%-20%）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 115000),  # 超支15%
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        mock_month_cost = MagicMock()
        mock_month_cost.total = None
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            mock_month_query,
        ]
        
        result = self.service.get_cost_alerts()
        
        alert = result["alerts"][0]
        self.assertEqual(alert["alert_level"], "medium")
        self.assertIn("超支", alert["message"])

    def test_get_cost_alerts_overrun_low(self):
        """测试轻微超支预警（<10%）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 105000),  # 超支5%
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        mock_month_cost = MagicMock()
        mock_month_cost.total = None
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            mock_month_query,
        ]
        
        result = self.service.get_cost_alerts()
        
        alert = result["alerts"][0]
        self.assertEqual(alert["alert_level"], "low")
        self.assertIn("轻微超支", alert["message"])

    def test_get_cost_alerts_budget_critical_high(self):
        """测试预算告急（>95%）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 97000),  # 使用97%
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        mock_month_cost = MagicMock()
        mock_month_cost.total = None
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            mock_month_query,
        ]
        
        result = self.service.get_cost_alerts()
        
        alert = result["alerts"][0]
        self.assertEqual(alert["alert_type"], "budget_critical")
        self.assertEqual(alert["alert_level"], "high")
        self.assertIn("即将用尽", alert["message"])

    def test_get_cost_alerts_budget_critical_medium(self):
        """测试预算告急（90%-95%）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 93000),  # 使用93%
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        mock_month_cost = MagicMock()
        mock_month_cost.total = None
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            mock_month_query,
        ]
        
        result = self.service.get_cost_alerts()
        
        alert = result["alerts"][0]
        self.assertEqual(alert["alert_level"], "medium")
        self.assertIn("告急", alert["message"])

    def test_get_cost_alerts_abnormal_cost_spike(self):
        """测试成本异常波动（本月成本是平均月成本的2倍以上）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 120000, 60000),  # 平均月成本=5000
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        # Mock 本月成本=12000（是平均月成本5000的2.4倍）
        mock_month_cost = MagicMock()
        mock_month_cost.total = 12000
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            mock_month_query,
        ]
        
        result = self.service.get_cost_alerts()
        
        # 应该检测到异常波动
        alert = result["alerts"][0]
        self.assertEqual(alert["alert_type"], "abnormal")
        self.assertEqual(alert["alert_level"], "high")
        self.assertIn("异常增长", alert["message"])

    def test_get_cost_alerts_no_alerts(self):
        """测试无预警情况"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 50000),  # 使用50%，正常
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        mock_month_cost = MagicMock()
        mock_month_cost.total = 4000  # 平均月成本=4167，本月成本正常
        mock_month_query = MagicMock()
        mock_month_query.filter.return_value.first.return_value = mock_month_cost
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            mock_month_query,
        ]
        
        result = self.service.get_cost_alerts()
        
        self.assertEqual(result["total_alerts"], 0)
        self.assertEqual(result["high_alerts"], 0)

    def test_get_cost_alerts_sorting(self):
        """测试预警排序（按级别和偏差率）"""
        projects = [
            self._create_mock_project(1, "P001", "项目A", 100000, 105000),  # 轻微超支5%
            self._create_mock_project(2, "P002", "项目B", 100000, 130000),  # 严重超支30%
            self._create_mock_project(3, "P003", "项目C", 100000, 115000),  # 中度超支15%
        ]
        
        mock_projects_query = MagicMock()
        mock_projects_query.filter.return_value.all.return_value = projects
        
        # Mock 本月成本查询（每个项目一次）
        mock_month_queries = []
        for _ in range(3):
            mock_month_cost = MagicMock()
            mock_month_cost.total = None
            mock_month_query = MagicMock()
            mock_month_query.filter.return_value.first.return_value = mock_month_cost
            mock_month_queries.append(mock_month_query)
        
        self.mock_db.query.side_effect = [
            mock_projects_query,
            *mock_month_queries,
        ]
        
        result = self.service.get_cost_alerts()
        
        # 验证排序：high级别优先，然后按偏差率降序
        self.assertEqual(result["alerts"][0]["project_code"], "P002")  # high, 30%
        self.assertEqual(result["alerts"][1]["project_code"], "P003")  # medium, 15%
        self.assertEqual(result["alerts"][2]["project_code"], "P001")  # low, 5%


class TestCostDashboardServiceProjectCostDashboard(unittest.TestCase):
    """测试 get_project_cost_dashboard() 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = CostDashboardService(self.mock_db)

    def _create_mock_project(self, project_id, code, name, budget, actual, contract):
        """创建mock项目对象"""
        project = MagicMock()
        project.id = project_id
        project.project_code = code
        project.project_name = name
        project.budget_amount = budget
        project.actual_cost = actual
        project.contract_amount = contract
        return project

    def test_get_project_cost_dashboard_basic(self):
        """测试基本的项目成本仪表盘"""
        project = self._create_mock_project(1, "P001", "项目A", 100000, 80000, 120000)
        
        # Mock 项目查询
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = project
        
        # Mock 成本分类（ProjectCost）
        mock_cost_breakdown_query = MagicMock()
        mock_cost_breakdown_query.filter.return_value.group_by.return_value.all.return_value = [
            ("人力成本", 50000),
            ("设备成本", 20000),
        ]
        
        # Mock 成本分类（FinancialProjectCost）
        mock_financial_breakdown_query = MagicMock()
        mock_financial_breakdown_query.filter.return_value.group_by.return_value.all.return_value = [
            ("其他成本", 10000),
        ]
        
        # Mock 月度成本查询（近12个月，每月2次查询：ProjectCost + FinancialProjectCost）
        mock_monthly_queries = []
        for i in range(12):
            # ProjectCost
            mock_month_cost_project = MagicMock()
            mock_month_cost_project.total = 6000 if i < 10 else 8000
            mock_month_project_query = MagicMock()
            mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
            mock_monthly_queries.append(mock_month_project_query)
            
            # FinancialProjectCost
            mock_month_cost_financial = MagicMock()
            mock_month_cost_financial.total = 1000 if i < 10 else 2000
            mock_month_financial_query = MagicMock()
            mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
            mock_monthly_queries.append(mock_month_financial_query)
        
        # Mock 收款查询
        mock_received_amount = MagicMock()
        mock_received_amount.total = 80000
        mock_received_query = MagicMock()
        mock_received_query.filter.return_value.first.return_value = mock_received_amount
        
        # Mock 开票查询
        mock_invoiced_amount = MagicMock()
        mock_invoiced_amount.total = 90000
        mock_invoiced_query = MagicMock()
        mock_invoiced_query.filter.return_value.first.return_value = mock_invoiced_amount
        
        self.mock_db.query.side_effect = [
            mock_project_query,  # 项目查询
            mock_cost_breakdown_query,  # ProjectCost分类
            mock_financial_breakdown_query,  # FinancialProjectCost分类
            *mock_monthly_queries,  # 月度成本查询（12个月 x 2）
            mock_received_query,  # 收款查询
            mock_invoiced_query,  # 开票查询
        ]
        
        # 执行
        result = self.service.get_project_cost_dashboard(project_id=1)
        
        # 验证基本信息
        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_code"], "P001")
        self.assertEqual(result["budget_amount"], 100000.0)
        self.assertEqual(result["actual_cost"], 80000.0)
        self.assertEqual(result["variance"], -20000.0)
        self.assertEqual(result["variance_pct"], -20.0)
        
        # 验证成本分类
        self.assertEqual(len(result["cost_breakdown"]), 3)
        total_breakdown = sum(item["amount"] for item in result["cost_breakdown"])
        self.assertEqual(total_breakdown, 80000.0)
        
        # 验证月度成本数据
        self.assertEqual(len(result["monthly_costs"]), 12)
        
        # 验证收入与利润
        self.assertEqual(result["received_amount"], 80000.0)
        self.assertEqual(result["invoiced_amount"], 90000.0)
        self.assertEqual(result["gross_profit"], 40000.0)  # 120000 - 80000
        self.assertEqual(result["profit_margin"], round(40000 / 120000 * 100, 2))

    def test_get_project_cost_dashboard_project_not_found(self):
        """测试项目不存在"""
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_project_query
        
        with self.assertRaises(ValueError) as context:
            self.service.get_project_cost_dashboard(project_id=999)
        
        self.assertIn("不存在", str(context.exception))

    def test_get_project_cost_dashboard_zero_contract_amount(self):
        """测试合同金额为0（利润率计算）"""
        project = self._create_mock_project(1, "P001", "项目A", 100000, 80000, 0)
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = project
        
        mock_cost_breakdown_query = MagicMock()
        mock_cost_breakdown_query.filter.return_value.group_by.return_value.all.return_value = []
        
        mock_financial_breakdown_query = MagicMock()
        mock_financial_breakdown_query.filter.return_value.group_by.return_value.all.return_value = []
        
        # Mock 月度成本查询
        mock_monthly_queries = []
        for _ in range(12):
            mock_month_cost_project = MagicMock()
            mock_month_cost_project.total = None
            mock_month_project_query = MagicMock()
            mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
            mock_monthly_queries.append(mock_month_project_query)
            
            mock_month_cost_financial = MagicMock()
            mock_month_cost_financial.total = None
            mock_month_financial_query = MagicMock()
            mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
            mock_monthly_queries.append(mock_month_financial_query)
        
        mock_received_amount = MagicMock()
        mock_received_amount.total = None
        mock_received_query = MagicMock()
        mock_received_query.filter.return_value.first.return_value = mock_received_amount
        
        mock_invoiced_amount = MagicMock()
        mock_invoiced_amount.total = None
        mock_invoiced_query = MagicMock()
        mock_invoiced_query.filter.return_value.first.return_value = mock_invoiced_amount
        
        self.mock_db.query.side_effect = [
            mock_project_query,
            mock_cost_breakdown_query,
            mock_financial_breakdown_query,
            *mock_monthly_queries,
            mock_received_query,
            mock_invoiced_query,
        ]
        
        result = self.service.get_project_cost_dashboard(project_id=1)
        
        # 合同金额为0时，利润率应为0
        self.assertEqual(result["profit_margin"], 0.0)

    def test_get_project_cost_dashboard_cost_trend(self):
        """测试成本趋势（累计成本）"""
        project = self._create_mock_project(1, "P001", "项目A", 120000, 90000, 150000)
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = project
        
        mock_cost_breakdown_query = MagicMock()
        mock_cost_breakdown_query.filter.return_value.group_by.return_value.all.return_value = []
        
        mock_financial_breakdown_query = MagicMock()
        mock_financial_breakdown_query.filter.return_value.group_by.return_value.all.return_value = []
        
        # Mock 月度成本查询（简化：每月固定成本）
        mock_monthly_queries = []
        for _ in range(12):
            mock_month_cost_project = MagicMock()
            mock_month_cost_project.total = 7000
            mock_month_project_query = MagicMock()
            mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
            mock_monthly_queries.append(mock_month_project_query)
            
            mock_month_cost_financial = MagicMock()
            mock_month_cost_financial.total = 500
            mock_month_financial_query = MagicMock()
            mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
            mock_monthly_queries.append(mock_month_financial_query)
        
        mock_received_amount = MagicMock()
        mock_received_amount.total = None
        mock_received_query = MagicMock()
        mock_received_query.filter.return_value.first.return_value = mock_received_amount
        
        mock_invoiced_amount = MagicMock()
        mock_invoiced_amount.total = None
        mock_invoiced_query = MagicMock()
        mock_invoiced_query.filter.return_value.first.return_value = mock_invoiced_amount
        
        self.mock_db.query.side_effect = [
            mock_project_query,
            mock_cost_breakdown_query,
            mock_financial_breakdown_query,
            *mock_monthly_queries,
            mock_received_query,
            mock_invoiced_query,
        ]
        
        result = self.service.get_project_cost_dashboard(project_id=1)
        
        # 验证成本趋势（累计）
        self.assertEqual(len(result["cost_trend"]), 12)
        # 第1个月: 累计=7500
        self.assertEqual(result["cost_trend"][0]["cumulative_cost"], 7500.0)
        # 第12个月: 累计=90000
        self.assertEqual(result["cost_trend"][11]["cumulative_cost"], 90000.0)


class TestCostDashboardServiceEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = CostDashboardService(self.mock_db)

    def test_cost_breakdown_null_cost_type(self):
        """测试成本分类为NULL的情况"""
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "项目A"
        project.budget_amount = 100000
        project.actual_cost = 80000
        project.contract_amount = 120000
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = project
        
        # Mock 成本分类（cost_type为None）
        mock_cost_breakdown_query = MagicMock()
        mock_cost_breakdown_query.filter.return_value.group_by.return_value.all.return_value = [
            (None, 50000),  # cost_type为None
            ("人力成本", 30000),
        ]
        
        mock_financial_breakdown_query = MagicMock()
        mock_financial_breakdown_query.filter.return_value.group_by.return_value.all.return_value = []
        
        # Mock 月度成本查询
        mock_monthly_queries = []
        for _ in range(12):
            mock_month_cost_project = MagicMock()
            mock_month_cost_project.total = None
            mock_month_project_query = MagicMock()
            mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
            mock_monthly_queries.append(mock_month_project_query)
            
            mock_month_cost_financial = MagicMock()
            mock_month_cost_financial.total = None
            mock_month_financial_query = MagicMock()
            mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
            mock_monthly_queries.append(mock_month_financial_query)
        
        mock_received_amount = MagicMock()
        mock_received_amount.total = None
        mock_received_query = MagicMock()
        mock_received_query.filter.return_value.first.return_value = mock_received_amount
        
        mock_invoiced_amount = MagicMock()
        mock_invoiced_amount.total = None
        mock_invoiced_query = MagicMock()
        mock_invoiced_query.filter.return_value.first.return_value = mock_invoiced_amount
        
        self.mock_db.query.side_effect = [
            mock_project_query,
            mock_cost_breakdown_query,
            mock_financial_breakdown_query,
            *mock_monthly_queries,
            mock_received_query,
            mock_invoiced_query,
        ]
        
        result = self.service.get_project_cost_dashboard(project_id=1)
        
        # 验证NULL cost_type被转为"其他"
        other_category = next(
            item for item in result["cost_breakdown"] if item["category"] == "其他"
        )
        self.assertEqual(other_category["amount"], 50000.0)

    def test_cost_breakdown_percentage_calculation(self):
        """测试成本分类百分比计算"""
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "项目A"
        project.budget_amount = 100000
        project.actual_cost = 100000
        project.contract_amount = 120000
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = project
        
        mock_cost_breakdown_query = MagicMock()
        mock_cost_breakdown_query.filter.return_value.group_by.return_value.all.return_value = [
            ("人力成本", 60000),
            ("设备成本", 40000),
        ]
        
        mock_financial_breakdown_query = MagicMock()
        mock_financial_breakdown_query.filter.return_value.group_by.return_value.all.return_value = []
        
        # Mock 月度成本查询
        mock_monthly_queries = []
        for _ in range(12):
            mock_month_cost_project = MagicMock()
            mock_month_cost_project.total = None
            mock_month_project_query = MagicMock()
            mock_month_project_query.filter.return_value.first.return_value = mock_month_cost_project
            mock_monthly_queries.append(mock_month_project_query)
            
            mock_month_cost_financial = MagicMock()
            mock_month_cost_financial.total = None
            mock_month_financial_query = MagicMock()
            mock_month_financial_query.filter.return_value.first.return_value = mock_month_cost_financial
            mock_monthly_queries.append(mock_month_financial_query)
        
        mock_received_amount = MagicMock()
        mock_received_amount.total = None
        mock_received_query = MagicMock()
        mock_received_query.filter.return_value.first.return_value = mock_received_amount
        
        mock_invoiced_amount = MagicMock()
        mock_invoiced_amount.total = None
        mock_invoiced_query = MagicMock()
        mock_invoiced_query.filter.return_value.first.return_value = mock_invoiced_amount
        
        self.mock_db.query.side_effect = [
            mock_project_query,
            mock_cost_breakdown_query,
            mock_financial_breakdown_query,
            *mock_monthly_queries,
            mock_received_query,
            mock_invoiced_query,
        ]
        
        result = self.service.get_project_cost_dashboard(project_id=1)
        
        # 验证百分比
        labor_cost = next(item for item in result["cost_breakdown"] if item["category"] == "人力成本")
        self.assertEqual(labor_cost["percentage"], 60.0)
        
        equipment_cost = next(item for item in result["cost_breakdown"] if item["category"] == "设备成本")
        self.assertEqual(equipment_cost["percentage"], 40.0)


if __name__ == "__main__":
    unittest.main()
