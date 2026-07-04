# -*- coding: utf-8 -*-
"""
OTD 风险快照表

每日扫描后落一条快照，用于趋势分析（风险等级/各维度命中/指标随时间的演化）。
照抄 app/models/project/risk_history.py:59 的 ProjectRiskSnapshot 骨架 +
借鉴 app/models/alert.py:395 ProjectHealthSnapshot 的指标列风格。

设计要点：
- snapshot_date 用 Date（非 DateTime），便于同项目同日幂等去重
- 关键维度命中列式冗余（便于全局 group_by 聚合，不用解析 JSON）
- risk_items JSON 整包回填（保留完整 evidence）
- metrics_snapshot JSON 存 7 指标快照值
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from app.models.base import Base, TimestampMixin


class OTDRiskSnapshot(Base, TimestampMixin):
    """OTD 每日风险快照。

    每次 batch_scan(create_snapshot=True) 时，每个扫描到的项目落一条。
    同项目同日幂等：重复扫描跳过（照抄 project_health_tasks.py:65-75 范式）。
    """

    __tablename__ = "otd_risk_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    snapshot_date = Column(Date, nullable=False, comment="快照日期")

    # 综合风险等级（照抄 ProjectRiskSnapshot.risk_level）
    severity = Column(String(20), comment="风险等级 LOW/MEDIUM/HIGH/CRITICAL")

    # 命中维度计数（列式，便于聚合）
    risk_items_count = Column(Integer, default=0, comment="命中维度总数")
    high_items_count = Column(
        Integer, default=0, comment="命中 HIGH/CRITICAL 的维度数"
    )

    # 各维度命中标记（列式冗余，便于全局 group_by 画"每日有多少项目命中某维度"）
    procurement_delay_hit = Column(Boolean, default=False, comment="采购延期命中")
    design_not_frozen_hit = Column(Boolean, default=False, comment="图纸未冻结命中")
    customer_change_hit = Column(Boolean, default=False, comment="客户变更频繁命中")
    budget_overrun_hit = Column(Boolean, default=False, comment="BOM超预算命中")
    field_debug_hit = Column(Boolean, default=False, comment="调试反复命中")
    acceptance_doc_hit = Column(Boolean, default=False, comment="验收资料缺失命中")
    payment_condition_hit = Column(Boolean, default=False, comment="回款条件不齐命中")
    key_milestone_hit = Column(Boolean, default=False, comment="关键节点延期命中")
    progress_lag_hit = Column(Boolean, default=False, comment="进度滞后命中")
    margin_deviation_hit = Column(Boolean, default=False, comment="毛利偏差命中")
    open_items_hit = Column(Boolean, default=False, comment="未关闭事项命中")

    # 完整数据（JSON 整包回填，保留 evidence，照抄 risk_factors）
    risk_items = Column(JSON, comment="完整 risk_items[]（含 dim/label/severity/msg/evidence）")
    metrics_snapshot = Column(JSON, comment="7 指标快照值（OTDMetricsService 产出）")
    suggestion = Column(Text, comment="AI 归因建议")

    __table_args__ = (
        Index("idx_otd_snapshot_project_date", "project_id", "snapshot_date"),
        Index("idx_otd_snapshot_date", "snapshot_date"),
        Index("idx_otd_snapshot_severity", "severity"),
        {"comment": "OTD 每日风险快照表"},
    )

    def __repr__(self):
        return f"<OTDRiskSnapshot project={self.project_id} date={self.snapshot_date} sev={self.severity}>"


__all__ = ["OTDRiskSnapshot"]
