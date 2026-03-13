# -*- coding: utf-8 -*-
"""
合同管理增强服务 - 完整的CRUD与审批流程

通过委托子模块实现职责分离：
- CRUD 操作：本模块
- 审批流程：contract.approval_service
- 状态流转：contract.status_service
- 条款管理：contract.term_service
- 附件管理：contract.attachment_service
- 统计分析：contract.analyzer
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.sales.contracts import (
    Contract,
    ContractApproval,
    ContractAttachment,
    ContractTerm,
)
from app.schemas.sales.contract_enhanced import (
    ContractAttachmentCreate,
    ContractCreate,
    ContractStats,
    ContractTermCreate,
    ContractUpdate,
)
from app.services.sales.contract.analyzer import ContractAnalyzer
from app.services.sales.contract.approval_service import ContractApprovalService
from app.services.sales.contract.attachment_service import ContractAttachmentService
from app.services.sales.contract.status_service import ContractStatusService
from app.services.sales.contract.term_service import ContractTermService
from app.utils.db_helpers import delete_obj
from app.utils.status_helpers import assert_status_allows


class ContractEnhancedService:
    """
    合同增强服务

    提供合同的完整生命周期管理，包括：
    - CRUD 操作
    - 审批流程
    - 状态流转
    - 条款和附件管理
    - 统计分析

    所有方法使用静态方法，db 作为第一个参数，保持向后兼容。
    内部委托给专业子服务处理具体逻辑。
    """

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
        contract_dict = contract_data.model_dump(exclude={"terms"})
        contract_dict["unreceived_amount"] = unreceived_amount
        contract_dict["status"] = "draft"  # 初始状态为草稿

        contract = Contract(**contract_dict)
        db.add(contract)
        db.flush()  # 获取合同ID

        # 创建合同条款
        if contract_data.terms:
            for term_data in contract_data.terms:
                term = ContractTerm(contract_id=contract.id, **term_data.model_dump())
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
        assert_status_allows(contract, "draft", "只能更新草稿状态的合同")

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

        assert_status_allows(contract, "draft", "只能删除草稿状态的合同")

        delete_obj(db, contract)
        return True

    # ========== 审批流程（委托给 approval_service）==========

    @staticmethod
    def submit_for_approval(db: Session, contract_id: int, user_id: int) -> Contract:
        """提交审批"""
        return ContractApprovalService(db).submit_for_approval(contract_id, user_id)

    @staticmethod
    def approve_contract(
        db: Session, contract_id: int, approval_id: int, user_id: int, opinion: Optional[str] = None
    ) -> Contract:
        """审批通过"""
        return ContractApprovalService(db).approve(contract_id, approval_id, user_id, opinion)

    @staticmethod
    def reject_contract(
        db: Session, contract_id: int, approval_id: int, user_id: int, opinion: str
    ) -> Contract:
        """审批驳回"""
        return ContractApprovalService(db).reject(contract_id, approval_id, user_id, opinion)

    @staticmethod
    def get_pending_approvals(db: Session, user_id: int) -> List[ContractApproval]:
        """获取待审批列表"""
        return ContractApprovalService(db).get_pending_approvals(user_id)

    # ========== 状态流转（委托给 status_service）==========

    @staticmethod
    def mark_as_signed(db: Session, contract_id: int) -> Contract:
        """标记为已签署"""
        return ContractStatusService(db).mark_as_signed(contract_id)

    @staticmethod
    def mark_as_executing(db: Session, contract_id: int) -> Contract:
        """标记为执行中"""
        return ContractStatusService(db).mark_as_executing(contract_id)

    @staticmethod
    def mark_as_completed(db: Session, contract_id: int) -> Contract:
        """标记为已完成"""
        return ContractStatusService(db).mark_as_completed(contract_id)

    @staticmethod
    def void_contract(db: Session, contract_id: int, reason: Optional[str] = None) -> Contract:
        """作废合同"""
        return ContractStatusService(db).void_contract(contract_id, reason)

    # ========== 条款管理（委托给 term_service）==========

    @staticmethod
    def add_term(db: Session, contract_id: int, term_data: ContractTermCreate) -> ContractTerm:
        """添加条款"""
        return ContractTermService(db).add_term(contract_id, term_data)

    @staticmethod
    def get_terms(db: Session, contract_id: int) -> List[ContractTerm]:
        """获取条款列表"""
        return ContractTermService(db).get_terms(contract_id)

    @staticmethod
    def update_term(db: Session, term_id: int, term_content: str) -> Optional[ContractTerm]:
        """更新条款"""
        return ContractTermService(db).update_term(term_id, term_content)

    @staticmethod
    def delete_term(db: Session, term_id: int) -> bool:
        """删除条款"""
        return ContractTermService(db).delete_term(term_id)

    # ========== 附件管理（委托给 attachment_service）==========

    @staticmethod
    def add_attachment(
        db: Session, contract_id: int, attachment_data: ContractAttachmentCreate, user_id: int
    ) -> ContractAttachment:
        """上传附件"""
        return ContractAttachmentService(db).add_attachment(contract_id, attachment_data, user_id)

    @staticmethod
    def get_attachments(db: Session, contract_id: int) -> List[ContractAttachment]:
        """获取附件列表"""
        return ContractAttachmentService(db).get_attachments(contract_id)

    @staticmethod
    def delete_attachment(db: Session, attachment_id: int) -> bool:
        """删除附件"""
        return ContractAttachmentService(db).delete_attachment(attachment_id)

    # ========== 统计分析（委托给 analyzer）==========

    @staticmethod
    def get_contract_stats(db: Session) -> ContractStats:
        """获取合同统计"""
        return ContractAnalyzer(db).get_stats()
