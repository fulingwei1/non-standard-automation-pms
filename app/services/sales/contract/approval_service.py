# -*- coding: utf-8 -*-
"""
合同审批兼容门面。

旧实现写入 contract_approvals；该表已归档删除。保留类名给老调用点使用，
实际全部转发到统一审批引擎服务。
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.services.contract_approval import ContractApprovalService as UnifiedContractApprovalService


class ContractApprovalService:
    """合同审批服务兼容层。"""

    def __init__(self, db: Session):
        self.db = db
        self.unified = UnifiedContractApprovalService(db)

    def submit_for_approval(self, contract_id: int, user_id: int) -> Contract:
        results, errors = self.unified.submit_contracts_for_approval(
            contract_ids=[contract_id],
            initiator_id=user_id,
        )
        if errors and not results:
            raise ValueError(errors[0].get("error") or "提交合同审批失败")
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        return contract

    def approve(
        self,
        contract_id: int,
        approval_id: int,
        user_id: int,
        opinion: Optional[str] = None,
    ) -> Any:
        """approval_id 在兼容层中按统一审批任务 task_id 解释。"""
        return self.unified.approve_task(
            task_id=approval_id,
            approver_id=user_id,
            comment=opinion,
        )

    def reject(
        self,
        contract_id: int,
        approval_id: int,
        user_id: int,
        opinion: str,
    ) -> Any:
        """approval_id 在兼容层中按统一审批任务 task_id 解释。"""
        return self.unified.reject_task(
            task_id=approval_id,
            approver_id=user_id,
            comment=opinion,
        )

    def get_pending_approvals(self, user_id: int) -> list[dict]:
        items, _total = self.unified.get_pending_tasks(user_id=user_id)
        return items
