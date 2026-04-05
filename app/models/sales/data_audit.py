# -*- coding: utf-8 -*-
"""
销售数据审核模型

用于敏感数据变更的审核流程，变更需审核通过后才能生效。
支持商机金额修改、合同条款变更、客户信息修改等场景。
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class DataAuditStatusEnum(str, Enum):
    """数据审核状态枚举"""

    PENDING = "PENDING"  # 待审核
    APPROVED = "APPROVED"  # 已通过
    REJECTED = "REJECTED"  # 已驳回
    CANCELLED = "CANCELLED"  # 已撤销


class DataAuditPriorityEnum(str, Enum):
    """审核优先级枚举"""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class SalesDataAuditRequest(Base):
    """销售数据审核请求表

    记录需要审核的数据变更请求，包括变更前后的值、
    审核状态、审核人意见等信息。
    """

    __tablename__ = "sales_data_audit_requests"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 业务实体标识
    entity_type = Column(
        String(50),
        nullable=False,
        comment="实体类型：OPPORTUNITY/CONTRACT/CUSTOMER/QUOTE",
    )
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    entity_code = Column(String(100), comment="实体编码")

    # 变更信息
    change_type = Column(
        String(50),
        nullable=False,
        comment="变更类型：FIELD_UPDATE/STATUS_CHANGE/AMOUNT_CHANGE/DELETE",
    )
    change_reason = Column(Text, comment="变更原因说明")
    old_value = Column(JSON, nullable=False, comment="变更前值（JSON格式）")
    new_value = Column(JSON, nullable=False, comment="变更后值（JSON格式）")
    changed_fields = Column(JSON, comment="变更字段列表")

    # 审核状态
    status = Column(
        String(20),
        nullable=False,
        default=DataAuditStatusEnum.PENDING.value,
        comment="状态：PENDING/APPROVED/REJECTED/CANCELLED",
    )
    priority = Column(
        String(20),
        nullable=False,
        default=DataAuditPriorityEnum.NORMAL.value,
        comment="优先级：LOW/NORMAL/HIGH/URGENT",
    )

    # 申请人信息
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    requester_dept = Column(String(100), comment="申请人部门")
    requested_at = Column(DateTime, default=datetime.now, nullable=False, comment="申请时间")

    # 审核人信息
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(DateTime, comment="审核时间")
    review_comment = Column(Text, comment="审核意见")

    # 执行信息（审核通过后应用变更）
    applied_at = Column(DateTime, comment="变更应用时间")
    applied_by = Column(Integer, ForeignKey("users.id"), comment="执行人ID")

    # 关系
    requester = relationship("User", foreign_keys=[requester_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    applier = relationship("User", foreign_keys=[applied_by])

    __table_args__ = (
        Index("idx_data_audit_entity", "entity_type", "entity_id"),
        Index("idx_data_audit_status", "status"),
        Index("idx_data_audit_requester", "requester_id"),
        Index("idx_data_audit_reviewer", "reviewer_id"),
        Index("idx_data_audit_time", "requested_at"),
        {"comment": "销售数据审核请求表"},
    )

    def __repr__(self):
        return (
            f"<SalesDataAuditRequest {self.entity_type}:{self.entity_id} "
            f"status={self.status}>"
        )


# 变更类型常量
class DataChangeType:
    """数据变更类型"""

    FIELD_UPDATE = "FIELD_UPDATE"  # 字段更新
    STATUS_CHANGE = "STATUS_CHANGE"  # 状态变更
    AMOUNT_CHANGE = "AMOUNT_CHANGE"  # 金额变更
    DELETE = "DELETE"  # 删除操作
    OWNER_CHANGE = "OWNER_CHANGE"  # 负责人变更
    CUSTOMER_MERGE = "CUSTOMER_MERGE"  # 客户合并


# 需要审核的实体类型和字段配置
AUDIT_REQUIRED_FIELDS = {
    "OPPORTUNITY": ["est_amount", "expected_close_date", "owner_id"],
    "CONTRACT": ["contract_amount", "signing_date", "payment_terms_summary"],
    "CUSTOMER": ["customer_name", "credit_limit", "industry"],
    "QUOTE": ["total_amount", "discount_rate", "validity_days"],
}
