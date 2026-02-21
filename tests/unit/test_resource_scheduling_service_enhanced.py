# -*- coding: utf-8 -*-
"""
增强的资源调度服务单元测试
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from app.models.resource_scheduling import (
    ResourceConflictDetection,
    ResourceDemandForecast,
    ResourceSchedulingLog,
    ResourceSchedulingSuggestion,
    ResourceUtilizationAnalysis,
)
from app.models.user import User
from app.services.resource_scheduling.resource_scheduling_service import (
    ResourceSchedulingService,
)


class TestResourceSchedulingServiceConflictDetection(unittest.TestCase):
    """资源冲突检测相关测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)
        self.service.ai_service = MagicMock()

    def test_detect_conflicts_success(self):
        """测试成功检测资源冲突"""
        # 准备数据
        mock_conflicts = [
            MagicMock(id=1, severity="CRITICAL"),
            MagicMock(id=2, severity="HIGH"),
            MagicMock(id=3, severity="MEDIUM"),
        ]
        self.service.ai_service.detect_resource_conflicts.return_value = mock_conflicts

        # 执行
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="DEVELOPER",
            project_id=100,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_generate_suggestions=False,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertEqual(result["total_conflicts"], 3)
        self.assertEqual(result["critical_conflicts"], 1)
        self.assertEqual(result["suggestions_generated"], 0)
        self.assertIn("detection_time_ms", result)
        self.service.ai_service.detect_resource_conflicts.assert_called_once()

    def test_detect_conflicts_with_auto_suggestions(self):
        """测试检测冲突时自动生成方案"""
        # 准备数据
        mock_conflicts = [
            MagicMock(id=i, severity="CRITICAL") for i in range(1, 8)
        ]
        self.service.ai_service.detect_resource_conflicts.return_value = mock_conflicts
        self.service.ai_service.generate_scheduling_suggestions.return_value = []

        # 执行
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="DEVELOPER",
            project_id=None,
            start_date=None,
            end_date=None,
            auto_generate_suggestions=True,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证 - 应该只为前5个冲突生成方案
        self.assertEqual(result["total_conflicts"], 7)
        self.assertEqual(result["suggestions_generated"], 5)
        self.assertEqual(
            self.service.ai_service.generate_scheduling_suggestions.call_count, 5
        )

    def test_detect_conflicts_auto_suggestions_with_errors(self):
        """测试自动生成方案时部分失败"""
        # 准备数据
        mock_conflicts = [MagicMock(id=i, severity="HIGH") for i in range(1, 4)]
        self.service.ai_service.detect_resource_conflicts.return_value = mock_conflicts

        # 第2个方案生成失败
        self.service.ai_service.generate_scheduling_suggestions.side_effect = [
            None,
            Exception("AI服务错误"),
            None,
        ]

        # 执行
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="DEVELOPER",
            project_id=100,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_generate_suggestions=True,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证 - 应该只统计成功的
        self.assertEqual(result["suggestions_generated"], 2)

    def test_detect_conflicts_no_conflicts(self):
        """测试没有检测到冲突的情况"""
        # 准备数据
        self.service.ai_service.detect_resource_conflicts.return_value = []

        # 执行
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="DEVELOPER",
            project_id=100,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_generate_suggestions=True,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertEqual(result["total_conflicts"], 0)
        self.assertEqual(result["critical_conflicts"], 0)
        self.assertEqual(result["suggestions_generated"], 0)

    def test_list_conflicts_no_filters(self):
        """测试查询冲突列表（无过滤条件）"""
        # 准备数据
        mock_conflicts = [MagicMock(id=i) for i in range(1, 6)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conflicts
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.list_conflicts(skip=0, limit=10)

        # 验证
        self.assertEqual(len(result), 5)
        self.mock_db.query.assert_called_once_with(ResourceConflictDetection)

    def test_list_conflicts_with_all_filters(self):
        """测试查询冲突列表（所有过滤条件）"""
        # 准备数据
        mock_query = MagicMock()
        # filter调用会返回自身以支持链式调用
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        # 执行
        self.service.list_conflicts(
            skip=10,
            limit=20,
            status="ACTIVE",
            severity="CRITICAL",
            resource_id=1,
            is_resolved=False,
        )

        # 验证所有filter都被调用
        self.assertEqual(mock_query.filter.call_count, 4)

    def test_get_conflict_found(self):
        """测试获取冲突详情（找到）"""
        # 准备数据
        mock_conflict = MagicMock(id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_conflict
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_conflict(conflict_id=1)

        # 验证
        self.assertEqual(result.id, 1)

    def test_get_conflict_not_found(self):
        """测试获取冲突详情（未找到）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_conflict(conflict_id=999)

        # 验证
        self.assertIsNone(result)

    def test_update_conflict_success(self):
        """测试更新冲突状态（成功）"""
        # 准备数据
        mock_conflict = MagicMock(id=1, status="ACTIVE")
        self.service.get_conflict = MagicMock(return_value=mock_conflict)

        # 执行
        result = self.service.update_conflict(
            conflict_id=1,
            update_data={"status": "RESOLVED", "resolution_method": "调整时间"},
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(mock_conflict.status, "RESOLVED")
        self.mock_db.commit.assert_called()
        self.mock_db.refresh.assert_called_with(mock_conflict)

    def test_update_conflict_mark_resolved(self):
        """测试标记冲突为已解决"""
        # 准备数据
        mock_conflict = MagicMock(id=1, status="ACTIVE")
        self.service.get_conflict = MagicMock(return_value=mock_conflict)

        # 执行
        result = self.service.update_conflict(
            conflict_id=1,
            update_data={"is_resolved": True},
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertEqual(mock_conflict.resolved_by, 1)
        self.assertIsNotNone(mock_conflict.resolved_at)
        self.assertEqual(mock_conflict.status, "RESOLVED")

    def test_update_conflict_not_found(self):
        """测试更新不存在的冲突"""
        # 准备数据
        self.service.get_conflict = MagicMock(return_value=None)

        # 执行
        result = self.service.update_conflict(
            conflict_id=999,
            update_data={"status": "RESOLVED"},
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertIsNone(result)
        self.mock_db.commit.assert_not_called()

    def test_delete_conflict_success(self):
        """测试删除冲突记录（成功）"""
        # 准备数据
        mock_conflict = MagicMock(id=1)
        self.service.get_conflict = MagicMock(return_value=mock_conflict)

        # 执行
        result = self.service.delete_conflict(conflict_id=1)

        # 验证
        self.assertTrue(result)
        self.mock_db.delete.assert_called_with(mock_conflict)
        self.mock_db.commit.assert_called()

    def test_delete_conflict_not_found(self):
        """测试删除不存在的冲突"""
        # 准备数据
        self.service.get_conflict = MagicMock(return_value=None)

        # 执行
        result = self.service.delete_conflict(conflict_id=999)

        # 验证
        self.assertFalse(result)
        self.mock_db.delete.assert_not_called()


class TestResourceSchedulingServiceSuggestions(unittest.TestCase):
    """AI调度方案推荐相关测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)
        self.service.ai_service = MagicMock()

    def test_generate_suggestions_success(self):
        """测试成功生成调度方案"""
        # 准备数据
        mock_suggestions = [
            MagicMock(id=1, is_recommended=True, ai_tokens_used=100),
            MagicMock(id=2, is_recommended=False, ai_tokens_used=80),
        ]
        self.service.ai_service.generate_scheduling_suggestions.return_value = (
            mock_suggestions
        )

        # 执行
        result = self.service.generate_suggestions(
            conflict_id=1,
            max_suggestions=2,
            prefer_minimal_impact=True,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual(result["recommended_id"], 1)
        self.assertEqual(result["total_tokens"], 180)
        self.assertIn("generation_time_ms", result)

    def test_generate_suggestions_no_recommended(self):
        """测试生成方案但无推荐"""
        # 准备数据
        mock_suggestions = [
            MagicMock(id=1, is_recommended=False, ai_tokens_used=100),
            MagicMock(id=2, is_recommended=False, ai_tokens_used=None),
        ]
        self.service.ai_service.generate_scheduling_suggestions.return_value = (
            mock_suggestions
        )

        # 执行
        result = self.service.generate_suggestions(
            conflict_id=1,
            max_suggestions=2,
            prefer_minimal_impact=False,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertIsNone(result["recommended_id"])
        self.assertEqual(result["total_tokens"], 100)

    def test_list_suggestions_no_filters(self):
        """测试查询方案列表（无过滤）"""
        # 准备数据
        mock_suggestions = [MagicMock(id=i) for i in range(1, 4)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_suggestions
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.list_suggestions(skip=0, limit=10)

        # 验证
        self.assertEqual(len(result), 3)

    def test_list_suggestions_with_filters(self):
        """测试查询方案列表（带过滤）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        # 执行
        self.service.list_suggestions(
            skip=0,
            limit=10,
            conflict_id=1,
            status="ACCEPTED",
            solution_type="RESCHEDULE",
            is_recommended=True,
        )

        # 验证 - 应该有4个filter调用
        self.assertEqual(mock_query.filter.call_count, 4)

    def test_get_suggestion_found(self):
        """测试获取方案详情（找到）"""
        # 准备数据
        mock_suggestion = MagicMock(id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_suggestion
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_suggestion(suggestion_id=1)

        # 验证
        self.assertEqual(result.id, 1)

    def test_get_suggestion_not_found(self):
        """测试获取方案详情（未找到）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_suggestion(suggestion_id=999)

        # 验证
        self.assertIsNone(result)

    def test_review_suggestion_accept(self):
        """测试审核方案（接受）"""
        # 准备数据
        mock_suggestion = MagicMock(id=1, status="PENDING")
        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        # 执行
        success, suggestion, error = self.service.review_suggestion(
            suggestion_id=1,
            action="ACCEPT",
            review_comment="方案可行",
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertTrue(success)
        self.assertEqual(suggestion.status, "ACCEPTED")
        self.assertEqual(suggestion.reviewed_by, 1)
        self.assertIsNotNone(suggestion.reviewed_at)
        self.assertEqual(suggestion.review_comment, "方案可行")

    def test_review_suggestion_reject(self):
        """测试审核方案（拒绝）"""
        # 准备数据
        mock_suggestion = MagicMock(id=1, status="PENDING")
        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        # 执行
        success, suggestion, error = self.service.review_suggestion(
            suggestion_id=1,
            action="REJECT",
            review_comment="影响太大",
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertTrue(success)
        self.assertEqual(suggestion.status, "REJECTED")

    def test_review_suggestion_invalid_action(self):
        """测试审核方案（无效操作）"""
        # 准备数据
        mock_suggestion = MagicMock(id=1)
        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        # 执行
        success, suggestion, error = self.service.review_suggestion(
            suggestion_id=1,
            action="INVALID",
            review_comment=None,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertFalse(success)
        self.assertIn("Invalid action", error)

    def test_review_suggestion_not_found(self):
        """测试审核不存在的方案"""
        # 准备数据
        self.service.get_suggestion = MagicMock(return_value=None)

        # 执行
        success, suggestion, error = self.service.review_suggestion(
            suggestion_id=999,
            action="ACCEPT",
            review_comment=None,
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertFalse(success)
        self.assertIn("not found", error)

    def test_implement_suggestion_success(self):
        """测试执行调度方案（成功）"""
        # 准备数据
        mock_suggestion = MagicMock(
            id=1, status="ACCEPTED", conflict_id=10, solution_type="RESCHEDULE"
        )
        mock_conflict = MagicMock(id=10)
        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_conflict
        self.mock_db.query.return_value = mock_query

        # 执行
        success, suggestion, error = self.service.implement_suggestion(
            suggestion_id=1,
            implementation_result="执行成功",
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertTrue(success)
        self.assertEqual(suggestion.status, "IMPLEMENTED")
        self.assertEqual(suggestion.implemented_by, 1)
        self.assertEqual(suggestion.implementation_result, "执行成功")
        # 验证关联冲突也被解决
        self.assertTrue(mock_conflict.is_resolved)
        self.assertEqual(mock_conflict.status, "RESOLVED")

    def test_implement_suggestion_not_accepted(self):
        """测试执行未接受的方案"""
        # 准备数据
        mock_suggestion = MagicMock(id=1, status="PENDING")
        self.service.get_suggestion = MagicMock(return_value=mock_suggestion)

        # 执行
        success, suggestion, error = self.service.implement_suggestion(
            suggestion_id=1,
            implementation_result="执行成功",
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertFalse(success)
        self.assertIn("ACCEPTED", error)

    def test_implement_suggestion_not_found(self):
        """测试执行不存在的方案"""
        # 准备数据
        self.service.get_suggestion = MagicMock(return_value=None)

        # 执行
        success, suggestion, error = self.service.implement_suggestion(
            suggestion_id=999,
            implementation_result="执行成功",
            operator_id=1,
            operator_name="测试员",
        )

        # 验证
        self.assertFalse(success)
        self.assertIn("not found", error)


class TestResourceSchedulingServiceForecasting(unittest.TestCase):
    """资源需求预测相关测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)
        self.service.ai_service = MagicMock()

    def test_generate_forecast_success(self):
        """测试生成资源需求预测"""
        # 准备数据
        mock_forecasts = [
            MagicMock(gap_severity="SHORTAGE", demand_gap=5),
            MagicMock(gap_severity="CRITICAL", demand_gap=10),
            MagicMock(gap_severity="BALANCED", demand_gap=0),
        ]
        self.service.ai_service.forecast_resource_demand.return_value = mock_forecasts

        # 执行
        result = self.service.generate_forecast(
            forecast_period="Q1_2024",
            resource_type="DEVELOPER",
            skill_category="BACKEND",
        )

        # 验证
        self.assertEqual(len(result["forecasts"]), 3)
        self.assertEqual(result["critical_gaps"], 2)
        self.assertEqual(result["total_hiring"], 15)
        self.assertIn("generation_time_ms", result)

    def test_generate_forecast_no_gaps(self):
        """测试预测无缺口"""
        # 准备数据
        mock_forecasts = [
            MagicMock(gap_severity="BALANCED", demand_gap=0),
            MagicMock(gap_severity="BALANCED", demand_gap=-2),
        ]
        self.service.ai_service.forecast_resource_demand.return_value = mock_forecasts

        # 执行
        result = self.service.generate_forecast(
            forecast_period="Q2_2024", resource_type=None, skill_category=None
        )

        # 验证
        self.assertEqual(result["critical_gaps"], 0)
        self.assertEqual(result["total_hiring"], 0)

    def test_list_forecasts_no_filters(self):
        """测试查询预测列表（无过滤）"""
        # 准备数据
        mock_forecasts = [MagicMock(id=i) for i in range(1, 4)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_forecasts
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.list_forecasts(skip=0, limit=10)

        # 验证
        self.assertEqual(len(result), 3)

    def test_list_forecasts_with_filters(self):
        """测试查询预测列表（带过滤）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        # 执行
        self.service.list_forecasts(
            skip=0, limit=10, forecast_period="Q1_2024", status="ACTIVE"
        )

        # 验证
        self.assertEqual(mock_query.filter.call_count, 2)

    def test_get_forecast_found(self):
        """测试获取预测详情（找到）"""
        # 准备数据
        mock_forecast = MagicMock(id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_forecast
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_forecast(forecast_id=1)

        # 验证
        self.assertEqual(result.id, 1)

    def test_get_forecast_not_found(self):
        """测试获取预测详情（未找到）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_forecast(forecast_id=999)

        # 验证
        self.assertIsNone(result)


class TestResourceSchedulingServiceUtilization(unittest.TestCase):
    """资源利用率分析相关测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)
        self.service.ai_service = MagicMock()

    def test_analyze_utilization_single_resource(self):
        """测试分析单个资源利用率"""
        # 准备数据
        mock_analysis = MagicMock(
            is_idle_resource=False, is_overloaded=True, utilization_rate=85.5
        )
        self.service.ai_service.analyze_resource_utilization.return_value = (
            mock_analysis
        )

        # 执行
        result = self.service.analyze_utilization(
            resource_id=1,
            start_date="2024-01-01",
            end_date="2024-03-31",
            analysis_period="Q1_2024",
        )

        # 验证
        self.assertEqual(len(result["analyses"]), 1)
        self.assertEqual(result["idle_count"], 0)
        self.assertEqual(result["overloaded_count"], 1)
        self.assertEqual(result["avg_utilization"], 85.5)

    def test_analyze_utilization_multiple_resources(self):
        """测试分析多个资源利用率"""
        # 准备数据
        mock_users = [MagicMock(id=i, is_active=True) for i in range(1, 4)]
        mock_query = MagicMock()
        mock_query.filter.return_value.limit.return_value.all.return_value = mock_users
        self.mock_db.query.return_value = mock_query

        mock_analyses = [
            MagicMock(is_idle_resource=True, is_overloaded=False, utilization_rate=20.0),
            MagicMock(
                is_idle_resource=False, is_overloaded=False, utilization_rate=60.0
            ),
            MagicMock(
                is_idle_resource=False, is_overloaded=True, utilization_rate=95.0
            ),
        ]
        self.service.ai_service.analyze_resource_utilization.side_effect = (
            mock_analyses
        )

        # 执行
        result = self.service.analyze_utilization(
            resource_id=None,
            start_date="2024-01-01",
            end_date="2024-03-31",
            analysis_period="Q1_2024",
        )

        # 验证
        self.assertEqual(len(result["analyses"]), 3)
        self.assertEqual(result["idle_count"], 1)
        self.assertEqual(result["overloaded_count"], 1)
        self.assertAlmostEqual(result["avg_utilization"], 58.33, places=1)
        self.assertEqual(result["optimization_opportunities"], 2)

    def test_analyze_utilization_with_errors(self):
        """测试分析时部分资源出错"""
        # 准备数据
        mock_users = [MagicMock(id=i, is_active=True) for i in range(1, 4)]
        mock_query = MagicMock()
        mock_query.filter.return_value.limit.return_value.all.return_value = mock_users
        self.mock_db.query.return_value = mock_query

        # 第2个资源分析失败
        self.service.ai_service.analyze_resource_utilization.side_effect = [
            MagicMock(is_idle_resource=False, is_overloaded=False, utilization_rate=50.0),
            Exception("分析失败"),
            MagicMock(is_idle_resource=True, is_overloaded=False, utilization_rate=10.0),
        ]

        # 执行
        result = self.service.analyze_utilization(
            resource_id=None,
            start_date="2024-01-01",
            end_date="2024-03-31",
            analysis_period="Q1_2024",
        )

        # 验证 - 应该只有2个成功的分析
        self.assertEqual(len(result["analyses"]), 2)

    def test_list_utilization_analyses_no_filters(self):
        """测试查询利用率分析列表（无过滤）"""
        # 准备数据
        mock_analyses = [MagicMock(id=i) for i in range(1, 4)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_analyses
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.list_utilization_analyses(skip=0, limit=10)

        # 验证
        self.assertEqual(len(result), 3)

    def test_list_utilization_analyses_with_filters(self):
        """测试查询利用率分析列表（带过滤）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        # 执行
        self.service.list_utilization_analyses(
            skip=0, limit=10, resource_id=1, is_idle=True, is_overloaded=False
        )

        # 验证
        self.assertEqual(mock_query.filter.call_count, 3)

    def test_get_utilization_analysis_found(self):
        """测试获取利用率分析详情（找到）"""
        # 准备数据
        mock_analysis = MagicMock(id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_analysis
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_utilization_analysis(analysis_id=1)

        # 验证
        self.assertEqual(result.id, 1)

    def test_get_utilization_analysis_not_found(self):
        """测试获取利用率分析详情（未找到）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_utilization_analysis(analysis_id=999)

        # 验证
        self.assertIsNone(result)


class TestResourceSchedulingServiceDashboard(unittest.TestCase):
    """仪表板和统计相关测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)

    def test_get_dashboard_summary(self):
        """测试获取仪表板摘要（简化版本，测试关键字段）"""
        # 由于dashboard_summary方法有非常复杂的查询链，我们简化测试
        # 只验证方法能正常运行并返回所有必需的字段
        
        # Mock所有查询返回合理的值
        def mock_func_count_scalar():
            mock_q = MagicMock()
            mock_q.scalar.return_value = 10
            return mock_q
            
        def mock_filter_scalar():
            mock_q = MagicMock()
            mock_q.scalar.return_value = 5
            return mock_q
        
        mock_query = MagicMock()
        # 简化：所有func.count查询返回10，filter查询返回5
        mock_query.scalar.return_value = 10
        mock_query.filter.return_value = mock_filter_scalar()
        
        # order_by查询（最近时间）
        mock_conflict = MagicMock(created_at=datetime(2024, 1, 15))
        mock_analysis = MagicMock(created_at=datetime(2024, 1, 16))
        
        order_results = [mock_conflict, mock_analysis]
        order_index = [0]
        
        def mock_order_by(*args):
            mock_chain = MagicMock()
            val = order_results[order_index[0]] if order_index[0] < len(order_results) else None
            order_index[0] += 1
            mock_chain.first.return_value = val
            return mock_chain
        
        mock_query.order_by = mock_order_by
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.get_dashboard_summary()

        # 验证返回结构完整
        expected_keys = [
            "total_conflicts", "critical_conflicts", "unresolved_conflicts",
            "total_suggestions", "pending_suggestions", "implemented_suggestions",
            "idle_resources", "overloaded_resources", "avg_utilization",
            "forecasts_count", "critical_gaps", "hiring_needed",
            "last_detection_time", "last_analysis_time"
        ]
        
        for key in expected_keys:
            self.assertIn(key, result, f"Missing key: {key}")
        
        # 验证时间字段
        self.assertEqual(result["last_detection_time"], datetime(2024, 1, 15))
        self.assertEqual(result["last_analysis_time"], datetime(2024, 1, 16))

    def test_get_dashboard_summary_empty(self):
        """测试获取空的仪表板摘要"""
        # 准备数据 - 所有查询返回0或None
        def mock_filter_chain(*args):
            mock_chain = MagicMock()
            mock_chain.scalar.return_value = 0
            return mock_chain
            
        def mock_order_by_chain(*args):
            mock_chain = MagicMock()
            mock_chain.first.return_value = None
            return mock_chain
        
        mock_base_query = MagicMock()
        mock_base_query.filter.side_effect = mock_filter_chain
        mock_base_query.scalar.return_value = 0
        mock_base_query.order_by.side_effect = mock_order_by_chain
        
        self.mock_db.query.return_value = mock_base_query

        # 执行
        result = self.service.get_dashboard_summary()

        # 验证
        self.assertEqual(result["total_conflicts"], 0)
        self.assertEqual(result["hiring_needed"], 0)
        self.assertIsNone(result["last_detection_time"])
        self.assertIsNone(result["last_analysis_time"])

    def test_list_logs_no_filters(self):
        """测试查询操作日志（无过滤）"""
        # 准备数据
        mock_logs = [MagicMock(id=i) for i in range(1, 6)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_logs
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.list_logs(skip=0, limit=10)

        # 验证
        self.assertEqual(len(result), 5)
        self.mock_db.query.assert_called_with(ResourceSchedulingLog)

    def test_list_logs_with_filters(self):
        """测试查询操作日志（带过滤）"""
        # 准备数据
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        # 执行
        self.service.list_logs(
            skip=0, limit=10, action_type="DETECT", conflict_id=1
        )

        # 验证
        self.assertEqual(mock_query.filter.call_count, 2)


class TestResourceSchedulingServiceLogging(unittest.TestCase):
    """日志记录相关测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ResourceSchedulingService(self.mock_db)

    def test_log_action_basic(self):
        """测试基本日志记录"""
        # 执行
        self.service._log_action(
            action_type="DETECT",
            action_desc="检测资源冲突",
            operator_id=1,
            operator_name="测试员",
            result="SUCCESS",
        )

        # 验证
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

        # 验证添加的日志对象
        call_args = self.mock_db.add.call_args[0][0]
        self.assertIsInstance(call_args, ResourceSchedulingLog)
        self.assertEqual(call_args.action_type, "DETECT")
        self.assertEqual(call_args.operator_id, 1)

    def test_log_action_with_all_fields(self):
        """测试包含所有字段的日志记录"""
        # 执行
        self.service._log_action(
            conflict_id=1,
            suggestion_id=2,
            action_type="IMPLEMENT",
            action_desc="执行调度方案",
            operator_id=1,
            operator_name="测试员",
            result="SUCCESS",
            execution_time_ms=500,
            ai_tokens_used=1000,
            error_message=None,
        )

        # 验证
        call_args = self.mock_db.add.call_args[0][0]
        self.assertEqual(call_args.conflict_id, 1)
        self.assertEqual(call_args.suggestion_id, 2)
        self.assertEqual(call_args.execution_time_ms, 500)
        self.assertEqual(call_args.ai_tokens_used, 1000)

    def test_log_action_failure(self):
        """测试记录失败操作日志"""
        # 执行
        self.service._log_action(
            action_type="DETECT",
            action_desc="检测失败",
            operator_id=1,
            operator_name="测试员",
            result="FAILURE",
            error_message="数据库连接失败",
        )

        # 验证
        call_args = self.mock_db.add.call_args[0][0]
        self.assertEqual(call_args.result, "FAILURE")
        self.assertEqual(call_args.error_message, "数据库连接失败")


if __name__ == "__main__":
    unittest.main()
