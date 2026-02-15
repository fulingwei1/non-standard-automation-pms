# -*- coding: utf-8 -*-
"""
合同管理增强模块 - 单元测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract, ContractApproval, ContractTerm, ContractAttachment
from app.schemas.sales.contract_enhanced import (
    ContractCreate,
    ContractUpdate,
    ContractTermCreate,
    ContractAttachmentCreate,
)
from app.services.sales.contract_enhanced import ContractEnhancedService


# ========== 测试夹具 ==========
@pytest.fixture
def sample_contract_data():
    """示例合同数据"""
    return ContractCreate(
        contract_name="测试销售合同001",
        contract_type="sales",
        customer_id=1,
        total_amount=Decimal("150000.00"),
        received_amount=Decimal("0.00"),
        signing_date=date.today(),
        effective_date=date.today(),
        contract_period=12,
        contract_subject="自动化设备采购",
        payment_terms="分3期付款",
        delivery_terms="签约后60天内交付",
        sales_owner_id=1,
    )


@pytest.fixture
def created_contract(db: Session, sample_contract_data):
    """创建一个测试合同"""
    contract = ContractEnhancedService.create_contract(db, sample_contract_data, user_id=1)
    return contract


# ========== 合同CRUD测试（15+用例） ==========
class TestContractCRUD:
    """合同CRUD测试"""
    
    def test_create_contract_with_auto_code(self, db: Session, sample_contract_data):
        """测试：创建合同（自动生成编号）"""
        contract = ContractEnhancedService.create_contract(db, sample_contract_data, user_id=1)
        
        assert contract.id is not None
        assert contract.contract_code is not None
        assert contract.contract_code.startswith("HT-")
        assert contract.contract_name == "测试销售合同001"
        assert contract.total_amount == Decimal("150000.00")
        assert contract.unreceived_amount == Decimal("150000.00")
        assert contract.status == "draft"
    
    def test_create_contract_with_custom_code(self, db: Session):
        """测试：创建合同（自定义编号）"""
        data = ContractCreate(
            contract_code="HT-CUSTOM-001",
            contract_name="自定义编号合同",
            contract_type="purchase",
            customer_id=1,
            total_amount=Decimal("80000.00"),
        )
        contract = ContractEnhancedService.create_contract(db, data, user_id=1)
        
        assert contract.contract_code == "HT-CUSTOM-001"
    
    def test_create_contract_with_terms(self, db: Session):
        """测试：创建合同并添加条款"""
        data = ContractCreate(
            contract_name="含条款合同",
            contract_type="sales",
            customer_id=1,
            total_amount=Decimal("200000.00"),
            terms=[
                ContractTermCreate(term_type="subject", term_content="设备采购明细"),
                ContractTermCreate(term_type="payment", term_content="首付30%，验收后70%"),
            ]
        )
        contract = ContractEnhancedService.create_contract(db, data, user_id=1)
        
        assert len(contract.terms) == 2
        assert contract.terms[0].term_type == "subject"
    
    def test_get_contract(self, db: Session, created_contract):
        """测试：获取合同详情"""
        contract = ContractEnhancedService.get_contract(db, created_contract.id)
        
        assert contract is not None
        assert contract.id == created_contract.id
        assert contract.contract_name == created_contract.contract_name
    
    def test_get_contract_not_found(self, db: Session):
        """测试：获取不存在的合同"""
        contract = ContractEnhancedService.get_contract(db, 9999)
        assert contract is None
    
    def test_get_contracts_list(self, db: Session, created_contract):
        """测试：获取合同列表"""
        contracts, total = ContractEnhancedService.get_contracts(db, skip=0, limit=10)
        
        assert total >= 1
        assert len(contracts) >= 1
    
    def test_get_contracts_filter_by_status(self, db: Session, created_contract):
        """测试：按状态筛选合同"""
        contracts, total = ContractEnhancedService.get_contracts(db, status="draft")
        
        assert all(c.status == "draft" for c in contracts)
    
    def test_get_contracts_filter_by_customer(self, db: Session, created_contract):
        """测试：按客户筛选合同"""
        contracts, total = ContractEnhancedService.get_contracts(db, customer_id=1)
        
        assert all(c.customer_id == 1 for c in contracts)
    
    def test_get_contracts_search_by_keyword(self, db: Session, created_contract):
        """测试：关键词搜索合同"""
        contracts, total = ContractEnhancedService.get_contracts(db, keyword="测试")
        
        assert total >= 1
    
    def test_update_contract(self, db: Session, created_contract):
        """测试：更新合同"""
        update_data = ContractUpdate(
            contract_name="修改后的合同名称",
            total_amount=Decimal("180000.00"),
        )
        contract = ContractEnhancedService.update_contract(db, created_contract.id, update_data)
        
        assert contract.contract_name == "修改后的合同名称"
        assert contract.total_amount == Decimal("180000.00")
        assert contract.unreceived_amount == Decimal("180000.00")
    
    def test_update_contract_not_in_draft(self, db: Session, created_contract):
        """测试：更新非草稿状态的合同（应失败）"""
        # 先提交审批
        created_contract.status = "approving"
        db.commit()
        
        update_data = ContractUpdate(contract_name="不应成功")
        
        with pytest.raises(ValueError, match="只能更新草稿状态的合同"):
            ContractEnhancedService.update_contract(db, created_contract.id, update_data)
    
    def test_delete_contract(self, db: Session, created_contract):
        """测试：删除合同"""
        success = ContractEnhancedService.delete_contract(db, created_contract.id)
        
        assert success is True
        assert ContractEnhancedService.get_contract(db, created_contract.id) is None
    
    def test_delete_contract_not_in_draft(self, db: Session, created_contract):
        """测试：删除非草稿状态的合同（应失败）"""
        created_contract.status = "signed"
        db.commit()
        
        with pytest.raises(ValueError, match="只能删除草稿状态的合同"):
            ContractEnhancedService.delete_contract(db, created_contract.id)
    
    def test_unreceived_amount_calculation(self, db: Session):
        """测试：未收款金额自动计算"""
        data = ContractCreate(
            contract_name="测试金额计算",
            contract_type="sales",
            customer_id=1,
            total_amount=Decimal("100000.00"),
            received_amount=Decimal("30000.00"),
        )
        contract = ContractEnhancedService.create_contract(db, data, user_id=1)
        
        assert contract.unreceived_amount == Decimal("70000.00")
    
    def test_contract_code_sequence(self, db: Session):
        """测试：合同编号自动递增"""
        # 创建多个合同
        for i in range(3):
            data = ContractCreate(
                contract_name=f"合同{i+1}",
                contract_type="sales",
                customer_id=1,
                total_amount=Decimal("50000.00"),
            )
            ContractEnhancedService.create_contract(db, data, user_id=1)
        
        # 验证编号递增
        contracts, _ = ContractEnhancedService.get_contracts(db, limit=100)
        codes = [c.contract_code for c in contracts if c.contract_code.startswith("HT-")]
        assert len(codes) >= 3


# ========== 审批流程测试（10+用例） ==========
class TestContractApproval:
    """审批流程测试"""
    
    def test_submit_for_approval_small_amount(self, db: Session, created_contract):
        """测试：提交审批（金额<10万）"""
        created_contract.total_amount = Decimal("80000.00")
        db.commit()
        
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        
        assert contract.status == "approving"
        assert len(contract.approvals) == 1
        assert contract.approvals[0].approval_role == "sales_manager"
    
    def test_submit_for_approval_medium_amount(self, db: Session, created_contract):
        """测试：提交审批（金额10-50万）"""
        created_contract.total_amount = Decimal("300000.00")
        db.commit()
        
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        
        assert contract.status == "approving"
        assert len(contract.approvals) == 1
        assert contract.approvals[0].approval_role == "sales_director"
    
    def test_submit_for_approval_large_amount(self, db: Session, created_contract):
        """测试：提交审批（金额>50万）"""
        created_contract.total_amount = Decimal("800000.00")
        db.commit()
        
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        
        assert contract.status == "approving"
        assert len(contract.approvals) == 3
        assert contract.approvals[0].approval_role == "sales_director"
        assert contract.approvals[1].approval_role == "finance_director"
        assert contract.approvals[2].approval_role == "general_manager"
    
    def test_submit_non_draft_contract(self, db: Session, created_contract):
        """测试：提交非草稿状态的合同（应失败）"""
        created_contract.status = "approved"
        db.commit()
        
        with pytest.raises(ValueError, match="只能提交草稿状态的合同"):
            ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
    
    def test_approve_contract(self, db: Session, created_contract):
        """测试：审批通过"""
        # 提交审批
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        approval_id = contract.approvals[0].id
        
        # 审批通过
        contract = ContractEnhancedService.approve_contract(
            db, created_contract.id, approval_id, user_id=2, opinion="同意"
        )
        
        approval = db.query(ContractApproval).filter(ContractApproval.id == approval_id).first()
        assert approval.approval_status == "approved"
        assert approval.approver_id == 2
        assert approval.approval_opinion == "同意"
        assert contract.status == "approved"
    
    def test_approve_already_processed(self, db: Session, created_contract):
        """测试：审批已处理的记录（应失败）"""
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        approval_id = contract.approvals[0].id
        
        # 第一次审批
        ContractEnhancedService.approve_contract(db, created_contract.id, approval_id, user_id=2)
        
        # 第二次审批同一记录
        with pytest.raises(ValueError, match="该审批已处理"):
            ContractEnhancedService.approve_contract(db, created_contract.id, approval_id, user_id=3)
    
    def test_reject_contract(self, db: Session, created_contract):
        """测试：审批驳回"""
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        approval_id = contract.approvals[0].id
        
        contract = ContractEnhancedService.reject_contract(
            db, created_contract.id, approval_id, user_id=2, opinion="不同意，需修改"
        )
        
        assert contract.status == "draft"
        approval = db.query(ContractApproval).filter(ContractApproval.id == approval_id).first()
        assert approval.approval_status == "rejected"
    
    def test_multi_level_approval(self, db: Session, created_contract):
        """测试：多级审批流程"""
        created_contract.total_amount = Decimal("600000.00")
        db.commit()
        
        # 提交审批
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        assert len(contract.approvals) == 3
        
        # 第一级审批
        ContractEnhancedService.approve_contract(db, created_contract.id, contract.approvals[0].id, user_id=2)
        contract = ContractEnhancedService.get_contract(db, created_contract.id)
        assert contract.status == "approving"  # 还有待审批
        
        # 第二级审批
        ContractEnhancedService.approve_contract(db, created_contract.id, contract.approvals[1].id, user_id=3)
        contract = ContractEnhancedService.get_contract(db, created_contract.id)
        assert contract.status == "approving"  # 还有待审批
        
        # 第三级审批
        ContractEnhancedService.approve_contract(db, created_contract.id, contract.approvals[2].id, user_id=4)
        contract = ContractEnhancedService.get_contract(db, created_contract.id)
        assert contract.status == "approved"  # 全部通过
    
    def test_get_pending_approvals(self, db: Session, created_contract):
        """测试：获取待审批列表"""
        ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        
        pending = ContractEnhancedService.get_pending_approvals(db, user_id=2)
        assert len(pending) >= 1
        assert all(a.approval_status == "pending" for a in pending)
    
    def test_approval_timestamp(self, db: Session, created_contract):
        """测试：审批时间戳记录"""
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        approval_id = contract.approvals[0].id
        
        before_time = datetime.now()
        ContractEnhancedService.approve_contract(db, created_contract.id, approval_id, user_id=2)
        after_time = datetime.now()
        
        approval = db.query(ContractApproval).filter(ContractApproval.id == approval_id).first()
        assert approval.approved_at is not None
        assert before_time <= approval.approved_at <= after_time


# ========== 状态流转测试（8+用例） ==========
class TestContractStatusFlow:
    """状态流转测试"""
    
    def test_status_flow_draft_to_signed(self, db: Session, created_contract):
        """测试：完整状态流转（草稿->已签署）"""
        # 草稿 -> 审批中
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        assert contract.status == "approving"
        
        # 审批中 -> 已审批
        ContractEnhancedService.approve_contract(
            db, created_contract.id, contract.approvals[0].id, user_id=2
        )
        contract = ContractEnhancedService.get_contract(db, created_contract.id)
        assert contract.status == "approved"
        
        # 已审批 -> 已签署
        contract = ContractEnhancedService.mark_as_signed(db, created_contract.id)
        assert contract.status == "signed"
    
    def test_mark_as_executing(self, db: Session, created_contract):
        """测试：标记为执行中"""
        # 设置为已签署
        created_contract.status = "signed"
        db.commit()
        
        contract = ContractEnhancedService.mark_as_executing(db, created_contract.id)
        assert contract.status == "executing"
    
    def test_mark_as_executing_invalid_status(self, db: Session, created_contract):
        """测试：错误状态标记为执行中（应失败）"""
        with pytest.raises(ValueError, match="只能标记已签署的合同为执行中"):
            ContractEnhancedService.mark_as_executing(db, created_contract.id)
    
    def test_mark_as_completed(self, db: Session, created_contract):
        """测试：标记为已完成"""
        created_contract.status = "executing"
        db.commit()
        
        contract = ContractEnhancedService.mark_as_completed(db, created_contract.id)
        assert contract.status == "completed"
    
    def test_mark_as_completed_invalid_status(self, db: Session, created_contract):
        """测试：错误状态标记为已完成（应失败）"""
        with pytest.raises(ValueError, match="只能标记执行中的合同为已完成"):
            ContractEnhancedService.mark_as_completed(db, created_contract.id)
    
    def test_void_contract(self, db: Session, created_contract):
        """测试：作废合同"""
        contract = ContractEnhancedService.void_contract(db, created_contract.id, reason="测试作废")
        assert contract.status == "voided"
    
    def test_void_completed_contract(self, db: Session, created_contract):
        """测试：作废已完成的合同（应失败）"""
        created_contract.status = "completed"
        db.commit()
        
        with pytest.raises(ValueError, match="已完成的合同不能作废"):
            ContractEnhancedService.void_contract(db, created_contract.id)
    
    def test_full_lifecycle(self, db: Session, created_contract):
        """测试：完整生命周期"""
        # 草稿 -> 审批 -> 签署 -> 执行 -> 完成
        contract = ContractEnhancedService.submit_for_approval(db, created_contract.id, user_id=1)
        ContractEnhancedService.approve_contract(db, contract.id, contract.approvals[0].id, user_id=2)
        contract = ContractEnhancedService.mark_as_signed(db, contract.id)
        contract = ContractEnhancedService.mark_as_executing(db, contract.id)
        contract = ContractEnhancedService.mark_as_completed(db, contract.id)
        
        assert contract.status == "completed"


# ========== 条款管理测试 ==========
class TestContractTerms:
    """条款管理测试"""
    
    def test_add_term(self, db: Session, created_contract):
        """测试：添加条款"""
        term_data = ContractTermCreate(
            term_type="payment",
            term_content="首付30%，发货前支付40%，验收后支付30%"
        )
        term = ContractEnhancedService.add_term(db, created_contract.id, term_data)
        
        assert term.id is not None
        assert term.contract_id == created_contract.id
        assert term.term_type == "payment"
    
    def test_get_terms(self, db: Session, created_contract):
        """测试：获取条款列表"""
        # 添加多个条款
        for term_type in ["subject", "price", "delivery"]:
            term_data = ContractTermCreate(term_type=term_type, term_content=f"{term_type}条款")
            ContractEnhancedService.add_term(db, created_contract.id, term_data)
        
        terms = ContractEnhancedService.get_terms(db, created_contract.id)
        assert len(terms) == 3
    
    def test_update_term(self, db: Session, created_contract):
        """测试：更新条款"""
        term_data = ContractTermCreate(term_type="warranty", term_content="原内容")
        term = ContractEnhancedService.add_term(db, created_contract.id, term_data)
        
        updated_term = ContractEnhancedService.update_term(db, term.id, "更新后的内容")
        assert updated_term.term_content == "更新后的内容"
    
    def test_delete_term(self, db: Session, created_contract):
        """测试：删除条款"""
        term_data = ContractTermCreate(term_type="breach", term_content="违约条款")
        term = ContractEnhancedService.add_term(db, created_contract.id, term_data)
        
        success = ContractEnhancedService.delete_term(db, term.id)
        assert success is True
        
        terms = ContractEnhancedService.get_terms(db, created_contract.id)
        assert len(terms) == 0


# ========== 附件管理测试 ==========
class TestContractAttachments:
    """附件管理测试"""
    
    def test_add_attachment(self, db: Session, created_contract):
        """测试：上传附件"""
        attachment_data = ContractAttachmentCreate(
            file_name="合同正本.pdf",
            file_path="/uploads/contracts/001.pdf",
            file_type="application/pdf",
            file_size=1024000,
        )
        attachment = ContractEnhancedService.add_attachment(
            db, created_contract.id, attachment_data, user_id=1
        )
        
        assert attachment.id is not None
        assert attachment.file_name == "合同正本.pdf"
        assert attachment.uploaded_by == 1
    
    def test_get_attachments(self, db: Session, created_contract):
        """测试：获取附件列表"""
        # 添加多个附件
        for i in range(3):
            attachment_data = ContractAttachmentCreate(
                file_name=f"附件{i+1}.pdf",
                file_path=f"/uploads/{i+1}.pdf",
            )
            ContractEnhancedService.add_attachment(db, created_contract.id, attachment_data, user_id=1)
        
        attachments = ContractEnhancedService.get_attachments(db, created_contract.id)
        assert len(attachments) == 3
    
    def test_delete_attachment(self, db: Session, created_contract):
        """测试：删除附件"""
        attachment_data = ContractAttachmentCreate(
            file_name="临时附件.docx",
            file_path="/uploads/temp.docx",
        )
        attachment = ContractEnhancedService.add_attachment(
            db, created_contract.id, attachment_data, user_id=1
        )
        
        success = ContractEnhancedService.delete_attachment(db, attachment.id)
        assert success is True


# ========== 统计功能测试 ==========
class TestContractStats:
    """统计功能测试"""
    
    def test_get_contract_stats(self, db: Session, created_contract):
        """测试：获取合同统计"""
        stats = ContractEnhancedService.get_contract_stats(db)
        
        assert stats.total_count >= 1
        assert stats.draft_count >= 1
        assert stats.total_amount >= Decimal("0")
    
    def test_stats_by_status(self, db: Session):
        """测试：按状态统计"""
        # 创建不同状态的合同
        for status in ["draft", "signed", "executing"]:
            data = ContractCreate(
                contract_name=f"{status}合同",
                contract_type="sales",
                customer_id=1,
                total_amount=Decimal("100000.00"),
            )
            contract = ContractEnhancedService.create_contract(db, data, user_id=1)
            if status != "draft":
                contract.status = status
                db.commit()
        
        stats = ContractEnhancedService.get_contract_stats(db)
        assert stats.draft_count >= 1
        assert stats.signed_count >= 1
        assert stats.executing_count >= 1
