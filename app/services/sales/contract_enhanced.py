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
from typing import Any, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.sales.operation_log import SalesOperationType
from app.models.sales.contracts import (
    Contract,
    ContractAttachment,
    ContractTerm,
)
from app.models.user import User
from app.schemas.sales.contract_enhanced import (
    ContractAttachmentCreate,
    ContractCreate,
    ContractStats,
    ContractTermCreate,
    ContractUpdate,
)
from app.services.contract_approval import (
    ContractApprovalService as UnifiedContractApprovalService,
)
from app.services.sales.contract.analyzer import ContractAnalyzer
from app.services.sales.contract.attachment_service import ContractAttachmentService
from app.services.sales.contract.status_service import (
    ContractStatusService,
    contract_status_query_values,
    normalize_contract_status,
)
from app.services.sales.contract.term_service import ContractTermService
from app.services.sales.contract_operation_audit import (
    contract_audit_value,
    log_contract_operation,
)
from app.utils.db_helpers import delete_obj


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
    def _get_operator(db: Session, operator_id: Optional[int]) -> Optional[User]:
        if not operator_id:
            return None
        operator = db.get(User, operator_id)
        return operator if isinstance(operator, User) else None

    @staticmethod
    def _snapshot(contract: Contract, **extra: Any) -> dict[str, Any]:
        value = contract_audit_value(contract)
        value.update(extra)
        return value

    @staticmethod
    def _log_contract_operation(
        db: Session,
        contract: Optional[Contract],
        operation_type: str,
        operator_id: Optional[int],
        *,
        old_value: Optional[dict[str, Any]] = None,
        new_value: Optional[dict[str, Any]] = None,
        operation_desc: str,
        remark: Optional[str] = None,
    ) -> None:
        operator = ContractEnhancedService._get_operator(db, operator_id)
        if not contract or not operator:
            return
        log_contract_operation(
            db,
            contract,
            operation_type,
            operator,
            old_value=old_value,
            new_value=new_value,
            operation_desc=operation_desc,
            remark=remark,
        )

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
        contract_dict["status"] = "DRAFT"  # 初始状态为草稿

        contract = Contract(**contract_dict)
        db.add(contract)
        db.flush()  # 获取合同ID

        # 创建合同条款
        if contract_data.terms:
            for term_data in contract_data.terms:
                term = ContractTerm(contract_id=contract.id, **term_data.model_dump())
                db.add(term)

        ContractEnhancedService._log_contract_operation(
            db,
            contract,
            SalesOperationType.CREATE,
            user_id,
            new_value=contract_audit_value(contract),
            operation_desc="增强合同创建",
        )
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
            query = query.filter(Contract.status.in_(contract_status_query_values(status)))
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
        db: Session,
        contract_id: int,
        contract_data: ContractUpdate,
        operator_id: Optional[int] = None,
    ) -> Optional[Contract]:
        """更新合同"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return None

        # 只允许在草稿状态下更新
        if normalize_contract_status(contract.status) != "DRAFT":
            raise ValueError("只能更新草稿状态的合同")

        update_data = contract_data.model_dump(exclude_unset=True)
        if "status" in update_data:
            raise ValueError("合同状态不可通过通用更新修改")

        old_value = (
            contract_audit_value(contract)
            if ContractEnhancedService._get_operator(db, operator_id)
            else None
        )

        # 更新字段
        for field, value in update_data.items():
            setattr(contract, field, value)

        # 重新计算未收款金额
        if contract_data.total_amount is not None or contract_data.received_amount is not None:
            contract.unreceived_amount = contract.total_amount - contract.received_amount

        ContractEnhancedService._log_contract_operation(
            db,
            contract,
            SalesOperationType.UPDATE,
            operator_id,
            old_value=old_value,
            new_value=contract_audit_value(contract),
            operation_desc="增强合同更新",
        )
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def delete_contract(
        db: Session, contract_id: int, operator_id: Optional[int] = None
    ) -> bool:
        """删除合同（仅草稿状态）"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False

        if normalize_contract_status(contract.status) != "DRAFT":
            raise ValueError("只能删除草稿状态的合同")

        old_value = (
            contract_audit_value(contract)
            if ContractEnhancedService._get_operator(db, operator_id)
            else None
        )
        ContractEnhancedService._log_contract_operation(
            db,
            contract,
            SalesOperationType.DELETE,
            operator_id,
            old_value=old_value,
            operation_desc="增强合同删除",
        )
        delete_obj(db, contract)
        return True

    # ========== 审批流程（委托给 approval_service）==========

    @staticmethod
    def submit_for_approval(db: Session, contract_id: int, user_id: int) -> Contract:
        """提交审批（统一审批引擎）。"""
        results, errors = UnifiedContractApprovalService(db).submit_contracts_for_approval(
            contract_ids=[contract_id],
            initiator_id=user_id,
        )
        if errors and not results:
            raise ValueError(errors[0].get("error") or "提交合同审批失败")
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        return contract

    @staticmethod
    def approve_contract(
        db: Session, contract_id: int, approval_id: int, user_id: int, opinion: Optional[str] = None
    ) -> Contract:
        """旧合同审批记录入口已停用。"""
        raise ValueError("旧合同审批记录入口已下线，请使用统一审批任务ID审批")

    @staticmethod
    def reject_contract(
        db: Session, contract_id: int, approval_id: int, user_id: int, opinion: str
    ) -> Contract:
        """旧合同审批记录入口已停用。"""
        raise ValueError("旧合同审批记录入口已下线，请使用统一审批任务ID审批")

    @staticmethod
    def get_pending_approvals(db: Session, user_id: int) -> List[dict]:
        """获取统一审批待办列表。"""
        items, _total = UnifiedContractApprovalService(db).get_pending_tasks(user_id=user_id)
        return items

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
    def add_term(
        db: Session,
        contract_id: int,
        term_data: ContractTermCreate,
        operator_id: Optional[int] = None,
    ) -> ContractTerm:
        """添加条款"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        old_value = (
            ContractEnhancedService._snapshot(contract)
            if contract and ContractEnhancedService._get_operator(db, operator_id)
            else None
        )
        term = ContractTermService(db).add_term(contract_id, term_data)
        if contract:
            ContractEnhancedService._log_contract_operation(
                db,
                contract,
                SalesOperationType.UPDATE,
                operator_id,
                old_value=old_value,
                new_value=ContractEnhancedService._snapshot(
                    contract,
                    term_id=term.id,
                    term_type=term.term_type,
                    term_content=term.term_content,
                ),
                operation_desc="新增合同条款",
            )
            db.commit()
        return term

    @staticmethod
    def get_terms(db: Session, contract_id: int) -> List[ContractTerm]:
        """获取条款列表"""
        return ContractTermService(db).get_terms(contract_id)

    @staticmethod
    def update_term(
        db: Session,
        term_id: int,
        term_content: str,
        operator_id: Optional[int] = None,
    ) -> Optional[ContractTerm]:
        """更新条款"""
        term_before = db.query(ContractTerm).filter(ContractTerm.id == term_id).first()
        contract = (
            db.query(Contract).filter(Contract.id == term_before.contract_id).first()
            if term_before
            else None
        )
        old_value = (
            ContractEnhancedService._snapshot(
                contract,
                term_id=term_before.id,
                term_type=term_before.term_type,
                term_content=term_before.term_content,
            )
            if contract
            and term_before
            and ContractEnhancedService._get_operator(db, operator_id)
            else None
        )
        term = ContractTermService(db).update_term(term_id, term_content)
        if contract and term:
            ContractEnhancedService._log_contract_operation(
                db,
                contract,
                SalesOperationType.UPDATE,
                operator_id,
                old_value=old_value,
                new_value=ContractEnhancedService._snapshot(
                    contract,
                    term_id=term.id,
                    term_type=term.term_type,
                    term_content=term.term_content,
                ),
                operation_desc="更新合同条款",
            )
            db.commit()
        return term

    @staticmethod
    def delete_term(
        db: Session, term_id: int, operator_id: Optional[int] = None
    ) -> bool:
        """删除条款"""
        term = db.query(ContractTerm).filter(ContractTerm.id == term_id).first()
        contract = (
            db.query(Contract).filter(Contract.id == term.contract_id).first()
            if term
            else None
        )
        old_value = (
            ContractEnhancedService._snapshot(
                contract,
                term_id=term.id,
                term_type=term.term_type,
                term_content=term.term_content,
            )
            if contract and term and ContractEnhancedService._get_operator(db, operator_id)
            else None
        )
        success = ContractTermService(db).delete_term(term_id)
        if success and contract:
            ContractEnhancedService._log_contract_operation(
                db,
                contract,
                SalesOperationType.UPDATE,
                operator_id,
                old_value=old_value,
                new_value=ContractEnhancedService._snapshot(
                    contract,
                    deleted_term_id=term_id,
                ),
                operation_desc="删除合同条款",
            )
            db.commit()
        return success

    # ========== 附件管理（委托给 attachment_service）==========

    @staticmethod
    def add_attachment(
        db: Session, contract_id: int, attachment_data: ContractAttachmentCreate, user_id: int
    ) -> ContractAttachment:
        """上传附件"""
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        old_value = (
            ContractEnhancedService._snapshot(contract)
            if contract and ContractEnhancedService._get_operator(db, user_id)
            else None
        )
        attachment = ContractAttachmentService(db).add_attachment(
            contract_id, attachment_data, user_id
        )
        if contract:
            ContractEnhancedService._log_contract_operation(
                db,
                contract,
                SalesOperationType.ATTACH,
                user_id,
                old_value=old_value,
                new_value=ContractEnhancedService._snapshot(
                    contract,
                    attachment_id=attachment.id,
                    file_name=attachment.file_name,
                    file_path=attachment.file_path,
                ),
                operation_desc="上传合同附件",
            )
            db.commit()
        return attachment

    @staticmethod
    def get_attachments(db: Session, contract_id: int) -> List[ContractAttachment]:
        """获取附件列表"""
        return ContractAttachmentService(db).get_attachments(contract_id)

    @staticmethod
    def delete_attachment(
        db: Session, attachment_id: int, operator_id: Optional[int] = None
    ) -> bool:
        """删除附件"""
        attachment = (
            db.query(ContractAttachment)
            .filter(ContractAttachment.id == attachment_id)
            .first()
        )
        contract = (
            db.query(Contract).filter(Contract.id == attachment.contract_id).first()
            if attachment
            else None
        )
        old_value = (
            ContractEnhancedService._snapshot(
                contract,
                attachment_id=attachment.id,
                file_name=attachment.file_name,
                file_path=attachment.file_path,
            )
            if contract
            and attachment
            and ContractEnhancedService._get_operator(db, operator_id)
            else None
        )
        success = ContractAttachmentService(db).delete_attachment(attachment_id)
        if success and contract:
            ContractEnhancedService._log_contract_operation(
                db,
                contract,
                SalesOperationType.DELETE,
                operator_id,
                old_value=old_value,
                new_value=ContractEnhancedService._snapshot(
                    contract,
                    deleted_attachment_id=attachment_id,
                ),
                operation_desc="删除合同附件",
            )
            db.commit()
        return success

    # ========== 统计分析（委托给 analyzer）==========

    @staticmethod
    def get_contract_stats(db: Session) -> ContractStats:
        """获取合同统计"""
        return ContractAnalyzer(db).get_stats()
