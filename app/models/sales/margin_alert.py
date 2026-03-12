# -*- coding: utf-8 -*-
"""
毛利率预警模型

提供毛利率预警配置和记录，当报价毛利率低于阈值时触发审批流程
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class MarginAlertLevelEnum(str, Enum):
    """毛利率预警级别"""

    GREEN = "GREEN"  # 正常 (>= 标准阈值)
    YELLOW = "YELLOW"  # 警告 (>= 警告阈值 且 < 标准阈值)
    RED = "RED"  # 警报 (< 警告阈值)


class MarginAlertStatusEnum(str, Enum):
    """毛利率预警状态"""

    PENDING = "PENDING"  # 待审批
    APPROVED = "APPROVED"  # 已批准
    REJECTED = "REJECTED"  # 已驳回
    ESCALATED = "ESCALATED"  # 已升级
    CANCELLED = "CANCELLED"  # 已取消


class MarginAlertConfig(Base, TimestampMixin):
    """
    毛利率预警配置

    按客户等级、项目类型等配置不同的毛利率阈值和审批规则
    """

    __tablename__ = "margin_alert_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 配置标识
    name = Column(String(100), nullable=False, comment="配置名称")
    code = Column(String(50), unique=True, nullable=False, comment="配置编码")
    description = Column(Text, comment="配置描述")

    # 适用范围
    customer_level = Column(String(50), comment="客户等级（A/B/C/D）")
    project_type = Column(String(50), comment="项目类型")
    industry = Column(String(50), comment="适用行业")

    # 毛利率阈值（百分比）
    standard_margin = Column(Numeric(5, 2), default=25, comment="标准毛利率阈值(%)")
    warning_margin = Column(Numeric(5, 2), default=20, comment="警告毛利率阈值(%)")
    alert_margin = Column(Numeric(5, 2), default=15, comment="警报毛利率阈值(%)")
    minimum_margin = Column(Numeric(5, 2), default=10, comment="最低毛利率(%)")

    # 审批规则
    # {
    #   "YELLOW": {"approver_role": "sales_manager", "auto_escalate_hours": 24},
    #   "RED": {"approver_role": "sales_director", "auto_escalate_hours": 12},
    #   "BELOW_MINIMUM": {"approver_role": "ceo", "auto_escalate_hours": 6}
    # }
    approval_rules = Column(JSON, comment="审批规则（JSON格式）")

    # 通知配置
    notify_roles = Column(JSON, comment="通知角色列表")
    notify_users = Column(JSON, comment="通知用户ID列表")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否默认配置")
    priority = Column(Integer, default=0, comment="优先级（数字越大优先级越高）")

    # 审计
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    __table_args__ = (
        Index("idx_margin_config_code", "code"),
        Index("idx_margin_config_customer_level", "customer_level"),
        Index("idx_margin_config_active", "is_active"),
        Index("idx_margin_config_default", "is_default"),
        {"comment": "毛利率预警配置表"},
    )

    def __repr__(self):
        return f"<MarginAlertConfig {self.code}: {self.name}>"


class MarginAlertRecord(Base, TimestampMixin):
    """
    毛利率预警记录

    记录毛利率预警的触发和处理过程
    """

    __tablename__ = "margin_alert_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价ID")
    quote_version_id = Column(Integer, ForeignKey("quote_versions.id"), comment="报价版本ID")
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), comment="商机ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户ID")
    config_id = Column(Integer, ForeignKey("margin_alert_configs.id"), comment="配置ID")

    # 预警信息
    alert_level = Column(String(20), nullable=False, comment="预警级别")
    alert_reason = Column(Text, comment="预警原因")

    # 毛利率信息
    total_price = Column(Numeric(14, 2), comment="总价")
    total_cost = Column(Numeric(14, 2), comment="总成本")
    gross_margin = Column(Numeric(5, 2), comment="毛利率(%)")
    threshold_margin = Column(Numeric(5, 2), comment="阈值毛利率(%)")
    margin_gap = Column(Numeric(5, 2), comment="毛利率差距(%)")

    # 成本明细快照
    cost_breakdown = Column(JSON, comment="成本拆解快照")

    # 申请信息
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    requested_at = Column(DateTime, default=datetime.now, comment="申请时间")
    justification = Column(Text, comment="申请理由")

    # 审批信息
    status = Column(String(20), default=MarginAlertStatusEnum.PENDING.value, comment="状态")
    current_approver_id = Column(Integer, ForeignKey("users.id"), comment="当前审批人ID")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comment = Column(Text, comment="审批意见")

    # 升级信息
    escalated_at = Column(DateTime, comment="升级时间")
    escalated_to = Column(Integer, ForeignKey("users.id"), comment="升级至用户ID")
    escalate_reason = Column(Text, comment="升级原因")

    # 有效期
    valid_until = Column(Date, comment="批准有效期至")

    # 审批历史
    # [
    #   {"approver_id": 1, "action": "APPROVE", "comment": "...", "at": "2026-03-12T10:00:00"},
    #   ...
    # ]
    approval_history = Column(JSON, comment="审批历史记录")

    # 关系
    quote = relationship("Quote", foreign_keys=[quote_id])
    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    config = relationship("MarginAlertConfig", foreign_keys=[config_id])
    requester = relationship("User", foreign_keys=[requested_by])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    approver = relationship("User", foreign_keys=[approved_by])
    escalated_user = relationship("User", foreign_keys=[escalated_to])

    __table_args__ = (
        Index("idx_margin_alert_quote", "quote_id"),
        Index("idx_margin_alert_opportunity", "opportunity_id"),
        Index("idx_margin_alert_status", "status"),
        Index("idx_margin_alert_level", "alert_level"),
        Index("idx_margin_alert_requested_by", "requested_by"),
        Index("idx_margin_alert_current_approver", "current_approver_id"),
        {"comment": "毛利率预警记录表"},
    )

    def __repr__(self):
        return f"<MarginAlertRecord {self.quote_id}: {self.alert_level} ({self.status})>"
