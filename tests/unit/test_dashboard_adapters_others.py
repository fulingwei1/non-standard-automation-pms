# -*- coding: utf-8 -*-
"""
dashboard_adapters/others.py 单元测试

策略：
1. 只mock外部依赖（db查询操作）
2. 让业务逻辑真实执行
3. 覆盖主要方法和边界情况
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from app.services.dashboard_adapters.others import (
    OthersDashboardAdapter,
    StaffMatchingDashboardAdapter,
    KitRateDashboardAdapter,
)
from app.schemas.dashboard import DashboardStatCard, DashboardWidget


class TestOthersDashboardAdapter(unittest.TestCase):
    """测试 OthersDashboardAdapter 类"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.adapter = OthersDashboardAdapter(self.db)

    # ========== get_quick_stats() 测试 ==========

    def test_get_quick_stats_success(self):
        """测试获取快速统计数据 - 成功"""
        # Mock 数据库查询
        mock_project_query = MagicMock()
        mock_project_query.count.return_value = 10

        mock_user_query = MagicMock()
        mock_user_query.count.return_value = 25

        mock_alert_query = MagicMock()
        mock_alert_filter = MagicMock()
        mock_alert_filter.count.return_value = 3
        mock_alert_query.filter.return_value = mock_alert_filter

        # 配置 db.query 返回值
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.user import User
            from app.models.alert import AlertRecord

            if model == Project:
                return mock_project_query
            elif model == User:
                return mock_user_query
            elif model == AlertRecord:
                return mock_alert_query
            return MagicMock()

        self.db.query.side_effect = query_side_effect

        # 执行
        result = self.adapter.get_quick_stats()

        # 验证
        self.assertEqual(result["project_count"], 10)
        self.assertEqual(result["user_count"], 25)
        self.assertEqual(result["alert_count"], 3)

    def test_get_quick_stats_exception(self):
        """测试获取快速统计数据 - 异常处理"""
        # Mock 抛出异常
        self.db.query.side_effect = Exception("Database error")

        # 执行
        result = self.adapter.get_quick_stats()

        # 验证返回默认值
        self.assertEqual(result["project_count"], 0)
        self.assertEqual(result["user_count"], 0)
        self.assertEqual(result["alert_count"], 0)

    # ========== get_recent_activities() 测试 ==========

    @patch("app.services.dashboard_adapters.others.ApprovalRecord")
    def test_get_recent_activities_without_user_filter(self, mock_approval_record):
        """测试获取最近活动 - 无用户过滤"""
        # Mock 活动记录
        mock_activity1 = MagicMock()
        mock_activity1.id = 1
        mock_activity2 = MagicMock()
        mock_activity2.id = 2

        mock_query = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = [mock_activity1, mock_activity2]
        mock_order_by.limit.return_value = mock_limit
        mock_query.order_by.return_value = mock_order_by

        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_recent_activities(limit=10)

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)

    @patch("app.services.dashboard_adapters.others.ApprovalRecord")
    def test_get_recent_activities_with_user_filter(self, mock_approval_record):
        """测试获取最近活动 - 有用户过滤"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = []
        mock_order_by.limit.return_value = mock_limit
        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter

        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_recent_activities(limit=5, user_id=123)

        # 验证
        self.assertEqual(result, [])

    def test_get_recent_activities_exception(self):
        """测试获取最近活动 - 异常处理"""
        self.db.query.side_effect = Exception("Query error")

        # 执行
        result = self.adapter.get_recent_activities()

        # 验证返回空列表
        self.assertEqual(result, [])

    # ========== get_system_health() 测试 ==========

    def test_get_system_health_all_healthy(self):
        """测试系统健康状态 - 全部健康"""
        # Mock 数据库连接正常
        self.db.execute.return_value = None

        # Mock redis客户端存在
        with patch("app.utils.redis_client.redis_client", MagicMock()):
            result = self.adapter.get_system_health()

        # 验证
        self.assertEqual(result["database"], "healthy")
        self.assertEqual(result["cache"], "healthy")
        self.assertEqual(result["status"], "healthy")

    def test_get_system_health_database_unhealthy(self):
        """测试系统健康状态 - 数据库异常"""
        # Mock 数据库执行失败
        self.db.execute.side_effect = Exception("DB connection failed")

        # Mock redis正常
        with patch("app.utils.redis_client.redis_client", MagicMock()):
            result = self.adapter.get_system_health()

        # 验证
        self.assertEqual(result["database"], "unhealthy")
        self.assertEqual(result["status"], "degraded")

    def test_get_system_health_cache_not_configured(self):
        """测试系统健康状态 - 缓存未配置"""
        # Mock 数据库正常
        self.db.execute.return_value = None

        # Mock redis_client 为 None
        with patch("app.utils.redis_client.redis_client", None):
            result = self.adapter.get_system_health()

        # 验证
        self.assertEqual(result["database"], "healthy")
        self.assertEqual(result["cache"], "not_configured")

    def test_get_system_health_cache_unavailable(self):
        """测试系统健康状态 - 缓存不可用"""
        # Mock 数据库正常
        self.db.execute.return_value = None

        # Mock redis导入失败
        with patch("app.utils.redis_client.redis_client") as mock_redis:
            mock_redis.side_effect = Exception("Redis unavailable")
            result = self.adapter.get_system_health()

        # 验证
        self.assertEqual(result["database"], "healthy")
        self.assertEqual(result["cache"], "unavailable")

    # ========== get_user_tasks() 测试 ==========

    @patch("app.services.dashboard_adapters.others.TaskItem")
    def test_get_user_tasks_basic(self, mock_task_item):
        """测试获取用户任务 - 基本功能"""
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task2 = MagicMock()
        mock_task2.id = 2

        mock_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter2 = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()

        mock_limit.all.return_value = [mock_task1, mock_task2]
        mock_order_by.limit.return_value = mock_limit
        mock_filter2.order_by.return_value = mock_order_by
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1

        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_user_tasks(user_id=123, status="PENDING")

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)

    @patch("app.services.dashboard_adapters.others.ApprovalTask")
    @patch("app.services.dashboard_adapters.others.TaskItem")
    def test_get_user_tasks_with_approvals(self, mock_task_item, mock_approval_task):
        """测试获取用户任务 - 包含审批任务"""
        # Mock 普通任务
        mock_task = MagicMock()
        mock_task.id = 1

        mock_task_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = [mock_task]
        mock_order_by.limit.return_value = mock_limit
        mock_filter1.order_by.return_value = mock_order_by
        mock_task_query.filter.return_value = mock_filter1

        # Mock 审批任务
        mock_approval = MagicMock()
        mock_approval.id = 2

        mock_approval_query = MagicMock()
        mock_approval_filter = MagicMock()
        mock_approval_limit = MagicMock()
        mock_approval_limit.all.return_value = [mock_approval]
        mock_approval_filter.limit.return_value = mock_approval_limit
        mock_approval_query.filter.return_value = mock_approval_filter

        # 配置 db.query 返回值
        query_calls = [mock_task_query, mock_approval_query]
        self.db.query.side_effect = query_calls

        # 执行
        result = self.adapter.get_user_tasks(user_id=123, include_approvals=True)

        # 验证
        self.assertEqual(len(result), 2)

    def test_get_user_tasks_exception(self):
        """测试获取用户任务 - 异常处理"""
        self.db.query.side_effect = Exception("Query failed")

        # 执行
        result = self.adapter.get_user_tasks(user_id=123)

        # 验证返回空列表
        self.assertEqual(result, [])

    def test_get_user_tasks_approval_exception(self):
        """测试获取用户任务 - 审批任务异常"""
        # Mock 普通任务成功
        mock_task_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = []
        mock_order_by.limit.return_value = mock_limit
        mock_filter.order_by.return_value = mock_order_by
        mock_task_query.filter.return_value = mock_filter

        # Mock 审批任务失败
        mock_approval_query = MagicMock()
        mock_approval_query.filter.side_effect = Exception("Approval query failed")

        self.db.query.side_effect = [mock_task_query, mock_approval_query]

        # 执行
        result = self.adapter.get_user_tasks(user_id=123, include_approvals=True)

        # 验证返回普通任务
        self.assertEqual(result, [])

    # ========== get_notifications() 测试 ==========

    def test_get_notifications_all(self):
        """测试获取通知 - 全部"""
        mock_notif1 = MagicMock()
        mock_notif1.id = 1
        mock_notif2 = MagicMock()
        mock_notif2.id = 2

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()

        mock_limit.all.return_value = [mock_notif1, mock_notif2]
        mock_order_by.limit.return_value = mock_limit
        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter

        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_notifications(user_id=123)

        # 验证
        self.assertEqual(len(result), 2)

    def test_get_notifications_unread_only(self):
        """测试获取通知 - 只获取未读"""
        mock_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter2 = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()

        mock_limit.all.return_value = []
        mock_order_by.limit.return_value = mock_limit
        mock_filter2.order_by.return_value = mock_order_by
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1

        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_notifications(user_id=123, unread_only=True)

        # 验证
        self.assertEqual(result, [])
        # 应该调用两次 filter（user_id 和 is_read）
        self.assertEqual(mock_filter1.filter.call_count, 1)

    def test_get_notifications_exception(self):
        """测试获取通知 - 异常处理"""
        self.db.query.side_effect = Exception("Query error")

        # 执行
        result = self.adapter.get_notifications(user_id=123)

        # 验证返回空列表
        self.assertEqual(result, [])


class TestStaffMatchingDashboardAdapter(unittest.TestCase):
    """测试 StaffMatchingDashboardAdapter 类"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.current_user = MagicMock()
        self.current_user.id = 1
        self.current_user.role = "hr"
        self.adapter = StaffMatchingDashboardAdapter(self.db, self.current_user)

    # ========== 属性测试 ==========

    def test_module_id(self):
        """测试模块ID"""
        self.assertEqual(self.adapter.module_id, "staff_matching")

    def test_module_name(self):
        """测试模块名称"""
        self.assertEqual(self.adapter.module_name, "人员匹配")

    def test_supported_roles(self):
        """测试支持的角色"""
        self.assertEqual(self.adapter.supported_roles, ["hr", "pmo", "admin"])

    # ========== get_stats() 测试 ==========

    def test_get_stats_success(self):
        """测试获取统计卡片 - 成功"""
        # Mock 需求统计查询
        mock_query = MagicMock()
        mock_filter = MagicMock()

        # 配置不同状态的返回值
        def scalar_side_effect():
            # 根据调用次数返回不同值
            values = [10, 5, 15, 50, 100, 30, 20, 0.85, 0]  # 各种统计值
            return values.pop(0) if values else 0

        mock_filter.scalar.side_effect = scalar_side_effect
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_stats()

        # 验证
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 6)
        self.assertIsInstance(result[0], DashboardStatCard)
        self.assertEqual(result[0].key, "open_needs")

    def test_get_stats_with_zeros(self):
        """测试获取统计卡片 - 数据为0"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.scalar.return_value = 0
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        # 执行
        result = self.adapter.get_stats()

        # 验证成功率为0
        success_rate_card = [c for c in result if c.key == "success_rate"][0]
        self.assertEqual(success_rate_card.value, 0.0)

    # ========== get_widgets() 测试 ==========

    def test_get_widgets_with_data(self):
        """测试获取Widget - 有数据"""
        # Mock 匹配日志
        mock_log1 = MagicMock()
        mock_log1.id = 1
        mock_log1.request_id = "req123"
        mock_log1.project_id = 10
        mock_log1.total_score = 0.85
        mock_log1.is_accepted = True
        mock_log1.matching_time = datetime.now()
        mock_log1.project = MagicMock()
        mock_log1.project.name = "项目A"
        mock_log1.candidate = MagicMock()
        mock_log1.candidate.name = "张三"

        mock_query = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = [mock_log1]
        mock_order_by.limit.return_value = mock_limit
        mock_query.order_by.return_value = mock_order_by

        # Mock 优先级统计
        mock_group_query = MagicMock()
        mock_filter = MagicMock()
        mock_group_by = MagicMock()
        mock_group_by.all.return_value = [("HIGH", 5), ("MEDIUM", 3)]
        mock_filter.group_by.return_value = mock_group_by
        mock_group_query.filter.return_value = mock_filter

        # 配置 db.query 返回值
        self.db.query.side_effect = [mock_query, mock_group_query]

        # 执行
        result = self.adapter.get_widgets()

        # 验证
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], DashboardWidget)
        self.assertEqual(result[0].widget_id, "recent_matches")
        self.assertEqual(result[1].widget_id, "priority_distribution")

    def test_get_widgets_empty_data(self):
        """测试获取Widget - 无数据"""
        mock_query = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = []
        mock_order_by.limit.return_value = mock_limit
        mock_query.order_by.return_value = mock_order_by

        mock_group_query = MagicMock()
        mock_filter = MagicMock()
        mock_group_by = MagicMock()
        mock_group_by.all.return_value = []
        mock_filter.group_by.return_value = mock_group_by
        mock_group_query.filter.return_value = mock_filter

        self.db.query.side_effect = [mock_query, mock_group_query]

        # 执行
        result = self.adapter.get_widgets()

        # 验证
        self.assertEqual(len(result), 2)

    def test_get_widgets_log_without_relations(self):
        """测试获取Widget - 日志无关联对象"""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.request_id = "req123"
        mock_log.project_id = None
        mock_log.total_score = 0.75
        mock_log.is_accepted = False
        mock_log.matching_time = datetime.now()
        mock_log.project = None
        mock_log.candidate = None

        mock_query = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_limit.all.return_value = [mock_log]
        mock_order_by.limit.return_value = mock_limit
        mock_query.order_by.return_value = mock_order_by

        mock_group_query = MagicMock()
        mock_filter = MagicMock()
        mock_group_by = MagicMock()
        mock_group_by.all.return_value = []
        mock_filter.group_by.return_value = mock_group_by
        mock_group_query.filter.return_value = mock_filter

        self.db.query.side_effect = [mock_query, mock_group_query]

        # 执行
        result = self.adapter.get_widgets()

        # 验证
        items = result[0].data["items"]
        self.assertEqual(items[0]["project_name"], None)
        self.assertEqual(items[0]["employee_name"], None)

    # ========== get_detailed_data() 测试 ==========

    def test_get_detailed_data(self):
        """测试获取详细数据"""
        # Mock get_stats
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.scalar.return_value = 0
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        # Mock 状态统计
        mock_status_query = MagicMock()
        mock_status_query.count.return_value = 5

        query_count = [0]

        def query_side_effect(*args, **kwargs):
            query_count[0] += 1
            # 前9次调用是 get_stats 的
            if query_count[0] <= 9:
                return mock_query
            # 后面是状态统计
            return mock_status_query

        self.db.query.side_effect = query_side_effect

        # 执行
        result = self.adapter.get_detailed_data()

        # 验证
        self.assertEqual(result.module_id, "staff_matching")
        self.assertEqual(result.module_name, "人员匹配")
        self.assertIn("summary", result.data)
        self.assertIn("details", result.data)
        self.assertIn("by_status", result.data["details"])


class TestKitRateDashboardAdapter(unittest.TestCase):
    """测试 KitRateDashboardAdapter 类"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.current_user = MagicMock()
        self.current_user.id = 1
        self.current_user.role = "pmo"
        self.adapter = KitRateDashboardAdapter(self.db, self.current_user)

    # ========== 属性测试 ==========

    def test_module_id(self):
        """测试模块ID"""
        self.assertEqual(self.adapter.module_id, "kit_rate")

    def test_module_name(self):
        """测试模块名称"""
        self.assertEqual(self.adapter.module_name, "齐套率")

    def test_supported_roles(self):
        """测试支持的角色"""
        self.assertEqual(
            self.adapter.supported_roles, ["procurement", "production", "pmo", "admin"]
        )

    # ========== get_stats() 测试 ==========

    @patch("app.services.dashboard_adapters.others.KitRateService")
    def test_get_stats_success(self, mock_service_class):
        """测试获取统计卡片 - 成功"""
        # Mock KitRateService
        mock_service = MagicMock()
        mock_service.get_dashboard.return_value = {
            "data": {
                "overall_stats": {
                    "total_projects": 20,
                    "avg_kit_rate": 0.856,
                    "can_start_count": 15,
                    "shortage_count": 5,
                }
            }
        }
        mock_service_class.return_value = mock_service

        # 执行
        result = self.adapter.get_stats()

        # 验证
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result[0], DashboardStatCard)
        self.assertEqual(result[0].key, "total_projects")
        self.assertEqual(result[0].value, 20)
        self.assertEqual(result[1].value, 0.9)  # 85.6% rounded to 1 decimal

    @patch("app.services.dashboard_adapters.others.KitRateService")
    def test_get_stats_empty_data(self, mock_service_class):
        """测试获取统计卡片 - 空数据"""
        mock_service = MagicMock()
        mock_service.get_dashboard.return_value = {"data": {}}
        mock_service_class.return_value = mock_service

        # 执行
        result = self.adapter.get_stats()

        # 验证
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].value, 0)

    # ========== get_widgets() 测试 ==========

    @patch("app.services.dashboard_adapters.others.KitRateService")
    def test_get_widgets_with_projects(self, mock_service_class):
        """测试获取Widget - 有项目数据"""
        mock_service = MagicMock()
        mock_service.get_dashboard.return_value = {
            "data": {
                "project_list": [
                    {"id": 1, "name": "项目A", "kit_rate": 0.95},
                    {"id": 2, "name": "项目B", "kit_rate": 0.80},
                ]
            }
        }
        mock_service_class.return_value = mock_service

        # 执行
        result = self.adapter.get_widgets()

        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].widget_id, "project_list")
        self.assertEqual(len(result[0].data["items"]), 2)

    @patch("app.services.dashboard_adapters.others.KitRateService")
    def test_get_widgets_truncate_list(self, mock_service_class):
        """测试获取Widget - 超过10个项目截断"""
        # 创建15个项目
        projects = [{"id": i, "name": f"项目{i}"} for i in range(15)]

        mock_service = MagicMock()
        mock_service.get_dashboard.return_value = {"data": {"project_list": projects}}
        mock_service_class.return_value = mock_service

        # 执行
        result = self.adapter.get_widgets()

        # 验证只保留前10个
        self.assertEqual(len(result[0].data["items"]), 10)

    @patch("app.services.dashboard_adapters.others.KitRateService")
    def test_get_widgets_empty_list(self, mock_service_class):
        """测试获取Widget - 空项目列表"""
        mock_service = MagicMock()
        mock_service.get_dashboard.return_value = {"data": {}}
        mock_service_class.return_value = mock_service

        # 执行
        result = self.adapter.get_widgets()

        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].data["items"], [])

    # ========== get_detailed_data() 测试 ==========

    @patch("app.services.dashboard_adapters.others.KitRateService")
    def test_get_detailed_data(self, mock_service_class):
        """测试获取详细数据"""
        mock_service = MagicMock()
        mock_service.get_dashboard.return_value = {
            "data": {
                "overall_stats": {
                    "total_projects": 10,
                    "avg_kit_rate": 0.85,
                },
                "project_list": [
                    {"id": 1, "name": "项目A"},
                ],
            }
        }
        mock_service_class.return_value = mock_service

        # 执行
        result = self.adapter.get_detailed_data()

        # 验证
        self.assertEqual(result.module_id, "kit_rate")
        self.assertEqual(result.module_name, "齐套率")
        self.assertIn("summary", result.data)
        self.assertIn("details", result.data)
        self.assertIn("project_list", result.data["details"])


if __name__ == "__main__":
    unittest.main()
