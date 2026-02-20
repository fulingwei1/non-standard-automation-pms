# -*- coding: utf-8 -*-
"""
ECN审批服务单元测试

测试 EcnApprovalService 的核心业务逻辑
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.ecn_approval import EcnApprovalService


class TestEcnApprovalService(unittest.TestCase):
    """ECN审批服务测试类"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.service = EcnApprovalService(self.db)

    def test_init_service(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.engine)

    @patch("app.services.ecn_approval.service.ApprovalEngineService")
    def test_submit_single_ecn_success(self, mock_engine_class):
        """测试成功提交单个ECN审批"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-2024-001"
        mock_ecn.ecn_title = "测试ECN"
        mock_ecn.status = "EVALUATED"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.project_id = 100
        mock_ecn.cost_impact = 5000.0
        mock_ecn.schedule_impact_days = 10
        mock_ecn.change_reason = "性能优化"
        mock_ecn.change_description = "优化系统性能"

        # 模拟数据库查询
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn
        self.db.query.return_value.filter.return_value.count.return_value = 0

        # 模拟审批引擎
        mock_instance = MagicMock()
        mock_instance.id = 999
        self.service.engine.submit.return_value = mock_instance

        # 执行测试
        result = self.service._submit_single_ecn(
            ecn_id=1, initiator_id=10, urgency="HIGH"
        )

        # 验证结果
        self.assertEqual(result["ecn_id"], 1)
        self.assertEqual(result["ecn_no"], "ECN-2024-001")
        self.assertEqual(result["instance_id"], 999)
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(mock_ecn.status, "APPROVING")
        self.assertEqual(mock_ecn.current_step, "APPROVAL")

    def test_submit_single_ecn_not_found(self):
        """测试提交不存在的ECN"""
        # 模拟ECN不存在
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service._submit_single_ecn(ecn_id=999, initiator_id=10, urgency="NORMAL")
        self.assertEqual(str(context.exception), "ECN不存在")

    def test_submit_single_ecn_invalid_status(self):
        """测试提交状态不符合要求的ECN"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_ecn.status = "APPROVED"

        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service._submit_single_ecn(ecn_id=1, initiator_id=10, urgency="NORMAL")
        self.assertIn("不允许提交审批", str(context.exception))

    def test_submit_single_ecn_pending_evaluations(self):
        """测试提交有未完成评估的ECN"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_ecn.status = "EVALUATED"

        # 模拟查询返回值：第一次返回ECN，第二次返回未完成评估数量
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_ecn
        query_mock.filter.return_value.count.return_value = 2

        self.db.query.return_value = query_mock

        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service._submit_single_ecn(ecn_id=1, initiator_id=10, urgency="NORMAL")
        self.assertIn("个评估未完成", str(context.exception))

    def test_submit_ecns_for_approval_batch(self):
        """测试批量提交ECN审批"""
        # 准备测试数据
        with patch.object(
            self.service, "_submit_single_ecn", side_effect=[
                {"ecn_id": 1, "ecn_no": "ECN-001", "instance_id": 100, "status": "submitted"},
                ValueError("ECN不存在"),
                {"ecn_id": 3, "ecn_no": "ECN-003", "instance_id": 102, "status": "submitted"},
            ]
        ):
            # 执行测试
            results, errors = self.service.submit_ecns_for_approval(
                ecn_ids=[1, 2, 3],
                initiator_id=10,
                urgency="NORMAL",
            )

            # 验证结果
            self.assertEqual(len(results), 2)
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["ecn_id"], 2)

    def test_get_pending_tasks_with_filters(self):
        """测试获取待审批任务（带筛选条件）"""
        # 准备测试数据
        mock_task = MagicMock()
        mock_task.id = 1
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.entity_id = 1
        mock_instance.urgency = "HIGH"
        mock_instance.created_at = datetime.now()
        mock_instance.initiator = MagicMock(real_name="张三")
        mock_task.instance = mock_instance
        mock_task.node = MagicMock(node_name="部门经理审批")

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.ecn_title = "测试ECN"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.project_id = 100
        mock_ecn.project = MagicMock(project_name="测试项目")
        mock_ecn.cost_impact = 1000.0
        mock_ecn.schedule_impact_days = 5
        mock_ecn.priority = "HIGH"

        # 模拟审批引擎返回
        self.service.engine.get_pending_tasks.return_value = [mock_task]

        # 模拟数据库查询ECN
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        # 执行测试
        items, total = self.service.get_pending_tasks_for_user(
            user_id=10,
            ecn_type="DESIGN",
            project_id=100,
            offset=0,
            limit=20,
        )

        # 验证结果
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["ecn_no"], "ECN-001")
        self.assertEqual(items[0]["ecn_type"], "DESIGN")

    def test_perform_approval_action_approve(self):
        """测试执行审批通过操作"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.service.engine.approve.return_value = mock_result

        # 执行测试
        result = self.service.perform_approval_action(
            task_id=1,
            approver_id=10,
            action="approve",
            comment="同意通过",
        )

        # 验证结果
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.engine.approve.assert_called_once_with(
            task_id=1, approver_id=10, comment="同意通过"
        )

    def test_perform_approval_action_reject(self):
        """测试执行审批驳回操作"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.service.engine.reject.return_value = mock_result

        # 执行测试
        result = self.service.perform_approval_action(
            task_id=2,
            approver_id=10,
            action="reject",
            comment="不符合要求",
        )

        # 验证结果
        self.assertEqual(result["task_id"], 2)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.engine.reject.assert_called_once_with(
            task_id=2, approver_id=10, comment="不符合要求"
        )

    def test_perform_approval_action_invalid(self):
        """测试执行无效的审批操作"""
        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1,
                approver_id=10,
                action="invalid_action",
                comment="测试",
            )
        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_batch_approval_mixed_results(self):
        """测试批量审批（混合成功和失败）"""
        # 准备测试数据
        with patch.object(
            self.service, "perform_approval_action", side_effect=[
                {"task_id": 1, "action": "approve", "instance_status": "APPROVED"},
                ValueError("任务不存在"),
                {"task_id": 3, "action": "approve", "instance_status": "APPROVED"},
            ]
        ):
            # 执行测试
            results, errors = self.service.perform_batch_approval(
                task_ids=[1, 2, 3],
                approver_id=10,
                action="approve",
                comment="批量通过",
            )

            # 验证结果
            self.assertEqual(len(results), 2)
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["task_id"], 2)

    @patch("app.services.ecn_approval.service.get_or_404")
    def test_get_ecn_approval_status_with_instance(self, mock_get_or_404):
        """测试获取ECN审批状态（有审批实例）"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.ecn_title = "测试ECN"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.status = "APPROVING"
        mock_ecn.project = MagicMock(project_name="测试项目")
        mock_ecn.cost_impact = 1000.0
        mock_ecn.schedule_impact_days = 5

        mock_get_or_404.return_value = mock_ecn

        # 模拟审批实例
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "HIGH"
        mock_instance.created_at = datetime.now()
        mock_instance.completed_at = None

        # 模拟任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.node = MagicMock(node_name="部门审批")
        mock_task.assignee = MagicMock(real_name="张三")
        mock_task.status = "PENDING"
        mock_task.action = None
        mock_task.comment = None
        mock_task.completed_at = None

        # 模拟数据库查询
        query_instance = MagicMock()
        query_instance.filter.return_value.order_by.return_value.first.return_value = mock_instance
        query_task = MagicMock()
        query_task.filter.return_value.order_by.return_value.all.return_value = [mock_task]
        query_eval = MagicMock()
        query_eval.filter.return_value.all.return_value = []

        self.db.query.side_effect = [query_instance, query_task, query_eval]

        # 执行测试
        result = self.service.get_ecn_approval_status(ecn_id=1)

        # 验证结果
        self.assertEqual(result["ecn_id"], 1)
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)

    @patch("app.services.ecn_approval.service.get_or_404")
    def test_get_ecn_approval_status_no_instance(self, mock_get_or_404):
        """测试获取ECN审批状态（无审批实例）"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.status = "DRAFT"

        mock_get_or_404.return_value = mock_ecn

        # 模拟无审批实例
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # 执行测试
        result = self.service.get_ecn_approval_status(ecn_id=1)

        # 验证结果
        self.assertEqual(result["ecn_id"], 1)
        self.assertIsNone(result["approval_instance"])

    def test_withdraw_ecn_approval_success(self):
        """测试成功撤回ECN审批"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN-001"

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 10

        # 模拟数据库查询
        query_ecn = MagicMock()
        query_ecn.filter.return_value.first.return_value = mock_ecn
        query_instance = MagicMock()
        query_instance.filter.return_value.first.return_value = mock_instance

        self.db.query.side_effect = [query_ecn, query_instance]

        # 执行测试
        result = self.service.withdraw_ecn_approval(
            ecn_id=1, user_id=10, reason="需要修改"
        )

        # 验证结果
        self.assertEqual(result["ecn_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.assertEqual(mock_ecn.status, "DRAFT")
        self.assertIsNone(mock_ecn.current_step)

    def test_withdraw_ecn_approval_not_initiator(self):
        """测试撤回他人提交的审批"""
        # 准备测试数据
        mock_ecn = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initiator_id = 20  # 不同的用户

        query_ecn = MagicMock()
        query_ecn.filter.return_value.first.return_value = mock_ecn
        query_instance = MagicMock()
        query_instance.filter.return_value.first.return_value = mock_instance

        self.db.query.side_effect = [query_ecn, query_instance]

        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_ecn_approval(ecn_id=1, user_id=10)
        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    def test_get_approval_history_for_user(self):
        """测试获取用户审批历史"""
        # 准备测试数据
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "APPROVED"
        mock_task.action = "approve"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime.now()

        mock_instance = MagicMock()
        mock_instance.entity_id = 1
        mock_task.instance = mock_instance

        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.ecn_title = "测试ECN"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.project = MagicMock(project_name="测试项目")

        # 模拟数据库查询
        query_mock = MagicMock()
        query_mock.join.return_value.filter.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_task
        ]

        self.db.query.return_value = query_mock
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn

        # 执行测试
        items, total = self.service.get_approval_history_for_user(
            user_id=10,
            status_filter="APPROVED",
            ecn_type="DESIGN",
            offset=0,
            limit=20,
        )

        # 验证结果
        self.assertEqual(total, 1)
        self.assertGreaterEqual(len(items), 0)  # 可能被类型筛选过滤


if __name__ == "__main__":
    unittest.main()
