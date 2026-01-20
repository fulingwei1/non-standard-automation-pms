# -*- coding: utf-8 -*-
"""
审批代理人模型

支持员工设置审批代理人（如请假时）
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovalDelegate(Base, TimestampMixin):
    """审批代理人配置"""

    __tablename__ = "approval_delegates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 原审批人
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="原审批人ID")

    # 代理人
    delegate_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="代理人ID")

    # 代理范围
    scope = Column(String(20), default="ALL", comment="""
        代理范围：
        ALL: 全部审批
        TEMPLATE: 指定模板
        CATEGORY: 指定分类
    """)

    # 指定的模板/分类（scope不为ALL时使用）
    template_ids = Column(JSON, comment="指定的模板ID列表")
    categories = Column(JSON, comment="指定的分类列表")

    # 代理时段
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    reason = Column(String(200), comment="代理原因（如出差、请假）")

    # 通知设置
    notify_original = Column(Boolean, default=True, comment="审批完成后是否通知原审批人")
    notify_delegate = Column(Boolean, default=True, comment="有新审批时是否通知代理人")

    # 创建人（可能是本人或管理员）
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    user = relationship("User", foreign_keys=[user_id])
    delegate = relationship("User", foreign_keys=[delegate_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_delegate_user", "user_id"),
        Index("idx_delegate_delegate", "delegate_id"),
        Index("idx_delegate_active", "is_active"),
        Index("idx_delegate_date_range", "start_date", "end_date"),
        Index("idx_delegate_user_active", "user_id", "is_active"),
    )

    def __repr__(self):
        return f"<ApprovalDelegate {self.user_id} -> {self.delegate_id}>"


class ApprovalDelegateLog(Base, TimestampMixin):
    """代理审批日志"""

    __tablename__ = "approval_delegate_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    delegate_config_id = Column(Integer, ForeignKey("approval_delegates.id"), nullable=False, comment="代理配置ID")
    task_id = Column(Integer, ForeignKey("approval_tasks.id"), nullable=False, comment="任务ID")
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False, comment="实例ID")

    # 原审批人和代理人
    original_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="原审批人ID")
    delegate_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="代理人ID")

    # 代理时的操作
    action = Column(String(20), comment="代理审批的操作：APPROVE/REJECT/TRANSFER等")
    action_at = Column(DateTime, comment="操作时间")

    # 原审批人是否已知悉
    original_notified = Column(Boolean, default=False, comment="原审批人是否已通知")
    original_notified_at = Column(DateTime, comment="通知时间")

    __table_args__ = (
        Index("idx_delegate_log_config", "delegate_config_id"),
        Index("idx_delegate_log_task", "task_id"),
        Index("idx_delegate_log_original", "original_user_id"),
    )

    def __repr__(self):
        return f"<ApprovalDelegateLog {self.task_id}>"
