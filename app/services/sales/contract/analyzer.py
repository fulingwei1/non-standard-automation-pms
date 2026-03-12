# -*- coding: utf-8 -*-
"""
合同统计分析服务

提供合同数据的统计和分析功能
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.schemas.sales.contract_enhanced import ContractStats
from app.utils.decimal_helpers import ZERO
from app.utils.status_helpers import count_by_status


class ContractAnalyzer:
    """合同统计分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> ContractStats:
        """获取合同统计"""
        total_count = self.db.query(func.count(Contract.id)).scalar() or 0

        # 使用 count_by_status 一次查询获取所有状态计数
        status_list = ["draft", "approving", "signed", "executing", "completed", "voided"]
        status_counts = count_by_status(self.db, Contract, status_list)

        total_amount = self.db.query(func.sum(Contract.total_amount)).scalar() or ZERO
        received_amount = self.db.query(func.sum(Contract.received_amount)).scalar() or ZERO
        unreceived_amount = self.db.query(func.sum(Contract.unreceived_amount)).scalar() or ZERO

        return ContractStats(
            total_count=total_count,
            draft_count=status_counts.get("draft", 0),
            approving_count=status_counts.get("approving", 0),
            signed_count=status_counts.get("signed", 0),
            executing_count=status_counts.get("executing", 0),
            completed_count=status_counts.get("completed", 0),
            voided_count=status_counts.get("voided", 0),
            total_amount=total_amount,
            received_amount=received_amount,
            unreceived_amount=unreceived_amount,
        )
