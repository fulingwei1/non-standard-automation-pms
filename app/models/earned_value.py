# -*- coding: utf-8 -*-
"""
挣值管理（EVM - Earned Value Management）数据模型
符合PMBOK标准的项目绩效测量体系
"""

from datetime import date
from decimal import Decimal

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

from app.models.base import Base, TimestampMixin


class EarnedValueData(Base, TimestampMixin):
    """
    挣值数据表 - 记录项目在特定时间点的EVM基础数据
    
    符合PMBOK标准，包含三个核心指标：
    - PV (Planned Value): 计划价值 - 截至某时间点应该完成的工作的预算成本
    - EV (Earned Value): 挣得价值 - 截至某时间点实际完成工作的预算成本  
    - AC (Actual Cost): 实际成本 - 截至某时间点实际发生的成本
    
    其他关键字段：
    - BAC (Budget at Completion): 完工预算 - 项目总预算
    - period_type: 数据周期类型（WEEK/MONTH/QUARTER）
    """

    __tablename__ = "earned_value_data"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 项目关联
    project_id = Column(
        Integer, 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="项目ID"
    )
    project_code = Column(String(50), comment="项目编号（冗余，便于查询）")
    
    # 数据周期
    period_type = Column(
        String(20), 
        nullable=False, 
        default="MONTH",
        comment="周期类型：WEEK（周）/MONTH（月）/QUARTER（季度）"
    )
    period_date = Column(
        Date, 
        nullable=False, 
        comment="周期截止日期（周末日期/月末日期/季末日期）"
    )
    period_label = Column(
        String(50), 
        comment="周期标签（如：2026-W07, 2026-02, 2026-Q1）"
    )
    
    # EVM核心三要素（使用Decimal避免浮点误差）
    planned_value = Column(
        Numeric(18, 4), 
        nullable=False, 
        default=Decimal('0.0000'),
        comment="PV - 计划价值（Planned Value）"
    )
    earned_value = Column(
        Numeric(18, 4), 
        nullable=False, 
        default=Decimal('0.0000'),
        comment="EV - 挣得价值（Earned Value）"
    )
    actual_cost = Column(
        Numeric(18, 4), 
        nullable=False, 
        default=Decimal('0.0000'),
        comment="AC - 实际成本（Actual Cost）"
    )
    
    # 项目基准
    budget_at_completion = Column(
        Numeric(18, 4), 
        nullable=False,
        comment="BAC - 完工预算（Budget at Completion）"
    )
    
    # 货币
    currency = Column(
        String(10), 
        default="CNY", 
        nullable=False,
        comment="币种（CNY/USD/EUR等）"
    )
    
    # 计算结果缓存（提升查询性能，避免重复计算）
    # 偏差指标
    schedule_variance = Column(
        Numeric(18, 4),
        comment="SV - 进度偏差（Schedule Variance = EV - PV）"
    )
    cost_variance = Column(
        Numeric(18, 4),
        comment="CV - 成本偏差（Cost Variance = EV - AC）"
    )
    
    # 绩效指数
    schedule_performance_index = Column(
        Numeric(10, 6),
        comment="SPI - 进度绩效指数（Schedule Performance Index = EV / PV）"
    )
    cost_performance_index = Column(
        Numeric(10, 6),
        comment="CPI - 成本绩效指数（Cost Performance Index = EV / AC）"
    )
    
    # 预测指标
    estimate_at_completion = Column(
        Numeric(18, 4),
        comment="EAC - 完工估算（Estimate at Completion）"
    )
    estimate_to_complete = Column(
        Numeric(18, 4),
        comment="ETC - 完工尚需估算（Estimate to Complete = EAC - AC）"
    )
    variance_at_completion = Column(
        Numeric(18, 4),
        comment="VAC - 完工偏差（Variance at Completion = BAC - EAC）"
    )
    to_complete_performance_index = Column(
        Numeric(10, 6),
        comment="TCPI - 完工尚需绩效指数（To-Complete Performance Index）"
    )
    
    # 完成百分比
    planned_percent_complete = Column(
        Numeric(5, 2),
        comment="计划完成百分比（PV / BAC * 100）"
    )
    actual_percent_complete = Column(
        Numeric(5, 2),
        comment="实际完成百分比（EV / BAC * 100）"
    )
    
    # 数据来源与状态
    data_source = Column(
        String(50),
        default="MANUAL",
        comment="数据来源：MANUAL（手工录入）/SYSTEM（系统计算）/IMPORT（导入）"
    )
    is_baseline = Column(
        Boolean,
        default=False,
        comment="是否基准数据（项目启动时的基准）"
    )
    is_forecast = Column(
        Boolean,
        default=False,
        comment="是否预测数据（未来的预测值）"
    )
    is_verified = Column(
        Boolean,
        default=False,
        comment="是否已核实（PMO或财务核实）"
    )
    
    # 审核信息
    verified_by = Column(Integer, ForeignKey("users.id"), comment="核实人ID")
    verified_at = Column(Date, comment="核实时间")
    
    # 备注
    notes = Column(Text, comment="备注说明")
    calculation_notes = Column(Text, comment="计算说明（记录特殊计算逻辑）")
    
    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    project = relationship("Project", back_populates="earned_value_data")
    creator = relationship("User", foreign_keys=[created_by])
    verifier = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        # 唯一约束：同一项目+同一周期类型+同一日期只能有一条记录
        UniqueConstraint(
            "project_id", 
            "period_type", 
            "period_date",
            name="uq_evm_project_period"
        ),
        # 索引优化查询性能
        Index("idx_evm_project", "project_id"),
        Index("idx_evm_period_type", "period_type"),
        Index("idx_evm_period_date", "period_date"),
        Index("idx_evm_project_date", "project_id", "period_date"),
        Index("idx_evm_verified", "is_verified"),
        Index("idx_evm_baseline", "is_baseline"),
        {"comment": "挣值管理数据表（符合PMBOK标准）"}
    )

    def __repr__(self):
        return f"<EarnedValueData project={self.project_code} period={self.period_label}>"


class EarnedValueSnapshot(Base, TimestampMixin):
    """
    EVM快照表 - 记录定期的EVM分析快照
    
    用于：
    - 月度/季度EVM报告存档
    - 历史对比分析
    - 趋势分析
    """

    __tablename__ = "earned_value_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 快照信息
    snapshot_code = Column(
        String(100), 
        unique=True, 
        nullable=False,
        comment="快照编码（如：PRJ001-2026-02-EVM）"
    )
    snapshot_name = Column(String(200), comment="快照名称")
    snapshot_date = Column(Date, nullable=False, comment="快照日期")
    snapshot_type = Column(
        String(20),
        default="MONTHLY",
        comment="快照类型：WEEKLY/MONTHLY/QUARTERLY/MILESTONE"
    )
    
    # 项目关联
    project_id = Column(
        Integer, 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False,
        comment="项目ID"
    )
    project_code = Column(String(50), comment="项目编号（冗余）")
    
    # 关联EVM数据
    evm_data_id = Column(
        Integer,
        ForeignKey("earned_value_data.id", ondelete="SET NULL"),
        comment="关联的EVM数据ID"
    )
    
    # 快照数据（JSON格式存储完整的EVM分析结果）
    snapshot_data = Column(
        Text,
        comment="快照数据（JSON格式，包含所有EVM指标和分析结果）"
    )
    
    # 分析结论
    performance_status = Column(
        String(20),
        comment="绩效状态：EXCELLENT/GOOD/WARNING/CRITICAL"
    )
    trend_direction = Column(
        String(20),
        comment="趋势方向：IMPROVING/STABLE/DECLINING"
    )
    risk_level = Column(
        String(20),
        comment="风险等级：LOW/MEDIUM/HIGH/CRITICAL"
    )
    
    # 关键发现和建议
    key_findings = Column(Text, comment="关键发现")
    recommendations = Column(Text, comment="改进建议")
    
    # 创建和审核
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(Date, comment="审核时间")
    
    # 关系
    project = relationship("Project")
    evm_data = relationship("EarnedValueData")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_evm_snapshot_project", "project_id"),
        Index("idx_evm_snapshot_date", "snapshot_date"),
        Index("idx_evm_snapshot_type", "snapshot_type"),
        Index("idx_evm_snapshot_status", "performance_status"),
        {"comment": "EVM分析快照表"}
    )

    def __repr__(self):
        return f"<EarnedValueSnapshot {self.snapshot_code}>"
