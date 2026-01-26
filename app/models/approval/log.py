# -*- coding: utf-8 -*-
"""
审批操作日志模型

完整审计追踪所有审批操作
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovalActionLog(Base, TimestampMixin):
    """审批操作日志 - 完整审计追踪"""

    __tablename__ = "approval_action_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False, comment="审批实例ID")
    task_id = Column(Integer, ForeignKey("approval_tasks.id"), comment="关联任务ID（可为空）")
    node_id = Column(Integer, ForeignKey("approval_node_definitions.id"), comment="关联节点ID")

    # 操作人
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作人ID")
    operator_name = Column(String(50), comment="操作人姓名（冗余）")

    # 操作类型
    action = Column(String(30), nullable=False, comment="""
        操作类型：
        SUBMIT: 提交审批
        SAVE_DRAFT: 保存草稿
        APPROVE: 审批通过
        REJECT: 审批驳回
        RETURN: 退回
        TRANSFER: 转审
        DELEGATE: 委托
        ADD_APPROVER_BEFORE: 前加签
        ADD_APPROVER_AFTER: 后加签
        ADD_CC: 加抄送
        WITHDRAW: 撤回
        CANCEL: 取消
        TERMINATE: 终止
        REMIND: 催办
        COMMENT: 评论
        READ_CC: 阅读抄送
        TIMEOUT: 超时处理
    """)

    # 操作详情
    action_detail = Column(JSON, comment="""
        操作详情，示例：
        - TRANSFER: {"from_user_id": 1, "to_user_id": 2}
        - ADD_APPROVER: {"approver_ids": [3, 4], "position": "AFTER"}
        - RETURN: {"return_to_node_id": 2}
        - TIMEOUT: {"timeout_action": "AUTO_PASS"}
    """)

    # 操作说明
    comment = Column(Text, comment="操作备注/审批意见")
    attachments = Column(JSON, comment="附件列表")

    # 操作前后状态
    before_status = Column(String(20), comment="操作前状态")
    after_status = Column(String(20), comment="操作后状态")
    before_node_id = Column(Integer, comment="操作前节点ID")
    after_node_id = Column(Integer, comment="操作后节点ID")

    # 操作时间
    action_at = Column(DateTime, nullable=False, default=datetime.now, comment="操作时间")

    # IP和设备信息（审计用）
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="User-Agent")

    # 关系
    instance = relationship("ApprovalInstance", back_populates="action_logs")
    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (
        Index("idx_action_log_instance", "instance_id"),
        Index("idx_action_log_task", "task_id"),
        Index("idx_action_log_operator", "operator_id"),
        Index("idx_action_log_action", "action"),
        Index("idx_action_log_time", "action_at"),
        Index("idx_action_log_instance_time", "instance_id", "action_at"),
    )

    def __repr__(self):
        return f"<ApprovalActionLog {self.action} by {self.operator_id}>"


class ApprovalComment(Base, TimestampMixin):
    """审批评论 - 支持审批过程中的讨论"""

    __tablename__ = "approval_comments"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False, comment="审批实例ID")

    # 评论人
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="评论人ID")
    user_name = Column(String(50), comment="评论人姓名（冗余）")

    # 评论内容
    content = Column(Text, nullable=False, comment="评论内容")
    attachments = Column(JSON, comment="附件列表")

    # 回复关联
    parent_id = Column(Integer, ForeignKey("approval_comments.id"), comment="父评论ID（回复时）")
    reply_to_user_id = Column(Integer, ForeignKey("users.id"), comment="回复的用户ID")

    # @提及
    mentioned_user_ids = Column(JSON, comment="@提及的用户ID列表")

    # 状态
    is_deleted = Column(Boolean, default=False, comment="是否已删除")
    deleted_at = Column(DateTime, comment="删除时间")
    deleted_by = Column(Integer, ForeignKey("users.id"), comment="删除人ID")

    # 关系
    user = relationship("User", foreign_keys=[user_id])
    reply_to_user = relationship("User", foreign_keys=[reply_to_user_id])
    parent = relationship("ApprovalComment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("idx_comment_instance", "instance_id"),
        Index("idx_comment_user", "user_id"),
        Index("idx_comment_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<ApprovalComment {self.id} by {self.user_id}>"
