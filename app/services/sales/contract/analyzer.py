# -*- coding: utf-8 -*-
"""
合同统计分析服务

提供合同数据的统计和分析功能
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.schemas.sales.contract_enhanced import ContractStats
from app.services.sales.contract.status_service import fold_contract_status_counts
from app.utils.decimal_helpers import ZERO


class ContractAnalyzer:
    """合同统计分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> ContractStats:
        """获取合同统计"""
        total_count = self.db.query(func.count(Contract.id)).scalar() or 0

        raw_status_counts = (
            self.db.query(Contract.status, func.count(Contract.id))
            .group_by(Contract.status)
            .all()
        )
        status_counts = fold_contract_status_counts(raw_status_counts)

        total_amount = self.db.query(func.sum(Contract.total_amount)).scalar() or ZERO
        received_amount = self.db.query(func.sum(Contract.received_amount)).scalar() or ZERO
        unreceived_amount = self.db.query(func.sum(Contract.unreceived_amount)).scalar() or ZERO

        return ContractStats(
            total_count=total_count,
            draft_count=status_counts.get("DRAFT", 0),
            approving_count=status_counts.get("PENDING_APPROVAL", 0),
            signed_count=status_counts.get("SIGNED", 0),
            executing_count=status_counts.get("EXECUTING", 0),
            completed_count=status_counts.get("COMPLETED", 0),
            voided_count=status_counts.get("CANCELLED", 0),
            total_amount=total_amount,
            received_amount=received_amount,
            unreceived_amount=unreceived_amount,
        )
