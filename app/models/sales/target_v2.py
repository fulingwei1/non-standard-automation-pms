# -*- coding: utf-8 -*-
"""
销售目标管理 V2 - 详细目标管理模型

支持多维度目标设定、目标分解、目标达成统计等功能
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    ForeignKey,
    Numeric,
    Index,
    CheckConstraint,
    Text,
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class TargetPeriodEnumV2(str, enum.Enum):
    """目标期间枚举"""
    YEAR = "year"  # 年度
    QUARTER = "quarter"  # 季度
    MONTH = "month"  # 月度


class TargetTypeEnumV2(str, enum.Enum):
    """目标类型枚举"""
    COMPANY = "company"  # 公司目标
    TEAM = "team"  # 团队目标
    PERSONAL = "personal"  # 个人目标


class SalesTargetV2(Base, TimestampMixin):
    """
    销售目标表 V2 - 详细的多维度目标管理
    
    支持：
    1. 多维度目标指标（销售额、回款、客户数、线索数等）
    2. 目标分解（公司 → 团队 → 个人）
    3. 实际完成值和完成率计算
    4. 目标达成排名和统计
    """
    __tablename__ = "sales_targets_v2"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="目标ID")
    
    # 目标期间
    target_period = Column(
        Enum(TargetPeriodEnumV2),
        nullable=False,
        comment="目标期间(year/quarter/month)"
    )
    target_year = Column(Integer, nullable=False, comment="目标年份")
    target_month = Column(Integer, nullable=True, comment="目标月份(1-12)")
    target_quarter = Column(Integer, nullable=True, comment="目标季度(1-4)")
    
    # 目标主体
    target_type = Column(
        Enum(TargetTypeEnumV2),
        nullable=False,
        comment="目标类型(company/team/personal)"
    )
    team_id = Column(
        Integer,
        ForeignKey("sales_teams.id", ondelete="CASCADE"),
        nullable=True,
        comment="团队ID"
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="用户ID"
    )
    
    # 目标指标
    sales_target = Column(
        Numeric(15, 2),
        default=0,
        nullable=False,
        comment="销售额目标"
    )
    payment_target = Column(
        Numeric(15, 2),
        default=0,
        nullable=False,
        comment="回款目标"
    )
    new_customer_target = Column(
        Integer,
        default=0,
        nullable=False,
        comment="新客户数目标"
    )
    lead_target = Column(
        Integer,
        default=0,
        nullable=False,
        comment="线索数目标"
    )
    opportunity_target = Column(
        Integer,
        default=0,
        nullable=False,
        comment="商机数目标"
    )
    deal_target = Column(
        Integer,
        default=0,
        nullable=False,
        comment="签单数目标"
    )
    
    # 实际完成值
    actual_sales = Column(
        Numeric(15, 2),
        default=0,
        nullable=False,
        comment="实际销售额"
    )
    actual_payment = Column(
        Numeric(15, 2),
        default=0,
        nullable=False,
        comment="实际回款"
    )
    actual_new_customers = Column(
        Integer,
        default=0,
        nullable=False,
        comment="实际新客户数"
    )
    actual_leads = Column(
        Integer,
        default=0,
        nullable=False,
        comment="实际线索数"
    )
    actual_opportunities = Column(
        Integer,
        default=0,
        nullable=False,
        comment="实际商机数"
    )
    actual_deals = Column(
        Integer,
        default=0,
        nullable=False,
        comment="实际签单数"
    )
    
    # 完成率
    completion_rate = Column(
        Numeric(5, 2),
        default=0,
        comment="完成率(%)"
    )
    
    # 目标分解关系
    parent_target_id = Column(
        Integer,
        ForeignKey("sales_targets_v2.id", ondelete="CASCADE"),
        nullable=True,
        comment="上级目标ID（用于目标分解）"
    )
    
    # 备注说明
    description = Column(Text, comment="目标描述")
    remark = Column(Text, comment="备注")
    
    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    team = relationship("SalesTeam", foreign_keys=[team_id])
    user = relationship("User", foreign_keys=[user_id])
    parent_target = relationship(
        "SalesTargetV2",
        remote_side=[id],
        backref="sub_targets",
        foreign_keys=[parent_target_id]
    )
    creator = relationship("User", foreign_keys=[created_by])
    
    # 索引和约束
    __table_args__ = (
        Index("idx_sales_target_v2_team", "team_id"),
        Index("idx_sales_target_v2_user", "user_id"),
        Index("idx_sales_target_v2_period", "target_year", "target_month"),
        Index("idx_sales_target_v2_parent", "parent_target_id"),
        Index("idx_sales_target_v2_type", "target_type"),
        # 约束：company 目标不需要 team_id 和 user_id，team 目标需要 team_id，personal 目标需要 user_id
        CheckConstraint(
            """
            (target_type = 'company' AND team_id IS NULL AND user_id IS NULL) OR
            (target_type = 'team' AND team_id IS NOT NULL AND user_id IS NULL) OR
            (target_type = 'personal' AND user_id IS NOT NULL)
            """,
            name="chk_target_type_v2"
        ),
    )

    def __repr__(self):
        return f"<SalesTargetV2(id={self.id}, type={self.target_type}, period={self.target_period})>"


class TargetBreakdownLog(Base, TimestampMixin):
    """
    目标分解日志表
    
    记录目标分解的历史和详情
    """
    __tablename__ = "target_breakdown_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    parent_target_id = Column(
        Integer,
        ForeignKey("sales_targets_v2.id", ondelete="CASCADE"),
        nullable=False,
        comment="上级目标ID"
    )
    breakdown_type = Column(
        String(20),
        nullable=False,
        comment="分解类型：AUTO(自动分解)/MANUAL(手动分解)"
    )
    breakdown_method = Column(
        String(50),
        comment="分解方法：EQUAL(平均分配)/RATIO(按比例)/CUSTOM(自定义)"
    )
    breakdown_details = Column(
        Text,
        comment="分解详情(JSON格式)"
    )
    created_by = Column(Integer, ForeignKey("users.id"), comment="分解操作人ID")
    
    # 关系
    parent_target = relationship("SalesTargetV2", foreign_keys=[parent_target_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    # 索引
    __table_args__ = (
        Index("idx_breakdown_log_parent", "parent_target_id"),
        Index("idx_breakdown_log_created", "created_at"),
    )

    def __repr__(self):
        return f"<TargetBreakdownLog(id={self.id}, parent={self.parent_target_id})>"
