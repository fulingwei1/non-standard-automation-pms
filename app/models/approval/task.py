# -*- coding: utf-8 -*-
"""
审批任务和抄送模型

记录分配给具体审批人的任务和抄送记录
"""


from sqlalchemy import (
    JSON,
    Boolean,
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


class ApprovalTask(Base, TimestampMixin):
    """审批任务 - 分配给具体审批人的任务"""

    __tablename__ = "approval_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False, comment="审批实例ID")
    node_id = Column(Integer, ForeignKey("approval_node_definitions.id"), nullable=False, comment="节点定义ID")

    # 任务类型
    task_type = Column(String(20), default="APPROVAL", comment="""
        任务类型：
        APPROVAL: 审批任务
        CC: 抄送任务（只读）
        EVALUATION: 评估任务（ECN等）
    """)

    # 任务序号（同一节点可能有多个任务，如会签）
    task_order = Column(Integer, default=1, comment="任务序号")

    # 审批人信息
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="被分配人ID")
    assignee_name = Column(String(50), comment="被分配人姓名（冗余）")
    assignee_dept_id = Column(Integer, ForeignKey("departments.id"), comment="被分配人部门ID")

    # 分配来源
    assignee_type = Column(String(20), default="NORMAL", comment="""
        分配类型：
        NORMAL: 正常分配
        DELEGATED: 代理分配
        TRANSFERRED: 转审分配
        ADDED_BEFORE: 前加签
        ADDED_AFTER: 后加签
    """)
    original_assignee_id = Column(Integer, ForeignKey("users.id"), comment="原审批人ID（委托/转审时）")

    # 任务状态
    status = Column(String(20), default="PENDING", comment="""
        任务状态：
        PENDING: 待处理
        COMPLETED: 已完成
        TRANSFERRED: 已转审
        DELEGATED: 已委托
        SKIPPED: 已跳过（条件跳过）
        EXPIRED: 已超时
        CANCELLED: 已取消（实例撤销时）
    """)

    # 审批结果
    action = Column(String(20), comment="""
        审批操作：
        APPROVE: 通过
        REJECT: 驳回
        RETURN: 退回（退回到指定节点）
    """)
    comment = Column(Text, comment="审批意见")
    attachments = Column(JSON, comment="附件列表")

    # 评估内容（用于ECN等需要填写评估的场景）
    eval_data = Column(JSON, comment="""
        评估数据，示例：
        {
            "impact_analysis": "影响生产排期",
            "cost_estimate": 5000,
            "schedule_estimate": 3,
            "risk_assessment": "中"
        }
    """)

    # 退回目标（当action=RETURN时）
    return_to_node_id = Column(Integer, ForeignKey("approval_node_definitions.id"), comment="退回到的节点ID")

    # 时间记录
    due_at = Column(DateTime, comment="截止时间")
    reminded_at = Column(DateTime, comment="最后提醒时间")
    remind_count = Column(Integer, default=0, comment="提醒次数")
    completed_at = Column(DateTime, comment="完成时间")

    # 会签相关
    is_countersign = Column(Boolean, default=False, comment="是否为会签任务")
    countersign_weight = Column(Integer, default=1, comment="会签权重（用于加权表决）")

    # 关系
    instance = relationship("ApprovalInstance", back_populates="tasks")
    node = relationship("ApprovalNodeDefinition", foreign_keys=[node_id], back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    assignee_dept = relationship("Department", foreign_keys=[assignee_dept_id])
    original_assignee = relationship("User", foreign_keys=[original_assignee_id])
    return_to_node = relationship("ApprovalNodeDefinition", foreign_keys=[return_to_node_id])

    __table_args__ = (
        Index("idx_approval_task_instance", "instance_id"),
        Index("idx_approval_task_node", "node_id"),
        Index("idx_approval_task_assignee", "assignee_id"),
        Index("idx_approval_task_status", "status"),
        Index("idx_approval_task_pending", "assignee_id", "status"),  # 待我审批查询优化
        Index("idx_approval_task_due", "due_at"),
        Index("idx_approval_task_type", "task_type"),
    )

    def __repr__(self):
        return f"<ApprovalTask {self.id} ({self.status})>"


class ApprovalCarbonCopy(Base, TimestampMixin):
    """抄送记录"""

    __tablename__ = "approval_carbon_copies"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False, comment="审批实例ID")
    node_id = Column(Integer, comment="触发抄送的节点ID（可为空，表示发起时抄送）")

    # 抄送人
    cc_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="抄送人ID")
    cc_user_name = Column(String(50), comment="抄送人姓名（冗余）")

    # 抄送来源
    cc_source = Column(String(20), default="FLOW", comment="""
        抄送来源：
        FLOW: 流程配置抄送
        INITIATOR: 发起人手动抄送
        APPROVER: 审批人手动加抄送
    """)
    added_by = Column(Integer, ForeignKey("users.id"), comment="添加人ID（手动抄送时）")

    # 阅读状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime, comment="阅读时间")

    # 关系
    instance = relationship("ApprovalInstance", back_populates="cc_records")
    cc_user = relationship("User", foreign_keys=[cc_user_id])
    adder = relationship("User", foreign_keys=[added_by])

    __table_args__ = (
        Index("idx_approval_cc_instance", "instance_id"),
        Index("idx_approval_cc_user", "cc_user_id"),
        Index("idx_approval_cc_unread", "cc_user_id", "is_read"),  # 未读抄送查询优化
    )

    def __repr__(self):
        return f"<ApprovalCarbonCopy {self.instance_id} -> {self.cc_user_id}>"


class ApprovalCountersignResult(Base, TimestampMixin):
    """会签结果统计表"""

    __tablename__ = "approval_countersign_results"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False, comment="审批实例ID")
    node_id = Column(Integer, ForeignKey("approval_node_definitions.id"), nullable=False, comment="节点ID")

    # 统计信息
    total_count = Column(Integer, default=0, comment="总任务数")
    approved_count = Column(Integer, default=0, comment="通过数")
    rejected_count = Column(Integer, default=0, comment="驳回数")
    pending_count = Column(Integer, default=0, comment="待处理数")

    # 最终结果
    final_result = Column(String(20), comment="""
        最终结果：
        PENDING: 进行中
        PASSED: 通过
        FAILED: 未通过
    """)
    result_reason = Column(Text, comment="结果说明")

    # 汇总数据
    summary_data = Column(JSON, comment="""
        汇总数据，示例（ECN评估）：
        {
            "total_cost": 15000,
            "total_schedule_days": 10,
            "max_risk": "高",
            "evaluations": [
                {"dept": "工程部", "result": "通过", "cost": 5000},
                {"dept": "采购部", "result": "通过", "cost": 10000}
            ]
        }
    """)

    __table_args__ = (
        Index("idx_countersign_instance", "instance_id"),
        Index("idx_countersign_node", "node_id"),
        Index("idx_countersign_instance_node", "instance_id", "node_id", unique=True),
    )

    def __repr__(self):
        return f"<ApprovalCountersignResult {self.instance_id}-{self.node_id}>"
