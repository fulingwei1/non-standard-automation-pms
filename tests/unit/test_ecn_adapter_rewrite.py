# -*- coding: utf-8 -*-
"""
ECN审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
from app.models.ecn import Ecn, EcnEvaluation, EcnApproval, EcnApprovalMatrix
from app.models.approval import ApprovalInstance, ApprovalTask, ApprovalNodeDefinition
from app.models.project import Project, Machine
from app.models.user import User, Role, UserRole


class TestEcnAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取ECN实体"""
        mock_ecn = MagicMock(spec=Ecn)
        mock_ecn.id = self.entity_id
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_ecn)
        self.db.query.assert_called_once_with(Ecn)

    def test_get_entity_not_found(self):
        """测试获取不存在的ECN"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_basic(self):
        """测试获取基础ECN数据"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-001",
            ecn_title="变更测试",
            ecn_type="DESIGN",
            status="DRAFT",
            priority="HIGH",
            urgency="URGENT",
            cost_impact=Decimal("5000.00"),
            schedule_impact_days=10
        )

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证基础字段
        self.assertEqual(result["ecn_no"], "ECN-2024-001")
        self.assertEqual(result["ecn_title"], "变更测试")
        self.assertEqual(result["ecn_type"], "DESIGN")
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["priority"], "HIGH")
        self.assertEqual(result["urgency"], "URGENT")
        self.assertEqual(result["cost_impact"], 5000.00)
        self.assertEqual(result["schedule_impact_days"], 10)

    def test_get_entity_data_with_project(self):
        """测试获取包含项目信息的ECN数据"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-002",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "测试项目"
        mock_ecn.project = mock_project

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证项目信息
        self.assertEqual(result["project_id"], 10)
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["project_name"], "测试项目")

    def test_get_entity_data_without_project(self):
        """测试ECN没有关联项目"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-003",
            project_id=None
        )
        mock_ecn.project = None

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_entity_data(self.entity_id)

        # 项目相关字段应为None
        self.assertIsNone(result["project_code"])
        self.assertIsNone(result["project_name"])

    def test_get_entity_data_with_applicant(self):
        """测试获取包含申请人信息的ECN数据"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-004",
            applicant_id=5
        )

        mock_user = MagicMock(spec=User)
        mock_user.name = "张三"
        mock_ecn.applicant = mock_user

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证申请人信息
        self.assertEqual(result["applicant_id"], 5)
        self.assertEqual(result["applicant_name"], "张三")

    def test_get_entity_data_without_applicant(self):
        """测试ECN没有申请人"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-005",
            applicant_id=None
        )
        mock_ecn.applicant = None

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_entity_data(self.entity_id)

        # 申请人名称应为None
        self.assertIsNone(result["applicant_name"])

    def test_get_entity_data_with_evaluations(self):
        """测试获取包含评估信息的ECN数据"""
        mock_ecn = self._create_mock_ecn(ecn_no="ECN-2024-006")

        # 创建多个评估记录
        evaluations = [
            self._create_mock_evaluation(
                eval_dept="工程部",
                status="COMPLETED",
                cost_estimate=Decimal("2000.00"),
                schedule_estimate=5
            ),
            self._create_mock_evaluation(
                eval_dept="采购部",
                status="PENDING",
                cost_estimate=Decimal("1000.00"),
                schedule_estimate=3
            ),
            self._create_mock_evaluation(
                eval_dept="生产部",
                status="COMPLETED",
                cost_estimate=Decimal("500.00"),
                schedule_estimate=2
            ),
        ]

        self._setup_query_returns(mock_ecn, evaluations)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证评估汇总
        eval_summary = result["evaluation_summary"]
        self.assertEqual(eval_summary["total_evaluations"], 3)
        self.assertEqual(eval_summary["completed_evaluations"], 2)
        self.assertEqual(eval_summary["pending_evaluations"], 1)
        self.assertEqual(eval_summary["total_cost_estimate"], 3500.00)
        self.assertEqual(eval_summary["total_schedule_estimate"], 10)
        self.assertIn("工程部", eval_summary["departments"])
        self.assertIn("采购部", eval_summary["departments"])
        self.assertIn("生产部", eval_summary["departments"])

    def test_get_entity_data_no_evaluations(self):
        """测试没有评估记录的ECN"""
        mock_ecn = self._create_mock_ecn(ecn_no="ECN-2024-007")

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_entity_data(self.entity_id)

        # 评估汇总应为空
        eval_summary = result["evaluation_summary"]
        self.assertEqual(eval_summary["total_evaluations"], 0)
        self.assertEqual(eval_summary["completed_evaluations"], 0)
        self.assertEqual(eval_summary["pending_evaluations"], 0)
        self.assertEqual(eval_summary["total_cost_estimate"], 0)
        self.assertEqual(eval_summary["total_schedule_estimate"], 0)

    def test_get_entity_data_not_found(self):
        """测试获取不存在ECN的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        # 应返回空字典
        self.assertEqual(result, {})

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_ecn = self._create_mock_ecn(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.on_submit(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_ecn.status, "EVALUATING")
        self.assertEqual(mock_ecn.current_step, "EVALUATION")
        self.db.flush.assert_called_once()

    def test_on_submit_ecn_not_found(self):
        """测试提交不存在的ECN"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试审批通过"""
        mock_ecn = self._create_mock_ecn(status="EVALUATING")
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.on_approved(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_ecn.status, "APPROVED")
        self.assertEqual(mock_ecn.approval_result, "APPROVED")
        self.assertEqual(mock_ecn.current_step, "EXECUTION")
        self.db.flush.assert_called_once()

    def test_on_approved_ecn_not_found(self):
        """测试审批通过不存在的ECN"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试审批驳回"""
        mock_ecn = self._create_mock_ecn(status="EVALUATING")
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_ecn.status, "REJECTED")
        self.assertEqual(mock_ecn.approval_result, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_ecn_not_found(self):
        """测试驳回不存在的ECN"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试撤回审批"""
        mock_ecn = self._create_mock_ecn(status="EVALUATING", current_step="EVALUATION")
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 验证状态恢复
        self.assertEqual(mock_ecn.status, "DRAFT")
        self.assertIsNone(mock_ecn.current_step)
        self.db.flush.assert_called_once()

    def test_on_withdrawn_ecn_not_found(self):
        """测试撤回不存在的ECN"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== get_title() 测试 ==========

    def test_get_title_with_ecn(self):
        """测试生成ECN标题"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-001",
            ecn_title="设计变更"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, "ECN审批 - ECN-2024-001: 设计变更")

    def test_get_title_ecn_not_found(self):
        """测试生成不存在ECN的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, f"ECN审批 - #{self.entity_id}")

    # ========== get_summary() 测试 ==========

    def test_get_summary_full_info(self):
        """测试生成完整摘要"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-001",
            ecn_type="DESIGN",
            project_id=10,
            cost_impact=Decimal("8000.50"),
            schedule_impact_days=15,
            priority="HIGH"
        )

        mock_project = MagicMock(spec=Project)
        mock_project.project_name = "测试项目A"
        mock_ecn.project = mock_project

        evaluations = []
        self._setup_query_returns(mock_ecn, evaluations)

        result = self.adapter.get_summary(self.entity_id)

        # 验证摘要包含所有关键信息
        self.assertIn("类型: DESIGN", result)
        self.assertIn("项目: 测试项目A", result)
        self.assertIn("成本影响: ¥8,000.50", result)
        self.assertIn("工期影响: 15天", result)
        self.assertIn("优先级: HIGH", result)

    def test_get_summary_partial_info(self):
        """测试生成部分信息的摘要"""
        mock_ecn = self._create_mock_ecn(
            ecn_no="ECN-2024-002",
            ecn_type="PROCESS",
            project_id=None,
            cost_impact=None,
            schedule_impact_days=0,
            priority=None
        )
        mock_ecn.project = None

        self._setup_query_returns(mock_ecn, [])

        result = self.adapter.get_summary(self.entity_id)

        # 只包含有值的字段
        self.assertIn("类型: PROCESS", result)
        self.assertNotIn("项目:", result)
        self.assertNotIn("成本影响:", result)
        self.assertNotIn("工期影响:", result)
        self.assertNotIn("优先级:", result)

    def test_get_summary_ecn_not_found(self):
        """测试生成不存在ECN的摘要"""
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_summary(self.entity_id)

        self.assertEqual(result, "")

    # ========== get_required_evaluators() 测试 ==========

    def test_get_required_evaluators_design_type(self):
        """测试设计类ECN的评估部门"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="DESIGN",
            cost_impact=Decimal("5000.00")
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 设计类需要：工程部 + 质量部
        dept_names = [e["dept"] for e in evaluators]
        self.assertIn("工程部", dept_names)
        self.assertIn("质量部", dept_names)

    def test_get_required_evaluators_material_type(self):
        """测试物料类ECN的评估部门"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="MATERIAL",
            cost_impact=Decimal("3000.00")
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 物料类需要：工程部 + 采购部 + 生产部
        dept_names = [e["dept"] for e in evaluators]
        self.assertIn("工程部", dept_names)
        self.assertIn("采购部", dept_names)
        self.assertIn("生产部", dept_names)

    def test_get_required_evaluators_supplier_type(self):
        """测试供应商类ECN的评估部门"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="SUPPLIER",
            cost_impact=Decimal("2000.00")
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 供应商类需要：工程部 + 采购部
        dept_names = [e["dept"] for e in evaluators]
        self.assertIn("工程部", dept_names)
        self.assertIn("采购部", dept_names)

    def test_get_required_evaluators_process_type(self):
        """测试工艺类ECN的评估部门"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="PROCESS",
            cost_impact=Decimal("1000.00")
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 工艺类需要：工程部 + 生产部
        dept_names = [e["dept"] for e in evaluators]
        self.assertIn("工程部", dept_names)
        self.assertIn("生产部", dept_names)

    def test_get_required_evaluators_spec_type(self):
        """测试规格类ECN的评估部门"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="SPEC",
            cost_impact=Decimal("500.00")
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 规格类需要：工程部 + 质量部
        dept_names = [e["dept"] for e in evaluators]
        self.assertIn("工程部", dept_names)
        self.assertIn("质量部", dept_names)

    def test_get_required_evaluators_high_cost_adds_finance(self):
        """测试高成本影响添加财务部评估"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="DESIGN",
            cost_impact=Decimal("15000.00")  # > 10000
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 成本超过10000需要财务部评估
        dept_names = [e["dept"] for e in evaluators]
        self.assertIn("财务部", dept_names)

    def test_get_required_evaluators_low_cost_no_finance(self):
        """测试低成本影响不添加财务部"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="DESIGN",
            cost_impact=Decimal("5000.00")  # <= 10000
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 不应包含财务部
        dept_names = [e["dept"] for e in evaluators]
        self.assertNotIn("财务部", dept_names)

    def test_get_required_evaluators_ecn_not_found(self):
        """测试获取不存在ECN的评估部门"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        evaluators = self.adapter.get_required_evaluators(self.entity_id)

        # 应返回空列表
        self.assertEqual(evaluators, [])

    # ========== create_evaluation_tasks() 测试 ==========

    def test_create_evaluation_tasks_success(self):
        """测试成功创建评估任务"""
        mock_ecn = self._create_mock_ecn(ecn_type="DESIGN")
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluations = self.adapter.create_evaluation_tasks(self.entity_id, self.instance)

        # 设计类ECN应创建工程部和质量部评估任务
        self.assertEqual(len(evaluations), 2)
        self.assertEqual(evaluations[0].ecn_id, self.entity_id)
        self.assertEqual(evaluations[0].status, "PENDING")
        self.db.add.assert_called()
        self.db.flush.assert_called_once()

    def test_create_evaluation_tasks_material_type(self):
        """测试物料类ECN创建多个评估任务"""
        mock_ecn = self._create_mock_ecn(
            ecn_type="MATERIAL",
            cost_impact=Decimal("15000.00")
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        evaluations = self.adapter.create_evaluation_tasks(self.entity_id, self.instance)

        # 物料类 + 高成本：工程部、采购部、生产部、财务部
        self.assertEqual(len(evaluations), 4)

    # ========== check_evaluation_complete() 测试 ==========

    def test_check_evaluation_complete_all_done(self):
        """测试所有评估完成"""
        evaluations = [
            self._create_mock_evaluation(
                eval_dept="工程部",
                status="COMPLETED",
                eval_result="APPROVE",
                cost_estimate=Decimal("1000.00"),
                schedule_estimate=5
            ),
            self._create_mock_evaluation(
                eval_dept="采购部",
                status="COMPLETED",
                eval_result="APPROVE",
                cost_estimate=Decimal("2000.00"),
                schedule_estimate=3
            ),
        ]

        self.db.query.return_value.filter.return_value.all.return_value = evaluations

        is_complete, summary = self.adapter.check_evaluation_complete(self.entity_id)

        # 验证完成状态
        self.assertTrue(is_complete)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["pending"], 0)
        self.assertEqual(summary["completed"], 2)
        self.assertEqual(summary["total_cost"], 3000.00)
        self.assertEqual(summary["total_days"], 8)
        self.assertTrue(summary["all_approved"])

    def test_check_evaluation_complete_has_pending(self):
        """测试有未完成的评估"""
        evaluations = [
            self._create_mock_evaluation(
                eval_dept="工程部",
                status="COMPLETED",
                eval_result="APPROVE"
            ),
            self._create_mock_evaluation(
                eval_dept="采购部",
                status="PENDING",
                eval_result=None
            ),
        ]

        self.db.query.return_value.filter.return_value.all.return_value = evaluations

        is_complete, summary = self.adapter.check_evaluation_complete(self.entity_id)

        # 验证未完成状态
        self.assertFalse(is_complete)
        self.assertEqual(summary["pending"], 1)
        self.assertEqual(summary["pending_depts"], ["采购部"])

    def test_check_evaluation_complete_has_rejection(self):
        """测试有评估拒绝"""
        evaluations = [
            self._create_mock_evaluation(
                eval_dept="工程部",
                status="COMPLETED",
                eval_result="APPROVE"
            ),
            self._create_mock_evaluation(
                eval_dept="采购部",
                status="COMPLETED",
                eval_result="REJECT"
            ),
        ]

        self.db.query.return_value.filter.return_value.all.return_value = evaluations

        is_complete, summary = self.adapter.check_evaluation_complete(self.entity_id)

        # 完成但不是全部通过
        self.assertTrue(is_complete)
        self.assertFalse(summary["all_approved"])

    def test_check_evaluation_complete_no_evaluations(self):
        """测试没有评估记录"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        is_complete, summary = self.adapter.check_evaluation_complete(self.entity_id)

        # 没有评估记录返回False
        self.assertFalse(is_complete)
        self.assertEqual(summary, {})

    # ========== sync_from_approval_instance() 测试 ==========

    def test_sync_from_approval_instance_approved(self):
        """测试同步审批通过状态"""
        mock_ecn = self._create_mock_ecn(approval_status="PENDING")
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.status = "APPROVED"
        mock_instance.completed_at = datetime(2024, 1, 15, 10, 0, 0)
        mock_instance.final_approver_id = 100
        mock_instance.final_comment = "批准执行"

        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)

        # 验证状态同步
        self.assertEqual(mock_ecn.approval_status, "APPROVED")
        self.assertEqual(mock_ecn.status, "APPROVED")
        self.assertEqual(mock_ecn.approval_result, "APPROVED")
        self.assertEqual(mock_ecn.approval_date, mock_instance.completed_at)
        self.assertEqual(mock_ecn.final_approver_id, 100)
        self.assertEqual(mock_ecn.approval_note, "批准执行")
        self.db.add.assert_called_once_with(mock_ecn)
        self.db.commit.assert_called_once()

    def test_sync_from_approval_instance_rejected(self):
        """测试同步审批驳回状态"""
        mock_ecn = self._create_mock_ecn(approval_status="PENDING")
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.status = "REJECTED"
        mock_instance.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_instance.final_comment = "需要重新评估"

        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)

        # 验证驳回状态
        self.assertEqual(mock_ecn.approval_status, "REJECTED")
        self.assertEqual(mock_ecn.status, "REJECTED")
        self.assertEqual(mock_ecn.approval_result, "REJECTED")
        self.assertEqual(mock_ecn.approval_note, "需要重新评估")

    def test_sync_from_approval_instance_cancelled(self):
        """测试同步取消状态"""
        mock_ecn = self._create_mock_ecn(approval_status="PENDING")
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.status = "CANCELLED"
        mock_instance.completed_at = None
        mock_instance.final_comment = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)

        # 验证取消状态
        self.assertEqual(mock_ecn.approval_status, "CANCELLED")
        self.assertEqual(mock_ecn.status, "CANCELLED")
        self.assertEqual(mock_ecn.approval_result, "CANCELLED")

    def test_sync_from_approval_instance_terminated(self):
        """测试同步终止状态"""
        mock_ecn = self._create_mock_ecn(approval_status="PENDING")
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.status = "TERMINATED"
        mock_instance.completed_at = None
        mock_instance.final_comment = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        self.adapter.sync_from_approval_instance(mock_instance, mock_ecn)

        # 验证终止状态
        self.assertEqual(mock_ecn.approval_status, "TERMINATED")
        self.assertEqual(mock_ecn.status, "TERMINATED")
        self.assertEqual(mock_ecn.approval_result, "TERMINATED")

    # ========== _determine_approval_level() 测试 ==========

    def test_determine_approval_level_with_node(self):
        """测试根据节点确定审批层级"""
        mock_ecn = self._create_mock_ecn()
        
        mock_node = MagicMock(spec=ApprovalNodeDefinition)
        mock_node.node_order = 2

        self.db.query.return_value.filter.return_value.first.return_value = mock_node

        level = self.adapter._determine_approval_level(10, mock_ecn)

        # 应使用node_order
        self.assertEqual(level, 2)

    def test_determine_approval_level_node_not_found(self):
        """测试节点不存在时的默认层级"""
        mock_ecn = self._create_mock_ecn()

        self.db.query.return_value.filter.return_value.first.return_value = None

        level = self.adapter._determine_approval_level(999, mock_ecn)

        # 默认返回1
        self.assertEqual(level, 1)

    # ========== get_ecn_approvers() 测试 ==========
    # 注意：由于该方法涉及复杂的数据库查询链，这里只测试基本逻辑

    def test_get_ecn_approvers_with_provided_matrix(self):
        """测试使用提供的审批矩阵获取审批人"""
        mock_ecn = self._create_mock_ecn(ecn_type="DESIGN")

        mock_matrix_item = MagicMock(spec=EcnApprovalMatrix)
        mock_matrix_item.approval_role = "ENGINEER_MANAGER"

        # 创建mock用户列表
        mock_user1 = MagicMock()
        mock_user1.id = 10
        mock_user2 = MagicMock()
        mock_user2.id = 20

        # 设置查询链的mock
        mock_query_chain = MagicMock()
        mock_query_chain.join.return_value = mock_query_chain
        mock_query_chain.filter.return_value = mock_query_chain
        mock_query_chain.all.return_value = [mock_user1, mock_user2]
        
        self.db.query.return_value = mock_query_chain

        approvers = self.adapter.get_ecn_approvers(mock_ecn, 1, [mock_matrix_item])

        # 应返回用户ID列表
        self.assertIn(10, approvers)
        self.assertIn(20, approvers)

    def test_get_ecn_approvers_deduplication(self):
        """测试审批人去重"""
        mock_ecn = self._create_mock_ecn(ecn_type="DESIGN")

        mock_matrix_item1 = MagicMock(spec=EcnApprovalMatrix)
        mock_matrix_item1.approval_role = "ROLE_A"

        mock_matrix_item2 = MagicMock(spec=EcnApprovalMatrix)
        mock_matrix_item2.approval_role = "ROLE_B"

        # 模拟重复的用户ID
        call_count = [0]
        
        def create_mock_query():
            mock_query_chain = MagicMock()
            mock_query_chain.join.return_value = mock_query_chain
            mock_query_chain.filter.return_value = mock_query_chain
            call_count[0] += 1
            if call_count[0] == 1:
                u1 = MagicMock()
                u1.id = 10
                u2 = MagicMock()
                u2.id = 20
                mock_query_chain.all.return_value = [u1, u2]
            else:
                u3 = MagicMock()
                u3.id = 20
                u4 = MagicMock()
                u4.id = 30
                mock_query_chain.all.return_value = [u3, u4]
            return mock_query_chain

        self.db.query.side_effect = lambda *args: create_mock_query()

        approvers = self.adapter.get_ecn_approvers(
            mock_ecn, 1, [mock_matrix_item1, mock_matrix_item2]
        )

        # 应去重
        self.assertEqual(set(approvers), {10, 20, 30})

    def test_get_ecn_approvers_query_from_db(self):
        """测试从数据库查询审批矩阵"""
        mock_ecn = self._create_mock_ecn(ecn_type="PROCESS")

        mock_matrix_item = MagicMock(spec=EcnApprovalMatrix)
        mock_matrix_item.approval_role = "ROLE_X"

        call_count = [0]

        def create_mock_query():
            mock_query_chain = MagicMock()
            call_count[0] += 1
            
            if call_count[0] == 1:
                # 第一次调用：查询矩阵
                mock_query_chain.filter.return_value = mock_query_chain
                mock_query_chain.all.return_value = [mock_matrix_item]
            else:
                # 后续调用：查询用户
                mock_query_chain.join.return_value = mock_query_chain
                mock_query_chain.filter.return_value = mock_query_chain
                u = MagicMock()
                u.id = 50
                mock_query_chain.all.return_value = [u]
            
            return mock_query_chain

        self.db.query.side_effect = lambda *args: create_mock_query()

        # 不传matrix参数，应从数据库查询
        approvers = self.adapter.get_ecn_approvers(mock_ecn, 2, None)

        # 应返回查询到的用户
        self.assertIn(50, approvers)

    # ========== submit_for_approval() 测试 ==========

    def test_submit_for_approval_success(self):
        """测试成功提交ECN到审批引擎"""
        # 在方法内部导入，所以需要patch正确的位置
        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as mock_wf_class:
            mock_ecn = self._create_mock_ecn(
                ecn_no="ECN-2024-001",
                ecn_title="测试变更",
                ecn_type="DESIGN",
                approval_instance_id=None
            )

            # Mock评估记录
            evaluations = [
                self._create_mock_evaluation(
                    eval_dept="工程部",
                    evaluator_id=10,
                    evaluator_name="张三",
                    cost_estimate=Decimal("1000.00"),
                    schedule_estimate=5,
                    status="COMPLETED",
                    eval_result="APPROVE"
                ),
            ]

            def query_side_effect(model):
                mock_query = MagicMock()
                if model == Ecn:
                    mock_query.filter.return_value.first.return_value = mock_ecn
                elif model == EcnEvaluation:
                    mock_query.filter.return_value.all.return_value = evaluations
                elif model == ApprovalInstance:
                    mock_query.filter.return_value.first.return_value = None
                return mock_query

            self.db.query.side_effect = query_side_effect

            # Mock WorkflowEngine
            mock_instance = MagicMock(spec=ApprovalInstance)
            mock_instance.id = 100
            mock_instance.status = "PENDING"

            mock_engine = MagicMock()
            mock_engine.create_instance.return_value = mock_instance
            mock_wf_class.return_value = mock_engine

            result = self.adapter.submit_for_approval(
                mock_ecn,
                initiator_id=1,
                title="自定义标题",
                urgency="URGENT"
            )

            # 验证调用
            mock_engine.create_instance.assert_called_once()
            self.assertEqual(mock_ecn.approval_instance_id, 100)
            self.assertEqual(result, mock_instance)
            self.db.add.assert_called_with(mock_ecn)
            self.db.commit.assert_called_once()

    def test_submit_for_approval_already_submitted(self):
        """测试ECN已提交审批"""
        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as mock_wf_class:
            mock_ecn = self._create_mock_ecn(
                ecn_no="ECN-2024-002",
                approval_instance_id=50  # 已有实例ID
            )

            mock_existing_instance = MagicMock(spec=ApprovalInstance)
            mock_existing_instance.id = 50

            self.db.query.return_value.filter.return_value.first.return_value = mock_existing_instance

            result = self.adapter.submit_for_approval(mock_ecn, initiator_id=1)

            # 应返回现有实例，不创建新的
            self.assertEqual(result, mock_existing_instance)
            mock_wf_class.assert_not_called()

    # ========== build_form_data() 辅助方法测试 ==========

    def test_build_form_data_in_submit_for_approval(self):
        """测试在submit_for_approval中构建表单数据"""
        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as mock_wf_class:
            mock_ecn = self._create_mock_ecn(
                id=1,
                ecn_no="ECN-2024-001",
                ecn_title="测试变更",
                ecn_type="DESIGN",
                applicant_id=5,
                project_id=10,
                approval_instance_id=None
            )
            mock_ecn.applicant_name = "李四"
            mock_ecn.impact_analysis = "影响分析内容"

            evaluations = []

            def query_side_effect(model):
                mock_query = MagicMock()
                if model == Ecn:
                    mock_query.filter.return_value.first.return_value = mock_ecn
                elif model == EcnEvaluation:
                    mock_query.filter.return_value.all.return_value = evaluations
                elif model == ApprovalInstance:
                    mock_query.filter.return_value.first.return_value = None
                return mock_query

            self.db.query.side_effect = query_side_effect

            mock_instance = MagicMock(spec=ApprovalInstance)
            mock_instance.id = 100
            mock_engine = MagicMock()
            mock_engine.create_instance.return_value = mock_instance
            mock_wf_class.return_value = mock_engine

            self.adapter.submit_for_approval(mock_ecn, initiator_id=1)

            # 获取create_instance的调用参数
            call_args = mock_engine.create_instance.call_args
            config = call_args.kwargs['config']

            # 验证表单数据
            ecn_data = config['ecn']
            self.assertEqual(ecn_data['ecn_id'], 1)
            self.assertEqual(ecn_data['ecn_no'], "ECN-2024-001")
            self.assertEqual(ecn_data['ecn_title'], "测试变更")
            self.assertEqual(ecn_data['ecn_type'], "DESIGN")
            self.assertEqual(ecn_data['applicant_id'], 5)
            self.assertEqual(ecn_data['project_id'], 10)

    # ========== 辅助方法 ==========

    def _create_mock_ecn(self, **kwargs):
        """创建模拟ECN对象"""
        mock_ecn = MagicMock(spec=Ecn)
        
        defaults = {
            'id': self.entity_id,
            'ecn_no': 'ECN-TEST-001',
            'ecn_title': '测试ECN',
            'ecn_type': 'DESIGN',
            'status': 'DRAFT',
            'priority': 'MEDIUM',
            'urgency': 'NORMAL',
            'cost_impact': None,
            'schedule_impact_days': 0,
            'quality_impact': None,
            'project_id': None,
            'machine_id': None,
            'source_type': None,
            'source_no': None,
            'applicant_id': None,
            'applicant_name': None,  # 添加这个字段
            'applicant_dept': None,
            'root_cause': None,
            'root_cause_category': None,
            'current_step': None,
            'approval_result': None,
            'approval_status': None,
            'approval_instance_id': None,
            'approval_note': None,
            'approval_date': None,
            'final_approver_id': None,
            'impact_analysis': None,  # 添加这个字段
            'project': None,
            'applicant': None,
        }
        
        defaults.update(kwargs)
        
        for key, value in defaults.items():
            setattr(mock_ecn, key, value)
        
        return mock_ecn

    def _create_mock_evaluation(self, **kwargs):
        """创建模拟评估对象"""
        mock_eval = MagicMock(spec=EcnEvaluation)
        
        defaults = {
            'ecn_id': self.entity_id,
            'eval_dept': '工程部',
            'evaluator_id': None,
            'evaluator_name': None,
            'status': 'PENDING',
            'eval_result': None,
            'cost_estimate': None,
            'schedule_estimate': None,
            'impact_analysis': None,
            'resource_requirement': None,
            'risk_assessment': None,
            'eval_opinion': None,
        }
        
        defaults.update(kwargs)
        
        for key, value in defaults.items():
            setattr(mock_eval, key, value)
        
        return mock_eval

    def _setup_query_returns(self, mock_ecn, evaluations):
        """设置基础查询返回"""
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Ecn:
                mock_query.filter.return_value.first.return_value = mock_ecn
            elif model == EcnEvaluation:
                mock_query.filter.return_value.all.return_value = evaluations
            return mock_query

        self.db.query.side_effect = query_side_effect


class TestAdapterEntityType(unittest.TestCase):
    """测试适配器类属性"""

    def test_entity_type(self):
        """测试entity_type类属性"""
        self.assertEqual(EcnApprovalAdapter.entity_type, "ECN")


if __name__ == '__main__':
    unittest.main()
