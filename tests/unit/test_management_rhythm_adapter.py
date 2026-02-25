# -*- coding: utf-8 -*-
"""
管理节律 Dashboard 适配器单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

from app.models.enums import (
    ActionItemStatus,
    MeetingRhythmLevel,
)
from app.services.dashboard_adapters.management_rhythm import (
    ManagementRhythmDashboardAdapter,
)


class TestManagementRhythmDashboardAdapter(unittest.TestCase):
    """测试管理节律Dashboard适配器"""

    def setUp(self):
        """测试前准备"""
        # Mock DB Session
        self.db = MagicMock()
        
        # Mock Current User
        self.current_user = MagicMock()
        self.current_user.id = 1
        self.current_user.name = "测试用户"
        
        # 创建适配器实例
        self.adapter = ManagementRhythmDashboardAdapter(
            db=self.db, 
            current_user=self.current_user
        )

    # ========== 属性测试 ==========

    def test_module_id(self):
        """测试module_id属性"""
        self.assertEqual(self.adapter.module_id, "management_rhythm")

    def test_module_name(self):
        """测试module_name属性"""
        self.assertEqual(self.adapter.module_name, "管理节律")

    def test_supported_roles(self):
        """测试supported_roles属性"""
        expected_roles = ["admin", "pmo", "management"]
        self.assertEqual(self.adapter.supported_roles, expected_roles)
        self.assertIn("admin", self.adapter.supported_roles)
        self.assertIn("pmo", self.adapter.supported_roles)
        self.assertIn("management", self.adapter.supported_roles)

    # ========== get_stats() 测试 ==========

    def test_get_stats_with_snapshot_data(self):
        """测试get_stats - 有快照数据的情况"""
        # Mock快照数据
        mock_strategic_snapshot = MagicMock()
        mock_strategic_snapshot.health_status = "GREEN"
        
        # Mock query链
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        
        # 设置不同查询的返回值
        def query_side_effect(*args):
            q = MagicMock()
            # 战略快照查询
            if hasattr(args[0], '__name__') and 'RhythmDashboardSnapshot' in str(args[0]):
                q.filter.return_value.order_by.return_value.first.return_value = mock_strategic_snapshot
            # 会议总数查询
            elif 'StrategicMeeting' in str(args[0]):
                if hasattr(q, 'filter'):
                    q.filter.return_value.count.return_value = 10
            # 行动项查询
            elif 'MeetingActionItem' in str(args[0]):
                # 总行动项
                q.count.return_value = 50
                # 已完成
                if hasattr(q, 'filter'):
                    filter_q = q.filter.return_value
                    filter_q.count.return_value = 35
            return q
        
        self.db.query.side_effect = query_side_effect
        
        # 精确mock每个查询路径
        # 1. 战略快照
        strategic_query = MagicMock()
        strategic_query.filter.return_value.order_by.return_value.first.return_value = mock_strategic_snapshot
        
        # 2. 运营快照
        operational_query = MagicMock()
        operational_query.filter.return_value.order_by.return_value.first.return_value = None
        
        # 3. 会议总数
        meetings_query = MagicMock()
        meetings_query.filter.return_value.count.return_value = 10
        
        # 4. 总行动项
        total_action_items_query = MagicMock()
        total_action_items_query.count.return_value = 50
        
        # 5. 已完成行动项
        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 35
        
        # 6. 逾期行动项
        overdue_query = MagicMock()
        overdue_query.filter.return_value.count.return_value = 5
        
        # 按调用顺序返回
        self.db.query.side_effect = [
            strategic_query,      # 战略快照
            operational_query,    # 运营快照
            meetings_query,       # 会议总数
            total_action_items_query,  # 总行动项
            completed_query,      # 已完成
            overdue_query,        # 逾期
        ]
        
        # 执行
        result = self.adapter.get_stats()
        
        # 验证
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 6)
        
        # 验证每个卡片
        stat_keys = [card.key for card in result]
        self.assertIn("total_meetings", stat_keys)
        self.assertIn("total_action_items", stat_keys)
        self.assertIn("completed_action_items", stat_keys)
        self.assertIn("overdue_action_items", stat_keys)
        self.assertIn("completion_rate", stat_keys)
        self.assertIn("strategic_health", stat_keys)
        
        # 验证数值
        meetings_card = next(c for c in result if c.key == "total_meetings")
        self.assertEqual(meetings_card.value, 10)
        
        action_items_card = next(c for c in result if c.key == "total_action_items")
        self.assertEqual(action_items_card.value, 50)
        
        completed_card = next(c for c in result if c.key == "completed_action_items")
        self.assertEqual(completed_card.value, 35)
        
        # 完成率 = 35/50 = 70%
        completion_card = next(c for c in result if c.key == "completion_rate")
        self.assertEqual(completion_card.value, 70.0)
        
        # 健康度
        health_card = next(c for c in result if c.key == "strategic_health")
        self.assertEqual(health_card.value, "GREEN")

    def test_get_stats_without_snapshot(self):
        """测试get_stats - 无快照数据的情况"""
        # Mock所有查询返回None或0
        strategic_query = MagicMock()
        strategic_query.filter.return_value.order_by.return_value.first.return_value = None
        
        operational_query = MagicMock()
        operational_query.filter.return_value.order_by.return_value.first.return_value = None
        
        meetings_query = MagicMock()
        meetings_query.filter.return_value.count.return_value = 0
        
        total_action_items_query = MagicMock()
        total_action_items_query.count.return_value = 0
        
        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 0
        
        overdue_query = MagicMock()
        overdue_query.filter.return_value.count.return_value = 0
        
        self.db.query.side_effect = [
            strategic_query,
            operational_query,
            meetings_query,
            total_action_items_query,
            completed_query,
            overdue_query,
        ]
        
        # 执行
        result = self.adapter.get_stats()
        
        # 验证
        self.assertEqual(len(result), 6)
        
        # 验证完成率为0（避免除零错误）
        completion_card = next(c for c in result if c.key == "completion_rate")
        self.assertEqual(completion_card.value, 0)
        
        # 验证健康度为N/A
        health_card = next(c for c in result if c.key == "strategic_health")
        self.assertEqual(health_card.value, "N/A")

    def test_get_stats_completion_rate_calculation(self):
        """测试完成率计算 - 各种比例"""
        # Case 1: 100%完成率
        strategic_query = MagicMock()
        strategic_query.filter.return_value.order_by.return_value.first.return_value = None
        
        operational_query = MagicMock()
        operational_query.filter.return_value.order_by.return_value.first.return_value = None
        
        meetings_query = MagicMock()
        meetings_query.filter.return_value.count.return_value = 5
        
        total_action_items_query = MagicMock()
        total_action_items_query.count.return_value = 20
        
        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 20
        
        overdue_query = MagicMock()
        overdue_query.filter.return_value.count.return_value = 0
        
        self.db.query.side_effect = [
            strategic_query,
            operational_query,
            meetings_query,
            total_action_items_query,
            completed_query,
            overdue_query,
        ]
        
        result = self.adapter.get_stats()
        completion_card = next(c for c in result if c.key == "completion_rate")
        self.assertEqual(completion_card.value, 100.0)

    # ========== get_widgets() 测试 ==========

    def test_get_widgets_with_data(self):
        """测试get_widgets - 有数据的情况"""
        today = date.today()
        
        # Mock即将召开的会议
        mock_meeting1 = MagicMock()
        mock_meeting1.id = 1
        mock_meeting1.title = "战略研讨会"
        mock_meeting1.rhythm_level = "STRATEGIC"
        mock_meeting1.meeting_date = today
        mock_meeting1.status = "SCHEDULED"
        
        mock_meeting2 = MagicMock()
        mock_meeting2.id = 2
        mock_meeting2.title = "运营例会"
        mock_meeting2.rhythm_level = "OPERATIONAL"
        mock_meeting2.meeting_date = today
        mock_meeting2.status = "SCHEDULED"
        
        # Mock我的行动项
        mock_action1 = MagicMock()
        mock_action1.id = 1
        mock_action1.title = "完成方案设计"
        mock_action1.due_date = today
        mock_action1.status = ActionItemStatus.IN_PROGRESS.value
        mock_action1.priority = "HIGH"
        
        mock_action2 = MagicMock()
        mock_action2.id = 2
        mock_action2.title = "提交报告"
        mock_action2.due_date = today
        mock_action2.status = ActionItemStatus.TODO.value
        mock_action2.priority = "NORMAL"
        
        # Mock query链 - 即将召开的会议
        meetings_query = MagicMock()
        meetings_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_meeting1, mock_meeting2
        ]
        
        # Mock query链 - 我的行动项
        actions_query = MagicMock()
        actions_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_action1, mock_action2
        ]
        
        self.db.query.side_effect = [meetings_query, actions_query]
        
        # 执行
        result = self.adapter.get_widgets()
        
        # 验证
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        
        # 验证即将召开的会议widget
        upcoming_widget = result[0]
        self.assertEqual(upcoming_widget.widget_id, "upcoming_meetings")
        self.assertEqual(upcoming_widget.widget_type, "list")
        self.assertEqual(upcoming_widget.title, "即将召开的会议")
        self.assertEqual(len(upcoming_widget.data), 2)
        self.assertEqual(upcoming_widget.data[0]["title"], "战略研讨会")
        
        # 验证我的行动项widget
        action_widget = result[1]
        self.assertEqual(action_widget.widget_id, "my_action_items")
        self.assertEqual(action_widget.widget_type, "list")
        self.assertEqual(action_widget.title, "我的待办行动项")
        self.assertEqual(len(action_widget.data), 2)
        self.assertEqual(action_widget.data[0]["title"], "完成方案设计")

    def test_get_widgets_empty_data(self):
        """测试get_widgets - 无数据的情况"""
        # Mock空结果
        meetings_query = MagicMock()
        meetings_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        actions_query = MagicMock()
        actions_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        self.db.query.side_effect = [meetings_query, actions_query]
        
        # 执行
        result = self.adapter.get_widgets()
        
        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0].data), 0)
        self.assertEqual(len(result[1].data), 0)

    def test_get_widgets_uses_current_user(self):
        """测试get_widgets使用当前用户ID过滤行动项"""
        # 设置用户ID
        self.current_user.id = 999
        
        meetings_query = MagicMock()
        meetings_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        actions_query = MagicMock()
        actions_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        self.db.query.side_effect = [meetings_query, actions_query]
        
        # 执行
        result = self.adapter.get_widgets()
        
        # 验证调用了filter (无法直接验证参数，但可以确保调用了)
        self.assertTrue(actions_query.filter.called)

    # ========== get_detailed_data() 测试 ==========

    def test_get_detailed_data_complete(self):
        """测试get_detailed_data - 完整数据"""
        # Mock get_stats返回
        mock_strategic_snapshot = MagicMock()
        mock_strategic_snapshot.health_status = "YELLOW"
        
        # 为get_stats准备mock
        strategic_query = MagicMock()
        strategic_query.filter.return_value.order_by.return_value.first.return_value = mock_strategic_snapshot
        
        operational_query = MagicMock()
        operational_query.filter.return_value.order_by.return_value.first.return_value = None
        
        meetings_query = MagicMock()
        meetings_query.filter.return_value.count.return_value = 15
        
        total_action_items_query = MagicMock()
        total_action_items_query.count.return_value = 60
        
        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 40
        
        overdue_query = MagicMock()
        overdue_query.filter.return_value.count.return_value = 8
        
        # Mock按层级统计的查询
        # STRATEGIC
        strategic_level_query = MagicMock()
        strategic_level_query.filter.return_value.count.return_value = 5
        
        strategic_completed_query = MagicMock()
        strategic_completed_query.filter.return_value.count.return_value = 3
        
        # OPERATIONAL
        operational_level_query = MagicMock()
        operational_level_query.filter.return_value.count.return_value = 4
        
        operational_completed_query = MagicMock()
        operational_completed_query.filter.return_value.count.return_value = 2
        
        # OPERATION
        operation_level_query = MagicMock()
        operation_level_query.filter.return_value.count.return_value = 3
        
        operation_completed_query = MagicMock()
        operation_completed_query.filter.return_value.count.return_value = 1
        
        # TASK
        task_level_query = MagicMock()
        task_level_query.filter.return_value.count.return_value = 3
        
        task_completed_query = MagicMock()
        task_completed_query.filter.return_value.count.return_value = 1
        
        # 设置side_effect按调用顺序
        self.db.query.side_effect = [
            # get_stats() 的6个查询
            strategic_query,
            operational_query,
            meetings_query,
            total_action_items_query,
            completed_query,
            overdue_query,
            # get_detailed_data() 的8个查询 (4个层级 x 2)
            strategic_level_query,
            strategic_completed_query,
            operational_level_query,
            operational_completed_query,
            operation_level_query,
            operation_completed_query,
            task_level_query,
            task_completed_query,
        ]
        
        # 执行
        result = self.adapter.get_detailed_data()
        
        # 验证
        self.assertEqual(result.module, "management_rhythm")
        self.assertEqual(result.module_name, "管理节律")
        
        # 验证summary
        self.assertIn("total_meetings", result.summary)
        self.assertEqual(result.summary["total_meetings"], 15)
        
        # 验证details
        self.assertIn("level_stats", result.details)
        level_stats = result.details["level_stats"]
        self.assertEqual(len(level_stats), 4)
        
        # 验证各层级统计
        strategic_stat = level_stats[0]
        self.assertEqual(strategic_stat["level"], MeetingRhythmLevel.STRATEGIC.value)
        self.assertEqual(strategic_stat["meetings_count"], 5)
        self.assertEqual(strategic_stat["completed_meetings"], 3)
        
        # 验证generated_at
        self.assertIsInstance(result.generated_at, datetime)

    def test_get_detailed_data_zero_counts(self):
        """测试get_detailed_data - 所有计数为0"""
        # Mock所有查询返回0
        mock_queries = []
        for _ in range(14):  # 6 (get_stats) + 8 (level_stats)
            q = MagicMock()
            if hasattr(q, 'filter'):
                q.filter.return_value.count.return_value = 0
                q.filter.return_value.order_by.return_value.first.return_value = None
            q.count.return_value = 0
            mock_queries.append(q)
        
        self.db.query.side_effect = mock_queries
        
        # 执行
        result = self.adapter.get_detailed_data()
        
        # 验证
        self.assertEqual(result.summary["total_meetings"], 0)
        level_stats = result.details["level_stats"]
        self.assertEqual(len(level_stats), 4)
        
        for stat in level_stats:
            self.assertEqual(stat["meetings_count"], 0)
            self.assertEqual(stat["completed_meetings"], 0)

    # ========== 边界情况测试 ==========

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertIsNotNone(self.adapter.db)
        self.assertIsNotNone(self.adapter.current_user)
        self.assertEqual(self.adapter.current_user.id, 1)

    def test_get_stats_with_partial_data(self):
        """测试get_stats - 部分数据缺失"""
        # 只有会议数据，没有行动项
        strategic_query = MagicMock()
        strategic_query.filter.return_value.order_by.return_value.first.return_value = None
        
        operational_query = MagicMock()
        operational_query.filter.return_value.order_by.return_value.first.return_value = None
        
        meetings_query = MagicMock()
        meetings_query.filter.return_value.count.return_value = 5
        
        total_action_items_query = MagicMock()
        total_action_items_query.count.return_value = 0
        
        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 0
        
        overdue_query = MagicMock()
        overdue_query.filter.return_value.count.return_value = 0
        
        self.db.query.side_effect = [
            strategic_query,
            operational_query,
            meetings_query,
            total_action_items_query,
            completed_query,
            overdue_query,
        ]
        
        result = self.adapter.get_stats()
        
        meetings_card = next(c for c in result if c.key == "total_meetings")
        self.assertEqual(meetings_card.value, 5)
        
        # 完成率应该是0（避免除零）
        completion_card = next(c for c in result if c.key == "completion_rate")
        self.assertEqual(completion_card.value, 0)

    def test_get_widgets_widget_order(self):
        """测试widget顺序"""
        meetings_query = MagicMock()
        meetings_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        actions_query = MagicMock()
        actions_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        self.db.query.side_effect = [meetings_query, actions_query]
        
        result = self.adapter.get_widgets()
        
        # 验证顺序
        self.assertEqual(result[0].order, 1)
        self.assertEqual(result[1].order, 2)
        
        # 验证span
        self.assertEqual(result[0].span, 12)
        self.assertEqual(result[1].span, 12)

    def test_get_stats_card_properties(self):
        """测试统计卡片的属性完整性"""
        strategic_query = MagicMock()
        strategic_query.filter.return_value.order_by.return_value.first.return_value = None
        
        operational_query = MagicMock()
        operational_query.filter.return_value.order_by.return_value.first.return_value = None
        
        meetings_query = MagicMock()
        meetings_query.filter.return_value.count.return_value = 1
        
        total_action_items_query = MagicMock()
        total_action_items_query.count.return_value = 1
        
        completed_query = MagicMock()
        completed_query.filter.return_value.count.return_value = 1
        
        overdue_query = MagicMock()
        overdue_query.filter.return_value.count.return_value = 0
        
        self.db.query.side_effect = [
            strategic_query,
            operational_query,
            meetings_query,
            total_action_items_query,
            completed_query,
            overdue_query,
        ]
        
        result = self.adapter.get_stats()
        
        # 验证每个卡片都有必要的属性
        for card in result:
            self.assertIsNotNone(card.key)
            self.assertIsNotNone(card.title)
            self.assertIsNotNone(card.value)

    def test_get_detailed_data_summary_keys(self):
        """测试detailed_data的summary包含所有stats的key"""
        # 简化mock
        mock_queries = []
        for _ in range(14):
            q = MagicMock()
            q.filter.return_value.count.return_value = 1
            q.filter.return_value.order_by.return_value.first.return_value = None
            q.count.return_value = 1
            mock_queries.append(q)
        
        self.db.query.side_effect = mock_queries
        
        result = self.adapter.get_detailed_data()
        
        # 验证summary包含所有stats的key
        expected_keys = [
            "total_meetings",
            "total_action_items",
            "completed_action_items",
            "overdue_action_items",
            "completion_rate",
            "strategic_health",
        ]
        
        for key in expected_keys:
            self.assertIn(key, result.summary)


if __name__ == "__main__":
    unittest.main()
