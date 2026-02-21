# -*- coding: utf-8 -*-
"""
部门报表生成器单元测试

策略:
1. 只mock外部依赖(db.query及其链式调用)
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock
from datetime import date, datetime
from app.services.report_framework.generators.department import DeptReportGenerator


class TestDeptReportGeneratorWeekly(unittest.TestCase):
    """测试周报生成"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.dept_id = 1
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 7)

    def _create_mock_department(self, dept_id=1, dept_name="研发部", dept_code="DEV"):
        """创建mock部门对象"""
        dept = MagicMock()
        dept.id = dept_id
        dept.dept_name = dept_name
        dept.dept_code = dept_code
        dept.name = dept_name  # 备用属性
        return dept

    def _create_mock_user(self, user_id, username, real_name, department_id=1, position="工程师"):
        """创建mock用户对象"""
        user = MagicMock()
        user.id = user_id
        user.username = username
        user.real_name = real_name
        user.department_id = department_id
        user.department = "研发部"
        user.is_active = True
        user.position = position
        return user

    def _create_mock_timesheet(self, user_id, project_id, hours, work_date):
        """创建mock工时记录"""
        ts = MagicMock()
        ts.user_id = user_id
        ts.project_id = project_id
        ts.hours = hours
        ts.work_date = work_date
        return ts

    def _create_mock_project(self, proj_id, project_name, stage="S1", health="H1"):
        """创建mock项目对象"""
        proj = MagicMock()
        proj.id = proj_id
        proj.project_name = project_name
        proj.stage = stage
        proj.health = health
        proj.is_active = True
        proj.created_at = datetime(2024, 1, 1)
        proj.updated_at = datetime(2024, 1, 5)
        return proj

    def test_generate_weekly_success(self):
        """测试周报生成成功"""
        # 准备mock数据
        mock_dept = self._create_mock_department(1, "研发部", "DEV")
        mock_users = [
            self._create_mock_user(1, "zhangsan", "张三", 1, "高级工程师"),
            self._create_mock_user(2, "lisi", "李四", 1, "工程师"),
        ]
        mock_timesheets = [
            self._create_mock_timesheet(1, 101, 8, date(2024, 1, 1)),
            self._create_mock_timesheet(1, 101, 8, date(2024, 1, 2)),
            self._create_mock_timesheet(2, 102, 6, date(2024, 1, 3)),
        ]
        
        # 设置db.query的返回值
        # 查询部门
        dept_query = MagicMock()
        dept_query.filter.return_value.first.return_value = mock_dept
        
        # 查询用户
        user_query = MagicMock()
        user_query.filter.return_value.all.return_value = mock_users
        
        # 查询工时
        timesheet_query = MagicMock()
        timesheet_query.filter.return_value.all.return_value = mock_timesheets
        
        # 查询项目（用于工时分布）
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = self._create_mock_project(101, "项目A")
        
        # 配置db.query按调用次序返回不同的query对象
        query_call_count = [0]
        def query_side_effect(model):
            query_call_count[0] += 1
            if query_call_count[0] == 1:  # 第1次：查部门
                return dept_query
            elif query_call_count[0] == 2:  # 第2次：查用户
                return user_query
            elif query_call_count[0] == 3:  # 第3次：查工时汇总
                return timesheet_query
            elif query_call_count[0] == 4:  # 第4次：查工时分布
                return timesheet_query
            elif query_call_count[0] >= 5:  # 第5+次：查项目（可能多次）
                return project_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行测试
        result = DeptReportGenerator.generate_weekly(
            self.mock_db, self.dept_id, self.start_date, self.end_date
        )
        
        # 验证结果
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["department_id"], 1)
        self.assertEqual(result["summary"]["department_name"], "研发部")
        self.assertEqual(result["summary"]["member_count"], 2)
        
        self.assertIn("members", result)
        self.assertEqual(result["members"]["total_count"], 2)
        
        self.assertIn("timesheet", result)
        self.assertEqual(result["timesheet"]["total_hours"], 22.0)  # 8+8+6
        
        self.assertIn("workload", result)
        self.assertEqual(len(result["workload"]), 2)

    def test_generate_weekly_department_not_found(self):
        """测试部门不存在"""
        # 模拟部门不存在
        dept_query = MagicMock()
        dept_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = dept_query
        
        result = DeptReportGenerator.generate_weekly(
            self.mock_db, 999, self.start_date, self.end_date
        )
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "部门不存在")
        self.assertEqual(result["department_id"], 999)

    def test_generate_weekly_no_members(self):
        """测试部门无成员"""
        mock_dept = self._create_mock_department()
        
        # 部门存在
        dept_query = MagicMock()
        dept_query.filter.return_value.first.return_value = mock_dept
        
        # 但无成员
        user_query = MagicMock()
        user_query.filter.return_value.all.return_value = []
        
        timesheet_query = MagicMock()
        timesheet_query.filter.return_value.all.return_value = []
        
        query_call_count = [0]
        def query_side_effect(model):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                return dept_query
            elif query_call_count[0] == 2:
                return user_query
            else:
                return timesheet_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator.generate_weekly(
            self.mock_db, self.dept_id, self.start_date, self.end_date
        )
        
        self.assertEqual(result["summary"]["member_count"], 0)
        self.assertEqual(result["members"]["total_count"], 0)
        self.assertEqual(result["timesheet"]["total_hours"], 0)
        self.assertEqual(len(result["workload"]), 0)


class TestDeptReportGeneratorMonthly(unittest.TestCase):
    """测试月报生成"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.dept_id = 1
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 31)

    def _create_mock_department(self, dept_id=1, dept_name="研发部", dept_code="DEV"):
        """创建mock部门对象"""
        dept = MagicMock()
        dept.id = dept_id
        dept.dept_name = dept_name
        dept.dept_code = dept_code
        return dept

    def _create_mock_user(self, user_id, username, real_name):
        """创建mock用户对象"""
        user = MagicMock()
        user.id = user_id
        user.username = username
        user.real_name = real_name
        user.department_id = 1
        user.is_active = True
        user.position = "工程师"
        return user

    def _create_mock_timesheet(self, user_id, project_id, hours, work_date):
        """创建mock工时记录"""
        ts = MagicMock()
        ts.user_id = user_id
        ts.project_id = project_id
        ts.hours = hours
        ts.work_date = work_date
        return ts

    def _create_mock_project(self, proj_id, project_name, stage="S1", health="H1"):
        """创建mock项目对象"""
        proj = MagicMock()
        proj.id = proj_id
        proj.project_name = project_name
        proj.stage = stage
        proj.health = health
        proj.is_active = True
        proj.created_at = datetime(2024, 1, 1)
        proj.updated_at = datetime(2024, 1, 15)
        return proj

    def _create_mock_project_member(self, user_id, project_id):
        """创建mock项目成员"""
        pm = MagicMock()
        pm.user_id = user_id
        pm.project_id = project_id
        return pm

    def test_generate_monthly_success(self):
        """测试月报生成成功"""
        mock_dept = self._create_mock_department(1, "研发部", "DEV")
        mock_users = [
            self._create_mock_user(1, "zhangsan", "张三"),
            self._create_mock_user(2, "lisi", "李四"),
        ]
        mock_timesheets = [
            self._create_mock_timesheet(1, 101, 40, date(2024, 1, 1)),
            self._create_mock_timesheet(2, 102, 35, date(2024, 1, 2)),
        ]
        mock_project_members = [
            self._create_mock_project_member(1, 101),
            self._create_mock_project_member(2, 102),
        ]
        mock_projects = [
            self._create_mock_project(101, "项目A", "S3", "H1"),
            self._create_mock_project(102, "项目B", "S5", "H2"),
        ]
        
        # 设置查询返回
        dept_query = MagicMock()
        dept_query.filter.return_value.first.return_value = mock_dept
        
        user_query = MagicMock()
        user_query.filter.return_value.all.return_value = mock_users
        
        pm_query = MagicMock()
        pm_query.filter.return_value.all.return_value = mock_project_members
        
        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = mock_projects
        project_query.filter.return_value.first.return_value = mock_projects[0]
        
        timesheet_query = MagicMock()
        timesheet_query.filter.return_value.all.return_value = mock_timesheets
        
        query_call_count = [0]
        def query_side_effect(model):
            query_call_count[0] += 1
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            
            if query_call_count[0] == 1:  # 部门
                return dept_query
            elif query_call_count[0] == 2:  # 用户
                return user_query
            elif query_call_count[0] == 3:  # 项目成员
                return pm_query
            elif query_call_count[0] == 4:  # 项目
                return project_query
            else:  # 工时或其他
                return timesheet_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator.generate_monthly(
            self.mock_db, self.dept_id, self.start_date, self.end_date
        )
        
        # 验证结果
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["department_id"], 1)
        self.assertEqual(result["summary"]["report_type"], "月报")
        
        self.assertIn("key_metrics", result)
        self.assertEqual(result["key_metrics"]["total_members"], 2)
        self.assertEqual(result["key_metrics"]["total_hours"], 75.0)
        self.assertEqual(result["key_metrics"]["projects_involved"], 2)
        
        self.assertIn("project_stats", result)
        self.assertEqual(result["project_stats"]["total"], 2)
        
        self.assertIn("member_workload", result)

    def test_generate_monthly_department_not_found(self):
        """测试部门不存在（月报）"""
        dept_query = MagicMock()
        dept_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = dept_query
        
        result = DeptReportGenerator.generate_monthly(
            self.mock_db, 999, self.start_date, self.end_date
        )
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "部门不存在")


class TestGetDepartmentMembers(unittest.TestCase):
    """测试获取部门成员"""

    def setUp(self):
        self.mock_db = MagicMock()

    def _create_mock_department(self, dept_id=1, dept_name="研发部"):
        """创建mock部门"""
        dept = MagicMock()
        dept.id = dept_id
        dept.dept_name = dept_name
        dept.name = dept_name
        return dept

    def _create_mock_user(self, user_id, username, department_id=1):
        """创建mock用户"""
        user = MagicMock()
        user.id = user_id
        user.username = username
        user.department_id = department_id
        user.department = "研发部"
        user.is_active = True
        return user

    def test_get_members_by_department_id(self):
        """测试通过department_id获取成员"""
        mock_dept = self._create_mock_department(1, "研发部")
        mock_users = [
            self._create_mock_user(1, "user1", 1),
            self._create_mock_user(2, "user2", 1),
        ]
        
        user_query = MagicMock()
        user_query.filter.return_value.all.return_value = mock_users
        self.mock_db.query.return_value = user_query
        
        result = DeptReportGenerator._get_department_members(self.mock_db, mock_dept)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)

    def test_get_members_fallback_to_dept_name(self):
        """测试回退到部门名称查询"""
        mock_dept = self._create_mock_department(1, "研发部")
        mock_users = [self._create_mock_user(1, "user1", 1)]
        
        # 第一次查询返回空，第二次返回结果
        user_query_empty = MagicMock()
        user_query_empty.filter.return_value.all.return_value = []
        
        user_query_with_data = MagicMock()
        user_query_with_data.filter.return_value.all.return_value = mock_users
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            if query_calls[0] == 1:
                return user_query_empty
            else:
                return user_query_with_data
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_department_members(self.mock_db, mock_dept)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_get_members_no_results(self):
        """测试无成员情况"""
        mock_dept = self._create_mock_department(1, "")
        
        user_query = MagicMock()
        user_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = user_query
        
        result = DeptReportGenerator._get_department_members(self.mock_db, mock_dept)
        
        self.assertEqual(len(result), 0)


class TestTimesheetSummary(unittest.TestCase):
    """测试工时汇总"""

    def setUp(self):
        self.mock_db = MagicMock()

    def _create_mock_timesheet(self, user_id, hours, work_date):
        """创建mock工时记录"""
        ts = MagicMock()
        ts.user_id = user_id
        ts.hours = hours
        ts.work_date = work_date
        return ts

    def test_timesheet_summary_success(self):
        """测试工时汇总成功"""
        mock_timesheets = [
            self._create_mock_timesheet(1, 8, date(2024, 1, 1)),
            self._create_mock_timesheet(1, 6.5, date(2024, 1, 2)),
            self._create_mock_timesheet(2, 7, date(2024, 1, 3)),
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        self.mock_db.query.return_value = ts_query
        
        result = DeptReportGenerator._get_timesheet_summary(
            self.mock_db, [1, 2], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(result["total_hours"], 21.5)
        self.assertEqual(result["timesheet_count"], 3)

    def test_timesheet_summary_empty_user_ids(self):
        """测试空用户列表"""
        result = DeptReportGenerator._get_timesheet_summary(
            self.mock_db, [], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(result["total_hours"], 0)
        self.assertEqual(result["timesheet_count"], 0)

    def test_timesheet_summary_no_records(self):
        """测试无工时记录"""
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = ts_query
        
        result = DeptReportGenerator._get_timesheet_summary(
            self.mock_db, [1, 2], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(result["total_hours"], 0)
        self.assertEqual(result["timesheet_count"], 0)


class TestProjectBreakdown(unittest.TestCase):
    """测试项目工时分布"""

    def setUp(self):
        self.mock_db = MagicMock()

    def _create_mock_timesheet(self, user_id, project_id, hours):
        """创建mock工时记录"""
        ts = MagicMock()
        ts.user_id = user_id
        ts.project_id = project_id
        ts.hours = hours
        ts.work_date = date(2024, 1, 1)
        return ts

    def _create_mock_project(self, proj_id, project_name):
        """创建mock项目"""
        proj = MagicMock()
        proj.id = proj_id
        proj.project_name = project_name
        return proj

    def test_project_breakdown_success(self):
        """测试项目工时分布"""
        mock_timesheets = [
            self._create_mock_timesheet(1, 101, 10),
            self._create_mock_timesheet(1, 101, 8),
            self._create_mock_timesheet(2, 102, 6),
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        
        proj_query = MagicMock()
        def get_project(proj_id):
            if proj_id == 101:
                return self._create_mock_project(101, "项目A")
            elif proj_id == 102:
                return self._create_mock_project(102, "项目B")
            return None
        
        proj_query.filter.return_value.first.side_effect = lambda: get_project(101)
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            if query_calls[0] == 1:
                return ts_query
            else:
                # 每次查项目都需要新的query对象
                pq = MagicMock()
                # 根据filter条件确定返回哪个项目
                pq.filter.return_value.first.return_value = self._create_mock_project(101, "项目A")
                return pq
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_project_breakdown(
            self.mock_db, [1, 2], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertGreater(len(result), 0)
        # 项目A应该排第一（18小时）
        self.assertEqual(result[0]["project_id"], 101)
        self.assertEqual(result[0]["hours"], 18)
        self.assertEqual(result[0]["percentage"], 75.0)  # 18/(18+6)*100

    def test_project_breakdown_with_null_project(self):
        """测试包含非项目工作"""
        mock_timesheets = [
            self._create_mock_timesheet(1, None, 5),
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        self.mock_db.query.return_value = ts_query
        
        result = DeptReportGenerator._get_project_breakdown(
            self.mock_db, [1], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["project_id"], 0)
        self.assertEqual(result[0]["project_name"], "非项目工作")

    def test_project_breakdown_empty_user_ids(self):
        """测试空用户列表"""
        result = DeptReportGenerator._get_project_breakdown(
            self.mock_db, [], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(len(result), 0)

    def test_project_breakdown_limit(self):
        """测试结果限制"""
        # 创建15个项目的工时
        mock_timesheets = [
            self._create_mock_timesheet(1, i, 10 - i*0.5)
            for i in range(1, 16)
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        
        proj_query = MagicMock()
        proj_query.filter.return_value.first.return_value = self._create_mock_project(1, "项目")
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            if query_calls[0] == 1:
                return ts_query
            else:
                return proj_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_project_breakdown(
            self.mock_db, [1], date(2024, 1, 1), date(2024, 1, 7), limit=5
        )
        
        self.assertEqual(len(result), 5)


class TestMemberWorkload(unittest.TestCase):
    """测试成员工作负荷"""

    def setUp(self):
        self.mock_db = MagicMock()

    def _create_mock_user(self, user_id, username, real_name, position="工程师"):
        """创建mock用户"""
        user = MagicMock()
        user.id = user_id
        user.username = username
        user.real_name = real_name
        user.position = position
        return user

    def _create_mock_timesheet(self, user_id, hours, work_date):
        """创建mock工时记录"""
        ts = MagicMock()
        ts.user_id = user_id
        ts.hours = hours
        ts.work_date = work_date
        return ts

    def test_member_workload_success(self):
        """测试成员负荷计算"""
        mock_users = [
            self._create_mock_user(1, "zhangsan", "张三", "高级工程师"),
            self._create_mock_user(2, "lisi", "李四", "工程师"),
        ]
        mock_timesheets = [
            self._create_mock_timesheet(1, 8, date(2024, 1, 1)),
            self._create_mock_timesheet(1, 7, date(2024, 1, 2)),
            self._create_mock_timesheet(2, 6, date(2024, 1, 1)),
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        self.mock_db.query.return_value = ts_query
        
        result = DeptReportGenerator._get_member_workload(
            self.mock_db, mock_users, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["user_id"], 1)
        self.assertEqual(result[0]["total_hours"], 15)
        self.assertEqual(result[0]["position"], "高级工程师")

    def test_member_workload_empty_members(self):
        """测试空成员列表"""
        result = DeptReportGenerator._get_member_workload(
            self.mock_db, [], date(2024, 1, 1), date(2024, 1, 7)
        )
        
        self.assertEqual(len(result), 0)

    def test_member_workload_detailed_success(self):
        """测试详细工作负荷计算"""
        mock_users = [
            self._create_mock_user(1, "zhangsan", "张三"),
        ]
        mock_timesheets = [
            self._create_mock_timesheet(1, 8, date(2024, 1, 1)),
            self._create_mock_timesheet(1, 8, date(2024, 1, 2)),
            self._create_mock_timesheet(1, 8, date(2024, 1, 3)),
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        self.mock_db.query.return_value = ts_query
        
        working_days = 20
        result = DeptReportGenerator._get_member_workload_detailed(
            self.mock_db, mock_users, date(2024, 1, 1), date(2024, 1, 31), working_days
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["total_hours"], 24)
        self.assertEqual(result[0]["expected_hours"], 160)  # 20*8
        self.assertEqual(result[0]["utilization_rate"], 15.0)  # 24/160*100
        self.assertEqual(result[0]["timesheet_days"], 3)

    def test_member_workload_detailed_sorted(self):
        """测试结果按工时排序"""
        mock_users = [
            self._create_mock_user(1, "user1", "用户1"),
            self._create_mock_user(2, "user2", "用户2"),
        ]
        mock_timesheets = [
            self._create_mock_timesheet(1, 10, date(2024, 1, 1)),
            self._create_mock_timesheet(2, 20, date(2024, 1, 1)),
        ]
        
        ts_query = MagicMock()
        ts_query.filter.return_value.all.return_value = mock_timesheets
        self.mock_db.query.return_value = ts_query
        
        result = DeptReportGenerator._get_member_workload_detailed(
            self.mock_db, mock_users, date(2024, 1, 1), date(2024, 1, 7), 5
        )
        
        # 应该按工时降序排列
        self.assertEqual(result[0]["user_id"], 2)
        self.assertEqual(result[0]["total_hours"], 20)
        self.assertEqual(result[1]["user_id"], 1)
        self.assertEqual(result[1]["total_hours"], 10)


class TestProjectStats(unittest.TestCase):
    """测试项目统计"""

    def setUp(self):
        self.mock_db = MagicMock()

    def _create_mock_project_member(self, user_id, project_id):
        """创建mock项目成员"""
        pm = MagicMock()
        pm.user_id = user_id
        pm.project_id = project_id
        return pm

    def _create_mock_project(self, proj_id, name, stage="S1", health="H1", 
                           created_at=None, updated_at=None):
        """创建mock项目"""
        proj = MagicMock()
        proj.id = proj_id
        proj.project_name = name
        proj.stage = stage
        proj.health = health
        proj.is_active = True
        proj.created_at = created_at or datetime(2023, 12, 1)
        proj.updated_at = updated_at or datetime(2024, 1, 15)
        return proj

    def test_project_stats_success(self):
        """测试项目统计成功"""
        mock_pms = [
            self._create_mock_project_member(1, 101),
            self._create_mock_project_member(1, 102),
        ]
        mock_projects = [
            self._create_mock_project(101, "项目A", "S3", "H1"),
            self._create_mock_project(102, "项目B", "S5", "H2"),
        ]
        
        pm_query = MagicMock()
        pm_query.filter.return_value.all.return_value = mock_pms
        
        proj_query = MagicMock()
        proj_query.filter.return_value.all.return_value = mock_projects
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            if query_calls[0] == 1:
                return pm_query
            else:
                return proj_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_project_stats(
            self.mock_db, [1], date(2024, 1, 1), date(2024, 1, 31)
        )
        
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["by_stage"]["S3"], 1)
        self.assertEqual(result["by_stage"]["S5"], 1)
        self.assertEqual(result["by_health"]["H1"], 1)
        self.assertEqual(result["by_health"]["H2"], 1)

    def test_project_stats_completed_this_month(self):
        """测试统计本月完成的项目"""
        mock_pms = [self._create_mock_project_member(1, 101)]
        # S9表示已完成
        mock_projects = [
            self._create_mock_project(
                101, "完成项目", "S9", "H1",
                updated_at=datetime(2024, 1, 20)
            ),
        ]
        
        pm_query = MagicMock()
        pm_query.filter.return_value.all.return_value = mock_pms
        
        proj_query = MagicMock()
        proj_query.filter.return_value.all.return_value = mock_projects
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            return pm_query if query_calls[0] == 1 else proj_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_project_stats(
            self.mock_db, [1], date(2024, 1, 1), date(2024, 1, 31)
        )
        
        self.assertEqual(result["completed_this_month"], 1)

    def test_project_stats_started_this_month(self):
        """测试统计本月新开项目"""
        mock_pms = [self._create_mock_project_member(1, 101)]
        mock_projects = [
            self._create_mock_project(
                101, "新项目", "S1", "H1",
                created_at=datetime(2024, 1, 5)
            ),
        ]
        
        pm_query = MagicMock()
        pm_query.filter.return_value.all.return_value = mock_pms
        
        proj_query = MagicMock()
        proj_query.filter.return_value.all.return_value = mock_projects
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            return pm_query if query_calls[0] == 1 else proj_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_project_stats(
            self.mock_db, [1], date(2024, 1, 1), date(2024, 1, 31)
        )
        
        self.assertEqual(result["started_this_month"], 1)

    def test_project_stats_empty_user_ids(self):
        """测试空用户列表"""
        result = DeptReportGenerator._get_project_stats(
            self.mock_db, [], date(2024, 1, 1), date(2024, 1, 31)
        )
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_stage"], {})
        self.assertEqual(result["by_health"], {})
        self.assertEqual(result["completed_this_month"], 0)
        self.assertEqual(result["started_this_month"], 0)

    def test_project_stats_no_projects(self):
        """测试无项目情况"""
        pm_query = MagicMock()
        pm_query.filter.return_value.all.return_value = []
        
        proj_query = MagicMock()
        proj_query.filter.return_value.all.return_value = []
        
        query_calls = [0]
        def query_side_effect(model):
            query_calls[0] += 1
            return pm_query if query_calls[0] == 1 else proj_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = DeptReportGenerator._get_project_stats(
            self.mock_db, [1], date(2024, 1, 1), date(2024, 1, 31)
        )
        
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main()
