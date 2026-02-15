# -*- coding: utf-8 -*-
"""
合同管理增强服务 - 完整的CRUD与审批流程
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.sales.contracts import (
    Contract,
    ContractApproval,
    ContractAttachment,
    ContractTerm,
)
from app.schemas.sales.contract_enhanced import (
    ContractApprovalCreate,
    ContractApprovalUpdate,
    ContractAttachmentCreate,
    ContractCreate,
    ContractStats,
    ContractTermCreate,
    ContractUpdate,
)


class ContractEnhancedService:
    """合同增强服务"""

    # ========== 合同CRUD ==========
    @staticmethod
    def create_contract(db: Session, contract_data: ContractCreate, user_id: int) -> Contract:
        """创建合同"""
        # 生成合同编号（如果未提供）
        if not contract_data.contract_code:
            contract_data.contract_code = ContractEnhancedService._generate_contract_code(db)
        
        # 计算未收款金额
        unreceived_amount = contract_data.total_amount - contract_data.received_amount
        
        # 创建合同主体
        contract_dict = contract_data.model_dump(exclude={'terms'})
        contract_dict['unreceived_amount'] = unreceived_amount
        contract_dict['status'] = 'draft'  # 初始状态为草稿
        
        contract = Contract(**contract_dict)
        db.add(contract)
        db.flush()  # 获取合同ID
        
        # 创建合同条款
        if contract_data.terms:
            for term_data in contract_data.terms:
                term = ContractTerm(
                    contract_id=contract.id,
                    **term_data.model_dump()
                )
                db.add(term)
        
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def _generate_contract_code(db: Session) -> str:
        """生成合同编号: HT-YYYYMMDD-XXX"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"HT-{today}-"
        
        # 查询今天的最大编号
        last_contract = (
            db.query(Contract)
            .filter(Contract.contract_code.like(f"{prefix}%"))
            .order_by(Contract.contract_code.desc())
            .first()
        )
        
        if last_contract:
            last_number = int(last_contract.contract_code.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:03d}"

    @staticmethod
    def get_contract(db: Session, contract_id: int) -> Optional[Contract]:
        """获取合同详情"""
        return (
            db.query(Contract)
            .options(
                joinedload(Contract.terms),
                joinedload(Contract.approvals),
                joinedload(Contract.attachments),
            )
            .filter(Contract.id == contract_id)
            .first()
        )

    @staticmethod
    def get_contracts(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        contract_type: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> tuple[List[Contract], int]:
        """获取合同列表（支持搜索/筛选）"""
        query = db.query(Contract)
        
        # 筛选条件
        if status:
            query = query.filter(Contract.status == status)
        if customer_id:
            query = query.filter(Contract.customer_id == customer_id)
        if contract_type:
            query = query.filter(Contract.contract_type == contract_type)
        if keyword:
            query = query.filter(
                or_(
                    Contract.contract_code.like(f"%{keyword}%"),
                    Contract.contract_name.like(f"%{keyword}%"),
                    Contract.customer_contract_no.like(f"%{keyword}%"),
                )
            )
        
        total = query.count()
        contracts = query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()
        
        return contracts, total

    @staticmethod
    def update_contract(
        db: Session, contract_id: int, contract_data: ContractUpdate
    ) -> Optional[Contract]:
        """更新合同"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return None
        
        # 只允许在草稿状态下更新
        if contract.status != 'draft':
            raise ValueError("只能更新草稿状态的合同")
        
        # 更新字段
        update_data = contract_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)
        
        # 重新计算未收款金额
        if contract_data.total_amount is not None or contract_data.received_amount is not None:
            contract.unreceived_amount = contract.total_amount - contract.received_amount
        
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def delete_contract(db: Session, contract_id: int) -> bool:
        """删除合同（仅草稿状态）"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False
        
        if contract.status != 'draft':
            raise ValueError("只能删除草稿状态的合同")
        
        db.delete(contract)
        db.commit()
        return True

    # ========== 合同审批流程 ==========
    @staticmethod
    def submit_for_approval(db: Session, contract_id: int, user_id: int) -> Contract:
        """提交审批"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        
        if contract.status != 'draft':
            raise ValueError("只能提交草稿状态的合同")
        
        # 根据金额创建审批流程
        approvals = ContractEnhancedService._create_approval_flow(
            db, contract.id, contract.total_amount
        )
        
        # 更新合同状态
        contract.status = 'approving' if approvals else 'approved'
        
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def _create_approval_flow(db: Session, contract_id: int, amount: Decimal) -> List[ContractApproval]:
        """创建审批流程（根据金额分级）"""
        approvals = []
        
        if amount < 100000:
            # 金额<10万：销售经理审批
            approvals.append(
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=1,
                    approval_role="sales_manager",
                    approval_status="pending",
                )
            )
        elif amount < 500000:
            # 金额10-50万：销售总监审批
            approvals.append(
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=1,
                    approval_role="sales_director",
                    approval_status="pending",
                )
            )
        else:
            # 金额>50万：销售总监 + 财务总监 + 总经理审批
            approvals.extend([
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=1,
                    approval_role="sales_director",
                    approval_status="pending",
                ),
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=2,
                    approval_role="finance_director",
                    approval_status="pending",
                ),
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=3,
                    approval_role="general_manager",
                    approval_status="pending",
                ),
            ])
        
        for approval in approvals:
            db.add(approval)
        
        db.flush()
        return approvals

    @staticmethod
    def approve_contract(
        db: Session, contract_id: int, approval_id: int, user_id: int, opinion: Optional[str] = None
    ) -> Contract:
        """审批通过"""
        approval = (
            db.query(ContractApproval)
            .filter(
                ContractApproval.id == approval_id,
                ContractApproval.contract_id == contract_id,
            )
            .first()
        )
        
        if not approval:
            raise ValueError("审批记录不存在")
        
        if approval.approval_status != "pending":
            raise ValueError("该审批已处理")
        
        # 更新审批记录
        approval.approver_id = user_id
        approval.approval_status = "approved"
        approval.approval_opinion = opinion
        approval.approved_at = datetime.now()
        
        # 检查是否所有审批都已完成
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        pending_count = (
            db.query(ContractApproval)
            .filter(
                ContractApproval.contract_id == contract_id,
                ContractApproval.approval_status == "pending",
            )
            .count()
        )
        
        if pending_count == 0:
            # 所有审批通过，更新合同状态
            contract.status = "approved"
        
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def reject_contract(
        db: Session, contract_id: int, approval_id: int, user_id: int, opinion: str
    ) -> Contract:
        """审批驳回"""
        approval = (
            db.query(ContractApproval)
            .filter(
                ContractApproval.id == approval_id,
                ContractApproval.contract_id == contract_id,
            )
            .first()
        )
        
        if not approval:
            raise ValueError("审批记录不存在")
        
        if approval.approval_status != "pending":
            raise ValueError("该审批已处理")
        
        # 更新审批记录
        approval.approver_id = user_id
        approval.approval_status = "rejected"
        approval.approval_opinion = opinion
        approval.approved_at = datetime.now()
        
        # 驳回合同，回到草稿状态
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        contract.status = "draft"
        
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def get_pending_approvals(db: Session, user_id: int) -> List[ContractApproval]:
        """获取待审批列表（我的待办）"""
        # TODO: 需要根据用户角色匹配approval_role
        return (
            db.query(ContractApproval)
            .filter(ContractApproval.approval_status == "pending")
            .options(joinedload(ContractApproval.contract))
            .all()
        )

    # ========== 合同条款管理 ==========
    @staticmethod
    def add_term(db: Session, contract_id: int, term_data: ContractTermCreate) -> ContractTerm:
        """添加条款"""
        term = ContractTerm(contract_id=contract_id, **term_data.model_dump())
        db.add(term)
        db.commit()
        db.refresh(term)
        return term

    @staticmethod
    def get_terms(db: Session, contract_id: int) -> List[ContractTerm]:
        """获取条款列表"""
        return db.query(ContractTerm).filter(ContractTerm.contract_id == contract_id).all()

    @staticmethod
    def update_term(db: Session, term_id: int, term_content: str) -> Optional[ContractTerm]:
        """更新条款"""
        term = db.query(ContractTerm).filter(ContractTerm.id == term_id).first()
        if term:
            term.term_content = term_content
            db.commit()
            db.refresh(term)
        return term

    @staticmethod
    def delete_term(db: Session, term_id: int) -> bool:
        """删除条款"""
        term = db.query(ContractTerm).filter(ContractTerm.id == term_id).first()
        if term:
            db.delete(term)
            db.commit()
            return True
        return False

    # ========== 合同附件管理 ==========
    @staticmethod
    def add_attachment(
        db: Session, contract_id: int, attachment_data: ContractAttachmentCreate, user_id: int
    ) -> ContractAttachment:
        """上传附件"""
        attachment = ContractAttachment(
            contract_id=contract_id,
            uploaded_by=user_id,
            **attachment_data.model_dump()
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    @staticmethod
    def get_attachments(db: Session, contract_id: int) -> List[ContractAttachment]:
        """获取附件列表"""
        return db.query(ContractAttachment).filter(ContractAttachment.contract_id == contract_id).all()

    @staticmethod
    def delete_attachment(db: Session, attachment_id: int) -> bool:
        """删除附件"""
        attachment = db.query(ContractAttachment).filter(ContractAttachment.id == attachment_id).first()
        if attachment:
            db.delete(attachment)
            db.commit()
            return True
        return False

    # ========== 合同状态流转 ==========
    @staticmethod
    def mark_as_signed(db: Session, contract_id: int) -> Contract:
        """标记为已签署"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        
        if contract.status != "approved":
            raise ValueError("只能标记已审批的合同为已签署")
        
        contract.status = "signed"
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def mark_as_executing(db: Session, contract_id: int) -> Contract:
        """标记为执行中"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        
        if contract.status != "signed":
            raise ValueError("只能标记已签署的合同为执行中")
        
        contract.status = "executing"
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def mark_as_completed(db: Session, contract_id: int) -> Contract:
        """标记为已完成"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        
        if contract.status != "executing":
            raise ValueError("只能标记执行中的合同为已完成")
        
        contract.status = "completed"
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def void_contract(db: Session, contract_id: int, reason: Optional[str] = None) -> Contract:
        """作废合同"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        
        if contract.status == "completed":
            raise ValueError("已完成的合同不能作废")
        
        contract.status = "voided"
        db.commit()
        db.refresh(contract)
        return contract

    # ========== 合同统计 ==========
    @staticmethod
    def get_contract_stats(db: Session) -> ContractStats:
        """获取合同统计"""
        total_count = db.query(func.count(Contract.id)).scalar() or 0
        draft_count = db.query(func.count(Contract.id)).filter(Contract.status == "draft").scalar() or 0
        approving_count = db.query(func.count(Contract.id)).filter(Contract.status == "approving").scalar() or 0
        signed_count = db.query(func.count(Contract.id)).filter(Contract.status == "signed").scalar() or 0
        executing_count = db.query(func.count(Contract.id)).filter(Contract.status == "executing").scalar() or 0
        completed_count = db.query(func.count(Contract.id)).filter(Contract.status == "completed").scalar() or 0
        voided_count = db.query(func.count(Contract.id)).filter(Contract.status == "voided").scalar() or 0
        
        total_amount = db.query(func.sum(Contract.total_amount)).scalar() or Decimal(0)
        received_amount = db.query(func.sum(Contract.received_amount)).scalar() or Decimal(0)
        unreceived_amount = db.query(func.sum(Contract.unreceived_amount)).scalar() or Decimal(0)
        
        return ContractStats(
            total_count=total_count,
            draft_count=draft_count,
            approving_count=approving_count,
            signed_count=signed_count,
            executing_count=executing_count,
            completed_count=completed_count,
            voided_count=voided_count,
            total_amount=total_amount,
            received_amount=received_amount,
            unreceived_amount=unreceived_amount,
        )
