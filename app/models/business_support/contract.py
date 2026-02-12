# -*- coding: utf-8 -*-
"""
商务支持模块 - 合同审核模型
"""

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ContractReview(Base, TimestampMixin):
    """合同审核记录表"""

    __tablename__ = "contract_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    review_type = Column(String(20), comment="审核类型：business/legal/finance")
    review_status = Column(String(20), default="pending", comment="审核状态：pending/passed/rejected")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    review_comment = Column(Text, comment="审核意见")
    reviewed_at = Column(DateTime, comment="审核时间")
    risk_items = Column(JSON, comment="风险项列表")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_contract_review_contract", "contract_id"),
        Index("idx_contract_review_status", "review_status"),
    )

    def __repr__(self):
        return f"<ContractReview {self.id}>"


class ContractSealRecord(Base, TimestampMixin):
    """合同盖章邮寄记录表"""

    __tablename__ = "contract_seal_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    seal_status = Column(String(20), default="pending", comment="盖章状态：pending/sealed/sent/received/archived")
    seal_date = Column(Date, comment="盖章日期")
    seal_operator_id = Column(Integer, ForeignKey("users.id"), comment="盖章操作人ID")
    send_date = Column(Date, comment="邮寄日期")
    tracking_no = Column(String(50), comment="快递单号")
    courier_company = Column(String(50), comment="快递公司")
    receive_date = Column(Date, comment="回收日期")
    archive_date = Column(Date, comment="归档日期")
    archive_location = Column(String(200), comment="归档位置")
    remark = Column(Text, comment="备注")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    seal_operator = relationship("User", foreign_keys=[seal_operator_id])

    __table_args__ = (
        Index("idx_seal_record_contract", "contract_id"),
        Index("idx_seal_status", "seal_status"),
    )

    def __repr__(self):
        return f"<ContractSealRecord {self.id}>"
