# -*- coding: utf-8 -*-
"""
项目毛利率快照表

每日落一条，用于毛利率趋势分析（全局平均毛利率演化、各健康度项目数变化）。
照抄 app/models/otd_risk_snapshot.py 的骨架，但用 Numeric 列存毛利率数值
（OTDRiskSnapshot.margin_deviation_hit 是布尔命中，画不出连续毛利率折线）。

数值列式存储，便于 func.avg 全局聚合（照抄 trend_service 的列式聚合范式）。
"""

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)

from app.models.base import Base, TimestampMixin


class ProjectMarginSnapshot(Base, TimestampMixin):
    """项目毛利率每日快照。

    每天 daily_margin_snapshot 任务为活跃项目落一条。
    同项目同日幂等去重（照抄 project_health_tasks.py:63-75）。
    """

    __tablename__ = "project_margin_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    snapshot_date = Column(Date, nullable=False, comment="快照日期")

    # 毛利率数值（核心，来自 ProfitAnalysisService.get_margin_analysis）
    current_margin_rate = Column(Numeric(5, 2), comment="当前毛利率(%)")
    forecast_margin_rate = Column(Numeric(5, 2), comment="预测毛利率(%)")
    margin_gap = Column(Numeric(5, 2), comment="毛利率偏差(当前-目标,负值=低于目标)")
    target_margin_rate = Column(Numeric(5, 2), comment="目标毛利率(%)")

    # 健康度（便于全局按 health 分桶统计）
    health = Column(String(20), comment="健康度 healthy/warning/critical")

    # 金额（便于下钻）
    contract_amount = Column(Numeric(14, 2), comment="合同金额")
    actual_cost = Column(Numeric(14, 2), comment="实际成本")
    budget_amount = Column(Numeric(14, 2), comment="预算金额")

    __table_args__ = (
        Index("idx_margin_snapshot_project_date", "project_id", "snapshot_date"),
        Index("idx_margin_snapshot_date", "snapshot_date"),
        Index("idx_margin_snapshot_health", "health"),
        {"comment": "项目毛利率每日快照表"},
    )

    def __repr__(self):
        return (
            f"<ProjectMarginSnapshot project={self.project_id} "
            f"date={self.snapshot_date} rate={self.current_margin_rate}>"
        )


__all__ = ["ProjectMarginSnapshot"]
