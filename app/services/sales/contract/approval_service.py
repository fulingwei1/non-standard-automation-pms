# -*- coding: utf-8 -*-
"""
合同审批服务

处理合同审批流程：
- 提交审批
- 审批通过/驳回
- 查询待审批列表
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.sales.contracts import Contract, ContractApproval
from app.utils.status_helpers import assert_status_allows


class ContractApprovalService:
    """合同审批服务"""

    def __init__(self, db: Session):
        self.db = db

    def submit_for_approval(self, contract_id: int, user_id: int) -> Contract:
        """提交审批"""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")

        assert_status_allows(contract, "draft", "只能提交草稿状态的合同")

        # 根据金额创建审批流程
        approvals = self._create_approval_flow(contract.id, contract.total_amount)

        # 更新合同状态
        contract.status = "approving" if approvals else "approved"

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def _create_approval_flow(
        self, contract_id: int, amount: Decimal
    ) -> List[ContractApproval]:
        """
        创建审批流程（根据金额分级）

        审批规则：
        - 金额 < 10万：销售经理审批
        - 金额 10-50万：销售总监审批
        - 金额 > 50万：销售总监 + 财务总监 + 总经理审批
        """
        approvals = []

        if amount < 100000:
            approvals.append(
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=1,
                    approval_role="sales_manager",
                    approval_status="pending",
                )
            )
        elif amount < 500000:
            approvals.append(
                ContractApproval(
                    contract_id=contract_id,
                    approval_level=1,
                    approval_role="sales_director",
                    approval_status="pending",
                )
            )
        else:
            approvals.extend(
                [
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
                ]
            )

        for approval in approvals:
            self.db.add(approval)

        self.db.flush()
        return approvals

    def approve(
        self,
        contract_id: int,
        approval_id: int,
        user_id: int,
        opinion: Optional[str] = None,
    ) -> Contract:
        """审批通过"""
        approval = (
            self.db.query(ContractApproval)
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
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        pending_count = (
            self.db.query(ContractApproval)
            .filter(
                ContractApproval.contract_id == contract_id,
                ContractApproval.approval_status == "pending",
            )
            .count()
        )

        if pending_count == 0:
            contract.status = "approved"

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def reject(
        self,
        contract_id: int,
        approval_id: int,
        user_id: int,
        opinion: str,
    ) -> Contract:
        """审批驳回"""
        approval = (
            self.db.query(ContractApproval)
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
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        contract.status = "draft"

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_pending_approvals(self, user_id: int) -> List[ContractApproval]:
        """获取待审批列表（我的待办）"""
        # TODO: 需要根据用户角色匹配 approval_role
        return (
            self.db.query(ContractApproval)
            .filter(ContractApproval.approval_status == "pending")
            .options(joinedload(ContractApproval.contract))
            .all()
        )
