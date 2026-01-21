# -*- coding: utf-8 -*-
"""
销售团队管理模型

支持一人多队的灵活团队结构，用于销售目标管理、团队排名和业绩PK。
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class SalesTeam(Base, TimestampMixin):
    """
    销售团队表

    团队是用于销售目标管理的固定人员分组，与项目组不同：
    - 项目组：临时的、项目驱动的
    - 销售团队：长期的、业绩驱动的
    """
    __tablename__ = "sales_teams"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    team_code = Column(String(20), unique=True, nullable=False, comment="团队编码")
    team_name = Column(String(100), nullable=False, comment="团队名称")
    description = Column(Text, comment="团队描述")

    # 团队类型：按区域、按行业、按客户规模等
    team_type = Column(
        String(20),
        default="REGION",
        comment="团队类型：REGION(区域)/INDUSTRY(行业)/SCALE(客户规模)/OTHER(其他)"
    )

    # 所属部门（团队通常隶属于某个部门）
    department_id = Column(Integer, ForeignKey("departments.id"), comment="所属部门ID")

    # 团队负责人
    leader_id = Column(Integer, ForeignKey("users.id"), comment="团队负责人ID")

    # 上级团队（支持团队层级，如：销售一部 > 华东组）
    parent_team_id = Column(Integer, ForeignKey("sales_teams.id"), comment="上级团队ID")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 排序
    sort_order = Column(Integer, default=0, comment="排序序号")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    department = relationship("Department", foreign_keys=[department_id])
    leader = relationship("User", foreign_keys=[leader_id])
    creator = relationship("User", foreign_keys=[created_by])
    parent_team = relationship("SalesTeam", remote_side=[id], backref="sub_teams")
    members = relationship("SalesTeamMember", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sales_team_code", "team_code"),
        Index("idx_sales_team_type", "team_type"),
        Index("idx_sales_team_department", "department_id"),
        Index("idx_sales_team_leader", "leader_id"),
        Index("idx_sales_team_parent", "parent_team_id"),
        Index("idx_sales_team_active", "is_active"),
    )

    def __repr__(self):
        return f"<SalesTeam {self.team_code}: {self.team_name}>"


class SalesTeamMember(Base, TimestampMixin):
    """
    销售团队成员表（多对多关系）

    支持一人多队：一个销售可以同时属于多个团队
    例如：张三同时属于"华东组"和"大客户组"
    """
    __tablename__ = "sales_team_members"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    team_id = Column(Integer, ForeignKey("sales_teams.id", ondelete="CASCADE"), nullable=False, comment="团队ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")

    # 成员角色
    role = Column(
        String(20),
        default="MEMBER",
        comment="成员角色：LEADER(负责人)/DEPUTY(副负责人)/MEMBER(成员)"
    )

    # 加入时间
    joined_at = Column(DateTime, default=datetime.now, comment="加入时间")

    # 是否为主团队（用于业绩归属统计，一个人可以有一个主团队）
    is_primary = Column(Boolean, default=False, comment="是否为主团队")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否有效")

    # 备注
    remark = Column(String(200), comment="备注")

    # 关系
    team = relationship("SalesTeam", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        # 同一团队中，同一用户只能有一条记录
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
        Index("idx_team_member_team", "team_id"),
        Index("idx_team_member_user", "user_id"),
        Index("idx_team_member_role", "role"),
        Index("idx_team_member_primary", "user_id", "is_primary"),
        Index("idx_team_member_active", "is_active"),
    )

    def __repr__(self):
        return f"<SalesTeamMember team={self.team_id} user={self.user_id}>"


class TeamPerformanceSnapshot(Base, TimestampMixin):
    """
    团队业绩快照表

    定期记录团队业绩数据，用于排名和趋势分析。
    """
    __tablename__ = "team_performance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    team_id = Column(Integer, ForeignKey("sales_teams.id", ondelete="CASCADE"), nullable=False, comment="团队ID")

    # 快照周期
    period_type = Column(String(20), nullable=False, comment="周期类型：DAILY/WEEKLY/MONTHLY/QUARTERLY")
    period_value = Column(String(20), nullable=False, comment="周期标识：2026-01-20/2026-W03/2026-01/2026-Q1")
    snapshot_date = Column(DateTime, nullable=False, comment="快照时间")

    # 业绩指标
    lead_count = Column(Integer, default=0, comment="线索数量")
    opportunity_count = Column(Integer, default=0, comment="商机数量")
    opportunity_amount = Column(Numeric(14, 2), default=0, comment="商机金额")
    contract_count = Column(Integer, default=0, comment="签约数量")
    contract_amount = Column(Numeric(14, 2), default=0, comment="签约金额")
    collection_amount = Column(Numeric(14, 2), default=0, comment="回款金额")

    # 目标完成情况
    target_amount = Column(Numeric(14, 2), default=0, comment="目标金额")
    completion_rate = Column(Numeric(5, 2), default=0, comment="完成率(%)")

    # 排名
    rank_in_department = Column(Integer, comment="部门内排名")
    rank_overall = Column(Integer, comment="全公司排名")

    # 团队规模（快照时的成员数）
    member_count = Column(Integer, default=0, comment="成员数量")

    # 关系
    team = relationship("SalesTeam")

    __table_args__ = (
        # 同一团队同一周期只有一条记录
        UniqueConstraint("team_id", "period_type", "period_value", name="uq_team_performance_period"),
        Index("idx_team_perf_team", "team_id"),
        Index("idx_team_perf_period", "period_type", "period_value"),
        Index("idx_team_perf_date", "snapshot_date"),
        Index("idx_team_perf_rank", "period_type", "period_value", "rank_overall"),
    )

    def __repr__(self):
        return f"<TeamPerformanceSnapshot team={self.team_id} period={self.period_value}>"


class TeamPKRecord(Base, TimestampMixin):
    """
    团队PK记录表

    记录团队间的业绩PK比赛。
    """
    __tablename__ = "team_pk_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    pk_name = Column(String(100), nullable=False, comment="PK名称")
    pk_type = Column(String(20), nullable=False, comment="PK类型：CONTRACT_AMOUNT/COLLECTION_AMOUNT/LEAD_COUNT")

    # 参与团队（JSON数组存储团队ID列表）
    team_ids = Column(Text, nullable=False, comment="参与团队ID列表(JSON)")

    # PK周期
    start_date = Column(DateTime, nullable=False, comment="开始时间")
    end_date = Column(DateTime, nullable=False, comment="结束时间")

    # 目标值（可选，如果设定则比较目标完成率）
    target_value = Column(Numeric(14, 2), comment="PK目标值")

    # 状态
    status = Column(String(20), default="ONGOING", comment="状态：PENDING/ONGOING/COMPLETED/CANCELLED")

    # 结果
    winner_team_id = Column(Integer, ForeignKey("sales_teams.id"), comment="获胜团队ID")
    result_summary = Column(Text, comment="结果汇总(JSON)")

    # 奖励说明
    reward_description = Column(Text, comment="奖励说明")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    winner_team = relationship("SalesTeam", foreign_keys=[winner_team_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_team_pk_status", "status"),
        Index("idx_team_pk_date", "start_date", "end_date"),
        Index("idx_team_pk_winner", "winner_team_id"),
    )

    def __repr__(self):
        return f"<TeamPKRecord {self.pk_name}>"
