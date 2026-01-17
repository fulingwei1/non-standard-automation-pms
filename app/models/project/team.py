# -*- coding: utf-8 -*-
"""
项目团队模型 - ProjectMember, ProjectMemberContribution
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ProjectMember(Base, TimestampMixin):
    """项目成员表"""

    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role_code = Column(String(50), nullable=False, comment="角色编码（兼容旧版）")

    # 新增：角色类型关联（支持灵活配置）
    role_type_id = Column(
        Integer,
        ForeignKey("project_role_types.id"),
        nullable=True,
        comment="角色类型ID（关联角色字典）"
    )
    is_lead = Column(Boolean, default=False, comment="是否为该角色的负责人")

    # 新增：设备级成员分配
    machine_id = Column(
        Integer,
        ForeignKey("machines.id"),
        nullable=True,
        comment="设备ID（设备级成员分配）"
    )

    # 新增：团队层级关系
    lead_member_id = Column(
        Integer,
        ForeignKey("project_members.id"),
        nullable=True,
        comment="所属负责人ID（团队成员指向其负责人）"
    )

    # 分配信息
    allocation_pct = Column(Numeric(5, 2), default=100, comment="分配比例")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")

    # 矩阵式管理字段
    commitment_level = Column(String(20), comment="投入级别：FULL/PARTIAL/ADVISORY")
    reporting_to_pm = Column(Boolean, default=True, comment="是否向项目经理汇报")
    dept_manager_notified = Column(Boolean, default=False, comment="部门经理是否已通知")

    # 状态
    is_active = Column(Boolean, default=True)

    # 备注
    remark = Column(Text, comment="备注")

    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    role_type = relationship("ProjectRoleType", foreign_keys=[role_type_id])
    machine = relationship("Machine", foreign_keys=[machine_id])
    lead = relationship("ProjectMember", remote_side=[id], foreign_keys=[lead_member_id])
    team_members = relationship(
        "ProjectMember",
        back_populates="lead",
        foreign_keys=[lead_member_id]
    )

    __table_args__ = (
        Index("idx_project_members_project", "project_id"),
        Index("idx_project_members_user", "user_id"),
        Index("idx_project_members_role_type", "role_type_id"),
        Index("idx_project_members_is_lead", "is_lead"),
        Index("idx_project_members_machine", "machine_id"),
        Index("idx_project_members_lead", "lead_member_id"),
        Index("idx_project_members_project_user_role", "project_id", "user_id", "role_code", unique=True),
    )


class ProjectMemberContribution(Base, TimestampMixin):
    """项目成员贡献度表"""
    __tablename__ = "project_member_contributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    period = Column(String(7), nullable=False, comment="统计周期 YYYY-MM")

    # 工作量指标
    task_count = Column(Integer, default=0, comment="完成任务数")
    task_hours = Column(Numeric(10, 2), default=0, comment="任务工时")
    actual_hours = Column(Numeric(10, 2), default=0, comment="实际投入工时")

    # 质量指标
    deliverable_count = Column(Integer, default=0, comment="交付物数量")
    issue_count = Column(Integer, default=0, comment="问题数")
    issue_resolved = Column(Integer, default=0, comment="解决问题数")

    # 贡献度评分
    contribution_score = Column(Numeric(5, 2), comment="贡献度评分")
    pm_rating = Column(Integer, comment="项目经理评分 1-5")

    # 奖金关联
    bonus_amount = Column(Numeric(14, 2), default=0, comment="项目奖金金额")

    # 关系
    project = relationship("Project")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_project_member_contrib_project", "project_id"),
        Index("idx_project_member_contrib_user", "user_id"),
        Index("idx_project_member_contrib_period", "period"),
        Index("idx_project_member_contrib_unique", "project_id", "user_id", "period", unique=True),
    )

    def __repr__(self):
        return f"<ProjectMemberContribution {self.project_id}-{self.user_id}-{self.period}>"
