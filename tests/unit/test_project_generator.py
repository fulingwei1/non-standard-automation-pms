# -*- coding: utf-8 -*-
"""
项目报表生成器单元测试

目标:
1. 只mock外部依赖（db.query等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from app.services.report_framework.generators.project import ProjectReportGenerator


class TestProjectReportGeneratorWeekly(unittest.TestCase):
    """测试周报生成功能"""

    def setUp(self):
        """初始化测试数据"""
        self.db = MagicMock()
        self.project_id = 1
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 7)

    def test_generate_weekly_success(self):
        """测试成功生成周报"""
        # Mock项目数据
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "P001"
        mock_project.customer_name = "客户A"
        mock_project.current_stage = "S2"
        mock_project.health_status = "H1"
        mock_project.progress = 50.5

        # Mock里程碑数据
        mock_milestone1 = MagicMock()
        mock_milestone1.id = 1
        mock_milestone1.milestone_name = "设计完成"
        mock_milestone1.planned_date = date(2024, 1, 5)
        mock_milestone1.actual_date = date(2024, 1, 5)
        mock_milestone1.status = "COMPLETED"

        mock_milestone2 = MagicMock()
        mock_milestone2.id = 2
        mock_milestone2.milestone_name = "开发完成"
        mock_milestone2.planned_date = date(2024, 1, 10)
        mock_milestone2.actual_date = None
        mock_milestone2.status = "IN_PROGRESS"

        # Mock工时数据
        mock_timesheet1 = MagicMock()
        mock_timesheet1.hours = 8
        mock_timesheet1.user_id = 101

        mock_timesheet2 = MagicMock()
        mock_timesheet2.hours = 6.5
        mock_timesheet2.user_id = 102

        mock_timesheet3 = MagicMock()
        mock_timesheet3.hours = 7
        mock_timesheet3.user_id = 101

        # Mock机台数据
        mock_machine1 = MagicMock()
        mock_machine1.id = 1
        mock_machine1.machine_code = "M001"
        mock_machine1.machine_name = "机台1号"
        mock_machine1.status = "RUNNING"
        mock_machine1.progress = 30.0

        mock_machine2 = MagicMock()
        mock_machine2.id = 2
        mock_machine2.machine_code = "M002"
        mock_machine2.machine_name = "机台2号"
        mock_machine2.status = "PENDING"
        mock_machine2.progress = 0.0

        # 配置mock查询链
        # Project查询
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        # Milestone查询
        mock_milestone_query = MagicMock()
        mock_milestone_query.filter.return_value.all.return_value = [mock_milestone1, mock_milestone2]
        
        # Timesheet查询
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value.all.return_value = [
            mock_timesheet1,
            mock_timesheet2,
            mock_timesheet3,
        ]
        
        # Machine查询
        mock_machine_query = MagicMock()
        mock_machine_query.filter.return_value.all.return_value = [mock_machine1, mock_machine2]
        
        # 配置db.query根据模型类返回不同的query对象
        from app.models.project import Machine, Project, ProjectMilestone
        from app.models.timesheet import Timesheet
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == ProjectMilestone:
                return mock_milestone_query
            elif model == Timesheet:
                return mock_timesheet_query
            elif model == Machine:
                return mock_machine_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect

        # 执行
        result = ProjectReportGenerator.generate_weekly(
            self.db, self.project_id, self.start_date, self.end_date
        )

        # 验证
        self.assertIn("summary", result)
        self.assertIn("milestones", result)
        self.assertIn("timesheet", result)
        self.assertIn("machines", result)
        self.assertIn("risks", result)

        # 验证summary
        summary = result["summary"]
        self.assertEqual(summary["project_id"], 1)
        self.assertEqual(summary["project_name"], "测试项目")
        self.assertEqual(summary["project_code"], "P001")
        self.assertEqual(summary["customer_name"], "客户A")
        self.assertEqual(summary["current_stage"], "S2")
        self.assertEqual(summary["health_status"], "H1")
        self.assertEqual(summary["progress"], 50.5)

        # 验证milestones
        milestones = result["milestones"]
        self.assertEqual(milestones["summary"]["total"], 2)
        self.assertEqual(milestones["summary"]["completed"], 1)
        self.assertEqual(milestones["summary"]["in_progress"], 1)
        self.assertEqual(milestones["summary"]["delayed"], 0)

        # 验证timesheet
        timesheet = result["timesheet"]
        self.assertEqual(timesheet["total_hours"], 21.5)
        self.assertEqual(timesheet["unique_workers"], 2)
        self.assertEqual(timesheet["avg_hours_per_worker"], 10.75)

        # 验证machines
        machines = result["machines"]
        self.assertEqual(len(machines), 2)
        self.assertEqual(machines[0]["machine_code"], "M001")

    def test_generate_weekly_project_not_found(self):
        """测试项目不存在"""
        # Mock返回None
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = ProjectReportGenerator.generate_weekly(
            self.db, self.project_id, self.start_date, self.end_date
        )

        self.assertIn("error", result)
        self.assertEqual(result["error"], "项目不存在")
        self.assertEqual(result["project_id"], self.project_id)

    def test_generate_weekly_with_delayed_milestones(self):
        """测试包含延期里程碑的周报"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.progress = 30.0
        mock_project.health_status = "H2"

        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.milestone_name = "延期里程碑"
        mock_milestone.planned_date = date(2024, 1, 3)
        mock_milestone.actual_date = None
        mock_milestone.status = "DELAYED"

        # 配置mock查询链
        from app.models.project import Machine, Project, ProjectMilestone
        from app.models.timesheet import Timesheet
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        mock_milestone_query = MagicMock()
        mock_milestone_query.filter.return_value.all.return_value = [mock_milestone]
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value.all.return_value = []
        
        mock_machine_query = MagicMock()
        mock_machine_query.filter.return_value.all.return_value = []
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == ProjectMilestone:
                return mock_milestone_query
            elif model == Timesheet:
                return mock_timesheet_query
            elif model == Machine:
                return mock_machine_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect

        result = ProjectReportGenerator.generate_weekly(
            self.db, self.project_id, self.start_date, self.end_date
        )

        # 验证风险评估
        risks = result["risks"]
        self.assertGreater(len(risks), 0)
        
        # 检查健康度风险
        health_risk = next((r for r in risks if r["type"] == "健康度"), None)
        self.assertIsNotNone(health_risk)
        self.assertEqual(health_risk["level"], "MEDIUM")

        # 检查延期风险
        delay_risk = next((r for r in risks if r["type"] == "里程碑延期"), None)
        self.assertIsNotNone(delay_risk)
        self.assertEqual(delay_risk["level"], "HIGH")


class TestProjectReportGeneratorMonthly(unittest.TestCase):
    """测试月报生成功能"""

    def setUp(self):
        """初始化测试数据"""
        self.db = MagicMock()
        self.project_id = 1
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 31)

    def test_generate_monthly_success(self):
        """测试成功生成月报"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "月度项目"
        mock_project.project_code = "P002"
        mock_project.progress = 60.0
        mock_project.budget_amount = 100000.0

        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.milestone_name = "阶段一"
        mock_milestone.planned_date = date(2024, 1, 15)
        mock_milestone.status = "COMPLETED"

        mock_timesheet = MagicMock()
        mock_timesheet.hours = 8
        mock_timesheet.user_id = 101
        mock_timesheet.work_date = date(2024, 1, 5)

        # 配置mock查询链
        from app.models.project import Machine, Project, ProjectMilestone
        from app.models.timesheet import Timesheet
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        mock_milestone_query = MagicMock()
        mock_milestone_query.filter.return_value.all.return_value = [mock_milestone]
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value.all.return_value = [mock_timesheet]
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == ProjectMilestone:
                return mock_milestone_query
            elif model == Timesheet:
                return mock_timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect

        result = ProjectReportGenerator.generate_monthly(
            self.db, self.project_id, self.start_date, self.end_date
        )

        # 验证
        self.assertIn("summary", result)
        self.assertIn("milestones", result)
        self.assertIn("progress_trend", result)
        self.assertIn("cost", result)

        # 验证summary包含report_type
        self.assertEqual(result["summary"]["report_type"], "月报")

        # 验证cost
        cost = result["cost"]
        self.assertEqual(cost["planned_cost"], 100000.0)
        self.assertEqual(cost["actual_cost"], 0)

    def test_generate_monthly_project_not_found(self):
        """测试月报项目不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = ProjectReportGenerator.generate_monthly(
            self.db, self.project_id, self.start_date, self.end_date
        )

        self.assertIn("error", result)
        self.assertEqual(result["error"], "项目不存在")


class TestProjectReportGeneratorHelperMethods(unittest.TestCase):
    """测试辅助方法"""

    def setUp(self):
        """初始化测试数据"""
        self.db = MagicMock()
        self.project_id = 1

    def test_build_project_summary(self):
        """测试构建项目摘要"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "P001"
        mock_project.customer_name = "客户A"
        mock_project.current_stage = "S3"
        mock_project.health_status = "H1"
        mock_project.progress = 75.5

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        result = ProjectReportGenerator._build_project_summary(
            mock_project, start_date, end_date
        )

        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["project_code"], "P001")
        self.assertEqual(result["customer_name"], "客户A")
        self.assertEqual(result["current_stage"], "S3")
        self.assertEqual(result["health_status"], "H1")
        self.assertEqual(result["progress"], 75.5)
        self.assertEqual(result["period_start"], "2024-01-01")
        self.assertEqual(result["period_end"], "2024-01-07")

    def test_build_project_summary_missing_attributes(self):
        """测试项目缺少某些属性时的默认值"""
        # 使用spec限制mock对象只有特定属性
        mock_project = MagicMock(spec=['id', 'project_name', 'progress'])
        mock_project.id = 1
        mock_project.project_name = "简单项目"
        mock_project.progress = None

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        result = ProjectReportGenerator._build_project_summary(
            mock_project, start_date, end_date
        )

        self.assertEqual(result["project_code"], "")
        self.assertEqual(result["customer_name"], "")
        self.assertEqual(result["current_stage"], "S1")
        self.assertEqual(result["health_status"], "H1")
        self.assertEqual(result["progress"], 0.0)

    def test_get_milestone_data(self):
        """测试获取里程碑数据"""
        mock_milestone1 = MagicMock()
        mock_milestone1.id = 1
        mock_milestone1.milestone_name = "里程碑1"
        mock_milestone1.planned_date = date(2024, 1, 5)
        mock_milestone1.actual_date = date(2024, 1, 5)
        mock_milestone1.status = "COMPLETED"

        mock_milestone2 = MagicMock()
        mock_milestone2.id = 2
        mock_milestone2.milestone_name = "里程碑2"
        mock_milestone2.planned_date = date(2024, 1, 10)
        mock_milestone2.actual_date = None
        mock_milestone2.status = "DELAYED"

        mock_milestone3 = MagicMock()
        mock_milestone3.id = 3
        mock_milestone3.milestone_name = "里程碑3"
        mock_milestone3.planned_date = date(2024, 1, 15)
        mock_milestone3.actual_date = None
        mock_milestone3.status = "IN_PROGRESS"

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_milestone1,
            mock_milestone2,
            mock_milestone3,
        ]

        result = ProjectReportGenerator._get_milestone_data(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(result["summary"]["total"], 3)
        self.assertEqual(result["summary"]["completed"], 1)
        self.assertEqual(result["summary"]["delayed"], 1)
        self.assertEqual(result["summary"]["in_progress"], 1)
        self.assertEqual(len(result["details"]), 3)

    def test_get_milestone_data_empty(self):
        """测试没有里程碑的情况"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = ProjectReportGenerator._get_milestone_data(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 7)
        )

        self.assertEqual(result["summary"]["total"], 0)
        self.assertEqual(result["summary"]["completed"], 0)
        self.assertEqual(result["summary"]["delayed"], 0)
        self.assertEqual(result["summary"]["in_progress"], 0)
        self.assertEqual(len(result["details"]), 0)

    def test_get_timesheet_data(self):
        """测试获取工时数据"""
        mock_ts1 = MagicMock()
        mock_ts1.hours = 8.0
        mock_ts1.user_id = 101

        mock_ts2 = MagicMock()
        mock_ts2.hours = 7.5
        mock_ts2.user_id = 102

        mock_ts3 = MagicMock()
        mock_ts3.hours = 6.0
        mock_ts3.user_id = 101

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_ts1,
            mock_ts2,
            mock_ts3,
        ]

        result = ProjectReportGenerator._get_timesheet_data(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 7)
        )

        self.assertEqual(result["total_hours"], 21.5)
        self.assertEqual(result["unique_workers"], 2)
        self.assertEqual(result["avg_hours_per_worker"], 10.75)
        self.assertEqual(result["timesheet_count"], 3)

    def test_get_timesheet_data_empty(self):
        """测试没有工时记录"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = ProjectReportGenerator._get_timesheet_data(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 7)
        )

        self.assertEqual(result["total_hours"], 0.0)
        self.assertEqual(result["unique_workers"], 0)
        self.assertEqual(result["avg_hours_per_worker"], 0)
        self.assertEqual(result["timesheet_count"], 0)

    def test_get_timesheet_data_with_null_hours(self):
        """测试包含空工时的情况"""
        mock_ts1 = MagicMock()
        mock_ts1.hours = None
        mock_ts1.user_id = 101

        mock_ts2 = MagicMock()
        mock_ts2.hours = 8.0
        mock_ts2.user_id = 102

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_ts1,
            mock_ts2,
        ]

        result = ProjectReportGenerator._get_timesheet_data(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 7)
        )

        self.assertEqual(result["total_hours"], 8.0)
        self.assertEqual(result["unique_workers"], 2)

    def test_get_machine_data(self):
        """测试获取机台数据"""
        mock_m1 = MagicMock()
        mock_m1.id = 1
        mock_m1.machine_code = "M001"
        mock_m1.machine_name = "机台1"
        mock_m1.status = "RUNNING"
        mock_m1.progress = 50.0

        mock_m2 = MagicMock()
        mock_m2.id = 2
        mock_m2.machine_code = "M002"
        mock_m2.machine_name = "机台2"
        mock_m2.status = "PENDING"
        mock_m2.progress = 0.0

        self.db.query.return_value.filter.return_value.all.return_value = [mock_m1, mock_m2]

        result = ProjectReportGenerator._get_machine_data(self.db, self.project_id)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["machine_code"], "M001")
        self.assertEqual(result[0]["machine_name"], "机台1")
        self.assertEqual(result[0]["status"], "RUNNING")
        self.assertEqual(result[0]["progress"], 50.0)

    def test_get_machine_data_empty(self):
        """测试没有机台"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = ProjectReportGenerator._get_machine_data(self.db, self.project_id)

        self.assertEqual(len(result), 0)

    def test_get_machine_data_missing_attributes(self):
        """测试机台缺少某些属性"""
        mock_m = MagicMock()
        mock_m.id = 1
        mock_m.progress = None
        del mock_m.machine_code
        del mock_m.machine_name
        del mock_m.status

        self.db.query.return_value.filter.return_value.all.return_value = [mock_m]

        result = ProjectReportGenerator._get_machine_data(self.db, self.project_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["machine_code"], "M-1")
        self.assertEqual(result[0]["machine_name"], "机台1")
        self.assertEqual(result[0]["status"], "PENDING")
        self.assertEqual(result[0]["progress"], 0.0)

    def test_get_weekly_trend(self):
        """测试获取周度趋势"""
        # 创建mock工时数据，分布在不同周
        mock_ts1 = MagicMock()
        mock_ts1.hours = 8.0
        mock_ts1.work_date = date(2024, 1, 2)

        mock_ts2 = MagicMock()
        mock_ts2.hours = 7.0
        mock_ts2.work_date = date(2024, 1, 3)

        mock_ts3 = MagicMock()
        mock_ts3.hours = 9.0
        mock_ts3.work_date = date(2024, 1, 10)

        def query_side_effect(*args):
            mock_query = MagicMock()
            # 根据filter的日期范围返回不同数据
            filter_chain = mock_query.filter.return_value
            
            # 简单处理：第一次查询返回第一周的数据，后续返回第二周
            if not hasattr(query_side_effect, 'call_count'):
                query_side_effect.call_count = 0
            
            query_side_effect.call_count += 1
            if query_side_effect.call_count <= 2:  # 第一周
                filter_chain.all.return_value = [mock_ts1, mock_ts2]
            else:  # 第二周及之后
                filter_chain.all.return_value = [mock_ts3]
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = ProjectReportGenerator._get_weekly_trend(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 14)
        )

        self.assertGreater(len(result), 0)
        self.assertIn("week", result[0])
        self.assertIn("start", result[0])
        self.assertIn("end", result[0])
        self.assertIn("hours", result[0])

    def test_get_weekly_trend_single_day(self):
        """测试单天的周度趋势"""
        mock_ts = MagicMock()
        mock_ts.hours = 8.0

        self.db.query.return_value.filter.return_value.all.return_value = [mock_ts]

        result = ProjectReportGenerator._get_weekly_trend(
            self.db, self.project_id, date(2024, 1, 1), date(2024, 1, 1)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["week"], 1)
        self.assertEqual(result[0]["hours"], 8.0)

    def test_get_cost_summary(self):
        """测试获取成本概况"""
        mock_project = MagicMock()
        mock_project.budget_amount = 150000.0

        result = ProjectReportGenerator._get_cost_summary(mock_project)

        self.assertEqual(result["planned_cost"], 150000.0)
        self.assertEqual(result["actual_cost"], 0)
        self.assertEqual(result["cost_variance"], 0)
        self.assertEqual(result["cost_variance_percent"], 0)

    def test_get_cost_summary_no_budget(self):
        """测试没有预算金额"""
        mock_project = MagicMock()
        mock_project.budget_amount = None

        result = ProjectReportGenerator._get_cost_summary(mock_project)

        self.assertEqual(result["planned_cost"], 0)

    def test_get_cost_summary_missing_attribute(self):
        """测试缺少budget_amount属性"""
        mock_project = MagicMock(spec=[])  # 空spec，没有任何属性

        result = ProjectReportGenerator._get_cost_summary(mock_project)

        self.assertEqual(result["planned_cost"], 0)

    def test_assess_risks_healthy(self):
        """测试无风险的情况"""
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 0}}

        result = ProjectReportGenerator._assess_risks(summary, milestones)

        self.assertEqual(len(result), 0)

    def test_assess_risks_medium_health(self):
        """测试中等健康度风险"""
        summary = {"health_status": "H2"}
        milestones = {"summary": {"delayed": 0}}

        result = ProjectReportGenerator._assess_risks(summary, milestones)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "健康度")
        self.assertEqual(result[0]["level"], "MEDIUM")
        self.assertIn("H2", result[0]["description"])

    def test_assess_risks_high_health(self):
        """测试高健康度风险"""
        summary = {"health_status": "H3"}
        milestones = {"summary": {"delayed": 0}}

        result = ProjectReportGenerator._assess_risks(summary, milestones)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "健康度")
        self.assertEqual(result[0]["level"], "HIGH")
        self.assertIn("H3", result[0]["description"])

    def test_assess_risks_delayed_milestones(self):
        """测试里程碑延期风险"""
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 3}}

        result = ProjectReportGenerator._assess_risks(summary, milestones)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "里程碑延期")
        self.assertEqual(result[0]["level"], "HIGH")
        self.assertIn("3", result[0]["description"])

    def test_assess_risks_multiple(self):
        """测试多重风险"""
        summary = {"health_status": "H3"}
        milestones = {"summary": {"delayed": 2}}

        result = ProjectReportGenerator._assess_risks(summary, milestones)

        self.assertEqual(len(result), 2)
        risk_types = [r["type"] for r in result]
        self.assertIn("健康度", risk_types)
        self.assertIn("里程碑延期", risk_types)


class TestProjectReportGeneratorEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """初始化测试数据"""
        self.db = MagicMock()

    def test_milestone_with_missing_dates(self):
        """测试里程碑缺少日期字段"""
        mock_milestone = MagicMock(spec=['id', 'status'])
        mock_milestone.id = 1
        mock_milestone.status = "PENDING"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_milestone]

        result = ProjectReportGenerator._get_milestone_data(
            self.db, 1, date(2024, 1, 1), date(2024, 1, 7)
        )

        self.assertEqual(len(result["details"]), 1)
        self.assertIsNone(result["details"][0]["planned_date"])
        self.assertIsNone(result["details"][0]["actual_date"])

    def test_milestone_with_missing_name(self):
        """测试里程碑缺少名称"""
        mock_milestone = MagicMock(spec=['id', 'planned_date', 'status'])
        mock_milestone.id = 5
        mock_milestone.planned_date = date(2024, 1, 5)
        mock_milestone.status = "COMPLETED"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_milestone]

        result = ProjectReportGenerator._get_milestone_data(
            self.db, 1, date(2024, 1, 1), date(2024, 1, 7)
        )

        self.assertEqual(result["details"][0]["name"], "里程碑5")

    def test_milestone_unknown_status(self):
        """测试里程碑未知状态"""
        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.planned_date = date(2024, 1, 5)
        mock_milestone.status = "UNKNOWN_STATUS"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_milestone]

        result = ProjectReportGenerator._get_milestone_data(
            self.db, 1, date(2024, 1, 1), date(2024, 1, 7)
        )

        # 未知状态不应该计入completed/delayed/in_progress
        self.assertEqual(result["summary"]["completed"], 0)
        self.assertEqual(result["summary"]["delayed"], 0)
        self.assertEqual(result["summary"]["in_progress"], 0)


if __name__ == "__main__":
    unittest.main()
