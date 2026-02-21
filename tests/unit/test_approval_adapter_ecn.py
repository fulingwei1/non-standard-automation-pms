# -*- coding: utf-8 -*-
"""
ECN审批适配器单元测试

测试策略:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 参考 test_condition_parser_rewrite.py 的mock策略
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
from app.models.ecn import Ecn, EcnEvaluation
from app.models.approval import ApprovalInstance, ApprovalTask, ApprovalNodeDefinition
from app.models.user import User, Role, UserRole

# EcnApproval在源代码中是TYPE_CHECKING导入，运行时动态使用
# 这里为测试mock做导入
try:
    from app.models.ecn import EcnApproval
except ImportError:
    EcnApproval = None


class TestEcnApprovalAdapterBasics(unittest.TestCase):
    """测试基础方法"""

    def setUp(self):
        """每个测试前执行"""
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_entity_type(self):
        """测试entity_type属性"""
        self.assertEqual(self.adapter.entity_type, "ECN")

    def test_get_entity_success(self):
        """测试成功获取ECN实体"""
        # 准备mock数据
        mock_ecn = MagicMock(spec=Ecn)
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-2024-001"
        
        # 配置mock query
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        # 执行测试
        result = self.adapter.get_entity(1)
        
        # 验证结果
        self.assertEqual(result, mock_ecn)
        self.mock_db.query.assert_called_once_with(Ecn)

    def test_get_entity_not_found(self):
        """测试ECN不存在的情况"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_entity(999)
        
        self.assertIsNone(result)

    def test_get_title(self):
        """测试生成审批标题"""
        # 准备mock ECN
        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN-2024-001"
        mock_ecn.ecn_title = "变更设计规格"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        # 执行测试
        result = self.adapter.get_title(1)
        
        # 验证结果
        self.assertEqual(result, "ECN审批 - ECN-2024-001: 变更设计规格")

    def test_get_title_ecn_not_found(self):
        """测试ECN不存在时的标题"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_title(999)
        
        self.assertEqual(result, "ECN审批 - #999")


class TestEcnApprovalAdapterGetEntityData(unittest.TestCase):
    """测试get_entity_data方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_get_entity_data_full(self):
        """测试获取完整ECN数据"""
        # 准备mock ECN
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-2024-001"
        mock_ecn.ecn_title = "变更设计"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.status = "EVALUATING"
        mock_ecn.project_id = 10
        mock_ecn.machine_id = 20
        mock_ecn.source_type = "ISSUE"
        mock_ecn.source_no = "ISS-001"
        mock_ecn.priority = "HIGH"
        mock_ecn.urgency = "URGENT"
        mock_ecn.cost_impact = Decimal("5000.00")
        mock_ecn.schedule_impact_days = 3
        mock_ecn.quality_impact = "LOW"
        mock_ecn.applicant_id = 100
        mock_ecn.applicant_dept = "研发部"
        mock_ecn.root_cause = "DESIGN_ERROR"
        mock_ecn.root_cause_category = "设计缺陷"
        
        # Mock关联对象
        mock_ecn.project = MagicMock()
        mock_ecn.project.project_code = "PRJ-001"
        mock_ecn.project.project_name = "测试项目"
        
        mock_ecn.applicant = MagicMock()
        mock_ecn.applicant.name = "张三"
        
        # Mock evaluations
        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"
        mock_eval1.eval_dept = "工程部"
        mock_eval1.cost_estimate = Decimal("2000.00")
        mock_eval1.schedule_estimate = 2
        
        mock_eval2 = MagicMock()
        mock_eval2.status = "PENDING"
        mock_eval2.eval_dept = "采购部"
        mock_eval2.cost_estimate = Decimal("1000.00")
        mock_eval2.schedule_estimate = 1
        
        evaluations = [mock_eval1, mock_eval2]
        
        # 配置mock
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        self.mock_db.query.return_value.filter.return_value.all.return_value = evaluations
        
        # 执行测试
        result = self.adapter.get_entity_data(1)
        
        # 验证结果
        self.assertEqual(result["ecn_no"], "ECN-2024-001")
        self.assertEqual(result["ecn_type"], "DESIGN")
        self.assertEqual(result["priority"], "HIGH")
        self.assertEqual(result["cost_impact"], 5000.00)
        self.assertEqual(result["schedule_impact_days"], 3)
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["applicant_name"], "张三")
        
        # 验证evaluation_summary
        eval_summary = result["evaluation_summary"]
        self.assertEqual(eval_summary["total_evaluations"], 2)
        self.assertEqual(eval_summary["completed_evaluations"], 1)
        self.assertEqual(eval_summary["pending_evaluations"], 1)
        self.assertEqual(eval_summary["total_cost_estimate"], 3000.00)
        self.assertEqual(eval_summary["total_schedule_estimate"], 3)
        self.assertIn("工程部", eval_summary["departments"])
        self.assertIn("采购部", eval_summary["departments"])

    def test_get_entity_data_not_found(self):
        """测试ECN不存在的情况"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_entity_data(999)
        
        self.assertEqual(result, {})

    def test_get_entity_data_no_project(self):
        """测试没有关联项目的情况"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN-2024-001"
        mock_ecn.project = None
        mock_ecn.applicant = None
        mock_ecn.cost_impact = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.adapter.get_entity_data(1)
        
        self.assertIsNone(result["project_code"])
        self.assertIsNone(result["project_name"])
        self.assertIsNone(result["applicant_name"])
        self.assertEqual(result["cost_impact"], 0)


class TestEcnApprovalAdapterGetSummary(unittest.TestCase):
    """测试get_summary方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_get_summary_full(self):
        """测试生成完整摘要"""
        # 准备mock ECN
        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN-2024-001"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.cost_impact = Decimal("5000.00")
        mock_ecn.schedule_impact_days = 3
        mock_ecn.priority = "HIGH"
        mock_ecn.project = MagicMock()
        mock_ecn.project.project_name = "测试项目"
        mock_ecn.applicant = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.adapter.get_summary(1)
        
        # 验证结果包含所有关键信息
        self.assertIn("类型: DESIGN", result)
        self.assertIn("项目: 测试项目", result)
        self.assertIn("成本影响: ¥5,000.00", result)
        self.assertIn("工期影响: 3天", result)
        self.assertIn("优先级: HIGH", result)

    def test_get_summary_minimal(self):
        """测试最小化摘要"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = None
        mock_ecn.cost_impact = None
        mock_ecn.schedule_impact_days = None
        mock_ecn.priority = None
        mock_ecn.project = None
        mock_ecn.applicant = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.adapter.get_summary(1)
        
        # 空摘要或很短
        self.assertIsInstance(result, str)

    def test_get_summary_ecn_not_found(self):
        """测试ECN不存在时的摘要"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_summary(999)
        
        self.assertEqual(result, "")


class TestEcnApprovalAdapterLifecycleCallbacks(unittest.TestCase):
    """测试生命周期回调方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_on_submit(self):
        """测试提交审批时的回调"""
        mock_ecn = MagicMock()
        mock_instance = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        self.adapter.on_submit(1, mock_instance)
        
        # 验证状态更新
        self.assertEqual(mock_ecn.status, "EVALUATING")
        self.assertEqual(mock_ecn.current_step, "EVALUATION")
        self.mock_db.flush.assert_called_once()

    def test_on_submit_ecn_not_found(self):
        """测试ECN不存在时的提交回调"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_instance = MagicMock()
        
        # 不应该抛出异常
        self.adapter.on_submit(999, mock_instance)
        
        # flush不应被调用
        self.mock_db.flush.assert_not_called()

    def test_on_approved(self):
        """测试审批通过时的回调"""
        mock_ecn = MagicMock()
        mock_instance = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        self.adapter.on_approved(1, mock_instance)
        
        self.assertEqual(mock_ecn.status, "APPROVED")
        self.assertEqual(mock_ecn.approval_result, "APPROVED")
        self.assertEqual(mock_ecn.current_step, "EXECUTION")
        self.mock_db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回时的回调"""
        mock_ecn = MagicMock()
        mock_instance = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        self.adapter.on_rejected(1, mock_instance)
        
        self.assertEqual(mock_ecn.status, "REJECTED")
        self.assertEqual(mock_ecn.approval_result, "REJECTED")
        self.mock_db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回审批时的回调"""
        mock_ecn = MagicMock()
        mock_instance = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        self.adapter.on_withdrawn(1, mock_instance)
        
        self.assertEqual(mock_ecn.status, "DRAFT")
        self.assertIsNone(mock_ecn.current_step)
        self.mock_db.flush.assert_called_once()


class TestEcnApprovalAdapterSubmitForApproval(unittest.TestCase):
    """测试submit_for_approval方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_submit_for_approval_success(self):
        """测试成功提交审批"""
        # 准备mock ECN
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-2024-001"
        mock_ecn.ecn_title = "变更设计"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.applicant_id = 100
        mock_ecn.applicant_name = "张三"
        mock_ecn.project_id = 10
        mock_ecn.impact_analysis = "影响分析"
        mock_ecn.approval_instance_id = None  # 未提交
        
        # Mock evaluations
        mock_eval = MagicMock()
        mock_eval.eval_dept = "工程部"
        mock_eval.evaluator_id = 200
        mock_eval.evaluator_name = "李四"
        mock_eval.impact_analysis = "工程影响"
        mock_eval.cost_estimate = Decimal("1000.00")
        mock_eval.schedule_estimate = 2
        mock_eval.resource_requirement = "资源需求"
        mock_eval.risk_assessment = "风险评估"
        mock_eval.eval_result = "APPROVE"
        mock_eval.eval_opinion = "同意"
        mock_eval.status = "COMPLETED"
        
        # 配置db.query
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_eval]
        
        # Mock WorkflowEngine (在函数内部导入)
        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as mock_workflow_engine_class:
            mock_workflow_engine = MagicMock()
            mock_instance = MagicMock()
            mock_instance.id = 999
            mock_instance.status = "PENDING"
            mock_workflow_engine.create_instance.return_value = mock_instance
            mock_workflow_engine_class.return_value = mock_workflow_engine
            
            # 执行测试
            result = self.adapter.submit_for_approval(
                ecn=mock_ecn,
                initiator_id=100,
                title="自定义标题",
                summary="自定义摘要",
                urgency="URGENT",
                cc_user_ids=[101, 102]
            )
            
            # 验证WorkflowEngine被正确调用
            mock_workflow_engine.create_instance.assert_called_once()
            call_args = mock_workflow_engine.create_instance.call_args
            self.assertEqual(call_args[1]['flow_code'], "ECN_STANDARD")
            self.assertEqual(call_args[1]['business_type'], "ECN")
            self.assertEqual(call_args[1]['business_id'], 1)
            self.assertEqual(call_args[1]['submitted_by'], 100)
            
            # 验证ECN更新
            self.assertEqual(mock_ecn.approval_instance_id, 999)
            self.assertEqual(mock_ecn.approval_status, "PENDING")
            self.mock_db.add.assert_called_with(mock_ecn)
            self.mock_db.commit.assert_called_once()
            
            # 验证返回值
            self.assertEqual(result, mock_instance)

    def test_submit_for_approval_already_submitted(self):
        """测试重复提交"""
        # ECN已经提交过
        mock_ecn = MagicMock()
        mock_ecn.approval_instance_id = 888
        
        mock_existing_instance = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_instance
        
        result = self.adapter.submit_for_approval(
            ecn=mock_ecn,
            initiator_id=100
        )
        
        # 应该返回现有实例
        self.assertEqual(result, mock_existing_instance)


class TestEcnApprovalAdapterSyncFromApprovalInstance(unittest.TestCase):
    """测试sync_from_approval_instance方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_sync_approved(self):
        """测试同步审批通过状态"""
        mock_instance = MagicMock()
        mock_instance.status = "APPROVED"
        mock_instance.completed_at = datetime(2024, 1, 15, 10, 0, 0)
        mock_instance.final_approver_id = 200
        mock_instance.final_comment = "同意变更"
        
        mock_ecn = MagicMock()
        mock_ecn.approval_status = "PENDING"
        
        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)
        
        # 验证状态同步
        self.assertEqual(mock_ecn.approval_status, "APPROVED")
        self.assertEqual(mock_ecn.status, "APPROVED")
        self.assertEqual(mock_ecn.approval_result, "APPROVED")
        self.assertEqual(mock_ecn.approval_date, datetime(2024, 1, 15, 10, 0, 0))
        self.assertEqual(mock_ecn.final_approver_id, 200)
        self.assertEqual(mock_ecn.approval_note, "同意变更")
        
        self.mock_db.add.assert_called_with(mock_ecn)
        self.mock_db.commit.assert_called_once()

    def test_sync_rejected(self):
        """测试同步驳回状态"""
        mock_instance = MagicMock()
        mock_instance.status = "REJECTED"
        mock_instance.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_instance.final_comment = "不同意"
        
        mock_ecn = MagicMock()
        mock_ecn.approval_status = "PENDING"
        
        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)
        
        self.assertEqual(mock_ecn.status, "REJECTED")
        self.assertEqual(mock_ecn.approval_result, "REJECTED")

    def test_sync_cancelled(self):
        """测试同步取消状态"""
        mock_instance = MagicMock()
        mock_instance.status = "CANCELLED"
        mock_instance.final_comment = None
        
        mock_ecn = MagicMock()
        mock_ecn.approval_status = "PENDING"
        
        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)
        
        self.assertEqual(mock_ecn.status, "CANCELLED")
        self.assertEqual(mock_ecn.approval_result, "CANCELLED")


class TestEcnApprovalAdapterCreateApprovalRecords(unittest.TestCase):
    """测试create_ecn_approval_records方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_create_approval_records(self):
        """测试创建审批记录"""
        # Mock ApprovalInstance
        mock_instance = MagicMock()
        mock_instance.id = 100
        
        # Mock ECN
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-2024-001"
        
        # Mock ApprovalTask
        mock_task1 = MagicMock()
        mock_task1.node_id = 1
        mock_task1.assignee_id = 200
        mock_task1.node_name = "部门主管审批"
        mock_task1.due_at = datetime(2024, 1, 20)
        
        mock_task2 = MagicMock()
        mock_task2.node_id = 2
        mock_task2.assignee_id = 201
        mock_task2.node_name = "总经理审批"
        mock_task2.due_at = None
        
        tasks = [mock_task1, mock_task2]
        
        # Mock User
        mock_user1 = MagicMock()
        mock_user1.real_name = "张三"
        
        mock_user2 = MagicMock()
        mock_user2.real_name = "李四"
        
        # Mock ApprovalNodeDefinition
        mock_node1 = MagicMock()
        mock_node1.node_order = 1
        
        mock_node2 = MagicMock()
        mock_node2.node_order = 2
        
        # 配置mock query - 需要处理多个查询
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ApprovalTask:
                mock_query.filter.return_value.all.return_value = tasks
            elif model == User:
                # 根据filter条件返回不同的user
                def user_filter(*args):
                    filter_mock = MagicMock()
                    # 简化处理：返回mock_user1
                    filter_mock.first.side_effect = [mock_user1, mock_user2]
                    return filter_mock
                mock_query.filter.side_effect = user_filter
            elif model == EcnApproval:
                # 没有现有记录
                mock_query.filter.return_value.first.return_value = None
            elif model == ApprovalNodeDefinition:
                def node_filter(*args):
                    filter_mock = MagicMock()
                    filter_mock.first.side_effect = [mock_node1, mock_node2]
                    return filter_mock
                mock_query.filter.side_effect = node_filter
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行测试
        result = self.adapter.create_ecn_approval_records(mock_instance, mock_ecn)
        
        # 验证创建了2个审批记录
        self.assertEqual(len(result), 2)
        
        # 验证db.add被调用
        self.assertEqual(self.mock_db.add.call_count, 2)
        self.mock_db.commit.assert_called_once()


class TestEcnApprovalAdapterGetApprovers(unittest.TestCase):
    """测试get_ecn_approvers方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_get_ecn_approvers_with_matrix(self):
        """测试使用审批矩阵获取审批人"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "DESIGN"
        
        # Mock matrix
        mock_matrix_item = MagicMock()
        mock_matrix_item.approval_role = "DEPT_MANAGER"
        
        # Mock users
        mock_user1 = MagicMock()
        mock_user1.id = 100
        mock_user2 = MagicMock()
        mock_user2.id = 101
        
        # 简化mock策略 - 配置全局query行为
        # 第一次query().filter().all() - matrix查询
        # 第二次query().join().join().filter().all() - user查询
        matrix_query_result = MagicMock()
        matrix_query_result.filter.return_value.all.return_value = [mock_matrix_item]
        
        user_query_result = MagicMock()
        user_query_result.join.return_value.join.return_value.filter.return_value.all.return_value = [mock_user1, mock_user2]
        
        # 使用call count来区分不同的query调用
        call_count = [0]
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return matrix_query_result
            else:
                return user_query_result
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.adapter.get_ecn_approvers(mock_ecn, level=1)
        
        # 验证返回审批人ID列表
        self.assertIn(100, result)
        self.assertIn(101, result)

    def test_get_ecn_approvers_no_matrix(self):
        """测试无审批矩阵配置"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "DESIGN"
        
        # 没有matrix配置
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.adapter.get_ecn_approvers(mock_ecn, level=1)
        
        # 应该返回空列表
        self.assertEqual(result, [])

    def test_get_ecn_approvers_deduplication(self):
        """测试审批人去重"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "DESIGN"
        
        mock_matrix1 = MagicMock()
        mock_matrix1.approval_role = "MANAGER"
        mock_matrix2 = MagicMock()
        mock_matrix2.approval_role = "DIRECTOR"
        
        # 同一个用户有多个角色
        mock_user = MagicMock()
        mock_user.id = 100
        
        # Mock matrix查询 - 返回2个matrix项
        matrix_query_result = MagicMock()
        matrix_query_result.filter.return_value.all.return_value = [mock_matrix1, mock_matrix2]
        
        # Mock user查询 - 两次都返回同一个用户
        user_query_result = MagicMock()
        user_query_result.join.return_value.join.return_value.filter.return_value.all.return_value = [mock_user]
        
        call_count = [0]
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第一次：matrix查询
                return matrix_query_result
            else:
                # 后续：user查询（会被调用2次，因为有2个matrix项）
                return user_query_result
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.adapter.get_ecn_approvers(mock_ecn, level=1)
        
        # 应该去重
        self.assertEqual(result, [100])


class TestEcnApprovalAdapterUpdateApprovalFromAction(unittest.TestCase):
    """测试update_ecn_approval_from_action方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_update_approval_approve(self):
        """测试更新审批为通过"""
        # Mock task
        mock_task = MagicMock()
        mock_task.node_id = 1
        mock_task.instance = MagicMock()
        mock_task.instance.entity_id = 1
        mock_task.instance.entity = MagicMock()
        
        # Mock approval
        mock_approval = MagicMock()
        mock_approval.ecn_id = 1
        mock_approval.approval_level = 1
        
        # Mock node
        mock_node = MagicMock()
        mock_node.node_order = 1
        
        # 配置query
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ApprovalNodeDefinition:
                mock_query.filter.return_value.first.return_value = mock_node
            elif model == EcnApproval:
                mock_query.filter.return_value.first.return_value = mock_approval
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行测试
        result = self.adapter.update_ecn_approval_from_action(
            task=mock_task,
            action="APPROVE",
            comment="同意"
        )
        
        # 验证结果
        self.assertEqual(result, mock_approval)
        self.assertEqual(mock_approval.approval_result, "APPROVED")
        self.assertEqual(mock_approval.approval_opinion, "同意")
        self.assertEqual(mock_approval.status, "APPROVED")
        self.assertIsNotNone(mock_approval.approved_at)
        
        self.mock_db.add.assert_called_with(mock_approval)
        self.mock_db.commit.assert_called_once()

    def test_update_approval_reject(self):
        """测试更新审批为驳回"""
        mock_task = MagicMock()
        mock_task.node_id = 1
        mock_task.instance = MagicMock()
        mock_task.instance.entity_id = 1
        mock_task.instance.entity = MagicMock()
        
        mock_approval = MagicMock()
        mock_node = MagicMock()
        mock_node.node_order = 1
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ApprovalNodeDefinition:
                mock_query.filter.return_value.first.return_value = mock_node
            elif model == EcnApproval:
                mock_query.filter.return_value.first.return_value = mock_approval
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.adapter.update_ecn_approval_from_action(
            task=mock_task,
            action="REJECT",
            comment="不同意"
        )
        
        self.assertEqual(mock_approval.approval_result, "REJECTED")
        self.assertEqual(mock_approval.status, "REJECTED")

    def test_update_approval_not_found(self):
        """测试审批记录不存在"""
        mock_task = MagicMock()
        mock_task.node_id = 1
        mock_task.instance = MagicMock()
        mock_task.instance.entity_id = 1
        mock_task.instance.entity = MagicMock()
        
        mock_node = MagicMock()
        mock_node.node_order = 1
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ApprovalNodeDefinition:
                mock_query.filter.return_value.first.return_value = mock_node
            elif model == EcnApproval:
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.adapter.update_ecn_approval_from_action(
            task=mock_task,
            action="APPROVE"
        )
        
        # 应该返回None
        self.assertIsNone(result)


class TestEcnApprovalAdapterEvaluators(unittest.TestCase):
    """测试评估相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_get_required_evaluators_design(self):
        """测试DESIGN类型ECN需要的评估部门"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.cost_impact = Decimal("5000.00")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        result = self.adapter.get_required_evaluators(1)
        
        # 应该包含工程部和质量部
        depts = [e["dept"] for e in result]
        self.assertIn("工程部", depts)
        self.assertIn("质量部", depts)

    def test_get_required_evaluators_material(self):
        """测试MATERIAL类型ECN需要的评估部门"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "MATERIAL"
        mock_ecn.cost_impact = Decimal("5000.00")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        result = self.adapter.get_required_evaluators(1)
        
        depts = [e["dept"] for e in result]
        self.assertIn("工程部", depts)
        self.assertIn("采购部", depts)
        self.assertIn("生产部", depts)

    def test_get_required_evaluators_high_cost(self):
        """测试高成本影响需要财务评估"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.cost_impact = Decimal("15000.00")  # > 10000
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        result = self.adapter.get_required_evaluators(1)
        
        depts = [e["dept"] for e in result]
        self.assertIn("财务部", depts)

    def test_get_required_evaluators_not_found(self):
        """测试ECN不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_required_evaluators(999)
        
        self.assertEqual(result, [])

    def test_create_evaluation_tasks(self):
        """测试创建评估任务"""
        mock_ecn = MagicMock()
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.cost_impact = Decimal("5000.00")
        
        mock_instance = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn
        
        result = self.adapter.create_evaluation_tasks(1, mock_instance)
        
        # 应该创建了评估任务
        self.assertGreater(len(result), 0)
        
        # 验证db.add被调用
        self.assertGreater(self.mock_db.add.call_count, 0)
        self.mock_db.flush.assert_called_once()

    def test_check_evaluation_complete_all_done(self):
        """测试所有评估完成"""
        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"
        mock_eval1.eval_dept = "工程部"
        mock_eval1.eval_result = "APPROVE"
        mock_eval1.cost_estimate = Decimal("1000.00")
        mock_eval1.schedule_estimate = 2
        
        mock_eval2 = MagicMock()
        mock_eval2.status = "COMPLETED"
        mock_eval2.eval_dept = "采购部"
        mock_eval2.eval_result = "APPROVE"
        mock_eval2.cost_estimate = Decimal("2000.00")
        mock_eval2.schedule_estimate = 3
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_eval1, mock_eval2
        ]
        
        is_complete, summary = self.adapter.check_evaluation_complete(1)
        
        # 验证结果
        self.assertTrue(is_complete)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["pending"], 0)
        self.assertEqual(summary["completed"], 2)
        self.assertEqual(summary["total_cost"], 3000.00)
        self.assertEqual(summary["total_days"], 5)
        self.assertTrue(summary["all_approved"])

    def test_check_evaluation_complete_has_pending(self):
        """测试有待评估项"""
        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"
        mock_eval1.eval_dept = "工程部"
        mock_eval1.eval_result = "APPROVE"
        mock_eval1.cost_estimate = Decimal("1000.00")
        mock_eval1.schedule_estimate = 2
        
        mock_eval2 = MagicMock()
        mock_eval2.status = "PENDING"
        mock_eval2.eval_dept = "采购部"
        mock_eval2.cost_estimate = None
        mock_eval2.schedule_estimate = None
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_eval1, mock_eval2
        ]
        
        is_complete, summary = self.adapter.check_evaluation_complete(1)
        
        self.assertFalse(is_complete)
        self.assertEqual(summary["pending"], 1)
        self.assertIn("采购部", summary["pending_depts"])

    def test_check_evaluation_complete_no_evaluations(self):
        """测试无评估"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        is_complete, summary = self.adapter.check_evaluation_complete(1)
        
        self.assertFalse(is_complete)
        self.assertEqual(summary, {})


class TestEcnApprovalAdapterDetermineApprovalLevel(unittest.TestCase):
    """测试_determine_approval_level方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.mock_db)

    def test_determine_approval_level(self):
        """测试确定审批层级"""
        mock_ecn = MagicMock()
        
        mock_node = MagicMock()
        mock_node.node_order = 2
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_node
        
        result = self.adapter._determine_approval_level(10, mock_ecn)
        
        self.assertEqual(result, 2)

    def test_determine_approval_level_node_not_found(self):
        """测试节点不存在时默认返回1"""
        mock_ecn = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter._determine_approval_level(999, mock_ecn)
        
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
