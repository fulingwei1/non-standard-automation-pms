# -*- coding: utf-8 -*-
"""
合同状态流转服务

处理合同生命周期状态变更：
- 标记已签署
- 标记执行中
- 标记已完成
- 作废合同
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.models.sales.operation_log import SalesEntityType
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.status_helpers import assert_status_allows, assert_status_not


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
        self, contract: Contract, old_status: str, new_status: str
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
        assert_status_allows(contract, "approved", "只能标记已审批的合同为已签署")

        old_status = contract.status
        contract.status = "signed"
        self.db.commit()
        self.db.refresh(contract)

        self._log_status_change(contract, old_status, "signed")
        self.db.commit()

        return contract

    def mark_as_executing(self, contract_id: int) -> Contract:
        """标记为执行中"""
        contract = self._get_contract(contract_id)
        assert_status_allows(contract, "signed", "只能标记已签署的合同为执行中")

        old_status = contract.status
        contract.status = "executing"
        self.db.commit()
        self.db.refresh(contract)

        self._log_status_change(contract, old_status, "executing")
        self.db.commit()

        return contract

    def mark_as_completed(self, contract_id: int) -> Contract:
        """标记为已完成"""
        contract = self._get_contract(contract_id)
        assert_status_allows(contract, "executing", "只能标记执行中的合同为已完成")

        old_status = contract.status
        contract.status = "completed"
        self.db.commit()
        self.db.refresh(contract)

        self._log_status_change(contract, old_status, "completed")
        self.db.commit()

        return contract

    def void_contract(self, contract_id: int, reason: Optional[str] = None) -> Contract:
        """作废合同"""
        contract = self._get_contract(contract_id)
        assert_status_not(contract, "completed", "已完成的合同不能作废")

        old_status = contract.status
        contract.status = "voided"
        self.db.commit()
        self.db.refresh(contract)

        self._log_status_change(contract, old_status, "voided")
        self.db.commit()

        return contract
