# -*- coding: utf-8 -*-
"""
合同审批服务层单元测试

测试 ContractApprovalService 的核心业务逻辑
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.contract_approval import ContractApprovalService


class TestContractApprovalService(unittest.TestCase):
    """合同审批服务测试类"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.service = ContractApprovalService(self.mock_db)

    def test_submit_contracts_for_approval_success(self):
        """测试成功提交合同审批"""
        # 准备测试数据
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.status = "DRAFT"
        mock_contract.contract_amount = Decimal("100000.00")
        mock_contract.contract_code = "CT-2024-001"
        mock_contract.customer_contract_no = "CUST-001"
        mock_contract.customer_id = 10
        mock_contract.project_id = 20
        mock_contract.customer.name = "测试客户"
        mock_contract.signed_date = datetime(2024, 1, 1)
        mock_contract.payment_terms_summary = "30天付款"
        mock_contract.acceptance_summary = "验收通过"

        # 模拟查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        # 模拟审批引擎
        mock_instance = MagicMock()
        mock_instance.id = 100
        self.service.engine.submit = MagicMock(return_value=mock_instance)

        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[1],
            initiator_id=999,
            urgency="HIGH",
        )

        # 验证
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(results[0]["contract_id"], 1)
        self.assertEqual(results[0]["instance_id"], 100)
        self.service.engine.submit.assert_called_once()

    def test_submit_contracts_for_approval_invalid_status(self):
        """测试提交状态不允许的合同"""
        # 准备测试数据 - 已审批的合同
        mock_contract = MagicMock()
        mock_contract.id = 2
        mock_contract.status = "APPROVED"
        mock_contract.contract_amount = Decimal("100000.00")

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[2],
            initiator_id=999,
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不允许提交审批", errors[0]["error"])

    def test_submit_contracts_for_approval_invalid_amount(self):
        """测试提交金额无效的合同"""
        # 准备测试数据 - 金额为0
        mock_contract = MagicMock()
        mock_contract.id = 3
        mock_contract.status = "DRAFT"
        mock_contract.contract_amount = Decimal("0")

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[3],
            initiator_id=999,
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("金额必须大于0", errors[0]["error"])

    def test_submit_contracts_for_approval_not_found(self):
        """测试提交不存在的合同"""
        # 模拟查询返回 None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[999],
            initiator_id=1,
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不存在", errors[0]["error"])

    def test_get_pending_tasks_with_filters(self):
        """测试获取待审批任务（带筛选条件）"""
        # 准备测试数据
        mock_task = MagicMock()
        mock_task.id = 1
        
        mock_instance = MagicMock()
        mock_instance.entity_id = 10
        mock_instance.id = 100
        mock_instance.created_at = datetime(2024, 1, 1)
        mock_instance.urgency = "NORMAL"
        mock_instance.initiator.real_name = "张三"
        mock_task.instance = mock_instance
        
        mock_contract = MagicMock()
        mock_contract.id = 10
        mock_contract.contract_code = "CT-001"
        mock_contract.customer_contract_no = "CUST-001"
        mock_contract.customer_id = 5
        mock_contract.contract_amount = Decimal("50000.00")
        mock_contract.customer.name = "测试客户"
        mock_contract.project.project_name = "测试项目"
        
        mock_task.node.node_name = "部门审批"

        # 模拟 engine 返回任务
        self.service.engine.get_pending_tasks = MagicMock(return_value=[mock_task])

        # 模拟合同查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        # 执行 - 带筛选条件
        items, total = self.service.get_pending_tasks(
            user_id=1,
            page=1,
            page_size=20,
            customer_id=5,
            min_amount=10000.0,
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["contract_id"], 10)

    def test_approve_task(self):
        """测试审批通过"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.service.engine.approve = MagicMock(return_value=mock_result)

        # 执行
        result = self.service.approve_task(
            task_id=1,
            approver_id=999,
            comment="同意",
        )

        # 验证
        self.assertEqual(result.status, "APPROVED")
        self.service.engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=999,
            comment="同意",
        )

    def test_reject_task(self):
        """测试审批驳回"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.service.engine.reject = MagicMock(return_value=mock_result)

        # 执行
        result = self.service.reject_task(
            task_id=2,
            approver_id=999,
            comment="不同意",
        )

        # 验证
        self.assertEqual(result.status, "REJECTED")
        self.service.engine.reject.assert_called_once_with(
            task_id=2,
            approver_id=999,
            comment="不同意",
        )

    def test_batch_approve_or_reject_success(self):
        """测试批量审批成功"""
        self.service.engine.approve = MagicMock()
        self.service.engine.reject = MagicMock()

        # 执行 - 批量通过
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1, 2, 3],
            approver_id=999,
            action="approve",
            comment="批量同意",
        )

        # 验证
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.service.engine.approve.call_count, 3)

    def test_batch_approve_or_reject_with_errors(self):
        """测试批量审批部分失败"""
        # 第2个任务失败
        def approve_side_effect(task_id, approver_id, comment):
            if task_id == 2:
                raise ValueError("任务不存在")
            return MagicMock()

        self.service.engine.approve = MagicMock(side_effect=approve_side_effect)

        # 执行
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1, 2, 3],
            approver_id=999,
            action="approve",
        )

        # 验证
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("任务不存在", errors[0]["error"])

    def test_batch_approve_or_reject_invalid_action(self):
        """测试批量审批操作类型无效"""
        # 执行 - 无效的操作类型
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1],
            approver_id=999,
            action="invalid_action",
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不支持的操作", errors[0]["error"])

    def test_get_contract_approval_status_success(self):
        """测试查询合同审批状态成功"""
        # 准备测试数据
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_code = "CT-001"
        mock_contract.customer_contract_no = "CUST-001"
        mock_contract.status = "PENDING_APPROVAL"
        mock_contract.contract_amount = Decimal("100000.00")
        mock_contract.customer.name = "测试客户"

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1)
        mock_instance.completed_at = None

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "PENDING"
        mock_task.action = None
        mock_task.comment = None
        mock_task.completed_at = None
        mock_task.node.node_name = "部门审批"
        mock_task.assignee.real_name = "审批人"

        # 模拟查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_contract
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_instance
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

        # 执行
        result = self.service.get_contract_approval_status(1)

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result["contract_id"], 1)
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(len(result["task_history"]), 1)

    def test_get_contract_approval_status_not_found(self):
        """测试查询不存在的合同审批状态"""
        # 模拟合同不存在
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行并验证异常
        with self.assertRaises(ValueError) as context:
            self.service.get_contract_approval_status(999)

        self.assertIn("不存在", str(context.exception))

    def test_get_contract_approval_status_no_instance(self):
        """测试查询无审批记录的合同"""
        # 准备测试数据 - 合同存在但无审批实例
        mock_contract = MagicMock()
        mock_contract.id = 1

        # 第一次查询返回合同，第二次查询返回 None（无审批实例）
        query_mock = self.mock_db.query.return_value.filter.return_value
        
        # 配置不同的调用返回不同的值
        def first_side_effect():
            # 第一次调用返回合同，后续返回 None
            if not hasattr(first_side_effect, 'called'):
                first_side_effect.called = True
                return mock_contract
            return None
        
        query_mock.first.side_effect = first_side_effect
        query_mock.order_by.return_value.first.return_value = None

        # 执行
        result = self.service.get_contract_approval_status(1)

        # 验证
        self.assertIsNone(result)

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        # 准备测试数据
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_code = "CT-001"

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 999
        mock_instance.status = "PENDING"

        # 模拟查询
        query_mock = self.mock_db.query.return_value.filter.return_value
        
        # 第一次返回合同，第二次返回审批实例
        query_mock.first.side_effect = [mock_contract, mock_instance]

        # 模拟引擎撤回
        self.service.engine.withdraw = MagicMock()

        # 执行
        result = self.service.withdraw_approval(
            contract_id=1,
            user_id=999,
            reason="需要修改",
        )

        # 验证
        self.assertEqual(result["contract_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once()

    def test_withdraw_approval_not_initiator(self):
        """测试撤回非本人发起的审批"""
        # 准备测试数据
        mock_contract = MagicMock()
        mock_contract.id = 1

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 888  # 不同的发起人

        # 模拟查询
        query_mock = self.mock_db.query.return_value.filter.return_value
        query_mock.first.side_effect = [mock_contract, mock_instance]

        # 执行并验证异常
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(
                contract_id=1,
                user_id=999,  # 不是发起人
            )

        self.assertIn("只能撤回自己", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回无进行中审批的合同"""
        # 准备测试数据
        mock_contract = MagicMock()
        mock_contract.id = 1

        # 模拟查询 - 合同存在，但无进行中的审批
        query_mock = self.mock_db.query.return_value.filter.return_value
        query_mock.first.side_effect = [mock_contract, None]

        # 执行并验证异常
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(contract_id=1, user_id=999)

        self.assertIn("没有进行中", str(context.exception))

    def test_get_approval_history_success(self):
        """测试获取审批历史成功"""
        # 准备测试数据
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.action = "APPROVE"
        mock_task.status = "APPROVED"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 10)

        mock_instance = MagicMock()
        mock_instance.entity_id = 10
        mock_task.instance = mock_instance

        mock_contract = MagicMock()
        mock_contract.id = 10
        mock_contract.contract_code = "CT-001"
        mock_contract.contract_amount = Decimal("100000.00")
        mock_contract.customer.name = "测试客户"

        # 模拟查询
        query_chain = (
            self.mock_db.query.return_value
            .join.return_value
            .filter.return_value
        )
        query_chain.count.return_value = 1
        query_chain.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_task]
        
        # 模拟合同查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        # 执行
        items, total = self.service.get_approval_history(
            user_id=999,
            page=1,
            page_size=20,
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["status"], "APPROVED")

    def test_get_approval_history_with_status_filter(self):
        """测试获取审批历史带状态筛选"""
        # 模拟空结果
        query_chain = (
            self.mock_db.query.return_value
            .join.return_value
            .filter.return_value
            .filter.return_value
        )
        query_chain.count.return_value = 0
        query_chain.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        # 执行
        items, total = self.service.get_approval_history(
            user_id=999,
            page=1,
            page_size=20,
            status_filter="REJECTED",
        )

        # 验证
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)


if __name__ == "__main__":
    unittest.main()
