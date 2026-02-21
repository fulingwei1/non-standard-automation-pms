# -*- coding: utf-8 -*-
"""
合同审批服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作，ApprovalEngineService）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过
5. 覆盖率70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from sqlalchemy.orm import Query

from app.services.contract_approval.service import ContractApprovalService


class TestContractApprovalService(unittest.TestCase):
    """测试合同审批服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ContractApprovalService(self.db)
        
        # Mock ApprovalEngineService
        self.service.engine = MagicMock()

    def _create_mock_contract(
        self,
        contract_id=1,
        contract_code="CT20240001",
        status="DRAFT",
        amount=10000.0,
        customer_id=1,
        project_id=1,
    ):
        """创建Mock合同对象"""
        contract = MagicMock()
        contract.id = contract_id
        contract.contract_code = contract_code
        contract.customer_contract_no = "CUST-001"
        contract.status = status
        contract.contract_amount = Decimal(str(amount))
        contract.customer_id = customer_id
        contract.project_id = project_id
        contract.signed_date = datetime(2024, 1, 15)
        contract.payment_terms_summary = "30天付款"
        contract.acceptance_summary = "验收合格后付款"
        
        # Mock relationships
        contract.customer = MagicMock()
        contract.customer.name = "测试客户"
        contract.project = MagicMock()
        contract.project.project_name = "测试项目"
        
        return contract

    def _create_mock_instance(self, instance_id=1, entity_id=1, status="PENDING"):
        """创建Mock审批实例"""
        instance = MagicMock()
        instance.id = instance_id
        instance.entity_type = "CONTRACT"
        instance.entity_id = entity_id
        instance.status = status
        instance.urgency = "NORMAL"
        instance.created_at = datetime(2024, 1, 20, 10, 0, 0)
        instance.completed_at = None
        instance.initiator_id = 1
        
        instance.initiator = MagicMock()
        instance.initiator.real_name = "张三"
        
        return instance

    def _create_mock_task(self, task_id=1, instance_id=1, status="PENDING"):
        """创建Mock审批任务"""
        task = MagicMock()
        task.id = task_id
        task.instance_id = instance_id
        task.status = status
        task.action = None
        task.comment = None
        task.completed_at = None
        task.assignee_id = 2
        
        task.node = MagicMock()
        task.node.node_name = "部门经理审批"
        
        task.assignee = MagicMock()
        task.assignee.real_name = "李四"
        
        task.instance = self._create_mock_instance(instance_id=instance_id)
        
        return task

    # ========== submit_contracts_for_approval() 测试 ==========

    def test_submit_contracts_for_approval_success(self):
        """测试成功提交合同审批"""
        # 准备数据
        contract = self._create_mock_contract()
        mock_instance = self._create_mock_instance()
        
        # Mock db.query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contract
        self.db.query.return_value = mock_query
        
        # Mock engine.submit
        self.service.engine.submit.return_value = mock_instance
        
        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[1],
            initiator_id=1,
            urgency="URGENT",
            comment="紧急审批"
        )
        
        # 验证
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(results[0]["contract_id"], 1)
        self.assertEqual(results[0]["contract_code"], "CT20240001")
        self.assertEqual(results[0]["instance_id"], 1)
        self.assertEqual(results[0]["status"], "submitted")
        
        # 验证engine.submit被调用
        self.service.engine.submit.assert_called_once()
        call_args = self.service.engine.submit.call_args[1]
        self.assertEqual(call_args["template_code"], "SALES_CONTRACT_APPROVAL")
        self.assertEqual(call_args["entity_type"], "CONTRACT")
        self.assertEqual(call_args["entity_id"], 1)
        self.assertEqual(call_args["initiator_id"], 1)
        self.assertEqual(call_args["urgency"], "URGENT")

    def test_submit_contracts_contract_not_found(self):
        """测试合同不存在"""
        # Mock db.query返回None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[999],
            initiator_id=1
        )
        
        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["contract_id"], 999)
        self.assertEqual(errors[0]["error"], "合同不存在")

    def test_submit_contracts_invalid_status(self):
        """测试合同状态不允许提交审批"""
        # 准备数据 - 已通过的合同
        contract = self._create_mock_contract(status="APPROVED")
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contract
        self.db.query.return_value = mock_query
        
        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[1],
            initiator_id=1
        )
        
        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不允许提交审批", errors[0]["error"])

    def test_submit_contracts_invalid_amount(self):
        """测试合同金额无效"""
        # 准备数据 - 金额为0
        contract = self._create_mock_contract(amount=0)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contract
        self.db.query.return_value = mock_query
        
        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[1],
            initiator_id=1
        )
        
        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"], "合同金额必须大于0")

    def test_submit_contracts_engine_exception(self):
        """测试引擎提交时抛出异常"""
        contract = self._create_mock_contract()
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contract
        self.db.query.return_value = mock_query
        
        # Mock engine抛出异常
        self.service.engine.submit.side_effect = Exception("模板不存在")
        
        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[1],
            initiator_id=1
        )
        
        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"], "模板不存在")

    def test_submit_contracts_batch_mixed_results(self):
        """测试批量提交混合结果"""
        # 准备数据
        contract1 = self._create_mock_contract(contract_id=1, status="DRAFT")
        contract3 = self._create_mock_contract(contract_id=3, status="APPROVED")  # 状态不对
        
        # 使用列表来存储每次查询应返回的结果
        query_results = [contract1, None, contract3]
        query_index = [0]  # 使用列表来存储可变索引
        
        def query_side_effect(model):
            mock_query = MagicMock()
            def filter_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                mock_result.first.return_value = query_results[query_index[0]]
                query_index[0] += 1
                return mock_result
            
            mock_query.filter = filter_side_effect
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        # Mock engine.submit 对contract1成功
        mock_instance = self._create_mock_instance(entity_id=1)
        self.service.engine.submit.return_value = mock_instance
        
        # 执行
        results, errors = self.service.submit_contracts_for_approval(
            contract_ids=[1, 2, 3],
            initiator_id=1
        )
        
        # 验证
        self.assertEqual(len(results), 1)  # contract1成功
        self.assertEqual(len(errors), 2)   # contract2和contract3失败
        self.assertEqual(results[0]["contract_id"], 1)
        self.assertEqual(errors[0]["contract_id"], 2)
        self.assertEqual(errors[1]["contract_id"], 3)

    # ========== _build_contract_form_data() 测试 ==========

    def test_build_contract_form_data(self):
        """测试构建合同表单数据"""
        contract = self._create_mock_contract()
        
        form_data = self.service._build_contract_form_data(contract)
        
        self.assertEqual(form_data["contract_id"], 1)
        self.assertEqual(form_data["contract_code"], "CT20240001")
        self.assertEqual(form_data["customer_contract_no"], "CUST-001")
        self.assertEqual(form_data["contract_amount"], 10000.0)
        self.assertEqual(form_data["customer_id"], 1)
        self.assertEqual(form_data["customer_name"], "测试客户")
        self.assertEqual(form_data["project_id"], 1)
        self.assertEqual(form_data["signed_date"], "2024-01-15T00:00:00")  # isoformat包含时间
        self.assertEqual(form_data["payment_terms_summary"], "30天付款")
        self.assertEqual(form_data["acceptance_summary"], "验收合格后付款")

    def test_build_contract_form_data_with_null_values(self):
        """测试构建表单数据（包含空值）"""
        contract = self._create_mock_contract()
        contract.customer = None
        contract.signed_date = None
        contract.contract_amount = None
        
        form_data = self.service._build_contract_form_data(contract)
        
        self.assertIsNone(form_data["customer_name"])
        self.assertIsNone(form_data["signed_date"])
        self.assertEqual(form_data["contract_amount"], 0)

    # ========== get_pending_tasks() 测试 ==========

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务"""
        # 准备数据
        task = self._create_mock_task()
        contract = self._create_mock_contract()
        
        # Mock engine.get_pending_tasks
        self.service.engine.get_pending_tasks.return_value = [task]
        
        # Mock db.query for contract
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contract
        self.db.query.return_value = mock_query
        
        # 执行
        items, total = self.service.get_pending_tasks(user_id=2)
        
        # 验证
        self.assertEqual(len(items), 1)
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["contract_code"], "CT20240001")
        self.assertEqual(items[0]["customer_name"], "测试客户")
        self.assertEqual(items[0]["node_name"], "部门经理审批")
        
        self.service.engine.get_pending_tasks.assert_called_once_with(
            user_id=2, entity_type="CONTRACT"
        )

    def test_get_pending_tasks_with_filters(self):
        """测试带筛选条件获取任务"""
        task1 = self._create_mock_task(task_id=1)
        task2 = self._create_mock_task(task_id=2)
        
        contract1 = self._create_mock_contract(contract_id=1, customer_id=1, amount=5000)
        contract2 = self._create_mock_contract(contract_id=2, customer_id=2, amount=15000)
        
        self.service.engine.get_pending_tasks.return_value = [task1, task2]
        
        # Mock db.query返回不同的合同
        def query_side_effect(model):
            mock_query = MagicMock()
            def filter_side_effect(*args, **kwargs):
                if not hasattr(filter_side_effect, 'call_count'):
                    filter_side_effect.call_count = 0
                filter_side_effect.call_count += 1
                
                mock_result = MagicMock()
                if filter_side_effect.call_count <= 2:
                    mock_result.first.return_value = contract1
                else:
                    mock_result.first.return_value = contract2
                return mock_result
            
            mock_query.filter = filter_side_effect
            return mock_query
        
        self.db.query = query_side_effect
        
        # 执行 - 筛选customer_id=1且金额>=10000
        items, total = self.service.get_pending_tasks(
            user_id=2,
            customer_id=1,
            min_amount=10000.0
        )
        
        # 验证 - contract1金额5000不满足，contract2客户ID不满足
        # 所以都会被过滤掉
        self.assertEqual(len(items), 0)
        self.assertEqual(total, 0)

    def test_get_pending_tasks_pagination(self):
        """测试分页功能"""
        # 创建3个任务
        tasks = [self._create_mock_task(task_id=i) for i in range(1, 4)]
        contract = self._create_mock_contract()
        
        self.service.engine.get_pending_tasks.return_value = tasks
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contract
        self.db.query.return_value = mock_query
        
        # 执行 - 第2页，每页1条
        items, total = self.service.get_pending_tasks(
            user_id=2,
            page=2,
            page_size=1
        )
        
        # 验证
        self.assertEqual(len(items), 1)
        self.assertEqual(total, 3)
        self.assertEqual(items[0]["task_id"], 2)  # 第2页第1条

    def test_get_pending_tasks_contract_not_found(self):
        """测试合同不存在的任务会被跳过"""
        task = self._create_mock_task()
        
        self.service.engine.get_pending_tasks.return_value = [task]
        
        # Mock db.query返回None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        # 执行
        items, total = self.service.get_pending_tasks(user_id=2)
        
        # 验证 - 任务被跳过
        self.assertEqual(len(items), 0)
        self.assertEqual(total, 0)

    # ========== approve_task() 测试 ==========

    def test_approve_task(self):
        """测试审批通过"""
        mock_result = {"status": "success"}
        self.service.engine.approve.return_value = mock_result
        
        result = self.service.approve_task(
            task_id=1,
            approver_id=2,
            comment="同意"
        )
        
        self.assertEqual(result, mock_result)
        self.service.engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=2,
            comment="同意"
        )

    # ========== reject_task() 测试 ==========

    def test_reject_task(self):
        """测试审批驳回"""
        mock_result = {"status": "rejected"}
        self.service.engine.reject.return_value = mock_result
        
        result = self.service.reject_task(
            task_id=1,
            approver_id=2,
            comment="不同意"
        )
        
        self.assertEqual(result, mock_result)
        self.service.engine.reject.assert_called_once_with(
            task_id=1,
            approver_id=2,
            comment="不同意"
        )

    # ========== batch_approve_or_reject() 测试 ==========

    def test_batch_approve_success(self):
        """测试批量审批通过"""
        self.service.engine.approve.return_value = {"status": "success"}
        
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1, 2, 3],
            approver_id=2,
            action="approve",
            comment="批量同意"
        )
        
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 0)
        for i, result in enumerate(results):
            self.assertEqual(result["task_id"], i + 1)
            self.assertEqual(result["status"], "success")
        
        self.assertEqual(self.service.engine.approve.call_count, 3)

    def test_batch_reject_success(self):
        """测试批量驳回"""
        self.service.engine.reject.return_value = {"status": "rejected"}
        
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1, 2],
            approver_id=2,
            action="reject",
            comment="批量驳回"
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.service.engine.reject.call_count, 2)

    def test_batch_approve_invalid_action(self):
        """测试批量操作使用无效的action"""
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1],
            approver_id=2,
            action="invalid_action"
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不支持的操作", errors[0]["error"])

    def test_batch_approve_partial_failure(self):
        """测试批量操作部分失败"""
        # 第2个任务会抛出异常
        def approve_side_effect(task_id, approver_id, comment):
            if task_id == 2:
                raise Exception("任务不存在")
            return {"status": "success"}
        
        self.service.engine.approve.side_effect = approve_side_effect
        
        results, errors = self.service.batch_approve_or_reject(
            task_ids=[1, 2, 3],
            approver_id=2,
            action="approve"
        )
        
        self.assertEqual(len(results), 2)  # task 1和3成功
        self.assertEqual(len(errors), 1)   # task 2失败
        self.assertEqual(errors[0]["task_id"], 2)
        self.assertEqual(errors[0]["error"], "任务不存在")

    # ========== get_contract_approval_status() 测试 ==========

    def test_get_contract_approval_status_success(self):
        """测试查询合同审批状态"""
        contract = self._create_mock_contract()
        instance = self._create_mock_instance()
        
        task1 = self._create_mock_task(task_id=1, status="APPROVED")
        task1.action = "APPROVE"
        task1.comment = "同意"
        task1.completed_at = datetime(2024, 1, 21, 10, 0, 0)
        
        task2 = self._create_mock_task(task_id=2, status="PENDING")
        
        # Mock db.query
        def query_side_effect(model):
            mock_query = MagicMock()
            
            # Contract query
            if model.__name__ == 'Contract':
                mock_query.filter.return_value.first.return_value = contract
            # ApprovalInstance query
            elif model.__name__ == 'ApprovalInstance':
                mock_query.filter.return_value.order_by.return_value.first.return_value = instance
            # ApprovalTask query
            elif model.__name__ == 'ApprovalTask':
                mock_query.filter.return_value.order_by.return_value.all.return_value = [task1, task2]
            
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        status = self.service.get_contract_approval_status(contract_id=1)
        
        # 验证
        self.assertIsNotNone(status)
        self.assertEqual(status["contract_id"], 1)
        self.assertEqual(status["contract_code"], "CT20240001")
        self.assertEqual(status["instance_id"], 1)
        self.assertEqual(status["instance_status"], "PENDING")
        self.assertEqual(len(status["task_history"]), 2)
        self.assertEqual(status["task_history"][0]["status"], "APPROVED")
        self.assertEqual(status["task_history"][1]["status"], "PENDING")

    def test_get_contract_approval_status_contract_not_found(self):
        """测试查询不存在的合同"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.get_contract_approval_status(contract_id=999)
        
        self.assertEqual(str(context.exception), "合同不存在")

    def test_get_contract_approval_status_no_instance(self):
        """测试合同没有审批记录"""
        contract = self._create_mock_contract()
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Contract':
                mock_query.filter.return_value.first.return_value = contract
            else:
                mock_query.filter.return_value.order_by.return_value.first.return_value = None
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        status = self.service.get_contract_approval_status(contract_id=1)
        
        self.assertIsNone(status)

    # ========== withdraw_approval() 测试 ==========

    def test_withdraw_approval_success(self):
        """测试撤回审批成功"""
        contract = self._create_mock_contract()
        instance = self._create_mock_instance()
        instance.initiator_id = 1  # 提交人ID
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Contract':
                mock_query.filter.return_value.first.return_value = contract
            else:
                mock_query.filter.return_value.first.return_value = instance
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.withdraw_approval(
            contract_id=1,
            user_id=1,
            reason="需要修改"
        )
        
        self.assertEqual(result["contract_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once_with(
            instance_id=1,
            user_id=1
        )

    def test_withdraw_approval_contract_not_found(self):
        """测试撤回不存在的合同"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(contract_id=999, user_id=1)
        
        self.assertEqual(str(context.exception), "合同不存在")

    def test_withdraw_approval_no_pending_instance(self):
        """测试没有进行中的审批流程"""
        contract = self._create_mock_contract()
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Contract':
                mock_query.filter.return_value.first.return_value = contract
            else:
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(contract_id=1, user_id=1)
        
        self.assertEqual(str(context.exception), "没有进行中的审批流程可撤回")

    def test_withdraw_approval_unauthorized(self):
        """测试无权撤回（不是提交人）"""
        contract = self._create_mock_contract()
        instance = self._create_mock_instance()
        instance.initiator_id = 1  # 提交人是用户1
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Contract':
                mock_query.filter.return_value.first.return_value = contract
            else:
                mock_query.filter.return_value.first.return_value = instance
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        # 用户2尝试撤回
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(contract_id=1, user_id=2)
        
        self.assertEqual(str(context.exception), "只能撤回自己提交的审批")

    # ========== get_approval_history() 测试 ==========

    def test_get_approval_history_success(self):
        """测试获取审批历史"""
        task1 = self._create_mock_task(task_id=1, status="APPROVED")
        task1.action = "APPROVE"
        task1.comment = "同意"
        task1.completed_at = datetime(2024, 1, 21, 10, 0, 0)
        
        task2 = self._create_mock_task(task_id=2, status="REJECTED")
        task2.action = "REJECT"
        task2.comment = "不同意"
        task2.completed_at = datetime(2024, 1, 22, 10, 0, 0)
        
        contract = self._create_mock_contract()
        
        # Mock query
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [task1, task2]
        
        self.db.query.return_value = mock_query
        
        # Mock Contract query
        def query_side_effect_for_contract(model):
            if model.__name__ == 'ApprovalTask':
                return mock_query
            else:
                mock_contract_query = MagicMock()
                mock_contract_query.filter.return_value.first.return_value = contract
                return mock_contract_query
        
        self.db.query.side_effect = query_side_effect_for_contract
        
        # 执行
        items, total = self.service.get_approval_history(user_id=2)
        
        # 验证
        self.assertEqual(len(items), 2)
        self.assertEqual(total, 2)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["action"], "APPROVE")
        self.assertEqual(items[1]["task_id"], 2)
        self.assertEqual(items[1]["action"], "REJECT")

    def test_get_approval_history_with_status_filter(self):
        """测试带状态筛选的审批历史"""
        task = self._create_mock_task(task_id=1, status="APPROVED")
        contract = self._create_mock_contract()
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [task]
        
        def query_side_effect(model):
            if model.__name__ == 'ApprovalTask':
                return mock_query
            else:
                mock_contract_query = MagicMock()
                mock_contract_query.filter.return_value.first.return_value = contract
                return mock_contract_query
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        items, total = self.service.get_approval_history(
            user_id=2,
            status_filter="APPROVED"
        )
        
        # 验证
        self.assertEqual(len(items), 1)
        self.assertEqual(total, 1)
        
        # 验证filter被调用了两次（一次是初始filter，一次是status_filter）
        call_count = 0
        for call in mock_query.filter.call_args_list:
            call_count += 1
        self.assertGreaterEqual(call_count, 1)

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        tasks = [self._create_mock_task(task_id=i, status="APPROVED") for i in range(1, 6)]
        contract = self._create_mock_contract()
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = tasks[2:4]  # 第3、4条
        
        def query_side_effect(model):
            if model.__name__ == 'ApprovalTask':
                return mock_query
            else:
                mock_contract_query = MagicMock()
                mock_contract_query.filter.return_value.first.return_value = contract
                return mock_contract_query
        
        self.db.query.side_effect = query_side_effect
        
        # 执行 - 第2页，每页2条
        items, total = self.service.get_approval_history(
            user_id=2,
            page=2,
            page_size=2
        )
        
        # 验证
        self.assertEqual(len(items), 2)
        self.assertEqual(total, 5)
        mock_query.offset.assert_called_with(2)
        mock_query.limit.assert_called_with(2)

    def test_get_approval_history_contract_not_found(self):
        """测试审批历史中合同不存在的情况"""
        task = self._create_mock_task(task_id=1, status="APPROVED")
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [task]
        
        def query_side_effect(model):
            if model.__name__ == 'ApprovalTask':
                return mock_query
            else:
                mock_contract_query = MagicMock()
                mock_contract_query.filter.return_value.first.return_value = None
                return mock_contract_query
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        items, total = self.service.get_approval_history(user_id=2)
        
        # 验证 - 合同不存在时相关字段为None
        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0]["contract_code"])
        self.assertIsNone(items[0]["customer_name"])
        self.assertEqual(items[0]["contract_amount"], 0)


if __name__ == "__main__":
    unittest.main()
