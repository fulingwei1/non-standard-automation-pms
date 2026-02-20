# -*- coding: utf-8 -*-
"""
资源调度服务层单元测试
测试 ResourceSchedulingService 的核心业务逻辑
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.resource_scheduling.resource_scheduling_service import (
    ResourceSchedulingService,
)


class TestResourceSchedulingService(unittest.TestCase):
    """ResourceSchedulingService 单元测试"""

    def setUp(self):
        """测试前置准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)

    # ============================================================================
    # 1. 资源冲突检测测试
    # ============================================================================

    @patch("app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService")
    def test_detect_conflicts_success(self, mock_ai_service_class):
        """测试成功检测资源冲突"""
        # 准备mock数据
        mock_conflict = MagicMock()
        mock_conflict.id = 1
        mock_conflict.severity = "CRITICAL"

        mock_ai_service = MagicMock()
        mock_ai_service.detect_resource_conflicts.return_value = [mock_conflict]
        mock_ai_service_class.return_value = mock_ai_service

        # 重新创建service以使用mock的AI服务
        service = ResourceSchedulingService(self.mock_db)

        # 调用方法
        result = service.detect_conflicts(
            resource_id=1,
            resource_type="PERSON",
            project_id=10,
            start_date="2024-01-01",
            end_date="2024-01-31",
            auto_generate_suggestions=False,
            operator_id=100,
            operator_name="测试用户",
        )

        # 验证结果
        self.assertEqual(result["total_conflicts"], 1)
        self.assertEqual(result["critical_conflicts"], 1)
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertIn("detection_time_ms", result)

    @patch("app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService")
    def test_detect_conflicts_with_auto_suggestions(self, mock_ai_service_class):
        """测试自动生成调度方案"""
        # 准备mock数据
        mock_conflict = MagicMock()
        mock_conflict.id = 1
        mock_conflict.severity = "MEDIUM"

        mock_ai_service = MagicMock()
        mock_ai_service.detect_resource_conflicts.return_value = [mock_conflict]
        mock_ai_service.generate_scheduling_suggestions.return_value = []
        mock_ai_service_class.return_value = mock_ai_service

        service = ResourceSchedulingService(self.mock_db)

        # 调用方法（启用自动生成）
        result = service.detect_conflicts(
            resource_id=1,
            resource_type="PERSON",
            project_id=10,
            start_date="2024-01-01",
            end_date="2024-01-31",
            auto_generate_suggestions=True,
            operator_id=100,
            operator_name="测试用户",
        )

        # 验证AI服务被调用
        mock_ai_service.generate_scheduling_suggestions.assert_called_once()
        self.assertEqual(result["suggestions_generated"], 1)

    def test_list_conflicts_with_filters(self):
        """测试带筛选条件的冲突列表查询"""
        # 准备mock查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # 调用方法
        result = self.service.list_conflicts(
            skip=0,
            limit=10,
            status="ACTIVE",
            severity="CRITICAL",
            resource_id=1,
            is_resolved=False,
        )

        # 验证查询被调用
        self.mock_db.query.assert_called_once()
        self.assertEqual(result, [])

    def test_update_conflict_mark_resolved(self):
        """测试标记冲突为已解决"""
        # 准备mock数据
        mock_conflict = MagicMock()
        mock_conflict.id = 1
        mock_conflict.resolved_by = None
        mock_conflict.resolved_at = None
        mock_conflict.status = "ACTIVE"

        # Mock get_conflict方法
        self.service.get_conflict = MagicMock(return_value=mock_conflict)

        # 调用方法
        result = self.service.update_conflict(
            conflict_id=1,
            update_data={"is_resolved": True, "resolution_method": "手动调整"},
            operator_id=100,
            operator_name="测试用户",
        )

        # 验证状态更新
        self.assertIsNotNone(result)
        self.assertEqual(mock_conflict.resolved_by, 100)
        self.assertIsNotNone(mock_conflict.resolved_at)
        self.assertEqual(mock_conflict.status, "RESOLVED")

    # ============================================================================
    # 2. AI调度方案测试
    # ============================================================================

    @patch("app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService")
    def test_generate_suggestions_success(self, mock_ai_service_class):
        """测试成功生成调度方案"""
        # 准备mock数据
        mock_suggestion1 = MagicMock()
        mock_suggestion1.id = 1
        mock_suggestion1.is_recommended = True
        mock_suggestion1.ai_tokens_used = 500

        mock_suggestion2 = MagicMock()
        mock_suggestion2.id = 2
        mock_suggestion2.is_recommended = False
        mock_suggestion2.ai_tokens_used = 300

        mock_ai_service = MagicMock()
        mock_ai_service.generate_scheduling_suggestions.return_value = [
            mock_suggestion1,
            mock_suggestion2,
        ]
        mock_ai_service_class.return_value = mock_ai_service

        service = ResourceSchedulingService(self.mock_db)

        # 调用方法
        result = service.generate_suggestions(
            conflict_id=1,
            max_suggestions=3,
            prefer_minimal_impact=True,
            operator_id=100,
            operator_name="测试用户",
        )

        # 验证结果
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual(result["recommended_id"], 1)
        self.assertEqual(result["total_tokens"], 800)

    def test_review_suggestion_accept(self):
        """测试接受调度方案"""
        # 准备mock数据
        mock_suggestion = MagicMock()
        mock_suggestion.id = 1
        mock_suggestion.status = "PENDING"

        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        # 调用方法
        success, suggestion, error = self.service.review_suggestion(
            suggestion_id=1,
            action="ACCEPT",
            review_comment="方案合理",
            operator_id=100,
            operator_name="测试用户",
        )

        # 验证结果
        self.assertTrue(success)
        self.assertEqual(mock_suggestion.status, "ACCEPTED")
        self.assertEqual(mock_suggestion.reviewed_by, 100)
        self.assertIsNotNone(mock_suggestion.reviewed_at)

    def test_implement_suggestion_success(self):
        """测试执行调度方案"""
        # 准备mock数据
        mock_suggestion = MagicMock()
        mock_suggestion.id = 1
        mock_suggestion.status = "ACCEPTED"
        mock_suggestion.conflict_id = 10

        mock_conflict = MagicMock()
        mock_conflict.id = 10

        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        # Mock数据库查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_conflict

        # 调用方法
        success, suggestion, error = self.service.implement_suggestion(
            suggestion_id=1,
            implementation_result="执行成功",
            operator_id=100,
            operator_name="测试用户",
        )

        # 验证结果
        self.assertTrue(success)
        self.assertEqual(mock_suggestion.status, "IMPLEMENTED")
        self.assertEqual(mock_suggestion.implemented_by, 100)

    # ============================================================================
    # 3. 资源需求预测测试
    # ============================================================================

    @patch("app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService")
    def test_generate_forecast(self, mock_ai_service_class):
        """测试生成资源需求预测"""
        # 准备mock数据
        mock_forecast1 = MagicMock()
        mock_forecast1.gap_severity = "CRITICAL"
        mock_forecast1.demand_gap = 5

        mock_forecast2 = MagicMock()
        mock_forecast2.gap_severity = "NORMAL"
        mock_forecast2.demand_gap = -2

        mock_ai_service = MagicMock()
        mock_ai_service.forecast_resource_demand.return_value = [
            mock_forecast1,
            mock_forecast2,
        ]
        mock_ai_service_class.return_value = mock_ai_service

        service = ResourceSchedulingService(self.mock_db)

        # 调用方法
        result = service.generate_forecast(
            forecast_period="2024-Q1",
            resource_type="DEVELOPER",
            skill_category="Python",
        )

        # 验证结果
        self.assertEqual(len(result["forecasts"]), 2)
        self.assertEqual(result["critical_gaps"], 1)
        self.assertEqual(result["total_hiring"], 5)

    # ============================================================================
    # 4. 资源利用率分析测试
    # ============================================================================

    @patch("app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService")
    def test_analyze_utilization_single_resource(self, mock_ai_service_class):
        """测试单个资源利用率分析"""
        # 准备mock数据
        mock_analysis = MagicMock()
        mock_analysis.resource_id = 1
        mock_analysis.utilization_rate = 85.5
        mock_analysis.is_idle_resource = False
        mock_analysis.is_overloaded = False

        mock_ai_service = MagicMock()
        mock_ai_service.analyze_resource_utilization.return_value = mock_analysis
        mock_ai_service_class.return_value = mock_ai_service

        service = ResourceSchedulingService(self.mock_db)

        # 调用方法
        result = service.analyze_utilization(
            resource_id=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            analysis_period="MONTHLY",
        )

        # 验证结果
        self.assertEqual(len(result["analyses"]), 1)
        self.assertEqual(result["avg_utilization"], 85.5)
        self.assertEqual(result["idle_count"], 0)
        self.assertEqual(result["overloaded_count"], 0)

    @patch("app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService")
    @patch("app.services.resource_scheduling.resource_scheduling_service.User")
    def test_analyze_utilization_all_resources(self, mock_user_model, mock_ai_service_class):
        """测试批量资源利用率分析"""
        # 准备mock用户数据
        mock_user1 = MagicMock()
        mock_user1.id = 1

        mock_user2 = MagicMock()
        mock_user2.id = 2

        # Mock查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_user1, mock_user2]

        # 准备mock分析结果
        mock_analysis1 = MagicMock()
        mock_analysis1.utilization_rate = 90.0
        mock_analysis1.is_idle_resource = False
        mock_analysis1.is_overloaded = True

        mock_analysis2 = MagicMock()
        mock_analysis2.utilization_rate = 30.0
        mock_analysis2.is_idle_resource = True
        mock_analysis2.is_overloaded = False

        mock_ai_service = MagicMock()
        mock_ai_service.analyze_resource_utilization.side_effect = [
            mock_analysis1,
            mock_analysis2,
        ]
        mock_ai_service_class.return_value = mock_ai_service

        service = ResourceSchedulingService(self.mock_db)

        # 调用方法（不指定resource_id，分析所有资源）
        result = service.analyze_utilization(
            resource_id=None,
            start_date="2024-01-01",
            end_date="2024-01-31",
            analysis_period="MONTHLY",
        )

        # 验证结果
        self.assertEqual(len(result["analyses"]), 2)
        self.assertEqual(result["idle_count"], 1)
        self.assertEqual(result["overloaded_count"], 1)
        self.assertEqual(result["avg_utilization"], 60.0)  # (90 + 30) / 2

    # ============================================================================
    # 5. 仪表板统计测试
    # ============================================================================

    def test_get_dashboard_summary(self):
        """测试仪表板摘要数据"""
        # Mock所有统计查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 10
        mock_query.first.return_value = None

        # 调用方法
        result = self.service.get_dashboard_summary()

        # 验证结果结构
        self.assertIn("total_conflicts", result)
        self.assertIn("critical_conflicts", result)
        self.assertIn("total_suggestions", result)
        self.assertIn("avg_utilization", result)

    # ============================================================================
    # 6. 辅助方法测试
    # ============================================================================

    def test_log_action(self):
        """测试操作日志记录"""
        # 调用私有方法
        self.service._log_action(
            action_type="TEST",
            action_desc="测试日志",
            operator_id=100,
            operator_name="测试用户",
            result="SUCCESS",
        )

        # 验证数据库操作被调用
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
