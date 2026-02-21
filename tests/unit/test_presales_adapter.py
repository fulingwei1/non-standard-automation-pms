# -*- coding: utf-8 -*-
"""
售前分析 Dashboard 适配器单元测试

目标：
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.models.enums import LeadOutcomeEnum
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapters.presales import PresalesDashboardAdapter


class TestPresalesDashboardAdapterProperties(unittest.TestCase):
    """测试适配器基本属性"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)

    def test_module_id(self):
        """测试模块ID"""
        self.assertEqual(self.adapter.module_id, "presales")

    def test_module_name(self):
        """测试模块名称"""
        self.assertEqual(self.adapter.module_name, "售前分析")

    def test_supported_roles(self):
        """测试支持的角色列表"""
        roles = self.adapter.supported_roles
        self.assertIsInstance(roles, list)
        self.assertIn("presales", roles)
        self.assertIn("sales", roles)
        self.assertIn("admin", roles)
        self.assertEqual(len(roles), 3)


class TestPresalesDashboardAdapterGetStats(unittest.TestCase):
    """测试 get_stats() 方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)
        self.today = date.today()
        self.year_start = date(self.today.year, 1, 1)

    def _create_mock_project(self, outcome, loss_reason=None, created_at=None):
        """创建模拟项目对象"""
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = loss_reason
        project.created_at = created_at or datetime.now()
        return project

    def test_get_stats_empty_data(self):
        """测试空数据情况"""
        # Mock 数据库查询返回空列表
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        stats = self.adapter.get_stats()

        # 验证返回6个统计卡片
        self.assertEqual(len(stats), 6)
        self.assertIsInstance(stats[0], DashboardStatCard)

        # 验证空数据的统计值
        stats_dict = {card.key: card for card in stats}
        self.assertEqual(stats_dict["total_leads_ytd"].value, 0)
        self.assertEqual(stats_dict["won_leads_ytd"].value, 0)
        self.assertEqual(stats_dict["overall_win_rate"].value, "0.0%")
        self.assertEqual(stats_dict["avg_investment"].value, "0.0")
        self.assertEqual(stats_dict["waste_rate"].value, "0.0%")

    def test_get_stats_with_won_and_lost_projects(self):
        """测试有赢单和输单的情况"""
        # 创建模拟项目
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="COMPETITOR"),
        ]

        # Mock 项目查询
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects
        
        # Mock 工时查询 - 每个项目10小时
        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:  # WorkLog
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 验证统计值
        self.assertEqual(stats_dict["total_leads_ytd"].value, 4)
        self.assertEqual(stats_dict["won_leads_ytd"].value, 2)
        # 赢率 = 2 / (2 + 2) = 0.5 = 50%
        self.assertEqual(stats_dict["overall_win_rate"].value, "50.0%")
        # 平均投入 = 40小时 / 4个项目 = 10小时
        self.assertEqual(stats_dict["avg_investment"].value, "10.0")
        # 浪费率 = 20小时（2个lost项目） / 40小时 = 50%
        self.assertEqual(stats_dict["waste_rate"].value, "50.0%")

    def test_get_stats_with_abandoned_projects(self):
        """测试包含已放弃项目的情况"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
            self._create_mock_project(LeadOutcomeEnum.ABANDONED.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 验证: ABANDONED 也算浪费
        # 浪费工时 = 20小时（LOST + ABANDONED）
        # 浪费率 = 20 / 30 = 66.7%
        self.assertEqual(stats_dict["waste_rate"].value, "66.7%")

    def test_get_stats_wasted_cost_calculation(self):
        """测试浪费成本计算"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        # 失败项目投入100小时
        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 100

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 浪费成本 = 100小时 × 300元/小时 = 30000元
        wasted_cost = stats_dict["wasted_cost"].value
        self.assertIn("30,000", wasted_cost)
        self.assertIn("¥", wasted_cost)

    def test_get_stats_zero_hours_projects(self):
        """测试零工时项目的处理"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        # 工时查询返回None（没有工时记录）
        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = None

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 验证: None 应该被处理为 0
        self.assertEqual(stats_dict["avg_investment"].value, "0.0")
        self.assertEqual(stats_dict["waste_rate"].value, "0.0%")

    def test_get_stats_only_won_projects(self):
        """测试只有赢单的情况"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 验证: 100%赢率，0%浪费
        self.assertEqual(stats_dict["overall_win_rate"].value, "100.0%")
        self.assertEqual(stats_dict["waste_rate"].value, "0.0%")
        self.assertEqual(stats_dict["wasted_cost"].value, "¥0")

    def test_get_stats_card_structure(self):
        """测试统计卡片的结构完整性"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        stats = self.adapter.get_stats()

        # 验证每个卡片的必要字段
        for card in stats:
            self.assertIsNotNone(card.key)
            self.assertIsNotNone(card.label)
            self.assertIsNotNone(card.value)
            self.assertIsNotNone(card.icon)
            self.assertIsNotNone(card.color)

        # 验证特定卡片的存在
        keys = [card.key for card in stats]
        expected_keys = [
            "total_leads_ytd",
            "won_leads_ytd",
            "overall_win_rate",
            "avg_investment",
            "waste_rate",
            "wasted_cost",
        ]
        for key in expected_keys:
            self.assertIn(key, keys)


class TestPresalesDashboardAdapterGetWidgets(unittest.TestCase):
    """测试 get_widgets() 方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)
        self.today = date.today()

    def _create_mock_project(self, outcome, loss_reason=None, created_at=None):
        """创建模拟项目对象"""
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = loss_reason
        project.created_at = created_at or datetime.now()
        return project

    def test_get_widgets_empty_data(self):
        """测试空数据情况"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()

        # 验证返回2个widget
        self.assertEqual(len(widgets), 2)
        self.assertIsInstance(widgets[0], DashboardWidget)

        # 验证widget基本信息
        widget_ids = [w.widget_id for w in widgets]
        self.assertIn("loss_reasons", widget_ids)
        self.assertIn("monthly_trend", widget_ids)

    def test_get_widgets_loss_reasons_distribution(self):
        """测试失败原因分布"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="COMPETITOR"),
            self._create_mock_project(LeadOutcomeEnum.ABANDONED.value, loss_reason="TIMING"),
            self._create_mock_project(LeadOutcomeEnum.WON.value),  # 不应统计
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()

        # 找到失败原因widget
        loss_widget = next(w for w in widgets if w.widget_id == "loss_reasons")

        # 验证数据
        self.assertEqual(loss_widget.data["PRICE"], 2)
        self.assertEqual(loss_widget.data["COMPETITOR"], 1)
        self.assertEqual(loss_widget.data["TIMING"], 1)
        self.assertNotIn("WON", loss_widget.data)

    def test_get_widgets_loss_reasons_with_none(self):
        """测试失败原因为None的处理"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason=None),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        loss_widget = next(w for w in widgets if w.widget_id == "loss_reasons")

        # None 应该转为 "OTHER"
        self.assertEqual(loss_widget.data["OTHER"], 1)
        self.assertEqual(loss_widget.data["PRICE"], 1)

    def test_get_widgets_monthly_trend(self):
        """测试月度趋势统计"""
        # 创建不同月份的项目
        now = datetime.now()
        current_month = date(now.year, now.month, 1)

        projects = [
            # 当前月份
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
            # 上个月
            self._create_mock_project(
                LeadOutcomeEnum.WON.value,
                created_at=now - timedelta(days=35),
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()

        # 找到月度趋势widget
        trend_widget = next(w for w in widgets if w.widget_id == "monthly_trend")

        # 验证返回6个月的数据
        self.assertEqual(len(trend_widget.data), 6)

        # 验证数据结构
        for month_data in trend_widget.data:
            self.assertIn("month", month_data)
            self.assertIn("total", month_data)
            self.assertIn("won", month_data)
            self.assertIn("lost", month_data)
            self.assertIn("win_rate", month_data)

    def test_get_widgets_monthly_trend_win_rate_calculation(self):
        """测试月度赢率计算"""
        now = datetime.now()

        # 当前月: 2赢 1输, 赢率应该是 2/3 = 0.667
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        trend_widget = next(w for w in widgets if w.widget_id == "monthly_trend")

        # 找到当前月的数据
        current_month_key = now.strftime("%Y-%m")
        current_month_data = next(
            m for m in trend_widget.data if m["month"] == current_month_key
        )

        self.assertEqual(current_month_data["total"], 3)
        self.assertEqual(current_month_data["won"], 2)
        self.assertEqual(current_month_data["lost"], 1)
        self.assertAlmostEqual(current_month_data["win_rate"], 0.667, places=3)

    def test_get_widgets_monthly_trend_zero_projects(self):
        """测试月度趋势中零项目月份的处理"""
        # 只有一个项目在很久以前
        old_date = datetime.now() - timedelta(days=365)
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=old_date),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        trend_widget = next(w for w in widgets if w.widget_id == "monthly_trend")

        # 当前6个月应该都是空数据
        for month_data in trend_widget.data:
            if month_data["total"] == 0:
                self.assertEqual(month_data["won"], 0)
                self.assertEqual(month_data["lost"], 0)
                self.assertEqual(month_data["win_rate"], 0)

    def test_get_widgets_structure(self):
        """测试Widget结构完整性"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()

        for widget in widgets:
            self.assertIsNotNone(widget.widget_id)
            self.assertIsNotNone(widget.widget_type)
            self.assertIsNotNone(widget.title)
            self.assertIsNotNone(widget.data)
            self.assertIsNotNone(widget.order)
            self.assertIsNotNone(widget.span)

        # 验证widget类型
        for widget in widgets:
            self.assertEqual(widget.widget_type, "chart")


class TestPresalesDashboardAdapterGetDetailedData(unittest.TestCase):
    """测试 get_detailed_data() 方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)

    def _create_mock_project(self, outcome, created_at=None):
        """创建模拟项目对象"""
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = None
        project.created_at = created_at or datetime.now()
        return project

    def test_get_detailed_data_structure(self):
        """测试详细数据的结构"""
        # Mock 项目查询
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = []

        # Mock 工时查询
        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 0

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()

        # 验证返回类型
        self.assertIsInstance(result, DetailedDashboardResponse)

        # 验证必要字段
        self.assertEqual(result.module, "presales")
        self.assertEqual(result.module_name, "售前分析")
        self.assertIsNotNone(result.summary)
        self.assertIsNotNone(result.details)
        self.assertIsInstance(result.generated_at, datetime)

    def test_get_detailed_data_summary_from_stats(self):
        """测试summary是从get_stats()获取的"""
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()

        # summary应该包含stats的所有key
        expected_keys = [
            "total_leads_ytd",
            "won_leads_ytd",
            "overall_win_rate",
            "avg_investment",
            "waste_rate",
            "wasted_cost",
        ]
        for key in expected_keys:
            self.assertIn(key, result.summary)

    def test_get_detailed_data_monthly_stats_12_months(self):
        """测试月度统计返回12个月的数据"""
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = []

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 0

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()

        # 验证details中的monthly_stats
        self.assertIn("monthly_stats", result.details)
        monthly_stats = result.details["monthly_stats"]

        # 应该返回12个月的数据
        self.assertEqual(len(monthly_stats), 12)

    def test_get_detailed_data_monthly_stats_structure(self):
        """测试月度统计数据结构"""
        now = datetime.now()
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()
        monthly_stats = result.details["monthly_stats"]

        # 验证每个月的数据结构
        for month_data in monthly_stats:
            self.assertIn("month", month_data)
            self.assertIn("total", month_data)
            self.assertIn("won", month_data)
            self.assertIn("lost", month_data)
            self.assertIn("win_rate", month_data)

    def test_get_detailed_data_monthly_stats_values(self):
        """测试月度统计的具体数值"""
        now = datetime.now()
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()
        monthly_stats = result.details["monthly_stats"]

        # 找到当前月份的数据
        current_month_key = now.strftime("%Y-%m")
        current_month_data = next(
            m for m in monthly_stats if m["month"] == current_month_key
        )

        self.assertEqual(current_month_data["total"], 3)
        self.assertEqual(current_month_data["won"], 2)
        self.assertEqual(current_month_data["lost"], 1)
        # 赢率 = 2 / (2 + 1) = 0.667
        self.assertAlmostEqual(current_month_data["win_rate"], 0.667, places=3)


class TestPresalesDashboardAdapterEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)

    def test_project_with_none_created_at(self):
        """测试created_at为None的项目"""
        project = Mock()
        project.id = 1
        project.outcome = LeadOutcomeEnum.WON.value
        project.loss_reason = None
        project.created_at = None  # None值

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = [project]

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        # 应该不抛出异常
        widgets = self.adapter.get_widgets()
        self.assertIsNotNone(widgets)

    def test_divide_by_zero_protection(self):
        """测试除零保护"""
        # 没有项目时，平均投入应该为0而不是异常
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 不应该抛出异常，应该返回0
        self.assertEqual(stats_dict["avg_investment"].value, "0.0")

    def test_all_pending_projects(self):
        """测试所有项目都未结案的情况"""
        project1 = Mock()
        project1.id = 1
        project1.outcome = None  # 未结案
        project1.loss_reason = None
        project1.created_at = datetime.now()

        project2 = Mock()
        project2.id = 2
        project2.outcome = ""  # 空字符串
        project2.loss_reason = None
        project2.created_at = datetime.now()

        projects = [project1, project2]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 没有赢单和输单，赢率应该为0
        self.assertEqual(stats_dict["overall_win_rate"].value, "0.0%")

    def test_large_numbers_formatting(self):
        """测试大数字格式化"""
        projects = [self._create_mock_project(LeadOutcomeEnum.LOST.value)]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        # 10000小时
        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10000

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            else:
                return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        # 浪费成本 = 10000 × 300 = 3,000,000
        wasted_cost = stats_dict["wasted_cost"].value
        # 验证包含千位分隔符
        self.assertIn(",", wasted_cost)

    def _create_mock_project(self, outcome):
        """创建模拟项目对象"""
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = None
        project.created_at = datetime.now()
        return project


if __name__ == "__main__":
    unittest.main()
