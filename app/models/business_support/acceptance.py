# -*- coding: utf-8 -*-
"""
商务支持模块 - 验收跟踪模型
"""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
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


class AcceptanceTracking(Base, TimestampMixin):
    """验收单跟踪记录表（商务支持角度）"""

    __tablename__ = "acceptance_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acceptance_order_id = Column(Integer, ForeignKey("acceptance_orders.id"), nullable=False, comment="验收单ID")
    acceptance_order_no = Column(String(50), comment="验收单号")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    project_code = Column(String(50), comment="项目编号")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")

    # 验收条件检查
    condition_check_status = Column(String(20), default="pending", comment="验收条件检查状态：pending/checking/met/not_met")
    condition_check_result = Column(Text, comment="验收条件检查结果")
    condition_check_date = Column(DateTime, comment="验收条件检查日期")
    condition_checker_id = Column(Integer, ForeignKey("users.id"), comment="检查人ID")

    # 验收单跟踪
    tracking_status = Column(String(20), default="pending", comment="跟踪状态：pending/reminded/received")
    reminder_count = Column(Integer, default=0, comment="催签次数")
    last_reminder_date = Column(DateTime, comment="最后催签日期")
    last_reminder_by = Column(Integer, ForeignKey("users.id"), comment="最后催签人ID")
    received_date = Column(Date, comment="收到原件日期")
    signed_file_id = Column(Integer, comment="签收验收单文件ID")

    # 验收报告跟踪
    report_status = Column(String(20), default="pending", comment="报告状态：pending/generated/signed/archived")
    report_generated_date = Column(DateTime, comment="报告生成日期")
    report_signed_date = Column(DateTime, comment="报告签署日期")
    report_archived_date = Column(DateTime, comment="报告归档日期")

    # 质保期跟踪
    warranty_start_date = Column(Date, comment="质保开始日期")
    warranty_end_date = Column(Date, comment="质保结束日期")
    warranty_status = Column(String(20), default="not_started", comment="质保状态：not_started/active/expiring/expired")
    warranty_expiry_reminded = Column(Boolean, default=False, comment="是否已提醒质保到期")

    # 关联合同
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")
    contract_no = Column(String(50), comment="合同编号")

    # 负责人
    sales_person_id = Column(Integer, ForeignKey("users.id"), comment="业务员ID")
    sales_person_name = Column(String(50), comment="业务员")
    support_person_id = Column(Integer, ForeignKey("users.id"), comment="商务支持ID")

    remark = Column(Text, comment="备注")

    # 关系
    acceptance_order = relationship("AcceptanceOrder", foreign_keys=[acceptance_order_id])
    project = relationship("Project", foreign_keys=[project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    condition_checker = relationship("User", foreign_keys=[condition_checker_id])
    last_reminder_by_user = relationship("User", foreign_keys=[last_reminder_by])
    sales_person = relationship("User", foreign_keys=[sales_person_id])
    support_person = relationship("User", foreign_keys=[support_person_id])
    tracking_records = relationship("AcceptanceTrackingRecord", back_populates="tracking", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_acceptance_order", "acceptance_order_id"),
        Index("idx_project_tracking", "project_id"),
        Index("idx_customer_tracking", "customer_id"),
        Index("idx_tracking_status", "tracking_status"),
        Index("idx_condition_status", "condition_check_status"),
    )

    def __repr__(self):
        return f"<AcceptanceTracking {self.acceptance_order_no}>"


class AcceptanceTrackingRecord(Base, TimestampMixin):
    """验收单跟踪记录明细表（记录每次催签等操作）"""

    __tablename__ = "acceptance_tracking_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_id = Column(Integer, ForeignKey("acceptance_tracking.id"), nullable=False, comment="跟踪记录ID")
    record_type = Column(String(20), nullable=False, comment="记录类型：reminder/condition_check/report_track/warranty_reminder")
    record_content = Column(Text, comment="记录内容")
    record_date = Column(DateTime, nullable=False, comment="记录日期")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作人ID")
    operator_name = Column(String(50), comment="操作人")
    result = Column(String(20), comment="操作结果：success/failed/pending")
    remark = Column(Text, comment="备注")

    # 关系
    tracking = relationship("AcceptanceTracking", back_populates="tracking_records")
    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (
        Index("idx_tracking_record", "tracking_id"),
        Index("idx_record_type", "record_type"),
        Index("idx_record_date", "record_date"),
    )

    def __repr__(self):
        return f"<AcceptanceTrackingRecord {self.id}>"
