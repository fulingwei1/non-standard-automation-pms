# -*- coding: utf-8 -*-
"""
OTD 阈值配置表

照抄 app/models/sales/margin_alert.py:47 的 MarginAlertConfig 范式：
- code 唯一标识 + is_default 单套默认配置 + priority 预留
- Numeric 列存数值阈值，JSON 列存状态集合
- 通过 Base.metadata.create_all 自动建表（无需手写 migration）

运行时由 threshold_service.get_active_config() 加载：
- DB 有 is_default=True 且 is_active=True 的行 → 用它
- DB 无 → 返回内存默认实例（本文件 DEFAULT_XXX 常量）
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)

from app.models.base import Base, TimestampMixin


# ================================================================
# 代码层默认值（DB 无配置行时 fallback 用，与原硬编码阈值一致）
# ================================================================

DEFAULT_SCAN_LIMIT = 200
DEFAULT_STAGES_IN_DELIVERY = ["S2", "S3", "S4", "S5", "S6", "S7", "S8"]

DEFAULT_STATUS_SETS = {
    "issue_closed": ["RESOLVED", "COMPLETED", "CLOSED", "DONE"],
    "change_closed": ["COMPLETED", "CLOSED", "REJECTED", "CANCELLED"],
    "payment_pending": ["PENDING", "INVOICED"],
    "milestone_completed": ["COMPLETED", "DONE"],
}


class OtdThresholdConfig(Base, TimestampMixin):
    """OTD 11 维风险检测阈值配置。

    单表多配置行，运行时取 is_default=True 且 is_active=True 的那一行。
    首次运行 DB 无配置时，由 threshold_service 返回内存默认实例。
    """

    __tablename__ = "otd_threshold_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="配置名称")
    code = Column(String(50), unique=True, nullable=False, comment="配置编码")
    description = Column(Text, comment="配置描述")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否默认配置")
    priority = Column(Integer, default=0, comment="优先级（预留）")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # ---------- 扫描范围 ----------
    scan_limit = Column(Integer, default=200, comment="单次扫描项目上限")
    stages_in_delivery = Column(
        JSON, comment="纳入扫描的生命周期阶段（JSON 数组）"
    )

    # ---------- 维度1 采购延期（逾期天数三档分级）----------
    procurement_overdue_medium_days = Column(
        Integer, default=7, comment="采购逾期 MEDIUM 天数下限"
    )
    procurement_overdue_high_days = Column(
        Integer, default=15, comment="采购逾期 HIGH 天数下限"
    )
    procurement_overdue_critical_days = Column(
        Integer, default=30, comment="采购逾期 CRITICAL 天数下限"
    )

    # ---------- 维度2 图纸未冻结（阶段门禁）----------
    design_freeze_check_from_stage = Column(
        String(10), default="S3", comment="图纸冻结检测起始阶段（含）"
    )
    design_freeze_high_stage = Column(
        String(10), default="S4", comment="该阶段无 DDR 判 HIGH"
    )
    design_freeze_critical_stage = Column(
        String(10), default="S5", comment="该阶段无 DDR 判 CRITICAL"
    )
    design_review_pass_conclusions = Column(
        JSON, comment="DDR 评审通过结论集合（JSON 数组）"
    )

    # ---------- 维度3 客户变更频繁（时间窗+次数）----------
    change_window_short_days = Column(
        Integer, default=30, comment="客户变更短时间窗（天）"
    )
    change_window_long_days = Column(
        Integer, default=90, comment="客户变更长时间窗（天）"
    )
    change_critical_count = Column(
        Integer, default=5, comment="短窗内变更次数 CRITICAL 阈值"
    )
    change_high_count = Column(
        Integer, default=3, comment="短窗内变更次数 HIGH 阈值"
    )

    # ---------- 维度5 现场调试反复 ----------
    debug_window_days = Column(
        Integer, default=30, comment="调试问题时间窗（天）"
    )
    debug_high_count = Column(
        Integer, default=5, comment="窗内调试问题数 HIGH 阈值"
    )
    debug_medium_count = Column(
        Integer, default=3, comment="窗内调试问题数 MEDIUM 阈值"
    )
    debug_categories = Column(
        JSON, comment="调试类问题分类集合（JSON 数组）"
    )

    # ---------- 维度6 验收资料缺失 ----------
    acceptance_near_window_days = Column(
        Integer, default=60, comment="临近交付判定窗口（天，到该窗口才检测）"
    )
    acceptance_high_window_days = Column(
        Integer, default=30, comment="HIGH 级窗口（天，到该窗口判 HIGH）"
    )
    acceptance_check_from_stage = Column(
        String(10), default="S6", comment="验收资料检测起始阶段（含）"
    )
    acceptance_doc_keywords = Column(
        JSON, comment="验收资料缺失关键词集合（JSON 数组）"
    )

    # ---------- 维度7 回款临近条件不齐 ----------
    payment_upcoming_days = Column(
        Integer, default=7, comment="回款临近判定窗口（天）"
    )

    # ---------- 维度8 关键节点延期 ----------
    key_milestone_critical_days = Column(
        Integer, default=30, comment="关键节点逾期 CRITICAL 天数阈值"
    )
    key_milestone_critical_count = Column(
        Integer, default=2, comment="关键节点逾期 CRITICAL 数量阈值"
    )

    # ---------- 维度9 进度滞后 ----------
    progress_medium_threshold = Column(
        Numeric(5, 2), default=-15, comment="进度偏差 MEDIUM 阈值（负值）"
    )
    progress_high_threshold = Column(
        Numeric(5, 2), default=-25, comment="进度偏差 HIGH 阈值（负值）"
    )

    # ---------- 维度10 毛利偏差 ----------
    margin_medium_threshold = Column(
        Numeric(5, 2), default=-3, comment="毛利偏差 MEDIUM 阈值（负值）"
    )
    margin_high_threshold = Column(
        Numeric(5, 2), default=-5, comment="毛利偏差 HIGH 阈值（负值）"
    )
    margin_critical_threshold = Column(
        Numeric(5, 2), default=-10, comment="毛利偏差 CRITICAL 阈值（负值）"
    )

    # ---------- 维度11 未关闭事项 ----------
    open_items_high_count = Column(
        Integer, default=10, comment="未关闭事项总数 HIGH 阈值"
    )
    open_items_medium_count = Column(
        Integer, default=5, comment="未关闭事项总数 MEDIUM 阈值"
    )

    # ---------- 状态集合（集中存放，11 维共用）----------
    status_sets = Column(JSON, comment="状态集合（JSON：issue_closed/change_closed/...）")

    __table_args__ = (
        Index("idx_otd_threshold_code", "code"),
        Index("idx_otd_threshold_default", "is_default"),
        Index("idx_otd_threshold_active", "is_active"),
        {"comment": "OTD 风险检测阈值配置表"},
    )

    def __repr__(self):
        return f"<OtdThresholdConfig {self.code}: {self.name}>"


__all__ = ["OtdThresholdConfig"]
