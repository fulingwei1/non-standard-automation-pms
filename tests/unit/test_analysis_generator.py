# -*- coding: utf-8 -*-
"""
分析报表生成器单元测试

目标：
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from app.services.report_framework.generators.analysis import AnalysisReportGenerator


class TestAnalysisReportGenerator(unittest.TestCase):
    """测试分析报表生成器"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        
    # ========== generate_workload_analysis() 主入口测试 ==========
    
    def test_generate_workload_analysis_default_dates(self):
        """测试负荷分析（默认日期）"""
        # Mock用户数据
        mock_users = [
            MagicMock(id=1, real_name="张三", username="zhangsan", department="研发部", is_active=True),
            MagicMock(id=2, real_name="李四", username="lisi", department="研发部", is_active=True),
        ]
        
        # Mock工时数据
        mock_timesheets = [
            MagicMock(user_id=1, hours=8, work_date=date.today(), project_id=101),
            MagicMock(user_id=1, hours=8, work_date=date.today() - timedelta(days=1), project_id=101),
            MagicMock(user_id=2, hours=6, work_date=date.today(), project_id=102),
        ]
        
        # Mock query chain
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = mock_users
        query_mock.filter.return_value = filter_mock
        
        timesheet_query = MagicMock()
        timesheet_filter = MagicMock()
        timesheet_between = MagicMock()
        timesheet_between.all.return_value = mock_timesheets
        timesheet_filter.between.return_value = timesheet_between
        timesheet_query.filter.return_value = timesheet_filter
        
        def query_side_effect(model):
            from app.models.user import User
            from app.models.timesheet import Timesheet
            if model == User:
                return query_mock
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = AnalysisReportGenerator.generate_workload_analysis(self.db)
        
        # 验证
        self.assertIn("summary", result)
        self.assertIn("workload_details", result)
        self.assertIn("load_distribution", result)
        self.assertEqual(result["summary"]["scope"], "全公司")
        self.assertEqual(result["summary"]["total_users"], 2)
        
    def test_generate_workload_analysis_with_department(self):
        """测试负荷分析（指定部门）"""
        # Mock部门
        mock_dept = MagicMock(id=1, dept_name="研发部", name="研发部")
        
        # Mock用户
        mock_users = [
            MagicMock(id=1, real_name="张三", username="zhangsan", department="研发部", is_active=True),
        ]
        
        # Mock工时
        mock_timesheets = [
            MagicMock(user_id=1, hours=200, work_date=date.today(), project_id=101),
        ]
        
        # Setup query chains
        dept_query = MagicMock()
        dept_filter = MagicMock()
        dept_filter.first.return_value = mock_dept
        dept_query.filter.return_value = dept_filter
        
        user_query = MagicMock()
        user_filter = MagicMock()
        user_filter.all.return_value = mock_users
        user_query.filter.return_value = user_filter
        
        timesheet_query = MagicMock()
        timesheet_filter = MagicMock()
        timesheet_between = MagicMock()
        timesheet_between.all.return_value = mock_timesheets
        timesheet_filter.between.return_value = timesheet_between
        timesheet_query.filter.return_value = timesheet_filter
        
        def query_side_effect(model):
            from app.models.organization import Department
            from app.models.user import User
            from app.models.timesheet import Timesheet
            if model == Department:
                return dept_query
            elif model == User:
                return user_query
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = AnalysisReportGenerator.generate_workload_analysis(
            self.db, 
            department_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证
        self.assertEqual(result["summary"]["scope"], "研发部")
        self.assertEqual(result["summary"]["total_users"], 1)
        # 200小时 / 8 = 25天 > 22天阈值 = OVERLOAD
        self.assertEqual(result["load_distribution"]["OVERLOAD"], 1)
        
    def test_generate_workload_analysis_empty_users(self):
        """测试负荷分析（无用户）"""
        # Mock空用户列表
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = []
        query_mock.filter.return_value = filter_mock
        
        self.db.query.return_value = query_mock
        
        # 执行
        result = AnalysisReportGenerator.generate_workload_analysis(self.db)
        
        # 验证
        self.assertEqual(result["summary"]["total_users"], 0)
        self.assertEqual(result["summary"]["active_users"], 0)
        self.assertEqual(len(result["workload_details"]), 0)
        
    # ========== generate_cost_analysis() 主入口测试 ==========
    
    def test_generate_cost_analysis_default(self):
        """测试成本分析（默认参数）"""
        # Mock项目
        mock_projects = [
            MagicMock(id=1, project_name="项目A", budget_amount=100000, is_active=True, status="IN_PROGRESS"),
            MagicMock(id=2, project_name="项目B", budget_amount=50000, is_active=True, status="ON_HOLD"),
        ]
        
        # Mock工时
        mock_timesheets = [
            MagicMock(project_id=1, hours=100, work_date=date.today()),
            MagicMock(project_id=2, hours=50, work_date=date.today()),
        ]
        
        # Setup queries
        project_query = MagicMock()
        project_filter = MagicMock()
        project_in = MagicMock()
        project_in.all.return_value = mock_projects
        project_filter.in_.return_value = project_in
        project_query.filter.return_value = project_filter
        
        timesheet_query = MagicMock()
        timesheet_filter = MagicMock()
        timesheet_between = MagicMock()
        timesheet_between.all.return_value = mock_timesheets
        timesheet_filter.between.return_value = timesheet_between
        timesheet_query.filter.return_value = timesheet_filter
        
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            if model == Project:
                return project_query
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = AnalysisReportGenerator.generate_cost_analysis(self.db)
        
        # 验证
        self.assertIn("summary", result)
        self.assertIn("project_breakdown", result)
        self.assertEqual(result["summary"]["project_count"], 2)
        self.assertEqual(result["summary"]["total_budget"], 150000)
        # 项目A: 100小时 * 100元/小时 = 10000
        # 项目B: 50小时 * 100元/小时 = 5000
        self.assertEqual(result["summary"]["total_actual"], 15000)
        
    def test_generate_cost_analysis_specific_project(self):
        """测试成本分析（指定项目）"""
        # Mock单个项目
        mock_project = MagicMock(id=1, project_name="项目A", budget_amount=200000, is_active=True)
        
        # Mock工时
        mock_timesheets = [
            MagicMock(project_id=1, hours=500, work_date=date.today()),
        ]
        
        # Setup queries
        project_query = MagicMock()
        project_filter = MagicMock()
        project_filter.all.return_value = [mock_project]
        project_query.filter.return_value = project_filter
        
        timesheet_query = MagicMock()
        timesheet_filter = MagicMock()
        timesheet_between = MagicMock()
        timesheet_between.all.return_value = mock_timesheets
        timesheet_filter.between.return_value = timesheet_between
        timesheet_query.filter.return_value = timesheet_filter
        
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            if model == Project:
                return project_query
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = AnalysisReportGenerator.generate_cost_analysis(
            self.db, 
            project_id=1,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 29)
        )
        
        # 验证
        self.assertEqual(result["summary"]["project_count"], 1)
        self.assertEqual(result["summary"]["total_budget"], 200000)
        # 500小时 * 100元/小时 = 50000
        self.assertEqual(result["summary"]["total_actual"], 50000)
        
    def test_generate_cost_analysis_no_projects(self):
        """测试成本分析（无项目）"""
        # Mock空项目列表
        project_query = MagicMock()
        project_filter = MagicMock()
        project_in = MagicMock()
        project_in.all.return_value = []
        project_filter.in_.return_value = project_in
        project_query.filter.return_value = project_filter
        
        self.db.query.return_value = project_query
        
        # 执行
        result = AnalysisReportGenerator.generate_cost_analysis(self.db)
        
        # 验证
        self.assertEqual(result["summary"]["project_count"], 0)
        self.assertEqual(result["summary"]["total_budget"], 0)
        self.assertEqual(result["summary"]["total_actual"], 0)
        
    # ========== _get_user_scope() 辅助方法测试 ==========
    
    def test_get_user_scope_all_company(self):
        """测试获取全公司用户"""
        mock_users = [
            MagicMock(id=1, is_active=True),
            MagicMock(id=2, is_active=True),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = mock_users
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        users, scope_name = AnalysisReportGenerator._get_user_scope(self.db, None)
        
        # 验证
        self.assertEqual(len(users), 2)
        self.assertEqual(scope_name, "全公司")
        
    def test_get_user_scope_by_department_id(self):
        """测试按部门ID获取用户"""
        mock_dept = MagicMock(id=1, dept_name="研发部")
        mock_users = [MagicMock(id=1, department_id=1, is_active=True)]
        
        dept_query = MagicMock()
        dept_filter = MagicMock()
        dept_filter.first.return_value = mock_dept
        dept_query.filter.return_value = dept_filter
        
        user_query = MagicMock()
        user_filter = MagicMock()
        user_filter.all.return_value = mock_users
        user_query.filter.return_value = user_filter
        
        def query_side_effect(model):
            from app.models.organization import Department
            from app.models.user import User
            if model == Department:
                return dept_query
            elif model == User:
                return user_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        users, scope_name = AnalysisReportGenerator._get_user_scope(self.db, 1)
        
        # 验证
        self.assertEqual(len(users), 1)
        self.assertEqual(scope_name, "研发部")
        
    def test_get_user_scope_by_department_name(self):
        """测试按部门名称获取用户（ID查不到时的fallback）"""
        mock_dept = MagicMock(id=1, name="测试部", dept_name="测试部")
        
        dept_query = MagicMock()
        dept_filter = MagicMock()
        dept_filter.first.return_value = mock_dept
        dept_query.filter.return_value = dept_filter
        
        # 第一次查询返回空（按department_id）
        user_query_empty = MagicMock()
        user_filter_empty = MagicMock()
        user_filter_empty.all.return_value = []
        user_query_empty.filter.return_value = user_filter_empty
        
        # 第二次查询返回用户（按department名称）
        user_query_found = MagicMock()
        user_filter_found = MagicMock()
        mock_users = [MagicMock(id=1, department="测试部", is_active=True)]
        user_filter_found.all.return_value = mock_users
        user_query_found.filter.return_value = user_filter_found
        
        call_count = [0]
        def query_side_effect(model):
            from app.models.organization import Department
            from app.models.user import User
            if model == Department:
                return dept_query
            elif model == User:
                call_count[0] += 1
                if call_count[0] == 1:
                    return user_query_empty
                else:
                    return user_query_found
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        users, scope_name = AnalysisReportGenerator._get_user_scope(self.db, 1)
        
        # 验证
        self.assertEqual(len(users), 1)
        self.assertEqual(scope_name, "测试部")
        
    def test_get_user_scope_department_not_found(self):
        """测试部门不存在"""
        dept_query = MagicMock()
        dept_filter = MagicMock()
        dept_filter.first.return_value = None
        dept_query.filter.return_value = dept_filter
        self.db.query.return_value = dept_query
        
        # 执行
        users, scope_name = AnalysisReportGenerator._get_user_scope(self.db, 999)
        
        # 验证
        self.assertEqual(len(users), 0)
        self.assertEqual(scope_name, "部门")
        
    # ========== _calculate_workload() 辅助方法测试 ==========
    
    def test_calculate_workload_normal(self):
        """测试计算工作负荷（正常情况）"""
        users = [
            MagicMock(id=1, real_name="张三", username="zhangsan", department="研发部"),
            MagicMock(id=2, real_name="李四", username="lisi", department="测试部"),
        ]
        
        timesheets = [
            MagicMock(user_id=1, hours=160, project_id=101),  # 160/8=20天 HIGH
            MagicMock(user_id=1, hours=40, project_id=102),
            MagicMock(user_id=2, hours=80, project_id=103),   # 80/8=10天 LOW
        ]
        
        # 执行
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            self.db, users, timesheets
        )
        
        # 验证
        self.assertEqual(len(workload_list), 2)
        # 用户1: 200小时 = 25天 > 22 => OVERLOAD
        user1_data = next(w for w in workload_list if w["user_id"] == 1)
        self.assertEqual(user1_data["total_hours"], 200)
        self.assertEqual(user1_data["working_days"], 25)
        self.assertEqual(user1_data["project_count"], 2)
        self.assertEqual(user1_data["load_level"], "OVERLOAD")
        
        # 用户2: 80小时 = 10天 < 12 => LOW
        user2_data = next(w for w in workload_list if w["user_id"] == 2)
        self.assertEqual(user2_data["total_hours"], 80)
        self.assertEqual(user2_data["working_days"], 10)
        self.assertEqual(user2_data["load_level"], "LOW")
        
        # 负荷分布
        self.assertEqual(load_summary["OVERLOAD"], 1)
        self.assertEqual(load_summary["LOW"], 1)
        
    def test_calculate_workload_all_levels(self):
        """测试所有负荷级别"""
        users = [
            MagicMock(id=1, real_name="用户1", username="user1", department="部门1"),  # OVERLOAD
            MagicMock(id=2, real_name="用户2", username="user2", department="部门2"),  # HIGH
            MagicMock(id=3, real_name="用户3", username="user3", department="部门3"),  # MEDIUM
            MagicMock(id=4, real_name="用户4", username="user4", department="部门4"),  # LOW
        ]
        
        timesheets = [
            MagicMock(user_id=1, hours=200, project_id=1),  # 200/8=25天 OVERLOAD
            MagicMock(user_id=2, hours=160, project_id=2),  # 160/8=20天 HIGH
            MagicMock(user_id=3, hours=120, project_id=3),  # 120/8=15天 MEDIUM
            MagicMock(user_id=4, hours=80, project_id=4),   # 80/8=10天 LOW
        ]
        
        # 执行
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            self.db, users, timesheets
        )
        
        # 验证负荷分布
        self.assertEqual(load_summary["OVERLOAD"], 1)
        self.assertEqual(load_summary["HIGH"], 1)
        self.assertEqual(load_summary["MEDIUM"], 1)
        self.assertEqual(load_summary["LOW"], 1)
        
    def test_calculate_workload_no_timesheets(self):
        """测试无工时记录"""
        users = [
            MagicMock(id=1, real_name="张三", username="zhangsan", department="研发部"),
        ]
        timesheets = []
        
        # 执行
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            self.db, users, timesheets
        )
        
        # 验证
        self.assertEqual(len(workload_list), 1)
        self.assertEqual(workload_list[0]["total_hours"], 0)
        self.assertEqual(workload_list[0]["working_days"], 0)
        self.assertEqual(workload_list[0]["load_level"], "LOW")
        self.assertEqual(load_summary["LOW"], 1)
        
    def test_calculate_workload_user_without_real_name(self):
        """测试用户没有真实姓名"""
        users = [
            MagicMock(id=1, real_name=None, username="zhangsan", department="研发部"),
        ]
        timesheets = []
        
        # 执行
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            self.db, users, timesheets
        )
        
        # 验证使用username
        self.assertEqual(workload_list[0]["user_name"], "zhangsan")
        
    def test_calculate_workload_user_without_department(self):
        """测试用户没有部门属性"""
        users = [
            MagicMock(id=1, real_name="张三", username="zhangsan", spec=["department"]),
        ]
        # 删除department属性
        del users[0].department
        
        timesheets = []
        
        # 执行
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            self.db, users, timesheets
        )
        
        # 验证
        self.assertEqual(workload_list[0]["department"], "")
        
    # ========== _get_projects() 辅助方法测试 ==========
    
    def test_get_projects_all(self):
        """测试获取所有进行中项目"""
        mock_projects = [
            MagicMock(id=1, is_active=True, status="IN_PROGRESS"),
            MagicMock(id=2, is_active=True, status="ON_HOLD"),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        in_mock = MagicMock()
        in_mock.all.return_value = mock_projects
        filter_mock.in_.return_value = in_mock
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        projects = AnalysisReportGenerator._get_projects(self.db, None)
        
        # 验证
        self.assertEqual(len(projects), 2)
        
    def test_get_projects_specific(self):
        """测试获取指定项目"""
        mock_project = MagicMock(id=1, project_name="项目A")
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = [mock_project]
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        projects = AnalysisReportGenerator._get_projects(self.db, 1)
        
        # 验证
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].id, 1)
        
    # ========== _calculate_project_costs() 辅助方法测试 ==========
    
    def test_calculate_project_costs_normal(self):
        """测试计算项目成本（正常）"""
        projects = [
            MagicMock(id=1, project_name="项目A", budget_amount=100000),
            MagicMock(id=2, project_name="项目B", budget_amount=50000),
        ]
        
        timesheets_p1 = [MagicMock(hours=100)]
        timesheets_p2 = [MagicMock(hours=50)]
        
        def query_side_effect(*args):
            q = MagicMock()
            f = MagicMock()
            b = MagicMock()
            
            # 根据filter调用参数确定是哪个项目
            def filter_func(*filter_args):
                if hasattr(filter_args[0], 'right') and filter_args[0].right.value == 1:
                    b.all.return_value = timesheets_p1
                else:
                    b.all.return_value = timesheets_p2
                return b
            
            f.between.side_effect = lambda *a: b
            q.filter.side_effect = filter_func
            return q
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            self.db, projects, date(2024, 1, 1), date(2024, 1, 31)
        )
        
        # 验证
        self.assertEqual(len(summaries), 2)
        self.assertEqual(total_budget, 150000)
        self.assertEqual(total_actual, 15000)  # (100+50)*100
        
    def test_calculate_project_costs_no_budget(self):
        """测试项目无预算"""
        projects = [
            MagicMock(id=1, project_name="项目A", spec=["budget_amount"]),
        ]
        # 删除budget_amount属性
        del projects[0].budget_amount
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        between_mock = MagicMock()
        between_mock.all.return_value = []
        filter_mock.between.return_value = between_mock
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            self.db, projects, date.today(), date.today()
        )
        
        # 验证
        self.assertEqual(total_budget, 0)
        self.assertEqual(summaries[0]["budget"], 0)
        
    def test_calculate_project_costs_budget_none(self):
        """测试预算为None"""
        projects = [
            MagicMock(id=1, project_name="项目A", budget_amount=None),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        between_mock = MagicMock()
        between_mock.all.return_value = [MagicMock(hours=100)]
        filter_mock.between.return_value = between_mock
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            self.db, projects, date.today(), date.today()
        )
        
        # 验证
        self.assertEqual(total_budget, 0)
        self.assertEqual(summaries[0]["budget"], 0)
        self.assertEqual(summaries[0]["actual_cost"], 10000)  # 100*100
        
    def test_calculate_project_costs_zero_budget(self):
        """测试预算为0"""
        projects = [
            MagicMock(id=1, project_name="项目A", budget_amount=0),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        between_mock = MagicMock()
        between_mock.all.return_value = [MagicMock(hours=100)]
        filter_mock.between.return_value = between_mock
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            self.db, projects, date.today(), date.today()
        )
        
        # 验证
        self.assertEqual(summaries[0]["variance_percent"], 0)  # 预算为0时，百分比为0
        
    def test_calculate_project_costs_hours_none(self):
        """测试工时为None"""
        projects = [
            MagicMock(id=1, project_name="项目A", budget_amount=10000),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        between_mock = MagicMock()
        between_mock.all.return_value = [MagicMock(hours=None)]
        filter_mock.between.return_value = between_mock
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 执行
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            self.db, projects, date.today(), date.today()
        )
        
        # 验证
        self.assertEqual(summaries[0]["actual_cost"], 0)
        
    # ========== 边界情况和异常测试 ==========
    
    def test_workload_analysis_with_custom_dates(self):
        """测试自定义日期范围"""
        mock_users = [MagicMock(id=1, real_name="张三", username="zhangsan", department="研发部", is_active=True)]
        mock_timesheets = []
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = mock_users
        query_mock.filter.return_value = filter_mock
        
        timesheet_query = MagicMock()
        timesheet_filter = MagicMock()
        timesheet_between = MagicMock()
        timesheet_between.all.return_value = mock_timesheets
        timesheet_filter.between.return_value = timesheet_between
        timesheet_query.filter.return_value = timesheet_filter
        
        def query_side_effect(model):
            from app.models.user import User
            from app.models.timesheet import Timesheet
            if model == User:
                return query_mock
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = AnalysisReportGenerator.generate_workload_analysis(
            self.db, 
            start_date=start, 
            end_date=end
        )
        
        # 验证日期
        self.assertEqual(result["summary"]["period_start"], "2024-01-01")
        self.assertEqual(result["summary"]["period_end"], "2024-01-31")
        
    def test_workload_details_sorted_by_days(self):
        """测试工作负荷按工作天数排序"""
        users = [
            MagicMock(id=1, real_name="用户1", username="user1", department="部门1"),
            MagicMock(id=2, real_name="用户2", username="user2", department="部门2"),
            MagicMock(id=3, real_name="用户3", username="user3", department="部门3"),
        ]
        
        timesheets = [
            MagicMock(user_id=1, hours=80, project_id=1),   # 10天
            MagicMock(user_id=2, hours=160, project_id=2),  # 20天
            MagicMock(user_id=3, hours=120, project_id=3),  # 15天
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = users
        query_mock.filter.return_value = filter_mock
        
        timesheet_query = MagicMock()
        timesheet_filter = MagicMock()
        timesheet_between = MagicMock()
        timesheet_between.all.return_value = timesheets
        timesheet_filter.between.return_value = timesheet_between
        timesheet_query.filter.return_value = timesheet_filter
        
        def query_side_effect(model):
            from app.models.user import User
            from app.models.timesheet import Timesheet
            if model == User:
                return query_mock
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = AnalysisReportGenerator.generate_workload_analysis(self.db)
        
        # 验证排序（从高到低）
        details = result["workload_details"]
        self.assertEqual(details[0]["user_id"], 2)  # 20天
        self.assertEqual(details[1]["user_id"], 3)  # 15天
        self.assertEqual(details[2]["user_id"], 1)  # 10天
        
    def test_charts_structure(self):
        """测试图表结构"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = []
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock
        
        # 负荷分析图表
        result_workload = AnalysisReportGenerator.generate_workload_analysis(self.db)
        self.assertIn("charts", result_workload)
        self.assertEqual(len(result_workload["charts"]), 1)
        self.assertEqual(result_workload["charts"][0]["type"], "pie")
        self.assertEqual(result_workload["charts"][0]["title"], "负荷分布")
        
        # 成本分析图表
        result_cost = AnalysisReportGenerator.generate_cost_analysis(self.db)
        self.assertIn("charts", result_cost)
        self.assertEqual(len(result_cost["charts"]), 1)
        self.assertEqual(result_cost["charts"][0]["type"], "bar")
        self.assertEqual(result_cost["charts"][0]["title"], "预算 vs 实际成本")


if __name__ == "__main__":
    unittest.main()
