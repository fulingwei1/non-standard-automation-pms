# -*- coding: utf-8 -*-
"""
资源调度服务单元测试

策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过

目标：覆盖率 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from sqlalchemy.orm import Session

from app.models.resource_scheduling import (
    ResourceConflictDetection,
    ResourceSchedulingSuggestion,
    ResourceDemandForecast,
    ResourceUtilizationAnalysis,
    ResourceSchedulingLog,
)
from app.models.user import User
from app.services.resource_scheduling.resource_scheduling_service import ResourceSchedulingService


class TestResourceSchedulingService(unittest.TestCase):
    """资源调度服务测试"""

    def setUp(self):
        """测试前置设置"""
        # Mock数据库会话
        self.mock_db = MagicMock(spec=Session)
        
        # Mock AI服务
        with patch('app.services.resource_scheduling.resource_scheduling_service.ResourceSchedulingAIService'):
            self.service = ResourceSchedulingService(self.mock_db)
            self.service.ai_service = MagicMock()

    # ============================================================================
    # 1. 资源冲突检测测试
    # ============================================================================

    def test_detect_conflicts_success(self):
        """测试成功检测资源冲突"""
        # 准备mock冲突数据
        mock_conflicts = [
            self._create_mock_conflict(1, "CRITICAL"),
            self._create_mock_conflict(2, "MEDIUM"),
            self._create_mock_conflict(3, "CRITICAL"),
        ]
        
        self.service.ai_service.detect_resource_conflicts.return_value = mock_conflicts
        
        # 执行检测
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="PERSON",
            project_id=None,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_generate_suggestions=False,
            operator_id=1,
            operator_name="张三",
        )
        
        # 验证结果
        self.assertEqual(result["total_conflicts"], 3)
        self.assertEqual(result["critical_conflicts"], 2)
        self.assertEqual(len(result["conflicts"]), 3)
        self.assertIn("detection_time_ms", result)
        
        # 验证AI服务调用
        self.service.ai_service.detect_resource_conflicts.assert_called_once()

    def test_detect_conflicts_with_auto_suggestions(self):
        """测试检测冲突并自动生成方案"""
        mock_conflicts = [
            self._create_mock_conflict(i, "CRITICAL") for i in range(1, 8)
        ]
        
        self.service.ai_service.detect_resource_conflicts.return_value = mock_conflicts
        self.service.ai_service.generate_scheduling_suggestions.return_value = []
        
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="PERSON",
            project_id=None,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_generate_suggestions=True,
            operator_id=1,
            operator_name="张三",
        )
        
        # 应该只为前5个冲突生成方案
        self.assertEqual(result["suggestions_generated"], 5)
        self.assertEqual(self.service.ai_service.generate_scheduling_suggestions.call_count, 5)

    def test_detect_conflicts_no_conflicts(self):
        """测试无冲突情况"""
        self.service.ai_service.detect_resource_conflicts.return_value = []
        
        result = self.service.detect_conflicts(
            resource_id=1,
            resource_type="PERSON",
            project_id=None,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_generate_suggestions=False,
            operator_id=1,
            operator_name="张三",
        )
        
        self.assertEqual(result["total_conflicts"], 0)
        self.assertEqual(result["critical_conflicts"], 0)
        self.assertEqual(result["suggestions_generated"], 0)

    def test_list_conflicts_with_filters(self):
        """测试查询冲突列表（带过滤）"""
        mock_query = self._setup_query_mock([
            self._create_mock_conflict(1, "CRITICAL"),
            self._create_mock_conflict(2, "MEDIUM"),
        ])
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.list_conflicts(
            skip=0,
            limit=10,
            status="DETECTED",
            severity="CRITICAL",
            resource_id=1,
            is_resolved=False,
        )
        
        self.assertEqual(len(result), 2)
        
        # 验证调用了4次filter（每个过滤条件一次）
        self.assertEqual(mock_query.filter.call_count, 4)

    def test_list_conflicts_no_filters(self):
        """测试查询冲突列表（无过滤）"""
        mock_query = self._setup_query_mock([])
        self.mock_db.query.return_value = mock_query
        
        result = self.service.list_conflicts(skip=0, limit=10)
        
        self.assertIsInstance(result, list)

    def test_get_conflict_found(self):
        """测试获取单个冲突（存在）"""
        mock_conflict = self._create_mock_conflict(1, "CRITICAL")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_conflict
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_conflict(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    def test_get_conflict_not_found(self):
        """测试获取单个冲突（不存在）"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_conflict(999)
        
        self.assertIsNone(result)

    def test_update_conflict_success(self):
        """测试更新冲突状态"""
        mock_conflict = self._create_mock_conflict(1, "CRITICAL")
        
        with patch.object(self.service, 'get_conflict', return_value=mock_conflict):
            result = self.service.update_conflict(
                conflict_id=1,
                update_data={"status": "ANALYZING"},
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertIsNotNone(result)
        self.assertEqual(mock_conflict.status, "ANALYZING")
        self.mock_db.commit.assert_called()
        self.mock_db.refresh.assert_called_with(mock_conflict)

    def test_update_conflict_mark_resolved(self):
        """测试标记冲突为已解决"""
        mock_conflict = self._create_mock_conflict(1, "CRITICAL")
        
        with patch.object(self.service, 'get_conflict', return_value=mock_conflict):
            result = self.service.update_conflict(
                conflict_id=1,
                update_data={"is_resolved": True},
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertTrue(mock_conflict.is_resolved)
        self.assertEqual(mock_conflict.resolved_by, 1)
        self.assertEqual(mock_conflict.status, "RESOLVED")
        self.assertIsNotNone(mock_conflict.resolved_at)

    def test_update_conflict_not_found(self):
        """测试更新不存在的冲突"""
        with patch.object(self.service, 'get_conflict', return_value=None):
            result = self.service.update_conflict(
                conflict_id=999,
                update_data={"status": "RESOLVED"},
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertIsNone(result)

    def test_delete_conflict_success(self):
        """测试删除冲突"""
        mock_conflict = self._create_mock_conflict(1, "CRITICAL")
        
        with patch.object(self.service, 'get_conflict', return_value=mock_conflict):
            result = self.service.delete_conflict(1)
        
        self.assertTrue(result)
        self.mock_db.delete.assert_called_with(mock_conflict)
        self.mock_db.commit.assert_called()

    def test_delete_conflict_not_found(self):
        """测试删除不存在的冲突"""
        with patch.object(self.service, 'get_conflict', return_value=None):
            result = self.service.delete_conflict(999)
        
        self.assertFalse(result)

    # ============================================================================
    # 2. AI调度方案推荐测试
    # ============================================================================

    def test_generate_suggestions_success(self):
        """测试生成AI调度方案"""
        mock_suggestions = [
            self._create_mock_suggestion(1, "SHIFT_TIMELINE", True, 100),
            self._create_mock_suggestion(2, "REALLOCATE", False, 50),
        ]
        
        self.service.ai_service.generate_scheduling_suggestions.return_value = mock_suggestions
        
        result = self.service.generate_suggestions(
            conflict_id=1,
            max_suggestions=3,
            prefer_minimal_impact=True,
            operator_id=1,
            operator_name="张三",
        )
        
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual(result["recommended_id"], 1)
        self.assertEqual(result["total_tokens"], 150)
        self.assertIn("generation_time_ms", result)

    def test_generate_suggestions_no_recommended(self):
        """测试生成方案但无推荐"""
        mock_suggestions = [
            self._create_mock_suggestion(1, "SHIFT_TIMELINE", False, 100),
        ]
        
        self.service.ai_service.generate_scheduling_suggestions.return_value = mock_suggestions
        
        result = self.service.generate_suggestions(
            conflict_id=1,
            max_suggestions=3,
            prefer_minimal_impact=False,
            operator_id=1,
            operator_name="张三",
        )
        
        self.assertIsNone(result["recommended_id"])

    def test_list_suggestions_with_filters(self):
        """测试查询方案列表（带过滤）"""
        mock_query = self._setup_query_mock([
            self._create_mock_suggestion(1, "SHIFT_TIMELINE", True),
        ])
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.list_suggestions(
            skip=0,
            limit=10,
            conflict_id=1,
            status="PENDING",
            solution_type="SHIFT_TIMELINE",
            is_recommended=True,
        )
        
        self.assertEqual(len(result), 1)

    def test_get_suggestion_found(self):
        """测试获取单个方案"""
        mock_suggestion = self._create_mock_suggestion(1, "SHIFT_TIMELINE", True)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_suggestion
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_suggestion(1)
        
        self.assertIsNotNone(result)

    def test_review_suggestion_accept(self):
        """测试审核通过方案"""
        mock_suggestion = self._create_mock_suggestion(1, "SHIFT_TIMELINE", True)
        
        with patch.object(self.service, 'get_suggestion', return_value=mock_suggestion):
            success, result, error = self.service.review_suggestion(
                suggestion_id=1,
                action="ACCEPT",
                review_comment="方案可行",
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(mock_suggestion.status, "ACCEPTED")
        self.assertEqual(mock_suggestion.reviewed_by, 1)
        self.assertEqual(mock_suggestion.review_comment, "方案可行")

    def test_review_suggestion_reject(self):
        """测试审核拒绝方案"""
        mock_suggestion = self._create_mock_suggestion(1, "SHIFT_TIMELINE", True)
        
        with patch.object(self.service, 'get_suggestion', return_value=mock_suggestion):
            success, result, error = self.service.review_suggestion(
                suggestion_id=1,
                action="REJECT",
                review_comment="方案不合理",
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertTrue(success)
        self.assertEqual(mock_suggestion.status, "REJECTED")

    def test_review_suggestion_invalid_action(self):
        """测试审核方案（无效操作）"""
        mock_suggestion = self._create_mock_suggestion(1, "SHIFT_TIMELINE", True)
        
        with patch.object(self.service, 'get_suggestion', return_value=mock_suggestion):
            success, result, error = self.service.review_suggestion(
                suggestion_id=1,
                action="INVALID",
                review_comment=None,
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertFalse(success)
        self.assertIn("Invalid action", error)

    def test_review_suggestion_not_found(self):
        """测试审核不存在的方案"""
        with patch.object(self.service, 'get_suggestion', return_value=None):
            success, result, error = self.service.review_suggestion(
                suggestion_id=999,
                action="ACCEPT",
                review_comment=None,
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertFalse(success)
        self.assertIn("not found", error)

    def test_implement_suggestion_success(self):
        """测试执行调度方案"""
        mock_suggestion = self._create_mock_suggestion(1, "SHIFT_TIMELINE", True)
        mock_suggestion.status = "ACCEPTED"
        mock_suggestion.conflict_id = 1
        
        mock_conflict = self._create_mock_conflict(1, "CRITICAL")
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_conflict
        
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.service, 'get_suggestion', return_value=mock_suggestion):
            success, result, error = self.service.implement_suggestion(
                suggestion_id=1,
                implementation_result="方案已成功执行",
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(mock_suggestion.status, "IMPLEMENTED")
        self.assertEqual(mock_suggestion.implemented_by, 1)
        self.assertEqual(mock_suggestion.implementation_result, "方案已成功执行")
        
        # 验证关联冲突也被标记为已解决
        self.assertTrue(mock_conflict.is_resolved)
        self.assertEqual(mock_conflict.status, "RESOLVED")

    def test_implement_suggestion_not_accepted(self):
        """测试执行未审核通过的方案"""
        mock_suggestion = self._create_mock_suggestion(1, "SHIFT_TIMELINE", True)
        mock_suggestion.status = "PENDING"
        
        with patch.object(self.service, 'get_suggestion', return_value=mock_suggestion):
            success, result, error = self.service.implement_suggestion(
                suggestion_id=1,
                implementation_result="方案已执行",
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertFalse(success)
        self.assertIn("ACCEPTED", error)

    def test_implement_suggestion_not_found(self):
        """测试执行不存在的方案"""
        with patch.object(self.service, 'get_suggestion', return_value=None):
            success, result, error = self.service.implement_suggestion(
                suggestion_id=999,
                implementation_result="方案已执行",
                operator_id=1,
                operator_name="张三",
            )
        
        self.assertFalse(success)
        self.assertIn("not found", error)

    # ============================================================================
    # 3. 资源需求预测测试
    # ============================================================================

    def test_generate_forecast_success(self):
        """测试生成资源需求预测"""
        mock_forecasts = [
            self._create_mock_forecast(1, "SHORTAGE", 5),
            self._create_mock_forecast(2, "BALANCED", 0),
            self._create_mock_forecast(3, "CRITICAL", 10),
        ]
        
        self.service.ai_service.forecast_resource_demand.return_value = mock_forecasts
        
        result = self.service.generate_forecast(
            forecast_period="2024-Q1",
            resource_type="PERSON",
            skill_category="开发",
        )
        
        self.assertEqual(len(result["forecasts"]), 3)
        self.assertEqual(result["critical_gaps"], 2)
        self.assertEqual(result["total_hiring"], 15)
        self.assertIn("generation_time_ms", result)

    def test_generate_forecast_no_gaps(self):
        """测试生成预测（无缺口）"""
        mock_forecasts = [
            self._create_mock_forecast(1, "BALANCED", 0),
        ]
        
        self.service.ai_service.forecast_resource_demand.return_value = mock_forecasts
        
        result = self.service.generate_forecast(
            forecast_period="2024-Q1",
            resource_type="PERSON",
            skill_category="测试",
        )
        
        self.assertEqual(result["critical_gaps"], 0)
        self.assertEqual(result["total_hiring"], 0)

    def test_list_forecasts_with_filters(self):
        """测试查询预测列表（带过滤）"""
        mock_query = self._setup_query_mock([
            self._create_mock_forecast(1, "SHORTAGE", 5),
        ])
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.list_forecasts(
            skip=0,
            limit=10,
            forecast_period="2024-Q1",
            status="ACTIVE",
        )
        
        self.assertEqual(len(result), 1)

    def test_get_forecast_found(self):
        """测试获取单个预测"""
        mock_forecast = self._create_mock_forecast(1, "SHORTAGE", 5)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_forecast
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_forecast(1)
        
        self.assertIsNotNone(result)

    # ============================================================================
    # 4. 资源利用率分析测试
    # ============================================================================

    def test_analyze_utilization_single_resource(self):
        """测试分析单个资源利用率"""
        mock_analysis = self._create_mock_analysis(1, 0.85, False, False)
        
        self.service.ai_service.analyze_resource_utilization.return_value = mock_analysis
        
        result = self.service.analyze_utilization(
            resource_id=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            analysis_period="MONTHLY",
        )
        
        self.assertEqual(len(result["analyses"]), 1)
        self.assertEqual(result["idle_count"], 0)
        self.assertEqual(result["overloaded_count"], 0)
        self.assertAlmostEqual(result["avg_utilization"], 0.85)

    def test_analyze_utilization_multiple_resources(self):
        """测试分析多个资源利用率"""
        mock_users = [
            self._create_mock_user(1, "张三", True),
            self._create_mock_user(2, "李四", True),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.limit.return_value.all.return_value = mock_users
        
        self.mock_db.query.return_value = mock_query
        
        # 模拟两次AI分析调用
        self.service.ai_service.analyze_resource_utilization.side_effect = [
            self._create_mock_analysis(1, 0.3, True, False),
            self._create_mock_analysis(2, 1.2, False, True),
        ]
        
        result = self.service.analyze_utilization(
            resource_id=None,
            start_date="2024-01-01",
            end_date="2024-01-31",
            analysis_period="MONTHLY",
        )
        
        self.assertEqual(len(result["analyses"]), 2)
        self.assertEqual(result["idle_count"], 1)
        self.assertEqual(result["overloaded_count"], 1)
        self.assertEqual(result["optimization_opportunities"], 2)

    def test_analyze_utilization_empty_result(self):
        """测试分析利用率（无数据）"""
        mock_query = MagicMock()
        mock_query.filter.return_value.limit.return_value.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.analyze_utilization(
            resource_id=None,
            start_date="2024-01-01",
            end_date="2024-01-31",
            analysis_period="MONTHLY",
        )
        
        self.assertEqual(len(result["analyses"]), 0)
        self.assertEqual(result["avg_utilization"], 0)

    def test_list_utilization_analyses_with_filters(self):
        """测试查询利用率分析列表（带过滤）"""
        mock_query = self._setup_query_mock([
            self._create_mock_analysis(1, 0.85, False, False),
        ])
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.list_utilization_analyses(
            skip=0,
            limit=10,
            resource_id=1,
            is_idle=False,
            is_overloaded=False,
        )
        
        self.assertEqual(len(result), 1)

    def test_get_utilization_analysis_found(self):
        """测试获取单个利用率分析"""
        mock_analysis = self._create_mock_analysis(1, 0.85, False, False)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_analysis
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_utilization_analysis(1)
        
        self.assertIsNotNone(result)

    # ============================================================================
    # 5. 仪表板和统计测试
    # ============================================================================

    def test_get_dashboard_summary_full(self):
        """测试获取完整的仪表板摘要"""
        # Mock最近检测和分析时间
        mock_conflict = self._create_mock_conflict(1, "CRITICAL")
        mock_analysis = self._create_mock_analysis(1, 0.85, False, False)
        
        # 配置mock query链
        # 每次调用db.query()都会返回一个新的mock对象
        query_mocks = []
        
        # 创建12个scalar查询的mock + 2个order_by查询的mock
        scalar_values = [10, 3, 7, 15, 5, 8, 2, 3, 0.75, 4, 2, 12]
        
        for value in scalar_values:
            mock_q = MagicMock()
            if isinstance(value, (int, float)):
                # 处理filter().scalar()链
                if value in [3, 7, 5, 8, 2, 3, 4, 2]:  # 需要filter的查询
                    mock_q.filter.return_value.scalar.return_value = value
                else:  # 不需要filter的查询
                    mock_q.scalar.return_value = value
                    # sum查询需要特殊处理
                    if value == 12:
                        mock_q.filter.return_value.scalar.return_value = value
            query_mocks.append(mock_q)
        
        # 最后两个查询是order_by().first()
        mock_q1 = MagicMock()
        mock_q1.order_by.return_value.first.return_value = mock_conflict
        query_mocks.append(mock_q1)
        
        mock_q2 = MagicMock()
        mock_q2.order_by.return_value.first.return_value = mock_analysis
        query_mocks.append(mock_q2)
        
        self.mock_db.query.side_effect = query_mocks
        
        result = self.service.get_dashboard_summary()
        
        # 验证基本统计
        self.assertEqual(result["total_conflicts"], 10)
        self.assertEqual(result["critical_conflicts"], 3)
        self.assertEqual(result["unresolved_conflicts"], 7)
        self.assertEqual(result["total_suggestions"], 15)
        self.assertEqual(result["pending_suggestions"], 5)
        self.assertEqual(result["implemented_suggestions"], 8)
        self.assertEqual(result["idle_resources"], 2)
        self.assertEqual(result["overloaded_resources"], 3)
        self.assertEqual(result["avg_utilization"], 0.75)
        self.assertEqual(result["forecasts_count"], 4)
        self.assertEqual(result["critical_gaps"], 2)
        self.assertEqual(result["hiring_needed"], 12)

    def test_get_dashboard_summary_empty(self):
        """测试获取仪表板摘要（无数据）"""
        # 配置所有查询返回0或None
        query_mocks = []
        
        # 12个scalar查询，全部返回0
        for _ in range(12):
            mock_q = MagicMock()
            mock_q.scalar.return_value = 0
            mock_q.filter.return_value.scalar.return_value = 0
            query_mocks.append(mock_q)
        
        # 2个order_by().first()查询，返回None
        mock_q1 = MagicMock()
        mock_q1.order_by.return_value.first.return_value = None
        query_mocks.append(mock_q1)
        
        mock_q2 = MagicMock()
        mock_q2.order_by.return_value.first.return_value = None
        query_mocks.append(mock_q2)
        
        self.mock_db.query.side_effect = query_mocks
        
        result = self.service.get_dashboard_summary()
        
        self.assertEqual(result["total_conflicts"], 0)
        self.assertIsNone(result["last_detection_time"])
        self.assertIsNone(result["last_analysis_time"])

    def test_list_logs_with_filters(self):
        """测试查询操作日志（带过滤）"""
        mock_logs = [
            self._create_mock_log(1, "DETECT"),
            self._create_mock_log(2, "SUGGEST"),
        ]
        
        mock_query = self._setup_query_mock(mock_logs)
        self.mock_db.query.return_value = mock_query
        
        result = self.service.list_logs(
            skip=0,
            limit=10,
            action_type="DETECT",
            conflict_id=1,
        )
        
        self.assertEqual(len(result), 2)

    # ============================================================================
    # 6. 私有方法测试
    # ============================================================================

    def test_log_action(self):
        """测试记录操作日志"""
        self.service._log_action(
            action_type="DETECT",
            action_desc="检测资源冲突",
            operator_id=1,
            operator_name="张三",
            result="SUCCESS",
            conflict_id=1,
            execution_time_ms=150,
        )
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # 验证添加的日志对象
        log_obj = self.mock_db.add.call_args[0][0]
        self.assertIsInstance(log_obj, ResourceSchedulingLog)
        self.assertEqual(log_obj.action_type, "DETECT")
        self.assertEqual(log_obj.operator_id, 1)

    # ============================================================================
    # 辅助方法
    # ============================================================================

    def _create_mock_conflict(self, conflict_id, severity):
        """创建mock冲突对象"""
        conflict = MagicMock(spec=ResourceConflictDetection)
        conflict.id = conflict_id
        conflict.severity = severity
        conflict.status = "DETECTED"
        conflict.is_resolved = False
        conflict.created_at = datetime.now()
        conflict.updated_at = datetime.now()
        return conflict

    def _create_mock_suggestion(self, suggestion_id, solution_type, is_recommended, tokens=0):
        """创建mock方案对象"""
        suggestion = MagicMock(spec=ResourceSchedulingSuggestion)
        suggestion.id = suggestion_id
        suggestion.solution_type = solution_type
        suggestion.is_recommended = is_recommended
        suggestion.ai_tokens_used = tokens
        suggestion.status = "PENDING"
        suggestion.conflict_id = 1
        suggestion.rank_order = 1
        return suggestion

    def _create_mock_forecast(self, forecast_id, gap_severity, demand_gap):
        """创建mock预测对象"""
        forecast = MagicMock(spec=ResourceDemandForecast)
        forecast.id = forecast_id
        forecast.gap_severity = gap_severity
        forecast.demand_gap = demand_gap
        forecast.status = "ACTIVE"
        forecast.created_at = datetime.now()
        return forecast

    def _create_mock_analysis(self, analysis_id, utilization_rate, is_idle, is_overloaded):
        """创建mock利用率分析对象"""
        analysis = MagicMock(spec=ResourceUtilizationAnalysis)
        analysis.id = analysis_id
        analysis.resource_id = analysis_id
        analysis.utilization_rate = utilization_rate
        analysis.is_idle_resource = is_idle
        analysis.is_overloaded = is_overloaded
        analysis.created_at = datetime.now()
        return analysis

    def _create_mock_user(self, user_id, name, is_active):
        """创建mock用户对象"""
        user = MagicMock(spec=User)
        user.id = user_id
        user.name = name
        user.is_active = is_active
        return user

    def _create_mock_log(self, log_id, action_type):
        """创建mock日志对象"""
        log = MagicMock(spec=ResourceSchedulingLog)
        log.id = log_id
        log.action_type = action_type
        log.created_at = datetime.now()
        return log

    def _setup_query_mock(self, return_data):
        """设置query mock链"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = return_data
        return mock_query


if __name__ == "__main__":
    unittest.main()
