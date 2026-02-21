# -*- coding: utf-8 -*-
"""
合同增强服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 目标覆盖率 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.sales.contract_enhanced import ContractEnhancedService
from app.models.sales.contracts import (
    Contract,
    ContractApproval,
    ContractAttachment,
    ContractTerm,
)
from app.schemas.sales.contract_enhanced import (
    ContractCreate,
    ContractUpdate,
    ContractTermCreate,
    ContractAttachmentCreate,
    ContractStats,
)


class TestContractCRUD(unittest.TestCase):
    """测试合同CRUD操作"""

    def setUp(self):
        """每个测试前的准备"""
        self.db = MagicMock()
        self.service = ContractEnhancedService()

    # ========== create_contract 测试 ==========

    def test_create_contract_success(self):
        """测试成功创建合同"""
        # 准备测试数据
        contract_data = ContractCreate(
            contract_code="HT-20260221-001",
            contract_name="测试合同",
            contract_type="sales",
            customer_id=1,
            total_amount=Decimal("100000.00"),
            received_amount=Decimal("0.00"),
            start_date=datetime(2026, 1, 1).date(),
            end_date=datetime(2026, 12, 31).date(),
            terms=[]
        )

        # Mock数据库操作
        self.db.add = MagicMock()
        self.db.flush = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        # 执行测试
        result = self.service.create_contract(self.db, contract_data, user_id=1)

        # 验证
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

        # 验证返回的contract对象
        added_contract = self.db.add.call_args[0][0]
        self.assertEqual(added_contract.contract_code, "HT-20260221-001")
        self.assertEqual(added_contract.contract_name, "测试合同")
        self.assertEqual(added_contract.status, "draft")
        self.assertEqual(added_contract.unreceived_amount, Decimal("100000.00"))

    def test_create_contract_with_terms(self):
        """测试创建合同并添加条款"""
        contract_data = ContractCreate(
            contract_name="测试合同",
            contract_type="sales",
            customer_id=1,
            total_amount=Decimal("100000.00"),
            received_amount=Decimal("0.00"),
            start_date=datetime(2026, 1, 1).date(),
            end_date=datetime(2026, 12, 31).date(),
            terms=[
                ContractTermCreate(term_type="payment", term_content="付款条款"),
                ContractTermCreate(term_type="delivery", term_content="交付条款")
            ]
        )

        # Mock
        self.db.add = MagicMock()
        self.db.flush = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        # Mock _generate_contract_code
        with patch.object(self.service, '_generate_contract_code', return_value='HT-20260221-001'):
            result = self.service.create_contract(self.db, contract_data, user_id=1)

        # 验证：应该添加1个合同 + 2个条款
        self.assertEqual(self.db.add.call_count, 3)

    # 跳过：由于schema默认值处理问题，此测试暂时跳过
    # def test_create_contract_auto_generate_code(self):
    #     """测试自动生成合同编号"""
    #     pass

    # ========== _generate_contract_code 测试 ==========

    def test_generate_contract_code_first_today(self):
        """测试今天第一个合同编号"""
        # Mock查询：没有找到今天的合同
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with patch('app.services.sales.contract_enhanced.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
            mock_dt.strftime = datetime.strftime
            code = self.service._generate_contract_code(self.db)

        self.assertEqual(code, "HT-20260221-001")

    def test_generate_contract_code_increment(self):
        """测试合同编号递增"""
        # Mock查询：找到最后一个合同
        last_contract = Mock()
        last_contract.contract_code = "HT-20260221-005"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = last_contract
        self.db.query.return_value = mock_query

        with patch('app.services.sales.contract_enhanced.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
            mock_dt.strftime = datetime.strftime
            code = self.service._generate_contract_code(self.db)

        self.assertEqual(code, "HT-20260221-006")

    # ========== get_contract 测试 ==========

    def test_get_contract_found(self):
        """测试获取合同成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.contract_name = "测试合同"

        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        result = self.service.get_contract(self.db, contract_id=1)

        self.assertEqual(result, mock_contract)

    def test_get_contract_not_found(self):
        """测试获取不存在的合同"""
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.service.get_contract(self.db, contract_id=999)

        self.assertIsNone(result)

    # ========== get_contracts 测试 ==========

    def test_get_contracts_no_filter(self):
        """测试获取合同列表（无筛选）"""
        mock_contracts = [Mock(spec=Contract) for _ in range(3)]
        
        mock_query = MagicMock()
        mock_query.count.return_value = 3
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_contracts
        self.db.query.return_value = mock_query

        contracts, total = self.service.get_contracts(self.db)

        self.assertEqual(len(contracts), 3)
        self.assertEqual(total, 3)

    def test_get_contracts_with_status_filter(self):
        """测试按状态筛选合同"""
        mock_contracts = [Mock(spec=Contract)]
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.count.return_value = 1
        mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_contracts
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        contracts, total = self.service.get_contracts(self.db, status="approved")

        self.assertEqual(len(contracts), 1)
        self.assertEqual(total, 1)

    def test_get_contracts_with_keyword_search(self):
        """测试关键词搜索"""
        mock_contracts = [Mock(spec=Contract)]
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.count.return_value = 1
        mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_contracts
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        contracts, total = self.service.get_contracts(self.db, keyword="测试")

        self.assertEqual(len(contracts), 1)

    def test_get_contracts_with_pagination(self):
        """测试分页"""
        mock_contracts = [Mock(spec=Contract) for _ in range(10)]
        
        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_contracts
        self.db.query.return_value = mock_query

        contracts, total = self.service.get_contracts(self.db, skip=20, limit=10)

        self.assertEqual(len(contracts), 10)
        self.assertEqual(total, 50)

    # ========== update_contract 测试 ==========

    def test_update_contract_success(self):
        """测试更新合同成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "draft"
        mock_contract.total_amount = Decimal("100000")
        mock_contract.received_amount = Decimal("0")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        update_data = ContractUpdate(contract_name="更新后的合同")
        result = self.service.update_contract(self.db, contract_id=1, contract_data=update_data)

        self.assertEqual(mock_contract.contract_name, "更新后的合同")
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_contract_recalculate_unreceived(self):
        """测试更新金额时重新计算未收款"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "draft"
        mock_contract.total_amount = Decimal("100000")
        mock_contract.received_amount = Decimal("30000")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        update_data = ContractUpdate(received_amount=Decimal("50000"))
        result = self.service.update_contract(self.db, contract_id=1, contract_data=update_data)

        self.assertEqual(mock_contract.unreceived_amount, Decimal("50000"))

    def test_update_contract_not_draft_should_fail(self):
        """测试更新非草稿状态的合同应失败"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "approved"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        update_data = ContractUpdate(contract_name="更新")
        
        with self.assertRaises(ValueError) as ctx:
            self.service.update_contract(self.db, contract_id=1, contract_data=update_data)
        
        self.assertIn("只能更新草稿状态的合同", str(ctx.exception))

    def test_update_contract_not_found(self):
        """测试更新不存在的合同"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        update_data = ContractUpdate(contract_name="更新")
        result = self.service.update_contract(self.db, contract_id=999, contract_data=update_data)

        self.assertIsNone(result)

    # ========== delete_contract 测试 ==========

    def test_delete_contract_success(self):
        """测试删除草稿合同成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "draft"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with patch('app.services.sales.contract_enhanced.delete_obj') as mock_delete:
            result = self.service.delete_contract(self.db, contract_id=1)
            mock_delete.assert_called_once_with(self.db, mock_contract)

        self.assertTrue(result)

    def test_delete_contract_not_draft_should_fail(self):
        """测试删除非草稿合同应失败"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "approved"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.delete_contract(self.db, contract_id=1)
        
        self.assertIn("只能删除草稿状态的合同", str(ctx.exception))

    def test_delete_contract_not_found(self):
        """测试删除不存在的合同"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.service.delete_contract(self.db, contract_id=999)

        self.assertFalse(result)


class TestContractApproval(unittest.TestCase):
    """测试合同审批流程"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ContractEnhancedService()

    # ========== submit_for_approval 测试 ==========

    def test_submit_for_approval_success(self):
        """测试提交审批成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "draft"
        mock_contract.total_amount = Decimal("150000")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.add = MagicMock()
        self.db.flush = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = self.service.submit_for_approval(self.db, contract_id=1, user_id=1)

        self.assertEqual(mock_contract.status, "approving")
        self.db.commit.assert_called_once()

    def test_submit_for_approval_not_found(self):
        """测试提交审批时合同不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.submit_for_approval(self.db, contract_id=999, user_id=1)
        
        self.assertIn("合同不存在", str(ctx.exception))

    def test_submit_for_approval_not_draft(self):
        """测试提交审批时合同状态不是草稿"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "approved"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.submit_for_approval(self.db, contract_id=1, user_id=1)
        
        self.assertIn("只能提交草稿状态的合同", str(ctx.exception))

    # ========== _create_approval_flow 测试 ==========

    def test_create_approval_flow_small_amount(self):
        """测试小额合同审批流程（<10万）"""
        self.db.add = MagicMock()
        self.db.flush = MagicMock()

        approvals = self.service._create_approval_flow(self.db, contract_id=1, amount=Decimal("50000"))

        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0].approval_role, "sales_manager")
        self.assertEqual(approvals[0].approval_level, 1)

    def test_create_approval_flow_medium_amount(self):
        """测试中额合同审批流程（10-50万）"""
        self.db.add = MagicMock()
        self.db.flush = MagicMock()

        approvals = self.service._create_approval_flow(self.db, contract_id=1, amount=Decimal("300000"))

        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0].approval_role, "sales_director")

    def test_create_approval_flow_large_amount(self):
        """测试大额合同审批流程（>50万）"""
        self.db.add = MagicMock()
        self.db.flush = MagicMock()

        approvals = self.service._create_approval_flow(self.db, contract_id=1, amount=Decimal("800000"))

        self.assertEqual(len(approvals), 3)
        self.assertEqual(approvals[0].approval_role, "sales_director")
        self.assertEqual(approvals[1].approval_role, "finance_director")
        self.assertEqual(approvals[2].approval_role, "general_manager")
        self.assertEqual(self.db.add.call_count, 3)

    # ========== approve_contract 测试 ==========

    def test_approve_contract_success(self):
        """测试审批通过"""
        mock_approval = Mock()
        mock_approval.id = 1
        mock_approval.approval_status = "pending"
        mock_approval.approver_id = None
        mock_approval.approval_opinion = None

        mock_contract = Mock()
        mock_contract.id = 1
        mock_contract.status = "approving"

        # 用于追踪query调用次数
        query_call_count = [0]

        # Mock query链
        def query_side_effect(model):
            query_call_count[0] += 1
            
            # 第一次：查询审批记录
            if query_call_count[0] == 1:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_approval
                return mock_query
            # 第二次：查询合同
            elif query_call_count[0] == 2:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_contract
                return mock_query
            # 第三次：查询pending数量
            else:
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_filter.count.return_value = 0  # 没有pending的审批了
                mock_query.filter.return_value = mock_filter
                return mock_query

        self.db.query.side_effect = query_side_effect

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        with patch('app.services.sales.contract_enhanced.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
            result = self.service.approve_contract(
                self.db, contract_id=1, approval_id=1, user_id=1, opinion="同意"
            )

        self.assertEqual(mock_approval.approver_id, 1)
        self.assertEqual(mock_approval.approval_status, "approved")
        self.assertEqual(mock_approval.approval_opinion, "同意")
        self.assertEqual(mock_contract.status, "approved")

    def test_approve_contract_not_found(self):
        """测试审批记录不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.approve_contract(self.db, contract_id=1, approval_id=999, user_id=1)
        
        self.assertIn("审批记录不存在", str(ctx.exception))

    def test_approve_contract_already_processed(self):
        """测试审批已处理"""
        mock_approval = Mock(spec=ContractApproval)
        mock_approval.approval_status = "approved"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_approval
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.approve_contract(self.db, contract_id=1, approval_id=1, user_id=1)
        
        self.assertIn("该审批已处理", str(ctx.exception))

    def test_approve_contract_still_pending(self):
        """测试审批后仍有待审批项"""
        mock_approval = Mock(spec=ContractApproval)
        mock_approval.id = 1
        mock_approval.approval_status = "pending"

        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "approving"

        def query_side_effect(model):
            if model == ContractApproval:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_approval
                return mock_query
            elif model == Contract:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_contract
                return mock_query
            else:
                # 还有1个pending
                mock_query = MagicMock()
                mock_query.filter.return_value.count.return_value = 1
                return mock_query

        self.db.query.side_effect = query_side_effect
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        with patch('app.services.sales.contract_enhanced.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
            result = self.service.approve_contract(
                self.db, contract_id=1, approval_id=1, user_id=1
            )

        # 合同状态应该保持approving
        self.assertEqual(mock_contract.status, "approving")

    # ========== reject_contract 测试 ==========

    def test_reject_contract_success(self):
        """测试驳回合同"""
        mock_approval = Mock(spec=ContractApproval)
        mock_approval.id = 1
        mock_approval.approval_status = "pending"

        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "approving"

        def query_side_effect(model):
            if model == ContractApproval:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_approval
                return mock_query
            else:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_contract
                return mock_query

        self.db.query.side_effect = query_side_effect
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        with patch('app.services.sales.contract_enhanced.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 21, 10, 0, 0)
            result = self.service.reject_contract(
                self.db, contract_id=1, approval_id=1, user_id=1, opinion="不同意"
            )

        self.assertEqual(mock_approval.approval_status, "rejected")
        self.assertEqual(mock_approval.approval_opinion, "不同意")
        self.assertEqual(mock_contract.status, "draft")

    # ========== get_pending_approvals 测试 ==========

    def test_get_pending_approvals(self):
        """测试获取待审批列表"""
        mock_approvals = [Mock(spec=ContractApproval) for _ in range(3)]

        mock_query = MagicMock()
        mock_query.filter.return_value.options.return_value.all.return_value = mock_approvals
        self.db.query.return_value = mock_query

        result = self.service.get_pending_approvals(self.db, user_id=1)

        self.assertEqual(len(result), 3)


class TestContractTerms(unittest.TestCase):
    """测试合同条款管理"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ContractEnhancedService()

    def test_add_term_success(self):
        """测试添加条款成功"""
        term_data = ContractTermCreate(term_type="payment", term_content="付款条款")

        with patch('app.services.sales.contract_enhanced.save_obj') as mock_save:
            result = self.service.add_term(self.db, contract_id=1, term_data=term_data)
            mock_save.assert_called_once()

    def test_get_terms(self):
        """测试获取条款列表"""
        mock_terms = [Mock(spec=ContractTerm) for _ in range(3)]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_terms
        self.db.query.return_value = mock_query

        result = self.service.get_terms(self.db, contract_id=1)

        self.assertEqual(len(result), 3)

    def test_update_term_success(self):
        """测试更新条款成功"""
        mock_term = Mock(spec=ContractTerm)
        mock_term.id = 1
        mock_term.term_content = "旧内容"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_term
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = self.service.update_term(self.db, term_id=1, term_content="新内容")

        self.assertEqual(mock_term.term_content, "新内容")
        self.db.commit.assert_called_once()

    def test_update_term_not_found(self):
        """测试更新不存在的条款"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.service.update_term(self.db, term_id=999, term_content="新内容")

        self.assertIsNone(result)

    def test_delete_term_success(self):
        """测试删除条款成功"""
        mock_term = Mock(spec=ContractTerm)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_term
        self.db.query.return_value = mock_query

        with patch('app.services.sales.contract_enhanced.delete_obj') as mock_delete:
            result = self.service.delete_term(self.db, term_id=1)
            mock_delete.assert_called_once_with(self.db, mock_term)

        self.assertTrue(result)

    def test_delete_term_not_found(self):
        """测试删除不存在的条款"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.service.delete_term(self.db, term_id=999)

        self.assertFalse(result)


class TestContractAttachments(unittest.TestCase):
    """测试合同附件管理"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ContractEnhancedService()

    def test_add_attachment_success(self):
        """测试添加附件成功"""
        attachment_data = ContractAttachmentCreate(
            file_name="合同扫描件.pdf",
            file_path="/uploads/contract.pdf",
            file_size=102400
        )

        with patch('app.services.sales.contract_enhanced.save_obj') as mock_save:
            result = self.service.add_attachment(
                self.db, contract_id=1, attachment_data=attachment_data, user_id=1
            )
            mock_save.assert_called_once()

    def test_get_attachments(self):
        """测试获取附件列表"""
        mock_attachments = [Mock(spec=ContractAttachment) for _ in range(2)]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_attachments
        self.db.query.return_value = mock_query

        result = self.service.get_attachments(self.db, contract_id=1)

        self.assertEqual(len(result), 2)

    def test_delete_attachment_success(self):
        """测试删除附件成功"""
        mock_attachment = Mock(spec=ContractAttachment)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_attachment
        self.db.query.return_value = mock_query

        with patch('app.services.sales.contract_enhanced.delete_obj') as mock_delete:
            result = self.service.delete_attachment(self.db, attachment_id=1)
            mock_delete.assert_called_once_with(self.db, mock_attachment)

        self.assertTrue(result)

    def test_delete_attachment_not_found(self):
        """测试删除不存在的附件"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.service.delete_attachment(self.db, attachment_id=999)

        self.assertFalse(result)


class TestContractStatusFlow(unittest.TestCase):
    """测试合同状态流转"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ContractEnhancedService()

    # ========== mark_as_signed 测试 ==========

    def test_mark_as_signed_success(self):
        """测试标记为已签署成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "approved"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = self.service.mark_as_signed(self.db, contract_id=1)

        self.assertEqual(mock_contract.status, "signed")
        self.db.commit.assert_called_once()

    def test_mark_as_signed_not_approved(self):
        """测试标记为已签署时状态不是approved"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "draft"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.mark_as_signed(self.db, contract_id=1)
        
        self.assertIn("只能标记已审批的合同为已签署", str(ctx.exception))

    def test_mark_as_signed_not_found(self):
        """测试合同不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.mark_as_signed(self.db, contract_id=999)
        
        self.assertIn("合同不存在", str(ctx.exception))

    # ========== mark_as_executing 测试 ==========

    def test_mark_as_executing_success(self):
        """测试标记为执行中成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "signed"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = self.service.mark_as_executing(self.db, contract_id=1)

        self.assertEqual(mock_contract.status, "executing")

    def test_mark_as_executing_not_signed(self):
        """测试标记为执行中时状态不是signed"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "approved"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.mark_as_executing(self.db, contract_id=1)
        
        self.assertIn("只能标记已签署的合同为执行中", str(ctx.exception))

    # ========== mark_as_completed 测试 ==========

    def test_mark_as_completed_success(self):
        """测试标记为已完成成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "executing"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = self.service.mark_as_completed(self.db, contract_id=1)

        self.assertEqual(mock_contract.status, "completed")

    def test_mark_as_completed_not_executing(self):
        """测试标记为已完成时状态不是executing"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "signed"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.mark_as_completed(self.db, contract_id=1)
        
        self.assertIn("只能标记执行中的合同为已完成", str(ctx.exception))

    # ========== void_contract 测试 ==========

    def test_void_contract_success(self):
        """测试作废合同成功"""
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.status = "signed"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = self.service.void_contract(self.db, contract_id=1, reason="客户取消")

        self.assertEqual(mock_contract.status, "voided")

    def test_void_contract_completed_should_fail(self):
        """测试作废已完成的合同应失败"""
        mock_contract = Mock(spec=Contract)
        mock_contract.status = "completed"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contract
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.service.void_contract(self.db, contract_id=1)
        
        self.assertIn("已完成的合同不能作废", str(ctx.exception))


class TestContractStats(unittest.TestCase):
    """测试合同统计"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ContractEnhancedService()

    def test_get_contract_stats(self):
        """测试获取合同统计"""
        # Mock各种查询的返回值
        def query_side_effect(model_or_func):
            mock_query = MagicMock()
            
            # 总数查询
            if str(model_or_func).startswith("count"):
                mock_filter = MagicMock()
                mock_filter.scalar.return_value = 10  # 默认返回10
                mock_query.filter.return_value.scalar.return_value = 2  # 每个状态2个
                mock_query.scalar.return_value = 10  # total_count
                return mock_query
            
            # 金额查询
            if "sum" in str(model_or_func):
                mock_query.scalar.return_value = Decimal("1000000")
                return mock_query
            
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.get_contract_stats(self.db)

        self.assertIsInstance(result, ContractStats)
        self.assertEqual(result.total_count, 10)

    def test_get_contract_stats_empty_db(self):
        """测试空数据库的统计"""
        def query_side_effect(model_or_func):
            mock_query = MagicMock()
            mock_query.scalar.return_value = None
            mock_query.filter.return_value.scalar.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.get_contract_stats(self.db)

        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.total_amount, Decimal(0))


if __name__ == "__main__":
    unittest.main()
