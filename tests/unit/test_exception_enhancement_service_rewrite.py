# -*- coding: utf-8 -*-
"""
异常增强服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率（686行）
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException
import json

from app.services.production.exception.exception_enhancement_service import (
    ExceptionEnhancementService,
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


class TestExceptionEscalation(unittest.TestCase):
    """测试异常升级功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_escalate_exception_create_new_flow(self):
        """测试升级异常时创建新流程"""
        # Mock数据
        exception = ProductionException(
            id=1,
            exception_no="EXC-001",
            title="设备故障",
            status="REPORTED",
        )
        
        # Mock get_or_404返回异常对象
        with patch("app.services.production.exception.exception_enhancement_service.get_or_404", return_value=exception):
            # Mock query - 第一次查询flow返回None，第二次查询user返回user对象
            flow_mock = MagicMock()
            flow_mock.id = 10
            flow_mock.exception_id = 1
            flow_mock.status = FlowStatus.PROCESSING
            flow_mock.escalation_level = EscalationLevel.LEVEL_2
            flow_mock.escalation_reason = "问题严重，需要上级处理"
            flow_mock.escalated_to_id = 100
            flow_mock.escalated_at = datetime.now()
            flow_mock.created_at = datetime.now()
            flow_mock.updated_at = datetime.now()
            
            # Mock db.refresh将flow.id设置为10
            def mock_refresh(obj):
                if isinstance(obj, ExceptionHandlingFlow):
                    obj.id = 10
            
            self.db.refresh.side_effect = mock_refresh
            self.db.query.return_value.filter.return_value.first.side_effect = [
                None,  # 第一次查询flow
                User(id=100, username="李经理",
        password_hash="test_hash_123"
    )  # 第二次查询user
            ]
            
            result = self.service.escalate_exception(
                exception_id=1,
                escalation_level="LEVEL_2",
                reason="问题严重，需要上级处理",
                escalated_to_id=100,
            )
            
            # 验证
            self.assertEqual(result.exception_id, 1)
            self.assertEqual(result.escalation_level, "LEVEL_2")
            self.assertEqual(result.escalation_reason, "问题严重，需要上级处理")
            self.assertEqual(result.escalated_to_id, 100)
            self.assertEqual(result.escalated_to_name, "李经理")
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_escalate_exception_update_existing_flow(self):
        """测试升级异常时更新已有流程"""
        exception = ProductionException(
            id=1,
            exception_no="EXC-001",
            status="REPORTED",
        )
        
        flow = ExceptionHandlingFlow(
            id=10,
            exception_id=1,
            status=FlowStatus.PENDING,
            escalation_level=EscalationLevel.NONE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        with patch("app.services.production.exception.exception_enhancement_service.get_or_404", return_value=exception):
            # Mock返回已存在的flow
            self.db.query.return_value.filter.return_value.first.side_effect = [flow, None]
            
            result = self.service.escalate_exception(
                exception_id=1,
                escalation_level="LEVEL_1",
                reason="初级升级",
                escalated_to_id=None,
            )
            
            # 验证flow被更新
            self.assertEqual(flow.escalation_level, EscalationLevel.LEVEL_1)
            self.assertEqual(flow.escalation_reason, "初级升级")
            self.assertIsNotNone(flow.escalated_at)
            self.db.commit.assert_called_once()


class TestFlowTracking(unittest.TestCase):
    """测试流程跟踪功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_get_exception_flow_success(self):
        """测试获取流程跟踪成功"""
        exception = ProductionException(
            id=1,
            exception_no="EXC-001",
            title="设备故障",
        )
        
        user = User(id=100, username="张三",
        password_hash="test_hash_123"
    )
        verifier = User(id=200, username="李四",
        password_hash="test_hash_123"
    )
        
        flow = ExceptionHandlingFlow(
            id=10,
            exception_id=1,
            status=FlowStatus.RESOLVED,
            escalation_level=EscalationLevel.LEVEL_2,
            escalation_reason="需要技术支持",
            escalated_at=datetime.now(),
            pending_at=datetime.now() - timedelta(hours=2),
            processing_at=datetime.now() - timedelta(hours=1),
            resolved_at=datetime.now(),
            verify_result="PASSED",  # 使用字符串而不是bool
            verify_comment="问题已解决",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        flow.exception = exception
        flow.escalated_to = user
        flow.verifier = verifier
        
        # Mock query
        mock_query = self.db.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = flow
        
        result = self.service.get_exception_flow(exception_id=1)
        
        # 验证
        self.assertEqual(result.id, 10)
        self.assertEqual(result.exception_id, 1)
        self.assertEqual(result.exception_no, "EXC-001")
        self.assertEqual(result.exception_title, "设备故障")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.escalated_to_name, "张三")
        self.assertEqual(result.verifier_name, "李四")
        self.assertEqual(result.verify_result, "PASSED")

    def test_get_exception_flow_not_found(self):
        """测试流程不存在"""
        self.db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_exception_flow(exception_id=999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "未找到处理流程")

    def test_calculate_flow_duration(self):
        """测试计算流程时长"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        flow = ExceptionHandlingFlow(
            pending_at=base_time,
            processing_at=base_time + timedelta(minutes=30),
            resolved_at=base_time + timedelta(hours=2),
            closed_at=base_time + timedelta(hours=3),
        )
        
        self.service.calculate_flow_duration(flow)
        
        # 验证时长计算
        self.assertEqual(flow.pending_duration_minutes, 30)  # 30分钟
        self.assertEqual(flow.processing_duration_minutes, 90)  # 1.5小时
        self.assertEqual(flow.total_duration_minutes, 180)  # 3小时


class TestKnowledgeManagement(unittest.TestCase):
    """测试知识库管理功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_create_knowledge(self):
        """测试创建知识库条目"""
        request = MagicMock()
        request.title = "设备过热处理方案"
        request.exception_type = "EQUIPMENT_FAILURE"
        request.exception_level = "HIGH"
        request.symptom_description = "设备温度超过80度"
        request.solution = "立即停机检查冷却系统"
        request.solution_steps = json.dumps(["步骤1", "步骤2"])  # JSON字符串
        request.prevention_measures = json.dumps(["定期检查冷却液"])  # JSON字符串
        request.keywords = "过热,冷却"
        request.source_exception_id = 100
        request.attachments = json.dumps([])  # JSON字符串
        
        # Mock save_obj - 设置保存后的id
        def mock_save(db, obj):
            obj.id = 1
            obj.reference_count = 0
            obj.success_count = 0
            obj.is_approved = False
            obj.created_at = datetime.now()
            obj.updated_at = datetime.now()
        
        with patch("app.services.production.exception.exception_enhancement_service.save_obj", side_effect=mock_save):
            # Mock User查询
            self.db.query.return_value.filter.return_value.first.return_value = None
            
            result = self.service.create_knowledge(request, creator_id=1)
            
            # 验证
            self.assertEqual(result.title, "设备过热处理方案")
            self.assertEqual(result.exception_type, "EQUIPMENT_FAILURE")
            self.assertEqual(result.symptom_description, "设备温度超过80度")

    def test_search_knowledge_with_keyword(self):
        """测试关键词搜索知识库"""
        knowledge1 = ExceptionKnowledge(
            id=1,
            title="设备过热",
            exception_type="EQUIPMENT_FAILURE",
            exception_level="HIGH",
            symptom_description="温度异常",
            solution="检查冷却系统",
            keywords="过热,冷却",
            reference_count=10,
            success_count=8,
            is_approved=True,
            creator_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        knowledge2 = ExceptionKnowledge(
            id=2,
            title="冷却液不足",
            exception_type="EQUIPMENT_FAILURE",
            exception_level="MEDIUM",
            symptom_description="冷却液低于标准",
            solution="添加冷却液",
            keywords="冷却液",
            reference_count=5,
            success_count=5,
            is_approved=True,
            creator_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Mock query
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        
        # Mock apply_pagination
        with patch("app.services.production.exception.exception_enhancement_service.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [knowledge1, knowledge2]
            
            # Mock User查询返回None
            self.db.query.return_value.filter.return_value.first.return_value = None
            
            result = self.service.search_knowledge(
                keyword="冷却",
                exception_type=None,
                exception_level=None,
                is_approved=None,
                offset=0,
                limit=10,
                page=1,
                page_size=10,
            )
            
            # 验证
            self.assertEqual(result.total, 2)
            self.assertEqual(len(result.items), 2)
            self.assertEqual(result.page, 1)

    def test_build_knowledge_response_with_users(self):
        """测试构建知识库响应（包含用户信息）"""
        creator = User(id=1, username="创建者",
        password_hash="test_hash_123"
    )
        approver = User(id=2, username="审批者",
        password_hash="test_hash_123"
    )
        
        knowledge = ExceptionKnowledge(
            id=1,
            title="测试知识",
            exception_type="TEST",
            exception_level="LOW",
            symptom_description="症状",
            solution="解决方案",
            creator_id=1,
            approver_id=2,
            is_approved=True,
            reference_count=5,
            success_count=3,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Mock User查询
        self.db.query.return_value.filter.return_value.first.side_effect = [creator, approver]
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertEqual(result.creator_name, "创建者")
        self.assertEqual(result.approver_name, "审批者")


class TestStatisticsAnalysis(unittest.TestCase):
    """测试统计分析功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_get_exception_statistics_full(self):
        """测试完整的异常统计"""
        # 使用patch直接mock数据库查询方法
        with patch.object(self.db, 'query') as mock_query:
            # Mock总数查询 - ProductionException的count
            mock_exception_base = MagicMock()
            mock_exception_base.filter.return_value = mock_exception_base
            mock_exception_base.count.return_value = 100
            
            # Mock类型统计
            mock_type_query = MagicMock()
            mock_type_query.filter.return_value = mock_type_query
            mock_type_query.group_by.return_value.all.return_value = [
                ("EQUIPMENT_FAILURE", 40), ("QUALITY_ISSUE", 30), ("SAFETY_INCIDENT", 30)
            ]
            
            # Mock级别统计
            mock_level_query = MagicMock()
            mock_level_query.filter.return_value = mock_level_query
            mock_level_query.group_by.return_value.all.return_value = [
                ("HIGH", 20), ("MEDIUM", 50), ("LOW", 30)
            ]
            
            # Mock状态统计
            mock_status_query = MagicMock()
            mock_status_query.filter.return_value = mock_status_query
            mock_status_query.group_by.return_value.all.return_value = [
                ("REPORTED", 10), ("PROCESSING", 30), ("RESOLVED", 60)
            ]
            
            # Mock TOP异常统计
            mock_top_query = MagicMock()
            mock_top_query.filter.return_value = mock_top_query
            mock_top_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                ("EQUIPMENT_FAILURE", "设备故障", 15),
                ("QUALITY_ISSUE", "质量问题", 10)
            ]
            
            # Mock流程查询 - 平均解决时长
            flow1 = ExceptionHandlingFlow(total_duration_minutes=60)
            flow2 = ExceptionHandlingFlow(total_duration_minutes=120)
            
            mock_flow_avg = MagicMock()
            mock_flow_avg.join.return_value = mock_flow_avg
            mock_flow_avg.filter.return_value = mock_flow_avg
            mock_flow_avg.all.return_value = [flow1, flow2]
            
            # Mock流程查询 - 升级数量
            mock_flow_escalation = MagicMock()
            mock_flow_escalation.join.return_value = mock_flow_escalation
            mock_flow_escalation.filter.return_value = mock_flow_escalation
            mock_flow_escalation.count.return_value = 20
            
            # 设置query的side_effect，根据调用次数返回不同的mock
            call_count = [0]
            def query_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:  # 第一次：总数查询
                    return mock_exception_base
                elif call_count[0] == 2:  # 第二次：类型统计
                    return mock_type_query
                elif call_count[0] == 3:  # 第三次：级别统计
                    return mock_level_query
                elif call_count[0] == 4:  # 第四次：状态统计
                    return mock_status_query
                elif call_count[0] == 5:  # 第五次：平均解决时长
                    return mock_flow_avg
                elif call_count[0] == 6:  # 第六次：升级数量
                    return mock_flow_escalation
                else:  # 第七次：TOP异常
                    return mock_top_query
            
            mock_query.side_effect = query_side_effect
            
            result = self.service.get_exception_statistics(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
            )
            
            # 验证
            self.assertEqual(result.total_count, 100)
            self.assertEqual(result.by_type["EQUIPMENT_FAILURE"], 40)
            self.assertEqual(result.by_level["HIGH"], 20)
            self.assertEqual(result.by_status["RESOLVED"], 60)
            self.assertEqual(result.avg_resolution_time_minutes, 90)  # (60+120)/2
            self.assertEqual(result.escalation_rate, 20)  # 20/100*100
            self.assertEqual(len(result.top_exceptions), 2)


class TestPDCAManagement(unittest.TestCase):
    """测试PDCA管理功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_create_pdca(self):
        """测试创建PDCA记录"""
        exception = ProductionException(id=1, exception_no="EXC-001")
        
        request = MagicMock()
        request.exception_id = 1
        request.plan_description = "制定改进计划"
        request.plan_root_cause = "设备老化"
        request.plan_target = "降低故障率50%"
        request.plan_measures = json.dumps(["更换设备", "培训人员"])  # JSON字符串
        request.plan_owner_id = 100
        request.plan_deadline = datetime.now() + timedelta(days=30)
        
        def mock_save(db, obj):
            obj.id = 1
            obj.is_completed = False
            obj.created_at = datetime.now()
            obj.updated_at = datetime.now()
        
        with patch("app.services.production.exception.exception_enhancement_service.get_or_404", return_value=exception):
            with patch("app.services.production.exception.exception_enhancement_service.save_obj", side_effect=mock_save):
                # Mock User查询
                self.db.query.return_value.filter.return_value.first.return_value = None
                
                result = self.service.create_pdca(request, current_user_id=1)
                
                # 验证
                self.assertEqual(result.exception_id, 1)
                self.assertIn("PDCA-", result.pdca_no)
                self.assertEqual(result.current_stage, "PLAN")
                self.assertEqual(result.plan_description, "制定改进计划")

    def test_advance_pdca_stage_to_do(self):
        """测试推进PDCA到DO阶段"""
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            pdca_no="PDCA-001",
            current_stage=PDCAStage.PLAN,
            is_completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        request = MagicMock()
        request.stage = "DO"
        request.do_action_taken = "已执行设备更换"
        request.do_resources_used = "新设备一台"
        request.do_difficulties = "安装调试困难"
        request.do_owner_id = 100
        
        with patch("app.services.production.exception.exception_enhancement_service.get_or_404", return_value=pdca):
            # Mock User查询
            self.db.query.return_value.filter.return_value.first.return_value = None
            
            result = self.service.advance_pdca_stage(pdca_id=1, request=request)
            
            # 验证
            self.assertEqual(result.current_stage, "DO")
            self.assertEqual(pdca.current_stage, PDCAStage.DO)
            self.assertEqual(pdca.do_action_taken, "已执行设备更换")
            self.assertIsNotNone(pdca.do_completed_at)

    def test_advance_pdca_stage_invalid_transition(self):
        """测试无效的阶段转换"""
        pdca = ExceptionPDCA(
            id=1,
            current_stage=PDCAStage.PLAN,
            exception_id=1,
            pdca_no="PDCA-001",
            is_completed=False,
        )
        
        request = MagicMock()
        request.stage = "CHECK"  # 不能从PLAN直接跳到CHECK
        
        with patch("app.services.production.exception.exception_enhancement_service.get_or_404", return_value=pdca):
            with self.assertRaises(HTTPException) as context:
                self.service.advance_pdca_stage(pdca_id=1, request=request)
            
            self.assertEqual(context.exception.status_code, 400)


class TestRecurrenceAnalysis(unittest.TestCase):
    """测试重复异常分析功能"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_analyze_recurrence(self):
        """测试重复异常分析"""
        now = datetime.now()
        
        exceptions = [
            ProductionException(
                id=1,
                exception_type="EQUIPMENT_FAILURE",
                title="设备过热故障",
                report_time=now - timedelta(days=1),
            ),
            ProductionException(
                id=2,
                exception_type="EQUIPMENT_FAILURE",
                title="设备过热问题",
                report_time=now - timedelta(days=2),
            ),
            ProductionException(
                id=3,
                exception_type="QUALITY_ISSUE",
                title="产品质量不合格",
                report_time=now - timedelta(days=3),
            ),
        ]
        
        # Mock第一次query返回ProductionException对象
        mock_exception_query = MagicMock()
        mock_exception_query.filter.return_value = mock_exception_query
        mock_exception_query.all.return_value = exceptions
        
        # Mock第二次query返回PDCA对象
        pdca = ExceptionPDCA(
            id=1,
            exception_id=1,
            pdca_no="PDCA-001",
            current_stage=PDCAStage.PLAN,
            plan_root_cause="冷却系统故障",
            is_completed=False,
        )
        
        mock_pdca_query = MagicMock()
        mock_pdca_query.filter.return_value = mock_pdca_query
        mock_pdca_query.all.return_value = [pdca]
        
        # 设置query的side_effect
        def query_side_effect(*args, **kwargs):
            model = args[0] if args else None
            if model == ProductionException:
                return mock_exception_query
            elif model == ExceptionPDCA:
                return mock_pdca_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.analyze_recurrence(
            exception_type=None,
            days=7,
        )
        
        # 验证
        self.assertEqual(len(result), 2)  # 两种类型
        
        # 找到EQUIPMENT_FAILURE的结果
        equipment_result = next((r for r in result if r.exception_type == "EQUIPMENT_FAILURE"), None)
        self.assertIsNotNone(equipment_result)
        self.assertEqual(equipment_result.total_occurrences, 2)

    def test_find_similar_exceptions(self):
        """测试查找相似异常（Jaccard算法）"""
        exceptions = [
            ProductionException(id=1, title="设备 过热 故障 问题"),
            ProductionException(id=2, title="设备 过热 故障"),
            ProductionException(id=3, title="产品 质量 不合格"),
            ProductionException(id=4, title="质量 不合格 问题"),
        ]
        
        result = self.service.find_similar_exceptions(exceptions)
        
        # 验证相似组（"设备 过热 故障"相似度应该>60%）
        # Jaccard相似度计算：{"设备", "过热", "故障", "问题"} vs {"设备", "过热", "故障"}
        # 交集3个，并集4个，相似度3/4=0.75 > 0.6
        self.assertGreater(len(result), 0)

    def test_analyze_time_trend(self):
        """测试时间趋势分析"""
        now = datetime.now()
        
        exceptions = [
            ProductionException(id=1, report_time=now - timedelta(days=1)),
            ProductionException(id=2, report_time=now - timedelta(days=1)),
            ProductionException(id=3, report_time=now - timedelta(days=3)),
        ]
        
        result = self.service.analyze_time_trend(exceptions, days=7)
        
        # 验证趋势数据
        self.assertEqual(len(result), 7)  # 7天的数据

    def test_extract_common_root_causes(self):
        """测试提取常见根因"""
        pdca1 = ExceptionPDCA(id=1, exception_id=1, pdca_no="P1", current_stage=PDCAStage.PLAN, 
                              plan_root_cause="设备老化", is_completed=False)
        pdca2 = ExceptionPDCA(id=2, exception_id=2, pdca_no="P2", current_stage=PDCAStage.PLAN,
                              plan_root_cause="操作不当", is_completed=False)
        pdca3 = ExceptionPDCA(id=3, exception_id=3, pdca_no="P3", current_stage=PDCAStage.PLAN,
                              plan_root_cause="材料问题", is_completed=False)
        
        self.db.query.return_value.filter.return_value.all.return_value = [pdca1, pdca2, pdca3]
        
        result = self.service.extract_common_root_causes([1, 2, 3])
        
        # 验证
        self.assertEqual(len(result), 3)
        self.assertIn("设备老化", result)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ExceptionEnhancementService(self.db)

    def test_calculate_flow_duration_no_pending_at(self):
        """测试没有pending_at的流程"""
        flow = ExceptionHandlingFlow(
            pending_at=None,
            processing_at=None,
            resolved_at=None,
        )
        
        self.service.calculate_flow_duration(flow)
        
        # 不应该有时长
        self.assertIsNone(flow.pending_duration_minutes)
        self.assertIsNone(flow.total_duration_minutes)

    def test_build_knowledge_response_no_creator(self):
        """测试没有创建者的知识库条目"""
        knowledge = ExceptionKnowledge(
            id=1,
            title="测试",
            exception_type="TEST",
            exception_level="LOW",
            symptom_description="测试症状",
            solution="测试解决方案",
            reference_count=0,
            success_count=0,
            is_approved=False,
            creator_id=999,  # 不存在的用户
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Mock返回None（用户不存在）
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.build_knowledge_response(knowledge)
        
        self.assertIsNone(result.creator_name)

    def test_statistics_with_none_duration(self):
        """测试包含None时长的统计"""
        flow1 = ExceptionHandlingFlow(total_duration_minutes=60)
        flow3 = ExceptionHandlingFlow(total_duration_minutes=120)
        
        # 使用patch直接mock
        with patch.object(self.db, 'query') as mock_query:
            # Mock异常总数查询
            mock_exception_base = MagicMock()
            mock_exception_base.filter.return_value = mock_exception_base
            mock_exception_base.count.return_value = 3
            
            # Mock类型、级别、状态统计（返回空）
            mock_stats_query = MagicMock()
            mock_stats_query.filter.return_value = mock_stats_query
            mock_stats_query.group_by.return_value.all.return_value = []
            
            # Mock流程查询 - 只返回非None的flow
            mock_flow_avg = MagicMock()
            mock_flow_avg.join.return_value = mock_flow_avg
            mock_flow_avg.filter.return_value = mock_flow_avg
            mock_flow_avg.all.return_value = [flow1, flow3]  # 只返回有时长的
            
            # Mock升级数量查询
            mock_flow_escalation = MagicMock()
            mock_flow_escalation.join.return_value = mock_flow_escalation
            mock_flow_escalation.filter.return_value = mock_flow_escalation
            mock_flow_escalation.count.return_value = 0
            
            # Mock TOP异常查询
            mock_top_query = MagicMock()
            mock_top_query.filter.return_value = mock_top_query
            mock_top_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
            
            # 设置query的side_effect
            call_count = [0]
            def query_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:  # 总数查询
                    return mock_exception_base
                elif call_count[0] in [2, 3, 4]:  # 类型、级别、状态统计
                    return mock_stats_query
                elif call_count[0] == 5:  # 平均解决时长
                    return mock_flow_avg
                elif call_count[0] == 6:  # 升级数量
                    return mock_flow_escalation
                else:  # TOP异常
                    return mock_top_query
            
            mock_query.side_effect = query_side_effect
            
            result = self.service.get_exception_statistics(None, None)
            
            # 应该只计算非None的值：(60+120)/2 = 90
            self.assertEqual(result.avg_resolution_time_minutes, 90)


if __name__ == "__main__":
    unittest.main()
