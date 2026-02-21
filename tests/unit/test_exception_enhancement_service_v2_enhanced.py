# -*- coding: utf-8 -*-
"""
异常处理增强服务单元测试 - Enhanced V2
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from fastapi import HTTPException

from app.services.production.exception.exception_enhancement_service import ExceptionEnhancementService
from app.models.production import (
    ExceptionHandlingFlow,
    ExceptionKnowledge,
    ExceptionPDCA,
    FlowStatus,
    EscalationLevel,
    PDCAStage,
    ProductionException,
)
from app.models.user import User


class TestExceptionEnhancementService(unittest.TestCase):
    """异常处理增强服务测试套件"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()

    # ==================== 异常升级测试 ====================

    def test_escalate_exception_create_new_flow(self):
        """测试创建新处理流程的异常升级"""
        # 准备测试数据
        exception_id = 1
        exception = ProductionException(
            id=exception_id,
            exception_no="EXC-001",
            title="测试异常",
            status="REPORTED"
        )
        
        # 创建一个有id的flow用于refresh后返回
        new_flow = ExceptionHandlingFlow(
            id=100,
            exception_id=exception_id,
            status=FlowStatus.PROCESSING,
            escalation_level=EscalationLevel.LEVEL_2,
            escalation_reason="问题复杂需要升级",
            escalated_at=datetime.now(),
            pending_at=datetime.now(),
            processing_at=datetime.now(),
            escalated_to_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock数据库查询
        with patch('app.utils.db_helpers.get_or_404', return_value=exception):
            # Mock flow查询返回None（不存在）
            flow_query = MagicMock()
            flow_query.filter.return_value.first.return_value = None
            
            # Mock User查询
            escalated_user = User(id=2, username="张三")
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = escalated_user
            
            # 配置query的链式调用
            def query_side_effect(model):
                if model == ExceptionHandlingFlow:
                    return flow_query
                elif model == User:
                    return user_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            
            # Mock refresh返回完整的flow
            self.db.refresh.side_effect = lambda obj: setattr(obj, 'id', 100) or None
            
            # 执行升级
            result = self.service.escalate_exception(
                exception_id=exception_id,
                escalation_level="LEVEL_2",
                reason="问题复杂需要升级",
                escalated_to_id=2
            )
            
            # 验证
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()
            self.assertEqual(result.escalation_level, "LEVEL_2")
            self.assertEqual(result.escalation_reason, "问题复杂需要升级")
            self.assertEqual(result.escalated_to_name, "张三")

    def test_escalate_exception_update_existing_flow(self):
        """测试更新已存在的处理流程"""
        exception_id = 1
        exception = ProductionException(
            id=exception_id,
            exception_no="EXC-002",
            title="测试异常2",
            status="PROCESSING"  # 使用PROCESSING状态，不触发状态更新逻辑
        )
        
        # 已存在的flow
        existing_flow = ExceptionHandlingFlow(
            id=10,
            exception_id=exception_id,
            status=FlowStatus.PROCESSING,
            pending_at=datetime.now(),
            escalation_level=EscalationLevel.NONE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=exception):
            flow_query = MagicMock()
            flow_query.filter.return_value.first.return_value = existing_flow
            
            # Mock User查询
            escalated_user = User(id=3, username="李四")
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = escalated_user
            
            def query_side_effect(model):
                if model == ExceptionHandlingFlow:
                    return flow_query
                elif model == User:
                    return user_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.escalate_exception(
                exception_id=exception_id,
                escalation_level="LEVEL_3",
                reason="紧急问题",
                escalated_to_id=3
            )
            
            # 验证flow被更新
            self.db.add.assert_not_called()
            self.db.commit.assert_called_once()
            self.assertEqual(existing_flow.escalation_level, EscalationLevel.LEVEL_3)
            self.assertEqual(existing_flow.escalation_reason, "紧急问题")
            self.assertEqual(existing_flow.escalated_to_id, 3)

    def test_escalate_exception_invalid_level(self):
        """测试无效的升级级别使用默认值"""
        exception_id = 1
        exception = ProductionException(
            id=exception_id,
            exception_no="EXC-004",
            status="REPORTED"
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=exception):
            flow_query = MagicMock()
            flow_query.filter.return_value.first.return_value = None
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = None
            
            def query_side_effect(model):
                if model == ExceptionHandlingFlow:
                    return flow_query
                elif model == User:
                    return user_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            self.db.refresh.side_effect = lambda obj: setattr(obj, 'id', 102) or None
            
            result = self.service.escalate_exception(
                exception_id=exception_id,
                escalation_level="INVALID_LEVEL",
                reason="测试",
                escalated_to_id=None
            )
            
            # 应该使用默认的LEVEL_1
            added_flow = self.db.add.call_args[0][0]
            self.assertEqual(added_flow.escalation_level, EscalationLevel.LEVEL_1)

    def test_escalate_exception_without_escalated_user(self):
        """测试没有指定升级人员的情况"""
        exception = ProductionException(
            id=1,
            exception_no="EXC-003",
            status="REPORTED"
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=exception):
            flow_query = MagicMock()
            flow_query.filter.return_value.first.return_value = None
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = None
            
            def query_side_effect(model):
                if model == ExceptionHandlingFlow:
                    return flow_query
                elif model == User:
                    return user_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            self.db.refresh.side_effect = lambda obj: setattr(obj, 'id', 101) or None
            
            result = self.service.escalate_exception(
                exception_id=1,
                escalation_level="LEVEL_1",
                reason="测试",
                escalated_to_id=None
            )
            
            self.assertIsNone(result.escalated_to_name)

    # ==================== 处理流程跟踪测试 ====================

    def test_get_exception_flow_success(self):
        """测试获取异常处理流程成功"""
        exception_id = 1
        
        # 构造完整的flow对象
        exception = ProductionException(
            id=exception_id,
            exception_no="EXC-003",
            title="测试异常3"
        )
        escalated_user = User(id=2, username="张三")
        verifier = User(id=3, username="验证员")
        
        flow = ExceptionHandlingFlow(
            id=20,
            exception_id=exception_id,
            status=FlowStatus.RESOLVED,
            escalation_level=EscalationLevel.LEVEL_2,
            escalation_reason="需要技术支持",
            escalated_at=datetime.now(),
            pending_at=datetime.now() - timedelta(hours=2),
            processing_at=datetime.now() - timedelta(hours=1),
            resolved_at=datetime.now(),
            verify_result="PASS",
            verify_comment="验证通过"
        )
        flow.exception = exception
        flow.escalated_to = escalated_user
        flow.verifier = verifier
        
        # Mock查询
        query_mock = MagicMock()
        query_mock.options.return_value.filter.return_value.first.return_value = flow
        self.db.query.return_value = query_mock
        
        # 执行
        result = self.service.get_exception_flow(exception_id)
        
        # 验证
        self.assertEqual(result.exception_no, "EXC-003")
        self.assertEqual(result.exception_title, "测试异常3")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.escalated_to_name, "张三")
        self.assertEqual(result.verifier_name, "验证员")
        self.assertEqual(result.verify_result, "PASS")

    def test_get_exception_flow_not_found(self):
        """测试获取不存在的处理流程"""
        query_mock = MagicMock()
        query_mock.options.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_exception_flow(999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "未找到处理流程")

    def test_calculate_flow_duration_all_stages(self):
        """测试计算所有阶段的流程时长"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        flow = ExceptionHandlingFlow(
            pending_at=base_time,
            processing_at=base_time + timedelta(minutes=30),
            resolved_at=base_time + timedelta(minutes=90),
            closed_at=base_time + timedelta(minutes=120)
        )
        
        self.service.calculate_flow_duration(flow)
        
        # 验证时长计算
        self.assertEqual(flow.pending_duration_minutes, 30)
        self.assertEqual(flow.processing_duration_minutes, 60)
        self.assertEqual(flow.total_duration_minutes, 120)

    def test_calculate_flow_duration_in_progress(self):
        """测试计算进行中的流程时长"""
        past_time = datetime.now() - timedelta(minutes=45)
        
        flow = ExceptionHandlingFlow(
            pending_at=past_time,
            processing_at=None,
            resolved_at=None
        )
        
        self.service.calculate_flow_duration(flow)
        
        # 应该计算到当前时间
        self.assertGreaterEqual(flow.pending_duration_minutes, 44)
        self.assertLessEqual(flow.pending_duration_minutes, 46)

    def test_calculate_flow_duration_partial_stages(self):
        """测试计算部分阶段完成的流程时长"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        flow = ExceptionHandlingFlow(
            pending_at=base_time,
            processing_at=base_time + timedelta(minutes=20),
            resolved_at=None,
            closed_at=None
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_time + timedelta(minutes=50)
            
            self.service.calculate_flow_duration(flow)
            
            self.assertEqual(flow.pending_duration_minutes, 20)
            self.assertEqual(flow.processing_duration_minutes, 30)

    # ==================== 异常知识库测试 ====================

    def test_create_knowledge_success(self):
        """测试成功创建知识库条目"""
        request = MagicMock(
            title="设备故障解决方案",
            exception_type="EQUIPMENT_FAILURE",
            exception_level="CRITICAL",
            symptom_description="设备突然停机",
            solution="重启设备并检查电源",
            solution_steps="步骤1;步骤2",  # 使用字符串
            prevention_measures="预防措施1",  # 使用字符串
            keywords="设备,故障,停机",
            source_exception_id=10,
            attachments=None
        )
        
        creator = User(id=1, username="创建者")
        
        with patch('app.utils.db_helpers.save_obj') as mock_save:
            # Mock save_obj给对象添加必需字段
            def save_obj_side_effect(db, obj):
                obj.id = 1
                obj.reference_count = 0
                obj.success_count = 0
                obj.is_approved = False
                obj.created_at = datetime.now()
                obj.updated_at = datetime.now()
            
            mock_save.side_effect = save_obj_side_effect
            
            # Mock用户查询
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = creator
            
            self.db.query.return_value = user_query
            
            result = self.service.create_knowledge(request, creator_id=1)
            
            # 验证save_obj被调用
            mock_save.assert_called_once()
            saved_knowledge = mock_save.call_args[0][1]
            self.assertEqual(saved_knowledge.title, "设备故障解决方案")
            self.assertEqual(saved_knowledge.exception_type, "EQUIPMENT_FAILURE")
            self.assertEqual(saved_knowledge.creator_id, 1)

    def test_search_knowledge_with_keyword(self):
        """测试使用关键词搜索知识库"""
        knowledge1 = ExceptionKnowledge(
            id=1,
            title="设备故障",
            exception_type="EQUIPMENT",
            exception_level="HIGH",
            symptom_description="设备停机",
            solution="重启",
            keywords="设备,故障",
            reference_count=5,
            success_count=3,
            is_approved=True,
            creator_id=None,  # 简化测试，不需要查creator
            approver_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        knowledge2 = ExceptionKnowledge(
            id=2,
            title="质量问题",
            exception_type="QUALITY",
            exception_level="MEDIUM",
            symptom_description="产品不良",
            solution="调整参数",
            keywords="质量,不良",
            reference_count=3,
            success_count=2,
            is_approved=True,
            creator_id=None,
            approver_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock查询链 - 链式返回自己支持多次filter
        query_chain = MagicMock()
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value = query_chain
        query_chain.count.return_value = 2
        
        # Mock分页结果
        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = [knowledge1, knowledge2]
            
            # Mock用户查询 - 简化处理，返回None
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = None
            
            call_count = [0]
            
            def query_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    # 第一次是ExceptionKnowledge查询
                    return query_chain
                else:
                    # 后续都是User查询
                    return user_query
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.search_knowledge(
                keyword="设备",
                exception_type=None,
                exception_level=None,
                is_approved=None,
                offset=0,
                limit=10,
                page=1,
                page_size=10
            )
            
            self.assertEqual(result.total, 2)
            self.assertEqual(len(result.items), 2)
            # 验证关键词过滤被调用
            self.assertGreater(call_count[0], 1)

    def test_search_knowledge_with_filters(self):
        """测试使用多个过滤条件搜索"""
        knowledge = ExceptionKnowledge(
            id=1,
            title="测试",
            exception_type="EQUIPMENT",
            exception_level="HIGH",
            is_approved=True,
            creator_id=None,  # 简化测试
            approver_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock查询链 - 支持链式调用
        query_chain = MagicMock()
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value = query_chain
        query_chain.count.return_value = 1
        
        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = [knowledge]
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = None
            
            call_count = [0]
            
            def query_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return query_chain
                else:
                    return user_query
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.search_knowledge(
                keyword="测试",
                exception_type="EQUIPMENT",
                exception_level="HIGH",
                is_approved=True,
                offset=0,
                limit=10,
                page=1,
                page_size=10
            )
            
            self.assertEqual(result.total, 1)
            self.assertEqual(len(result.items), 1)
            # 验证多次filter被调用（关键词+类型+级别+审核状态）
            query_chain.filter.assert_called()

    def test_build_knowledge_response_with_creator_and_approver(self):
        """测试构建包含创建者和审批者的知识库响应"""
        knowledge = ExceptionKnowledge(
            id=1,
            title="测试知识",
            exception_type="TEST",
            exception_level="LOW",
            symptom_description="症状",
            solution="解决方案",
            keywords="test",
            reference_count=10,
            success_count=8,
            is_approved=True,
            creator_id=1,
            approver_id=2,
            approved_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        creator = User(id=1, username="创建者")
        approver = User(id=2, username="审批者")
        
        # Mock用户查询
        def filter_side_effect(condition):
            mock_result = MagicMock()
            # 根据查询条件返回不同的用户
            if hasattr(condition, 'right') and hasattr(condition.right, 'value'):
                user_id = condition.right.value
                if user_id == 1:
                    mock_result.first.return_value = creator
                elif user_id == 2:
                    mock_result.first.return_value = approver
            return mock_result
        
        user_query = MagicMock()
        user_query.filter.side_effect = filter_side_effect
        self.db.query.return_value = user_query
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertEqual(result.creator_name, "创建者")
        self.assertEqual(result.approver_name, "审批者")
        self.assertEqual(result.reference_count, 10)
        self.assertEqual(result.success_count, 8)

    def test_build_knowledge_response_without_users(self):
        """测试构建没有创建者和审批者的知识库响应"""
        knowledge = ExceptionKnowledge(
            id=1,
            title="测试",
            exception_type="TEST",
            exception_level="LOW",
            creator_id=None,
            approver_id=None,
            created_at=datetime.now()
        )
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = None
        self.db.query.return_value = user_query
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertIsNone(result.creator_name)
        self.assertIsNone(result.approver_name)

    # ==================== 异常统计分析测试 ====================

    def test_get_exception_statistics_full_data(self):
        """测试获取完整的异常统计数据"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock异常查询
        exception_query = MagicMock()
        filter_mock = MagicMock()
        
        exception_query.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 100
        
        # Mock统计查询
        type_stats = [("EQUIPMENT", 40), ("QUALITY", 35), ("PROCESS", 25)]
        level_stats = [("HIGH", 20), ("MEDIUM", 50), ("LOW", 30)]
        status_stats = [("RESOLVED", 70), ("PROCESSING", 20), ("REPORTED", 10)]
        
        # Mock flows查询
        flow1 = ExceptionHandlingFlow(total_duration_minutes=120)
        flow2 = ExceptionHandlingFlow(total_duration_minutes=180)
        flow3 = ExceptionHandlingFlow(total_duration_minutes=150)
        
        flows_query = MagicMock()
        flows_query.join.return_value.filter.return_value.all.return_value = [flow1, flow2, flow3]
        
        # Mock升级统计
        escalated_query = MagicMock()
        escalated_query.join.return_value.filter.return_value.count.return_value = 30
        
        # Mock TOP10
        top_exceptions = [
            ("EQUIPMENT", "设备故障A", 15),
            ("QUALITY", "质量问题B", 12),
            ("PROCESS", "流程异常C", 10),
        ]
        top_query = MagicMock()
        top_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = top_exceptions
        
        # 配置query的多次调用
        call_count = [0]
        
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # 第一次：总数查询
                return exception_query
            elif call_count[0] == 2:  # 第二次：按类型统计
                stats_query = MagicMock()
                stats_query.filter.return_value.group_by.return_value.all.return_value = type_stats
                return stats_query
            elif call_count[0] == 3:  # 第三次：按级别统计
                stats_query = MagicMock()
                stats_query.filter.return_value.group_by.return_value.all.return_value = level_stats
                return stats_query
            elif call_count[0] == 4:  # 第四次：按状态统计
                stats_query = MagicMock()
                stats_query.filter.return_value.group_by.return_value.all.return_value = status_stats
                return stats_query
            elif call_count[0] == 5:  # 第五次：flows查询
                return flows_query
            elif call_count[0] == 6:  # 第六次：升级统计
                return escalated_query
            elif call_count[0] == 7:  # 第七次：TOP10
                return top_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_exception_statistics(start_date, end_date)
        
        # 验证统计结果
        self.assertEqual(result.total_count, 100)
        self.assertEqual(result.by_type["EQUIPMENT"], 40)
        self.assertEqual(result.by_level["HIGH"], 20)
        self.assertEqual(result.by_status["RESOLVED"], 70)
        self.assertEqual(result.avg_resolution_time_minutes, 150.0)
        self.assertEqual(result.escalation_rate, 30.0)
        self.assertEqual(len(result.top_exceptions), 3)

    def test_get_exception_statistics_no_date_filter(self):
        """测试不带日期过滤的统计"""
        exception_query = MagicMock()
        exception_query.count.return_value = 50
        
        # Mock各种统计查询返回空
        empty_stats_query = MagicMock()
        empty_stats_query.filter.return_value.group_by.return_value.all.return_value = []
        
        flows_query = MagicMock()
        flows_query.join.return_value.filter.return_value.all.return_value = []
        
        escalated_query = MagicMock()
        escalated_query.join.return_value.filter.return_value.count.return_value = 0
        
        top_query = MagicMock()
        top_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        call_count = [0]
        
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return exception_query
            elif call_count[0] in [2, 3, 4]:
                return empty_stats_query
            elif call_count[0] == 5:
                return flows_query
            elif call_count[0] == 6:
                return escalated_query
            elif call_count[0] == 7:
                return top_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_exception_statistics(None, None)
        
        self.assertEqual(result.total_count, 50)
        self.assertEqual(result.by_type, {})
        self.assertIsNone(result.avg_resolution_time_minutes)
        self.assertEqual(result.escalation_rate, 0.0)

    def test_get_exception_statistics_zero_total(self):
        """测试总数为0时的升级率计算"""
        exception_query = MagicMock()
        exception_query.filter.return_value.filter.return_value.count.return_value = 0
        
        empty_stats_query = MagicMock()
        empty_stats_query.filter.return_value.group_by.return_value.all.return_value = []
        
        empty_flow_query = MagicMock()
        empty_flow_query.join.return_value.filter.return_value.all.return_value = []
        empty_flow_query.join.return_value.filter.return_value.count.return_value = 0
        
        top_query = MagicMock()
        top_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        call_count = [0]
        
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # 总数查询
                return exception_query
            elif call_count[0] in [2, 3, 4]:  # 各种统计查询
                return empty_stats_query
            elif call_count[0] in [5, 6]:  # flow查询
                return empty_flow_query
            elif call_count[0] == 7:  # TOP10查询
                return top_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_exception_statistics(datetime.now(), datetime.now())
        
        # 总数为0时升级率应该是0
        self.assertEqual(result.escalation_rate, 0.0)

    # ==================== PDCA管理测试 ====================

    def test_create_pdca_success(self):
        """测试成功创建PDCA记录"""
        exception_id = 1
        exception = ProductionException(
            id=exception_id,
            exception_no="EXC-100",
            title="测试异常"
        )
        
        request = MagicMock(
            exception_id=exception_id,
            plan_description="问题分析",
            plan_root_cause="根本原因",
            plan_target="改善目标",
            plan_measures="措施1;措施2",
            plan_owner_id=2,
            plan_deadline=datetime(2024, 12, 31)
        )
        
        # 准备一个完整的PDCA对象用于返回
        saved_pdca_obj = ExceptionPDCA(
            id=1,
            exception_id=exception_id,
            pdca_no="PDCA-20240101120000-1",
            current_stage=PDCAStage.PLAN,
            plan_description="问题分析",
            plan_root_cause="根本原因",
            plan_target="改善目标",
            plan_measures="措施1;措施2",
            plan_owner_id=2,
            plan_deadline=datetime(2024, 12, 31),
            plan_completed_at=datetime.now(),
            is_completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=exception), \
             patch('app.utils.db_helpers.save_obj') as mock_save:
            
            # Mock save_obj - 复制属性到传入的对象
            def save_obj_side_effect(db, obj):
                for key in ['id', 'is_completed', 'created_at', 'updated_at']:
                    setattr(obj, key, getattr(saved_pdca_obj, key))
            
            mock_save.side_effect = save_obj_side_effect
            
            # Mock用户查询
            user = User(id=2, username="负责人")
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = user
            
            exception_query = MagicMock()
            exception_query.filter.return_value.first.return_value = exception
            
            def query_side_effect(model):
                if model == User:
                    return user_query
                elif model == ProductionException:
                    return exception_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.create_pdca(request, current_user_id=1)
            
            # 验证
            mock_save.assert_called_once()
            saved_pdca = mock_save.call_args[0][1]
            self.assertEqual(saved_pdca.exception_id, exception_id)
            self.assertEqual(saved_pdca.current_stage, PDCAStage.PLAN)
            self.assertIsNotNone(saved_pdca.pdca_no)
            self.assertTrue(saved_pdca.pdca_no.startswith("PDCA-"))

    def test_advance_pdca_stage_plan_to_do(self):
        """测试PDCA从P阶段推进到D阶段"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            pdca_no="PDCA-001",
            current_stage=PDCAStage.PLAN
        )
        
        request = MagicMock(
            stage="DO",
            do_action_taken="执行的措施",
            do_resources_used="使用的资源",
            do_difficulties="遇到的困难",
            do_owner_id=3
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=pdca):
            user = User(id=3, username="执行人")
            exception = ProductionException(id=1, exception_no="EXC-001")
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = user
            
            exception_query = MagicMock()
            exception_query.filter.return_value.first.return_value = exception
            
            def query_side_effect(model):
                if model == User:
                    return user_query
                elif model == ProductionException:
                    return exception_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.advance_pdca_stage(1, request)
            
            # 验证阶段推进
            self.assertEqual(pdca.current_stage, PDCAStage.DO)
            self.assertEqual(pdca.do_action_taken, "执行的措施")
            self.assertIsNotNone(pdca.do_completed_at)
            self.db.commit.assert_called_once()

    def test_advance_pdca_stage_do_to_check(self):
        """测试PDCA从D阶段推进到C阶段"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            current_stage=PDCAStage.DO
        )
        
        request = MagicMock(
            stage="CHECK",
            check_result="检查结果",
            check_effectiveness="有效性评估",
            check_data="数据分析",
            check_gap="差距分析",
            check_owner_id=4
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=pdca):
            user = User(id=4, username="检查人")
            exception = ProductionException(id=1, exception_no="EXC-001")
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = user
            
            exception_query = MagicMock()
            exception_query.filter.return_value.first.return_value = exception
            
            def query_side_effect(model):
                if model == User:
                    return user_query
                elif model == ProductionException:
                    return exception_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(pdca.current_stage, PDCAStage.CHECK)
            self.assertEqual(pdca.check_result, "检查结果")
            self.assertIsNotNone(pdca.check_completed_at)

    def test_advance_pdca_stage_check_to_act(self):
        """测试PDCA从C阶段推进到A阶段"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            current_stage=PDCAStage.CHECK
        )
        
        request = MagicMock(
            stage="ACT",
            act_standardization="标准化措施",
            act_horizontal_deployment="横向展开",
            act_remaining_issues="遗留问题",
            act_next_cycle="下一循环计划",
            act_owner_id=5
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=pdca):
            user = User(id=5, username="行动人")
            exception = ProductionException(id=1, exception_no="EXC-001")
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = user
            
            exception_query = MagicMock()
            exception_query.filter.return_value.first.return_value = exception
            
            def query_side_effect(model):
                if model == User:
                    return user_query
                elif model == ProductionException:
                    return exception_query
                return MagicMock()
            
            self.db.query.side_effect = query_side_effect
            
            result = self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(pdca.current_stage, PDCAStage.ACT)
            self.assertEqual(pdca.act_standardization, "标准化措施")
            self.assertIsNotNone(pdca.act_completed_at)

    def test_advance_pdca_stage_act_to_completed(self):
        """测试PDCA从A阶段推进到完成"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            current_stage=PDCAStage.ACT
        )
        
        request = MagicMock(
            stage="COMPLETED",
            summary="总结",
            lessons_learned="经验教训"
        )
        
        with patch('app.utils.db_helpers.get_or_404', return_value=pdca):
            exception = ProductionException(id=1, exception_no="EXC-001")
            
            exception_query = MagicMock()
            exception_query.filter.return_value.first.return_value = exception
            self.db.query.return_value = exception_query
            
            result = self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(pdca.current_stage, PDCAStage.COMPLETED)
            self.assertTrue(pdca.is_completed)
            self.assertIsNotNone(pdca.completed_at)
            self.assertEqual(pdca.summary, "总结")

    def test_advance_pdca_stage_invalid_transition(self):
        """测试PDCA无效的阶段转换"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            current_stage=PDCAStage.PLAN
        )
        
        request = MagicMock(stage="CHECK")  # PLAN不能直接到CHECK
        
        with patch('app.utils.db_helpers.get_or_404', return_value=pdca):
            with self.assertRaises(HTTPException) as context:
                self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("不能从", context.exception.detail)

    def test_advance_pdca_stage_invalid_stage_name(self):
        """测试PDCA无效的阶段名称"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            current_stage=PDCAStage.PLAN
        )
        
        request = MagicMock(stage="INVALID_STAGE")
        
        with patch('app.utils.db_helpers.get_or_404', return_value=pdca):
            with self.assertRaises(HTTPException) as context:
                self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertEqual(context.exception.detail, "无效的阶段")

    def test_build_pdca_response_all_stages_completed(self):
        """测试构建完整的PDCA响应"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            pdca_no="PDCA-001",
            current_stage=PDCAStage.COMPLETED,
            plan_description="计划",
            plan_owner_id=1,
            do_action_taken="执行",
            do_owner_id=2,
            check_result="检查",
            check_owner_id=3,
            act_standardization="行动",
            act_owner_id=4,
            is_completed=True,
            completed_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        exception = ProductionException(id=1, exception_no="EXC-001")
        users = {
            1: User(id=1, username="计划者"),
            2: User(id=2, username="执行者"),
            3: User(id=3, username="检查者"),
            4: User(id=4, username="行动者"),
        }
        
        def filter_side_effect(condition):
            mock_result = MagicMock()
            if hasattr(condition, 'right') and hasattr(condition.right, 'value'):
                user_id = condition.right.value
                mock_result.first.return_value = users.get(user_id)
            return mock_result
        
        exception_query = MagicMock()
        exception_query.filter.return_value.first.return_value = exception
        
        user_query = MagicMock()
        user_query.filter.side_effect = filter_side_effect
        
        def query_side_effect(model):
            if model == ProductionException:
                return exception_query
            elif model == User:
                return user_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.build_pdca_response(pdca)
        
        self.assertEqual(result.exception_no, "EXC-001")
        self.assertEqual(result.plan_owner_name, "计划者")
        self.assertEqual(result.do_owner_name, "执行者")
        self.assertEqual(result.check_owner_name, "检查者")
        self.assertEqual(result.act_owner_name, "行动者")
        self.assertTrue(result.is_completed)

    # ==================== 重复异常分析测试 ====================

    def test_analyze_recurrence_single_type(self):
        """测试分析单一类型的重复异常"""
        now = datetime.now()
        exceptions = [
            ProductionException(
                id=1,
                exception_type="EQUIPMENT",
                title="设备故障A",
                report_time=now - timedelta(days=1)
            ),
            ProductionException(
                id=2,
                exception_type="EQUIPMENT",
                title="设备故障A",
                report_time=now - timedelta(days=2)
            ),
            ProductionException(
                id=3,
                exception_type="EQUIPMENT",
                title="设备故障B",
                report_time=now - timedelta(days=3)
            ),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.all.return_value = exceptions
        
        self.db.query.return_value = query_mock
        
        # Mock PDCA查询
        pdca_query = MagicMock()
        pdca_query.filter.return_value.all.return_value = [
            ExceptionPDCA(exception_id=1, plan_root_cause="维护不当"),
        ]
        
        def query_side_effect(model):
            if model == ProductionException:
                return query_mock
            elif model == ExceptionPDCA:
                return pdca_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        results = self.service.analyze_recurrence(
            exception_type="EQUIPMENT",
            days=7
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].exception_type, "EQUIPMENT")
        self.assertEqual(results[0].total_occurrences, 3)
        self.assertGreater(len(results[0].similar_exceptions), 0)
        self.assertIsNotNone(results[0].time_trend)

    def test_analyze_recurrence_all_types(self):
        """测试分析所有类型的重复异常"""
        now = datetime.now()
        exceptions = [
            ProductionException(
                id=1,
                exception_type="EQUIPMENT",
                title="设备故障",
                report_time=now - timedelta(days=1)
            ),
            ProductionException(
                id=2,
                exception_type="QUALITY",
                title="质量问题",
                report_time=now - timedelta(days=2)
            ),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.all.return_value = exceptions
        
        pdca_query = MagicMock()
        pdca_query.filter.return_value.all.return_value = []
        
        def query_side_effect(model):
            if model == ProductionException:
                return query_mock
            elif model == ExceptionPDCA:
                return pdca_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        results = self.service.analyze_recurrence(
            exception_type=None,
            days=30
        )
        
        self.assertEqual(len(results), 2)
        type_names = {r.exception_type for r in results}
        self.assertIn("EQUIPMENT", type_names)
        self.assertIn("QUALITY", type_names)

    def test_find_similar_exceptions_with_matches(self):
        """测试查找相似异常有匹配"""
        exceptions = [
            ProductionException(id=1, title="设备 A 故障"),
            ProductionException(id=2, title="设备 A 故障"),
            ProductionException(id=3, title="设备 B 故障"),
            ProductionException(id=4, title="质量问题"),
        ]
        
        result = self.service.find_similar_exceptions(exceptions)
        
        # 应该找到"设备 a 故障"这个模式出现2次
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['count'], 2)

    def test_find_similar_exceptions_no_duplicates(self):
        """测试查找相似异常无重复"""
        exceptions = [
            ProductionException(id=1, title="异常A"),
            ProductionException(id=2, title="异常B"),
            ProductionException(id=3, title="异常C"),
        ]
        
        result = self.service.find_similar_exceptions(exceptions)
        
        # 每个都只出现一次，应该返回空
        self.assertEqual(len(result), 0)

    def test_analyze_time_trend(self):
        """测试分析时间趋势"""
        base_date = datetime(2024, 1, 1)
        exceptions = [
            ProductionException(id=1, report_time=base_date),
            ProductionException(id=2, report_time=base_date),
            ProductionException(id=3, report_time=base_date + timedelta(days=1)),
        ]
        
        with patch('app.services.production.exception.exception_enhancement_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_date + timedelta(days=7)
            
            result = self.service.analyze_time_trend(exceptions, days=7)
            
            # 应该返回7天的趋势数据
            self.assertEqual(len(result), 7)
            self.assertEqual(result[0]['count'], 2)  # 第一天2个
            self.assertEqual(result[1]['count'], 1)  # 第二天1个
            self.assertEqual(result[2]['count'], 0)  # 第三天0个

    def test_extract_common_root_causes_with_data(self):
        """测试提取常见根因（有数据）"""
        pdca_records = [
            ExceptionPDCA(plan_root_cause="维护不当"),
            ExceptionPDCA(plan_root_cause="操作失误"),
            ExceptionPDCA(plan_root_cause="设备老化"),
            ExceptionPDCA(plan_root_cause="培训不足"),
        ]
        
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = pdca_records
        self.db.query.return_value = query_mock
        
        result = self.service.extract_common_root_causes([1, 2, 3, 4])
        
        # 应该返回前3个
        self.assertEqual(len(result), 3)
        self.assertIn("维护不当", result)
        self.assertIn("操作失误", result)

    def test_extract_common_root_causes_no_data(self):
        """测试提取常见根因（无数据）"""
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock
        
        result = self.service.extract_common_root_causes([1, 2])
        
        self.assertEqual(result, ["暂无根因分析"])

    def test_extract_common_root_causes_with_none_values(self):
        """测试提取常见根因（包含None值）"""
        pdca_records = [
            ExceptionPDCA(plan_root_cause="原因1"),
            ExceptionPDCA(plan_root_cause=None),
            ExceptionPDCA(plan_root_cause="原因2"),
        ]
        
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = pdca_records
        self.db.query.return_value = query_mock
        
        result = self.service.extract_common_root_causes([1, 2, 3])
        
        # 应该过滤掉None，只返回有效的根因
        self.assertEqual(len(result), 2)
        self.assertIn("原因1", result)
        self.assertIn("原因2", result)


if __name__ == '__main__':
    unittest.main()
