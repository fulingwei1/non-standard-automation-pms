# -*- coding: utf-8 -*-
"""
合同状态流转服务

处理合同生命周期状态变更：
- 标记已签署
- 标记执行中
- 标记已完成
- 作废合同
"""

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.models.sales.operation_log import SalesEntityType
from app.services.sales.operation_log_service import SalesOperationLogService


CANONICAL_CONTRACT_STATUSES = {
    "DRAFT",
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "SIGNED",
    "EXECUTING",
    "COMPLETED",
    "CANCELLED",
}

CONTRACT_STATUS_ALIASES = {
    "DRAFT": "DRAFT",
    "APPROVING": "PENDING_APPROVAL",
    "PENDING_APPROVAL": "PENDING_APPROVAL",
    "REVIEW": "APPROVED",
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "SIGNED": "SIGNED",
    "ACTIVE": "EXECUTING",
    "EXECUTING": "EXECUTING",
    "COMPLETED": "COMPLETED",
    "CANCELLED": "CANCELLED",
    "TERMINATED": "CANCELLED",
    "VOIDED": "CANCELLED",
}

CONTRACT_STATUS_QUERY_VALUES = {
    "DRAFT": {"DRAFT", "draft"},
    "PENDING_APPROVAL": {"PENDING_APPROVAL", "pending_approval", "APPROVING", "approving"},
    "APPROVED": {"APPROVED", "approved", "REVIEW", "review"},
    "REJECTED": {"REJECTED", "rejected"},
    "SIGNED": {"SIGNED", "signed"},
    "EXECUTING": {"EXECUTING", "executing", "ACTIVE", "active"},
    "COMPLETED": {"COMPLETED", "completed"},
    "CANCELLED": {"CANCELLED", "cancelled", "VOIDED", "voided", "TERMINATED", "terminated"},
}


def normalize_contract_status(status: str | None) -> str | None:
    """Normalize legacy contract statuses to the canonical uppercase vocabulary."""
    if status is None:
        return None
    raw = str(status).strip()
    if not raw:
        return None
    return CONTRACT_STATUS_ALIASES.get(raw.upper(), raw.upper())


def apply_contract_status(contract: Contract, status: str) -> str:
    """Apply a canonical contract status to an ORM object."""
    canonical = normalize_contract_status(status)
    if canonical not in CANONICAL_CONTRACT_STATUSES:
        raise ValueError(f"不支持的合同状态: {status}")
    contract.status = canonical
    return canonical


def contract_status_query_values(status: str | Iterable[str]) -> list[str]:
    """Expand a requested status into canonical and legacy DB values."""
    if isinstance(status, str):
        raw_values = [item.strip() for item in status.split(",") if item.strip()]
    else:
        raw_values = [str(item).strip() for item in status if str(item).strip()]

    values: set[str] = set()
    for raw in raw_values:
        canonical = normalize_contract_status(raw)
        if canonical in CONTRACT_STATUS_QUERY_VALUES:
            values.update(CONTRACT_STATUS_QUERY_VALUES[canonical])
        elif canonical:
            values.add(canonical)
    return sorted(values)


def fold_contract_status_counts(rows: Iterable[tuple[str | None, int]]) -> dict[str, int]:
    """Fold raw DB status counts into canonical status buckets."""
    counts = {status: 0 for status in CANONICAL_CONTRACT_STATUSES}
    for raw_status, count in rows:
        canonical = normalize_contract_status(raw_status)
        if canonical in counts:
            counts[canonical] += int(count or 0)
    return counts


class ContractStatusService:
    """合同状态流转服务"""

    def __init__(self, db: Session):
        self.db = db

    def _get_contract(self, contract_id: int) -> Contract:
        """获取合同，不存在则抛出异常"""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")
        return contract

    def _log_status_change(
        self, contract: Contract, old_status: str | None, new_status: str
    ) -> None:
        """记录状态变更日志"""
        from app.models.user import User

        system_user = self.db.query(User).filter(User.username == "system").first()
        if system_user:
            SalesOperationLogService.log_status_change(
                self.db,
                entity_type=SalesEntityType.CONTRACT,
                entity_id=contract.id,
                operator=system_user,
                old_status=old_status,
                new_status=new_status,
                entity_code=contract.contract_code,
            )

    def mark_as_signed(self, contract_id: int) -> Contract:
        """标记为已签署"""
        contract = self._get_contract(contract_id)
        if normalize_contract_status(contract.status) != "APPROVED":
            raise ValueError("只能标记已审批的合同为已签署")

        old_status = contract.status
        new_status = apply_contract_status(contract, "SIGNED")
        self._log_status_change(contract, old_status, new_status)
        self.db.commit()
        self.db.refresh(contract)

        return contract

    def mark_as_executing(self, contract_id: int) -> Contract:
        """标记为执行中"""
        contract = self._get_contract(contract_id)
        if normalize_contract_status(contract.status) != "SIGNED":
            raise ValueError("只能标记已签署的合同为执行中")

        old_status = contract.status
        new_status = apply_contract_status(contract, "EXECUTING")
        self._log_status_change(contract, old_status, new_status)
        self.db.commit()
        self.db.refresh(contract)

        return contract

    def mark_as_completed(self, contract_id: int, *, allow_archive: bool = False) -> Contract:
        """标记为已完成"""
        contract = self._get_contract(contract_id)
        if not allow_archive and normalize_contract_status(contract.status) != "EXECUTING":
            raise ValueError("只能标记执行中的合同为已完成")

        old_status = contract.status
        new_status = apply_contract_status(contract, "COMPLETED")
        self._log_status_change(contract, old_status, new_status)
        self.db.commit()
        self.db.refresh(contract)

        return contract

    def void_contract(self, contract_id: int, reason: Optional[str] = None) -> Contract:
        """作废合同"""
        contract = self._get_contract(contract_id)
        if normalize_contract_status(contract.status) == "COMPLETED":
            raise ValueError("已完成的合同不能作废")

        old_status = contract.status
        new_status = apply_contract_status(contract, "CANCELLED")
        self._log_status_change(contract, old_status, new_status)
        self.db.commit()
        self.db.refresh(contract)

        return contract
