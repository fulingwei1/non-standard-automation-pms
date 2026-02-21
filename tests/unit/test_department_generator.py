# -*- coding: utf-8 -*-
"""
部门报表生成器单元测试

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from app.services.report_framework.generators.department import DeptReportGenerator


class TestDeptReportGeneratorCore(unittest.TestCase):
    """测试核心生成方法"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.generator = DeptReportGenerator()

    # ========== generate_weekly() 测试 ==========

    def test_generate_weekly_department_not_found(self):
        """测试生成周报 - 部门不存在"""
        # Mock数据库查询返回None
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.generator.generate_weekly(
            self.db, 
            department_id=999,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        self.assertEqual(result["error"], "部门不存在")
        self.assertEqual(result["department_id"], 999)

    def test_generate_weekly_success_with_data(self):
        """测试生成周报 - 成功（有数据）"""
        # Mock部门
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"
        mock_dept.dept_code = "RD001"

        # Mock用户
        mock_user1 = MagicMock()
        mock_user1.id = 101
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"
        mock_user1.position = "工程师"
        mock_user1.is_active = True
        mock_user1.department_id = 1

        mock_user2 = MagicMock()
        mock_user2.id = 102
        mock_user2.real_name = "李四"
        mock_user2.username = "lisi"
        mock_user2.position = "高级工程师"
        mock_user2.is_active = True
        mock_user2.department_id = 1

        # Mock工时记录
        mock_timesheet1 = MagicMock()
        mock_timesheet1.user_id = 101
        mock_timesheet1.project_id = 1
        mock_timesheet1.hours = 8
        mock_timesheet1.work_date = date(2024, 1, 2)

        mock_timesheet2 = MagicMock()
        mock_timesheet2.user_id = 102
        mock_timesheet2.project_id = 1
        mock_timesheet2.hours = 7.5
        mock_timesheet2.work_date = date(2024, 1, 3)

        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目A"

        # 设置数据库查询mock
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "Department":
                mock_query.filter.return_value.first.return_value = mock_dept
            elif model.__name__ == "User":
                mock_query.filter.return_value.all.return_value = [mock_user1, mock_user2]
            elif model.__name__ == "Timesheet":
                mock_query.filter.return_value.all.return_value = [mock_timesheet1, mock_timesheet2]
            elif model.__name__ == "Project":
                mock_query.filter.return_value.first.return_value = mock_project
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator.generate_weekly(
            self.db,
            department_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        # 验证基础信息
        self.assertEqual(result["summary"]["department_id"], 1)
        self.assertEqual(result["summary"]["department_name"], "研发部")
        self.assertEqual(result["summary"]["department_code"], "RD001")
        self.assertEqual(result["summary"]["member_count"], 2)
        self.assertEqual(result["summary"]["period_start"], "2024-01-01")
        self.assertEqual(result["summary"]["period_end"], "2024-01-07")

        # 验证成员统计
        self.assertEqual(result["members"]["total_count"], 2)
        self.assertEqual(result["members"]["active_count"], 2)

        # 验证工时统计
        self.assertEqual(result["timesheet"]["total_hours"], 15.5)
        self.assertGreater(len(result["timesheet"]["project_breakdown"]), 0)

        # 验证人员负荷
        self.assertEqual(len(result["workload"]), 2)

    def test_generate_weekly_success_empty_members(self):
        """测试生成周报 - 成功（无成员）"""
        # Mock部门
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "新部门"
        mock_dept.dept_code = "NEW001"

        # 设置数据库查询mock
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "Department":
                mock_query.filter.return_value.first.return_value = mock_dept
            elif model.__name__ == "User":
                mock_query.filter.return_value.all.return_value = []
            elif model.__name__ == "Timesheet":
                mock_query.filter.return_value.all.return_value = []
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator.generate_weekly(
            self.db,
            department_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        # 验证空成员情况
        self.assertEqual(result["summary"]["member_count"], 0)
        self.assertEqual(result["members"]["total_count"], 0)
        self.assertEqual(result["timesheet"]["total_hours"], 0)
        self.assertEqual(len(result["workload"]), 0)

    # ========== generate_monthly() 测试 ==========

    def test_generate_monthly_department_not_found(self):
        """测试生成月报 - 部门不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.generator.generate_monthly(
            self.db,
            department_id=999,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        self.assertEqual(result["error"], "部门不存在")
        self.assertEqual(result["department_id"], 999)

    def test_generate_monthly_success_with_data(self):
        """测试生成月报 - 成功（有数据）"""
        # Mock部门
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"
        mock_dept.dept_code = "RD001"

        # Mock用户
        mock_user = MagicMock()
        mock_user.id = 101
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.position = "工程师"
        mock_user.is_active = True
        mock_user.department_id = 1

        # Mock工时记录
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 101
        mock_timesheet.project_id = 1
        mock_timesheet.hours = 8
        mock_timesheet.work_date = date(2024, 1, 2)

        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目A"
        mock_project.is_active = True
        mock_project.stage = "S3"
        mock_project.health = "H1"
        mock_project.created_at = datetime(2024, 1, 5)
        mock_project.updated_at = datetime(2024, 1, 20)

        # Mock项目成员
        mock_pm = MagicMock()
        mock_pm.project_id = 1
        mock_pm.user_id = 101

        # 设置数据库查询mock
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "Department":
                mock_query.filter.return_value.first.return_value = mock_dept
            elif model.__name__ == "User":
                mock_query.filter.return_value.all.return_value = [mock_user]
            elif model.__name__ == "Timesheet":
                mock_query.filter.return_value.all.return_value = [mock_timesheet]
            elif model.__name__ == "Project":
                mock_query.filter.return_value.first.return_value = mock_project
                mock_query.filter.return_value.all.return_value = [mock_project]
            elif model.__name__ == "ProjectMember":
                mock_query.filter.return_value.all.return_value = [mock_pm]
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator.generate_monthly(
            self.db,
            department_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        # 验证基础信息
        self.assertEqual(result["summary"]["department_id"], 1)
        self.assertEqual(result["summary"]["department_name"], "研发部")
        self.assertEqual(result["summary"]["report_type"], "月报")

        # 验证关键指标
        self.assertIn("key_metrics", result)
        self.assertEqual(result["key_metrics"]["total_members"], 1)
        self.assertGreater(result["key_metrics"]["total_hours"], 0)

        # 验证项目统计
        self.assertIn("project_stats", result)
        self.assertEqual(result["project_stats"]["total"], 1)
        
        # 验证人员工时详情
        self.assertIn("member_workload", result)
        self.assertEqual(len(result["member_workload"]), 1)

    # ========== _get_department_members() 测试 ==========

    def test_get_department_members_by_department_id(self):
        """测试通过department_id获取成员"""
        mock_dept = MagicMock()
        mock_dept.id = 1

        mock_user = MagicMock()
        mock_user.id = 101
        mock_user.is_active = True

        self.db.query.return_value.filter.return_value.all.return_value = [mock_user]

        result = self.generator._get_department_members(self.db, mock_dept)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 101)

    def test_get_department_members_by_dept_name_fallback(self):
        """测试通过部门名称获取成员（回退策略）"""
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"

        mock_user = MagicMock()
        mock_user.id = 101
        mock_user.is_active = True

        # 第一次查询返回空，第二次查询返回结果
        self.db.query.return_value.filter.return_value.all.side_effect = [[], [mock_user]]

        result = self.generator._get_department_members(self.db, mock_dept)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 101)

    def test_get_department_members_empty(self):
        """测试获取成员 - 空结果"""
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = ""

        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.generator._get_department_members(self.db, mock_dept)

        self.assertEqual(len(result), 0)

    # ========== _get_timesheet_summary() 测试 ==========

    def test_get_timesheet_summary_empty_users(self):
        """测试工时汇总 - 空用户列表"""
        result = self.generator._get_timesheet_summary(
            self.db,
            user_ids=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        self.assertEqual(result["total_hours"], 0)
        self.assertEqual(result["timesheet_count"], 0)

    def test_get_timesheet_summary_with_data(self):
        """测试工时汇总 - 有数据"""
        mock_ts1 = MagicMock()
        mock_ts1.hours = 8.0

        mock_ts2 = MagicMock()
        mock_ts2.hours = 7.5

        mock_ts3 = MagicMock()
        mock_ts3.hours = None  # 测试None值

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2, mock_ts3
        ]

        result = self.generator._get_timesheet_summary(
            self.db,
            user_ids=[101, 102],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        self.assertEqual(result["total_hours"], 15.5)
        self.assertEqual(result["timesheet_count"], 3)

    # ========== _get_project_breakdown() 测试 ==========

    def test_get_project_breakdown_empty_users(self):
        """测试项目工时分布 - 空用户列表"""
        result = self.generator._get_project_breakdown(
            self.db,
            user_ids=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        self.assertEqual(len(result), 0)

    def test_get_project_breakdown_with_data(self):
        """测试项目工时分布 - 有数据"""
        # Mock工时记录
        mock_ts1 = MagicMock()
        mock_ts1.project_id = 1
        mock_ts1.hours = 10.0

        mock_ts2 = MagicMock()
        mock_ts2.project_id = 1
        mock_ts2.hours = 5.0

        mock_ts3 = MagicMock()
        mock_ts3.project_id = 2
        mock_ts3.hours = 8.0

        mock_ts4 = MagicMock()
        mock_ts4.project_id = None  # 非项目工作
        mock_ts4.hours = 3.0

        # Mock项目
        mock_project1 = MagicMock()
        mock_project1.project_name = "项目A"

        mock_project2 = MagicMock()
        mock_project2.project_name = "项目B"

        # 设置数据库查询mock
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "Timesheet":
                mock_query.filter.return_value.all.return_value = [
                    mock_ts1, mock_ts2, mock_ts3, mock_ts4
                ]
            elif model.__name__ == "Project":
                def filter_side_effect(*args, **kwargs):
                    # 根据project_id返回不同的项目
                    filter_mock = MagicMock()
                    # 简化处理：总是返回project1
                    filter_mock.first.return_value = mock_project1
                    return filter_mock
                
                mock_query.filter.side_effect = filter_side_effect
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator._get_project_breakdown(
            self.db,
            user_ids=[101],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            limit=10,
        )

        # 验证结果
        self.assertGreater(len(result), 0)
        
        # 验证项目1（工时最多）
        project1_data = next((p for p in result if p["project_id"] == 1), None)
        self.assertIsNotNone(project1_data)
        self.assertEqual(project1_data["hours"], 15.0)
        self.assertEqual(project1_data["timesheet_count"], 2)
        
        # 验证非项目工作
        non_project_data = next((p for p in result if p["project_id"] == 0), None)
        self.assertIsNotNone(non_project_data)
        self.assertEqual(non_project_data["project_name"], "非项目工作")
        self.assertEqual(non_project_data["hours"], 3.0)

    def test_get_project_breakdown_with_limit(self):
        """测试项目工时分布 - 限制数量"""
        # 创建多个项目的工时
        timesheets = []
        for i in range(20):
            mock_ts = MagicMock()
            mock_ts.project_id = i + 1
            mock_ts.hours = 10 - i * 0.1  # 递减的工时
            timesheets.append(mock_ts)

        mock_project = MagicMock()
        mock_project.project_name = "测试项目"

        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "Timesheet":
                mock_query.filter.return_value.all.return_value = timesheets
            elif model.__name__ == "Project":
                mock_query.filter.return_value.first.return_value = mock_project
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator._get_project_breakdown(
            self.db,
            user_ids=[101],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            limit=5,
        )

        # 验证限制数量
        self.assertEqual(len(result), 5)

    # ========== _get_member_workload() 测试 ==========

    def test_get_member_workload_empty_members(self):
        """测试成员工作负荷 - 空成员列表"""
        result = self.generator._get_member_workload(
            self.db,
            members=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        self.assertEqual(len(result), 0)

    def test_get_member_workload_with_data(self):
        """测试成员工作负荷 - 有数据"""
        # Mock用户
        mock_user1 = MagicMock()
        mock_user1.id = 101
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"
        mock_user1.position = "工程师"

        mock_user2 = MagicMock()
        mock_user2.id = 102
        mock_user2.real_name = None  # 测试None值，应使用username
        mock_user2.username = "lisi"
        mock_user2.position = None  # 测试None值

        # Mock工时记录
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 101
        mock_ts1.hours = 8.0

        mock_ts2 = MagicMock()
        mock_ts2.user_id = 101
        mock_ts2.hours = 7.5

        mock_ts3 = MagicMock()
        mock_ts3.user_id = 102
        mock_ts3.hours = 6.0

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2, mock_ts3
        ]

        result = self.generator._get_member_workload(
            self.db,
            members=[mock_user1, mock_user2],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        self.assertEqual(len(result), 2)
        
        # 验证用户1
        user1_data = next((u for u in result if u["user_id"] == 101), None)
        self.assertIsNotNone(user1_data)
        self.assertEqual(user1_data["user_name"], "张三")
        self.assertEqual(user1_data["total_hours"], 15.5)
        self.assertEqual(user1_data["avg_daily_hours"], 3.1)
        
        # 验证用户2（测试None值处理）
        user2_data = next((u for u in result if u["user_id"] == 102), None)
        self.assertIsNotNone(user2_data)
        self.assertEqual(user2_data["user_name"], "lisi")
        self.assertEqual(user2_data["position"], "")

    # ========== _get_member_workload_detailed() 测试 ==========

    def test_get_member_workload_detailed_empty_members(self):
        """测试成员工作负荷详情 - 空成员列表"""
        result = self.generator._get_member_workload_detailed(
            self.db,
            members=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            working_days=22,
        )

        self.assertEqual(len(result), 0)

    def test_get_member_workload_detailed_with_data(self):
        """测试成员工作负荷详情 - 有数据"""
        # Mock用户
        mock_user = MagicMock()
        mock_user.id = 101
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.position = "工程师"

        # Mock工时记录
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 101
        mock_ts1.hours = 8.0
        mock_ts1.work_date = date(2024, 1, 2)

        mock_ts2 = MagicMock()
        mock_ts2.user_id = 101
        mock_ts2.hours = 8.0
        mock_ts2.work_date = date(2024, 1, 3)

        mock_ts3 = MagicMock()
        mock_ts3.user_id = 101
        mock_ts3.hours = 8.0
        mock_ts3.work_date = date(2024, 1, 3)  # 同一天

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2, mock_ts3
        ]

        result = self.generator._get_member_workload_detailed(
            self.db,
            members=[mock_user],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            working_days=22,
        )

        self.assertEqual(len(result), 1)
        
        user_data = result[0]
        self.assertEqual(user_data["user_id"], 101)
        self.assertEqual(user_data["total_hours"], 24.0)
        self.assertEqual(user_data["expected_hours"], 176)  # 22 * 8
        self.assertEqual(user_data["utilization_rate"], 13.6)  # 24/176*100
        self.assertEqual(user_data["timesheet_days"], 2)  # 2个不同日期

    def test_get_member_workload_detailed_zero_working_days(self):
        """测试成员工作负荷详情 - 零工作日"""
        mock_user = MagicMock()
        mock_user.id = 101
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.position = "工程师"

        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.generator._get_member_workload_detailed(
            self.db,
            members=[mock_user],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            working_days=0,  # 测试除以0的情况
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["utilization_rate"], 0)

    def test_get_member_workload_detailed_sorting(self):
        """测试成员工作负荷详情 - 按工时排序"""
        # Mock用户
        mock_user1 = MagicMock()
        mock_user1.id = 101
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"
        mock_user1.position = "工程师"

        mock_user2 = MagicMock()
        mock_user2.id = 102
        mock_user2.real_name = "李四"
        mock_user2.username = "lisi"
        mock_user2.position = "高级工程师"

        # Mock工时（user2工时更多）
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 101
        mock_ts1.hours = 10.0
        mock_ts1.work_date = date(2024, 1, 2)

        mock_ts2 = MagicMock()
        mock_ts2.user_id = 102
        mock_ts2.hours = 20.0
        mock_ts2.work_date = date(2024, 1, 2)

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2
        ]

        result = self.generator._get_member_workload_detailed(
            self.db,
            members=[mock_user1, mock_user2],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            working_days=22,
        )

        # 验证排序（工时多的在前）
        self.assertEqual(result[0]["user_id"], 102)
        self.assertEqual(result[1]["user_id"], 101)

    # ========== _get_project_stats() 测试 ==========

    def test_get_project_stats_empty_users(self):
        """测试项目统计 - 空用户列表"""
        result = self.generator._get_project_stats(
            self.db,
            user_ids=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_stage"], {})
        self.assertEqual(result["by_health"], {})
        self.assertEqual(result["completed_this_month"], 0)
        self.assertEqual(result["started_this_month"], 0)

    def test_get_project_stats_with_data(self):
        """测试项目统计 - 有数据"""
        # Mock项目成员
        mock_pm1 = MagicMock()
        mock_pm1.project_id = 1

        mock_pm2 = MagicMock()
        mock_pm2.project_id = 2

        # Mock项目
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.is_active = True
        mock_project1.stage = "S3"
        mock_project1.health = "H1"
        mock_project1.created_at = datetime(2024, 1, 5)
        mock_project1.updated_at = datetime(2024, 1, 20)

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.is_active = True
        mock_project2.stage = "S9"  # 已完成
        mock_project2.health = "H3"  # 高风险
        mock_project2.created_at = datetime(2023, 12, 1)
        mock_project2.updated_at = datetime(2024, 1, 15)

        # 设置数据库查询mock
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "ProjectMember":
                mock_query.filter.return_value.all.return_value = [mock_pm1, mock_pm2]
            elif model.__name__ == "Project":
                mock_query.filter.return_value.all.return_value = [mock_project1, mock_project2]
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator._get_project_stats(
            self.db,
            user_ids=[101],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        # 验证总数
        self.assertEqual(result["total"], 2)
        
        # 验证按阶段统计
        self.assertEqual(result["by_stage"]["S3"], 1)
        self.assertEqual(result["by_stage"]["S9"], 1)
        
        # 验证按健康度统计
        self.assertEqual(result["by_health"]["H1"], 1)
        self.assertEqual(result["by_health"]["H3"], 1)
        
        # 验证本月完成/新开项目
        self.assertEqual(result["completed_this_month"], 1)
        self.assertEqual(result["started_this_month"], 1)

    def test_get_project_stats_null_attributes(self):
        """测试项目统计 - 处理None属性"""
        # Mock项目成员
        mock_pm = MagicMock()
        mock_pm.project_id = 1

        # Mock项目（属性为None）
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.is_active = True
        mock_project.stage = None
        mock_project.health = None
        mock_project.created_at = None
        mock_project.updated_at = None

        def query_side_effect(model):
            mock_query = MagicMock()
            
            if model.__name__ == "ProjectMember":
                mock_query.filter.return_value.all.return_value = [mock_pm]
            elif model.__name__ == "Project":
                mock_query.filter.return_value.all.return_value = [mock_project]
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.generator._get_project_stats(
            self.db,
            user_ids=[101],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        # 验证None值被处理为默认值
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["by_stage"]["S1"], 1)  # 默认S1
        self.assertEqual(result["by_health"]["H1"], 1)  # 默认H1


if __name__ == "__main__":
    unittest.main()
