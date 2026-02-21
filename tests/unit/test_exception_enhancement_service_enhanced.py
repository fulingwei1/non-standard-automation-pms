# -*- coding: utf-8 -*-
"""
异常处理增强服务 - 增强单元测试
目标：35-45个测试用例，覆盖率70%+
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from fastapi import HTTPException
import pytest

from app.services.production.exception.exception_enhancement_service import (
    ExceptionEnhancementService
)
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
    """异常处理增强服务测试类"""

    def setUp(self):
        """测试前设置"""
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    # ==================== 异常升级测试 (5个) ====================

    def test_escalate_exception_new_flow_level1(self):
        """测试异常升级 - 新建流程 - LEVEL1"""
        # Mock数据
        exception = MagicMock(spec=ProductionException)
        exception.id = 1
        exception.status = "REPORTED"
        
        # Mock get_or_404
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = exception
            
            # Mock User查询
            user = MagicMock(spec=User)
            user.username = "test_user"
            
            # 修复：确保db.query的返回值可以区分flow查询和user查询
            flow_query = MagicMock()
            flow_query.filter.return_value.first.return_value = None  # 第一次查询flow返回None
            
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = user  # 第二次查询user返回user对象
            
            self.db.query.side_effect = [flow_query, user_query]
            
            # Mock db.refresh to set flow.id
            def mock_refresh(obj):
                if isinstance(obj, MagicMock) and not hasattr(obj, 'id'):
                    obj.id = 100
                    obj.created_at = datetime.now()
                    obj.updated_at = datetime.now()
            
            self.db.refresh = mock_refresh
            
            result = self.service.escalate_exception(
                exception_id=1,
                escalation_level="LEVEL_1",
                reason="测试升级",
                escalated_to_id=10
            )
            
            # 验证
            self.assertEqual(result.exception_id, 1)
            self.assertEqual(result.escalation_level, "LEVEL_1")
            self.assertEqual(result.escalation_reason, "测试升级")
            self.assertEqual(result.escalated_to_id, 10)
            self.assertEqual(result.escalated_to_name, "test_user")
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_escalate_exception_existing_flow_level2(self):
        """测试异常升级 - 已有流程 - LEVEL2"""
        exception = MagicMock(spec=ProductionException)
        exception.id = 2
        exception.status = "REPORTED"
        
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.id = 100
        flow.exception_id = 2
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = exception
            
            # 返回现有流程
            self.db.query.return_value.filter.return_value.first.side_effect = [flow, None]
            
            result = self.service.escalate_exception(
                exception_id=2,
                escalation_level="LEVEL_2",
                reason="紧急升级",
                escalated_to_id=20
            )
            
            # 验证
            self.assertEqual(result.exception_id, 2)
            self.assertEqual(result.escalation_level, "LEVEL_2")
            self.assertEqual(flow.escalation_level, EscalationLevel.LEVEL_2)
            self.db.add.assert_not_called()  # 不应该add，因为是已有流程

    def test_escalate_exception_level3_updates_status(self):
        """测试异常升级 - LEVEL3并更新状态"""
        exception = MagicMock(spec=ProductionException)
        exception.id = 3
        exception.status = "REPORTED"
        
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.exception_id = 3
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = exception
            self.db.query.return_value.filter.return_value.first.side_effect = [flow, None]
            
            self.service.escalate_exception(
                exception_id=3,
                escalation_level="LEVEL_3",
                reason="严重升级",
                escalated_to_id=30
            )
            
            # 验证异常状态变更
            self.assertEqual(exception.status, "PROCESSING")
            self.assertEqual(exception.handler_id, 30)
            self.assertEqual(flow.status, FlowStatus.PROCESSING)

    def test_escalate_exception_invalid_level_defaults_to_level1(self):
        """测试异常升级 - 无效级别默认为LEVEL1"""
        exception = MagicMock(spec=ProductionException)
        exception.status = "PROCESSING"
        
        flow = MagicMock(spec=ExceptionHandlingFlow)
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = exception
            self.db.query.return_value.filter.return_value.first.side_effect = [flow, None]
            
            result = self.service.escalate_exception(
                exception_id=1,
                escalation_level="INVALID_LEVEL",
                reason="测试",
                escalated_to_id=None
            )
            
            self.assertEqual(flow.escalation_level, EscalationLevel.LEVEL_1)

    def test_escalate_exception_without_user(self):
        """测试异常升级 - 无指定用户"""
        exception = MagicMock(spec=ProductionException)
        exception.status = "REPORTED"
        
        flow = MagicMock(spec=ExceptionHandlingFlow)
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = exception
            self.db.query.return_value.filter.return_value.first.side_effect = [flow]
            
            result = self.service.escalate_exception(
                exception_id=1,
                escalation_level="LEVEL_1",
                reason="自动升级",
                escalated_to_id=None
            )
            
            self.assertIsNone(result.escalated_to_id)
            self.assertIsNone(result.escalated_to_name)

    # ==================== 处理流程跟踪测试 (6个) ====================

    def test_get_exception_flow_success(self):
        """测试获取异常处理流程 - 成功"""
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.id = 1
        flow.exception_id = 10
        flow.status = FlowStatus.PROCESSING
        flow.escalation_level = EscalationLevel.LEVEL_1
        flow.escalation_reason = "测试升级原因"
        flow.escalated_at = datetime.now()
        flow.pending_duration_minutes = 10
        flow.processing_duration_minutes = 20
        flow.total_duration_minutes = 30
        flow.pending_at = datetime.now()
        flow.processing_at = datetime.now()
        flow.resolved_at = None
        flow.verified_at = None
        flow.closed_at = None
        flow.verify_result = None
        flow.verify_comment = None
        flow.created_at = datetime.now()
        flow.updated_at = datetime.now()
        
        exception = MagicMock(spec=ProductionException)
        exception.exception_no = "EXC001"
        exception.title = "测试异常"
        
        user = MagicMock(spec=User)
        user.username = "handler"
        
        flow.exception = exception
        flow.escalated_to = user
        flow.verifier = None
        
        # Mock query chain
        mock_query = self.db.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = flow
        
        result = self.service.get_exception_flow(10)
        
        self.assertEqual(result.exception_id, 10)
        self.assertEqual(result.exception_no, "EXC001")
        self.assertEqual(result.escalated_to_name, "handler")
        self.db.commit.assert_called_once()

    def test_get_exception_flow_not_found(self):
        """测试获取异常处理流程 - 未找到"""
        self.db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_exception_flow(999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "未找到处理流程")

    def test_calculate_flow_duration_pending_only(self):
        """测试计算流程时长 - 仅待处理阶段"""
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.pending_at = datetime.now() - timedelta(minutes=30)
        flow.processing_at = None
        flow.resolved_at = None
        flow.closed_at = None
        
        self.service.calculate_flow_duration(flow)
        
        self.assertIsNotNone(flow.pending_duration_minutes)
        self.assertGreater(flow.pending_duration_minutes, 29)

    def test_calculate_flow_duration_all_stages(self):
        """测试计算流程时长 - 所有阶段"""
        now = datetime.now()
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.pending_at = now - timedelta(minutes=60)
        flow.processing_at = now - timedelta(minutes=40)
        flow.resolved_at = now - timedelta(minutes=10)
        flow.closed_at = now
        
        self.service.calculate_flow_duration(flow)
        
        self.assertGreater(flow.pending_duration_minutes, 19)
        self.assertGreater(flow.processing_duration_minutes, 29)
        self.assertGreater(flow.total_duration_minutes, 59)

    def test_calculate_flow_duration_no_pending(self):
        """测试计算流程时长 - 无待处理时间"""
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.pending_at = None
        flow.processing_at = None
        flow.resolved_at = None
        flow.closed_at = None
        
        self.service.calculate_flow_duration(flow)
        
        # 应该不会设置任何时长

    def test_get_exception_flow_with_verifier(self):
        """测试获取异常处理流程 - 包含验证人"""
        flow = MagicMock(spec=ExceptionHandlingFlow)
        flow.id = 2
        flow.exception_id = 20
        flow.status = FlowStatus.PROCESSING
        flow.escalation_level = EscalationLevel.LEVEL_2
        flow.escalation_reason = "升级原因"
        flow.escalated_at = datetime.now()
        flow.verify_result = "PASSED"  # 应该是字符串不是布尔值
        flow.verify_comment = "验证通过"
        flow.pending_duration_minutes = 15
        flow.processing_duration_minutes = 25
        flow.total_duration_minutes = 40
        flow.pending_at = datetime.now()
        flow.processing_at = datetime.now()
        flow.resolved_at = None
        flow.verified_at = datetime.now()
        flow.closed_at = None
        flow.created_at = datetime.now()
        flow.updated_at = datetime.now()
        
        exception = MagicMock(spec=ProductionException)
        exception.exception_no = "EXC002"
        exception.title = "测试异常2"
        
        verifier = MagicMock(spec=User)
        verifier.username = "verifier_user"
        
        flow.exception = exception
        flow.escalated_to = None
        flow.verifier = verifier
        
        mock_query = self.db.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = flow
        
        result = self.service.get_exception_flow(20)
        
        self.assertEqual(result.verifier_name, "verifier_user")
        self.assertEqual(result.verify_comment, "验证通过")

    # ==================== 异常知识库测试 (8个) ====================

    def test_create_knowledge_success(self):
        """测试创建知识库条目 - 成功"""
        request = MagicMock()
        request.title = "测试知识"
        request.exception_type = "设备故障"
        request.exception_level = "HIGH"
        request.symptom_description = "症状描述"
        request.solution = "解决方案"
        request.solution_steps = ["步骤1", "步骤2"]
        request.prevention_measures = "预防措施"
        request.keywords = "关键词"
        request.source_exception_id = 1
        request.attachments = []
        
        # Mock build_knowledge_response to return actual response object
        from app.schemas.production.exception_enhancement import KnowledgeResponse
        
        with patch('app.services.production.exception.exception_enhancement_service.save_obj') as mock_save:
            mock_response = KnowledgeResponse(
                id=1,
                title="测试知识",
                exception_type="设备故障",
                exception_level="HIGH",
                symptom_description="症状描述",
                solution="解决方案",
                solution_steps="步骤1\n步骤2",
                prevention_measures="预防措施",
                keywords="关键词",
                source_exception_id=1,
                reference_count=0,
                success_count=0,
                last_referenced_at=None,
                is_approved=False,
                approver_name=None,
                approved_at=None,
                creator_name=None,
                attachments="[]",
                remark=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(self.service, 'build_knowledge_response', return_value=mock_response):
                result = self.service.create_knowledge(request, creator_id=100)
                
                mock_save.assert_called_once()
                self.assertEqual(result.title, "测试知识")

    def test_search_knowledge_with_keyword(self):
        """测试知识库搜索 - 使用关键词"""
        from app.schemas.production.exception_enhancement import KnowledgeResponse
        
        knowledge1 = MagicMock(spec=ExceptionKnowledge)
        knowledge1.id = 1
        knowledge1.title = "设备故障知识"
        knowledge1.creator_id = None
        knowledge1.approver_id = None
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        
        mock_response = KnowledgeResponse(
            id=1,
            title="设备故障知识",
            exception_type="设备故障",
            exception_level="HIGH",
            symptom_description="症状",
            solution="方案",
            solution_steps="步骤",
            prevention_measures="预防",
            keywords="设备",
            source_exception_id=None,
            reference_count=0,
            success_count=0,
            last_referenced_at=None,
            is_approved=False,
            approver_name=None,
            approved_at=None,
            creator_name=None,
            attachments="[]",
            remark=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.apply_pagination') as mock_page:
            mock_page.return_value.all.return_value = [knowledge1]
            
            with patch.object(self.service, 'build_knowledge_response', return_value=mock_response):
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
                
                self.assertEqual(result.total, 1)
                self.assertEqual(len(result.items), 1)

    def test_search_knowledge_with_filters(self):
        """测试知识库搜索 - 使用多个过滤器"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        
        with patch('app.services.production.exception.exception_enhancement_service.apply_pagination') as mock_page:
            mock_page.return_value.all.return_value = []
            
            result = self.service.search_knowledge(
                keyword="故障",
                exception_type="设备故障",
                exception_level="HIGH",
                is_approved=True,
                offset=0,
                limit=10,
                page=1,
                page_size=10
            )
            
            self.assertEqual(result.total, 0)
            # 验证filter被多次调用（关键词+类型+级别+审核状态）
            self.assertGreaterEqual(mock_query.filter.call_count, 3)

    def test_search_knowledge_pagination(self):
        """测试知识库搜索 - 分页"""
        from app.schemas.production.exception_enhancement import KnowledgeResponse
        
        knowledges = [MagicMock(spec=ExceptionKnowledge) for _ in range(5)]
        for k in knowledges:
            k.creator_id = None
            k.approver_id = None
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 25
        
        mock_response = KnowledgeResponse(
            id=1,
            title="知识",
            exception_type="类型",
            exception_level="HIGH",
            symptom_description="症状",
            solution="方案",
            solution_steps="步骤",
            prevention_measures="预防",
            keywords="关键词",
            source_exception_id=None,
            reference_count=0,
            success_count=0,
            last_referenced_at=None,
            is_approved=False,
            approver_name=None,
            approved_at=None,
            creator_name=None,
            attachments="[]",
            remark=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.apply_pagination') as mock_page:
            mock_page.return_value.all.return_value = knowledges
            
            with patch.object(self.service, 'build_knowledge_response', return_value=mock_response):
                result = self.service.search_knowledge(
                    keyword=None,
                    exception_type=None,
                    exception_level=None,
                    is_approved=None,
                    offset=10,
                    limit=5,
                    page=3,
                    page_size=5
                )
                
                self.assertEqual(result.total, 25)
                self.assertEqual(result.page, 3)
                self.assertEqual(result.page_size, 5)

    def test_build_knowledge_response_with_creator(self):
        """测试构建知识库响应 - 包含创建者"""
        knowledge = MagicMock(spec=ExceptionKnowledge)
        knowledge.id = 1
        knowledge.title = "知识条目"
        knowledge.creator_id = 100
        knowledge.approver_id = None
        knowledge.reference_count = 5
        knowledge.success_count = 3
        
        creator = MagicMock(spec=User)
        creator.username = "creator_user"
        
        self.db.query.return_value.filter.return_value.first.side_effect = [creator]
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertEqual(result.id, 1)
        self.assertEqual(result.creator_name, "creator_user")
        self.assertIsNone(result.approver_name)

    def test_build_knowledge_response_with_approver(self):
        """测试构建知识库响应 - 包含审核者"""
        knowledge = MagicMock(spec=ExceptionKnowledge)
        knowledge.id = 2
        knowledge.creator_id = 100
        knowledge.approver_id = 200
        
        creator = MagicMock(spec=User)
        creator.username = "creator"
        
        approver = MagicMock(spec=User)
        approver.username = "approver"
        
        self.db.query.return_value.filter.return_value.first.side_effect = [creator, approver]
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertEqual(result.creator_name, "creator")
        self.assertEqual(result.approver_name, "approver")

    def test_build_knowledge_response_no_users(self):
        """测试构建知识库响应 - 无用户信息"""
        knowledge = MagicMock(spec=ExceptionKnowledge)
        knowledge.id = 3
        knowledge.creator_id = None
        knowledge.approver_id = None
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertIsNone(result.creator_name)
        self.assertIsNone(result.approver_name)

    def test_build_knowledge_response_user_not_found(self):
        """测试构建知识库响应 - 用户不存在"""
        knowledge = MagicMock(spec=ExceptionKnowledge)
        knowledge.id = 4
        knowledge.creator_id = 999
        knowledge.approver_id = 888
        
        self.db.query.return_value.filter.return_value.first.side_effect = [None, None]
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertIsNone(result.creator_name)
        self.assertIsNone(result.approver_name)

    # ==================== 异常统计分析测试 (6个) ====================

    def test_get_exception_statistics_basic(self):
        """测试异常统计分析 - 基本统计"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        
        # Mock按类型统计
        mock_query.group_by.return_value.all.side_effect = [
            [("设备故障", 5), ("质量问题", 3)],  # by_type
            [("HIGH", 4), ("MEDIUM", 6)],  # by_level
            [("RESOLVED", 7), ("PROCESSING", 3)],  # by_status
        ]
        
        # Mock流程查询
        mock_query.join.return_value.filter.return_value.all.return_value = []
        mock_query.join.return_value.filter.return_value.count.return_value = 0
        
        # Mock高频异常
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_exception_statistics(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        self.assertEqual(result.total_count, 10)
        self.assertIn("设备故障", result.by_type)
        self.assertIn("HIGH", result.by_level)
        self.assertIn("RESOLVED", result.by_status)

    def test_get_exception_statistics_with_avg_resolution_time(self):
        """测试异常统计分析 - 包含平均解决时长"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        
        mock_query.group_by.return_value.all.side_effect = [
            [],  # by_type
            [],  # by_level
            [],  # by_status
        ]
        
        # Mock流程数据
        flow1 = MagicMock()
        flow1.total_duration_minutes = 120
        flow2 = MagicMock()
        flow2.total_duration_minutes = 180
        
        mock_query.join.return_value.filter.return_value.all.return_value = [flow1, flow2]
        mock_query.join.return_value.filter.return_value.count.return_value = 0
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_exception_statistics(None, None)
        
        self.assertEqual(result.avg_resolution_time_minutes, 150.0)

    def test_get_exception_statistics_escalation_rate(self):
        """测试异常统计分析 - 升级率"""
        # 创建两个独立的query mock
        main_query = MagicMock()
        escalation_query = MagicMock()
        
        # 主查询返回10个异常
        main_query.filter.return_value = main_query
        main_query.count.return_value = 10
        main_query.group_by.return_value.all.side_effect = [[], [], []]
        
        # 升级查询返回3个
        escalation_query.join.return_value.filter.return_value.all.return_value = []
        escalation_query.join.return_value.filter.return_value.count.return_value = 3
        
        # 高频异常查询
        top_query = MagicMock()
        top_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # 设置db.query返回不同的mock对象
        self.db.query.side_effect = [
            main_query,  # 第一次查询ProductionException
            main_query,  # by_type stats
            main_query,  # by_level stats
            main_query,  # by_status stats
            escalation_query,  # flows for avg_resolution_time
            escalation_query,  # escalated_count
            top_query,  # top_exceptions
        ]
        
        result = self.service.get_exception_statistics(None, None)
        
        self.assertEqual(result.escalation_rate, 30.0)  # 3/10 * 100

    def test_get_exception_statistics_top_exceptions(self):
        """测试异常统计分析 - 高频异常TOP10"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [5, 0, 0]
        
        mock_query.group_by.return_value.all.side_effect = [[], [], []]
        mock_query.join.return_value.filter.return_value.all.return_value = []
        
        top_data = [
            ("设备故障", "电机过热", 15),
            ("质量问题", "尺寸偏差", 10),
        ]
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = top_data
        
        result = self.service.get_exception_statistics(None, None)
        
        self.assertEqual(len(result.top_exceptions), 2)
        self.assertEqual(result.top_exceptions[0]["type"], "设备故障")
        self.assertEqual(result.top_exceptions[0]["count"], 15)

    def test_get_exception_statistics_no_data(self):
        """测试异常统计分析 - 无数据"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [0, 0, 0]
        
        mock_query.group_by.return_value.all.side_effect = [[], [], []]
        mock_query.join.return_value.filter.return_value.all.return_value = []
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_exception_statistics(None, None)
        
        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.escalation_rate, 0.0)
        self.assertIsNone(result.avg_resolution_time_minutes)

    def test_get_exception_statistics_date_range(self):
        """测试异常统计分析 - 指定日期范围"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [20, 0, 5]
        
        mock_query.group_by.return_value.all.side_effect = [[], [], []]
        mock_query.join.return_value.filter.return_value.all.return_value = []
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_exception_statistics(start, end)
        
        self.assertEqual(result.total_count, 20)
        # 验证filter被调用（日期范围过滤）
        self.assertGreater(mock_query.filter.call_count, 0)

    # ==================== PDCA管理测试 (7个) ====================

    def test_create_pdca_success(self):
        """测试创建PDCA记录 - 成功"""
        from app.schemas.production.exception_enhancement import PDCAResponse
        
        request = MagicMock()
        request.exception_id = 1
        request.plan_description = "计划描述"
        request.plan_root_cause = "根本原因"
        request.plan_target = "目标"
        request.plan_measures = ["措施1", "措施2"]
        request.plan_owner_id = 100
        request.plan_deadline = datetime.now() + timedelta(days=7)
        
        exception = MagicMock(spec=ProductionException)
        
        mock_response = PDCAResponse(
            id=1,
            exception_id=1,
            exception_no="EXC-001",
            pdca_no="PDCA-001",
            current_stage="PLAN",
            plan_description="计划描述",
            plan_root_cause="根本原因",
            plan_target="目标",
            plan_measures="措施1\n措施2",
            plan_owner_name="owner",
            plan_deadline=request.plan_deadline,
            plan_completed_at=datetime.now(),
            do_action_taken=None,
            do_resources_used=None,
            do_difficulties=None,
            do_owner_name=None,
            do_completed_at=None,
            check_result=None,
            check_effectiveness=None,
            check_data=None,
            check_gap=None,
            check_owner_name=None,
            check_completed_at=None,
            act_standardization=None,
            act_horizontal_deployment=None,
            act_remaining_issues=None,
            act_next_cycle=None,
            act_owner_name=None,
            act_completed_at=None,
            is_completed=False,
            completed_at=None,
            summary=None,
            lessons_learned=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = exception
            
            with patch('app.services.production.exception.exception_enhancement_service.save_obj') as mock_save:
                with patch.object(self.service, 'build_pdca_response', return_value=mock_response):
                    result = self.service.create_pdca(request, current_user_id=200)
                    
                    mock_save.assert_called_once()
                    self.assertEqual(result.plan_description, "计划描述")

    def test_advance_pdca_stage_plan_to_do(self):
        """测试推进PDCA阶段 - PLAN到DO"""
        from app.schemas.production.exception_enhancement import PDCAResponse
        
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.id = 1
        pdca.current_stage = PDCAStage.PLAN
        
        request = MagicMock()
        request.stage = "DO"
        request.do_action_taken = "执行动作"
        request.do_resources_used = "使用资源"
        request.do_difficulties = "遇到困难"
        request.do_owner_id = 100
        
        mock_response = PDCAResponse(
            id=1, exception_id=1, exception_no="EXC-001", pdca_no="PDCA-001",
            current_stage="DO", plan_description="计划", plan_root_cause="原因",
            plan_target="目标", plan_measures="措施", plan_owner_name="owner",
            plan_deadline=datetime.now(), plan_completed_at=datetime.now(),
            do_action_taken="执行动作", do_resources_used="使用资源",
            do_difficulties="遇到困难", do_owner_name="owner", do_completed_at=datetime.now(),
            check_result=None, check_effectiveness=None, check_data=None,
            check_gap=None, check_owner_name=None, check_completed_at=None,
            act_standardization=None, act_horizontal_deployment=None,
            act_remaining_issues=None, act_next_cycle=None, act_owner_name=None,
            act_completed_at=None, is_completed=False, completed_at=None,
            summary=None, lessons_learned=None, created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = pdca
            
            with patch.object(self.service, 'build_pdca_response', return_value=mock_response):
                result = self.service.advance_pdca_stage(1, request)
                
                self.assertEqual(pdca.current_stage, PDCAStage.DO)
                self.assertEqual(pdca.do_action_taken, "执行动作")
                self.db.commit.assert_called_once()

    def test_advance_pdca_stage_do_to_check(self):
        """测试推进PDCA阶段 - DO到CHECK"""
        from app.schemas.production.exception_enhancement import PDCAResponse
        
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.current_stage = PDCAStage.DO
        
        request = MagicMock()
        request.stage = "CHECK"
        request.check_result = "检查结果"
        request.check_effectiveness = "有效性评估"
        request.check_data = {"metric": "value"}
        request.check_gap = "差距分析"
        request.check_owner_id = 101
        
        mock_response = PDCAResponse(
            id=1, exception_id=1, exception_no="EXC-001", pdca_no="PDCA-001",
            current_stage="CHECK", plan_description=None, plan_root_cause=None,
            plan_target=None, plan_measures=None, plan_owner_name=None,
            plan_deadline=None, plan_completed_at=None,
            do_action_taken=None, do_resources_used=None,
            do_difficulties=None, do_owner_name=None, do_completed_at=None,
            check_result="检查结果", check_effectiveness="有效性评估", check_data='{"metric": "value"}',
            check_gap="差距分析", check_owner_name="owner", check_completed_at=datetime.now(),
            act_standardization=None, act_horizontal_deployment=None,
            act_remaining_issues=None, act_next_cycle=None, act_owner_name=None,
            act_completed_at=None, is_completed=False, completed_at=None,
            summary=None, lessons_learned=None, created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = pdca
            
            with patch.object(self.service, 'build_pdca_response', return_value=mock_response):
                result = self.service.advance_pdca_stage(1, request)
                
                self.assertEqual(pdca.current_stage, PDCAStage.CHECK)
                self.assertEqual(pdca.check_result, "检查结果")

    def test_advance_pdca_stage_check_to_act(self):
        """测试推进PDCA阶段 - CHECK到ACT"""
        from app.schemas.production.exception_enhancement import PDCAResponse
        
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.current_stage = PDCAStage.CHECK
        
        request = MagicMock()
        request.stage = "ACT"
        request.act_standardization = "标准化措施"
        request.act_horizontal_deployment = "横向展开"
        request.act_remaining_issues = "遗留问题"
        request.act_next_cycle = "下一循环"
        request.act_owner_id = 102
        
        mock_response = PDCAResponse(
            id=1, exception_id=1, exception_no="EXC-001", pdca_no="PDCA-001",
            current_stage="ACT", plan_description=None, plan_root_cause=None,
            plan_target=None, plan_measures=None, plan_owner_name=None,
            plan_deadline=None, plan_completed_at=None,
            do_action_taken=None, do_resources_used=None,
            do_difficulties=None, do_owner_name=None, do_completed_at=None,
            check_result=None, check_effectiveness=None, check_data=None,
            check_gap=None, check_owner_name=None, check_completed_at=None,
            act_standardization="标准化措施", act_horizontal_deployment="横向展开",
            act_remaining_issues="遗留问题", act_next_cycle="下一循环", act_owner_name="owner",
            act_completed_at=datetime.now(), is_completed=False, completed_at=None,
            summary=None, lessons_learned=None, created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = pdca
            
            with patch.object(self.service, 'build_pdca_response', return_value=mock_response):
                result = self.service.advance_pdca_stage(1, request)
                
                self.assertEqual(pdca.current_stage, PDCAStage.ACT)
                self.assertEqual(pdca.act_standardization, "标准化措施")

    def test_advance_pdca_stage_act_to_completed(self):
        """测试推进PDCA阶段 - ACT到COMPLETED"""
        from app.schemas.production.exception_enhancement import PDCAResponse
        
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.current_stage = PDCAStage.ACT
        
        request = MagicMock()
        request.stage = "COMPLETED"
        request.summary = "总结"
        request.lessons_learned = "经验教训"
        
        mock_response = PDCAResponse(
            id=1, exception_id=1, exception_no="EXC-001", pdca_no="PDCA-001",
            current_stage="COMPLETED", plan_description=None, plan_root_cause=None,
            plan_target=None, plan_measures=None, plan_owner_name=None,
            plan_deadline=None, plan_completed_at=None,
            do_action_taken=None, do_resources_used=None,
            do_difficulties=None, do_owner_name=None, do_completed_at=None,
            check_result=None, check_effectiveness=None, check_data=None,
            check_gap=None, check_owner_name=None, check_completed_at=None,
            act_standardization=None, act_horizontal_deployment=None,
            act_remaining_issues=None, act_next_cycle=None, act_owner_name=None,
            act_completed_at=None, is_completed=True, completed_at=datetime.now(),
            summary="总结", lessons_learned="经验教训", created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = pdca
            
            with patch.object(self.service, 'build_pdca_response', return_value=mock_response):
                result = self.service.advance_pdca_stage(1, request)
                
                self.assertEqual(pdca.current_stage, PDCAStage.COMPLETED)
                self.assertTrue(pdca.is_completed)
                self.assertIsNotNone(pdca.completed_at)

    def test_advance_pdca_stage_invalid_transition(self):
        """测试推进PDCA阶段 - 无效转换"""
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.current_stage = PDCAStage.PLAN
        
        request = MagicMock()
        request.stage = "CHECK"  # PLAN不能直接到CHECK
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = pdca
            
            with self.assertRaises(HTTPException) as context:
                self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("不能从", context.exception.detail)

    def test_advance_pdca_stage_invalid_stage_name(self):
        """测试推进PDCA阶段 - 无效阶段名"""
        pdca = MagicMock(spec=ExceptionPDCA)
        
        request = MagicMock()
        request.stage = "INVALID"
        
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.return_value = pdca
            
            with self.assertRaises(HTTPException) as context:
                self.service.advance_pdca_stage(1, request)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertEqual(context.exception.detail, "无效的阶段")

    # ==================== PDCA响应构建测试 (2个) ====================

    def test_build_pdca_response_complete(self):
        """测试构建PDCA响应 - 完整数据"""
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.id = 1
        pdca.exception_id = 10
        pdca.pdca_no = "PDCA-001"
        pdca.current_stage = PDCAStage.ACT
        pdca.plan_owner_id = 100
        pdca.do_owner_id = 101
        pdca.check_owner_id = 102
        pdca.act_owner_id = 103
        
        exception = MagicMock(spec=ProductionException)
        exception.exception_no = "EXC-001"
        
        users = [
            MagicMock(username="user1"),
            MagicMock(username="user2"),
            MagicMock(username="user3"),
            MagicMock(username="user4"),
        ]
        
        self.db.query.return_value.filter.return_value.first.side_effect = [exception] + users
        
        result = self.service.build_pdca_response(pdca)
        
        self.assertEqual(result.id, 1)
        self.assertEqual(result.exception_no, "EXC-001")
        self.assertEqual(result.plan_owner_name, "user1")
        self.assertEqual(result.do_owner_name, "user2")
        self.assertEqual(result.check_owner_name, "user3")
        self.assertEqual(result.act_owner_name, "user4")

    def test_build_pdca_response_no_owners(self):
        """测试构建PDCA响应 - 无责任人"""
        pdca = MagicMock(spec=ExceptionPDCA)
        pdca.id = 2
        pdca.exception_id = 20
        pdca.plan_owner_id = None
        pdca.do_owner_id = None
        pdca.check_owner_id = None
        pdca.act_owner_id = None
        
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.build_pdca_response(pdca)
        
        self.assertIsNone(result.plan_owner_name)
        self.assertIsNone(result.do_owner_name)
        self.assertIsNone(result.check_owner_name)
        self.assertIsNone(result.act_owner_name)

    # ==================== 重复异常分析测试 (6个) ====================

    def test_analyze_recurrence_basic(self):
        """测试重复异常分析 - 基本功能"""
        exceptions = [
            MagicMock(id=1, exception_type="设备故障", title="电机故障", report_time=datetime.now()),
            MagicMock(id=2, exception_type="设备故障", title="电机故障", report_time=datetime.now()),
            MagicMock(id=3, exception_type="质量问题", title="尺寸偏差", report_time=datetime.now()),
        ]
        
        self.db.query.return_value.filter.return_value.all.return_value = exceptions
        
        # Mock PDCA查询
        self.db.query.return_value.filter.return_value.all.side_effect = [
            exceptions,
            [],  # PDCA records
        ]
        
        result = self.service.analyze_recurrence(exception_type=None, days=30)
        
        self.assertEqual(len(result), 2)  # 2种类型
        self.assertIn("设备故障", [r.exception_type for r in result])

    def test_analyze_recurrence_with_type_filter(self):
        """测试重复异常分析 - 类型过滤"""
        exceptions = [
            MagicMock(id=1, exception_type="设备故障", title="故障1", report_time=datetime.now()),
        ]
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.all.side_effect = [exceptions, []]
        
        result = self.service.analyze_recurrence(exception_type="设备故障", days=7)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].exception_type, "设备故障")

    def test_find_similar_exceptions_high_similarity(self):
        """测试查找相似异常 - 高相似度"""
        exceptions = [
            MagicMock(id=1, title="电机过热故障"),
            MagicMock(id=2, title="电机过热故障"),
            MagicMock(id=3, title="电机过热异常"),
        ]
        
        result = self.service.find_similar_exceptions(exceptions)
        
        self.assertGreater(len(result), 0)
        self.assertGreaterEqual(result[0]["count"], 2)

    def test_find_similar_exceptions_no_similarity(self):
        """测试查找相似异常 - 无相似"""
        exceptions = [
            MagicMock(id=1, title="完全不同的异常A"),
            MagicMock(id=2, title="另一个异常B"),
        ]
        
        result = self.service.find_similar_exceptions(exceptions)
        
        self.assertEqual(len(result), 0)  # 无重复

    def test_analyze_time_trend(self):
        """测试时间趋势分析"""
        now = datetime.now()
        exceptions = [
            MagicMock(report_time=now),
            MagicMock(report_time=now),
            MagicMock(report_time=now - timedelta(days=1)),
        ]
        
        result = self.service.analyze_time_trend(exceptions, days=3)
        
        self.assertEqual(len(result), 3)  # 3天
        self.assertIn("date", result[0])
        self.assertIn("count", result[0])

    def test_extract_common_root_causes(self):
        """测试提取常见根因"""
        pdca1 = MagicMock()
        pdca1.plan_root_cause = "原因1"
        pdca2 = MagicMock()
        pdca2.plan_root_cause = "原因2"
        
        self.db.query.return_value.filter.return_value.all.return_value = [pdca1, pdca2]
        
        result = self.service.extract_common_root_causes([1, 2, 3])
        
        self.assertEqual(len(result), 2)
        self.assertIn("原因1", result)

    # ==================== 边界和异常情况测试 (5个) ====================

    def test_escalate_exception_not_found(self):
        """测试异常升级 - 异常不存在"""
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="异常不存在")
            
            with self.assertRaises(HTTPException):
                self.service.escalate_exception(999, "LEVEL_1", "测试", None)

    def test_create_knowledge_with_all_fields(self):
        """测试创建知识库 - 所有字段"""
        from app.schemas.production.exception_enhancement import KnowledgeResponse
        
        request = MagicMock()
        request.title = "完整知识"
        request.exception_type = "设备故障"
        request.exception_level = "CRITICAL"
        request.symptom_description = "详细症状"
        request.solution = "详细方案"
        request.solution_steps = ["步骤1", "步骤2", "步骤3"]
        request.prevention_measures = "预防措施"
        request.keywords = "关键词1,关键词2"
        request.source_exception_id = 100
        request.attachments = [{"name": "file.pdf", "url": "http://example.com/file.pdf"}]
        
        mock_response = KnowledgeResponse(
            id=1, title="完整知识", exception_type="设备故障", exception_level="CRITICAL",
            symptom_description="详细症状", solution="详细方案", solution_steps="步骤1\n步骤2\n步骤3",
            prevention_measures="预防措施", keywords="关键词1,关键词2", source_exception_id=100,
            reference_count=0, success_count=0, last_referenced_at=None, is_approved=False,
            approver_name=None, approved_at=None, creator_name="creator",
            attachments='[{"name": "file.pdf", "url": "http://example.com/file.pdf"}]',
            remark=None, created_at=datetime.now(), updated_at=datetime.now()
        )
        
        with patch('app.services.production.exception.exception_enhancement_service.save_obj'):
            with patch.object(self.service, 'build_knowledge_response', return_value=mock_response):
                result = self.service.create_knowledge(request, creator_id=1)
                
                self.assertEqual(result.title, "完整知识")

    def test_get_exception_statistics_zero_division(self):
        """测试异常统计分析 - 避免零除错误"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [0, 0, 5]  # total=0, 但有升级
        
        mock_query.group_by.return_value.all.side_effect = [[], [], []]
        mock_query.join.return_value.filter.return_value.all.return_value = []
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_exception_statistics(None, None)
        
        self.assertEqual(result.escalation_rate, 0.0)  # 不应抛出异常

    def test_advance_pdca_stage_not_found(self):
        """测试推进PDCA阶段 - 记录不存在"""
        with patch('app.services.production.exception.exception_enhancement_service.get_or_404') as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="PDCA记录不存在")
            
            request = MagicMock()
            request.stage = "DO"
            
            with self.assertRaises(HTTPException):
                self.service.advance_pdca_stage(999, request)

    def test_extract_common_root_causes_empty(self):
        """测试提取常见根因 - 无PDCA记录"""
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.extract_common_root_causes([1, 2, 3])
        
        self.assertEqual(result, ["暂无根因分析"])


if __name__ == '__main__':
    unittest.main()
