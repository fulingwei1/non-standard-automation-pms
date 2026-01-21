# -*- coding: utf-8 -*-
"""
战略管理核心模型 - Strategy, CSF, KPI
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class Strategy(Base, TimestampMixin):
    """战略主表 - 公司级战略规划"""

    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="战略编码，如 STR-2026")
    name = Column(String(200), nullable=False, comment="战略名称")
    vision = Column(Text, comment="愿景描述")
    mission = Column(Text, comment="使命描述")
    slogan = Column(String(200), comment="战略口号（响亮、易记）")

    # 战略周期
    year = Column(Integer, nullable=False, comment="战略年度")
    start_date = Column(Date, comment="战略周期开始")
    end_date = Column(Date, comment="战略周期结束")

    # 状态
    status = Column(String(20), default="DRAFT", comment="状态：DRAFT/ACTIVE/ARCHIVED")

    # 审批信息
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    published_at = Column(DateTime, comment="发布时间")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    csfs = relationship("CSF", back_populates="strategy", lazy="dynamic")
    reviews = relationship("StrategyReview", back_populates="strategy", lazy="dynamic")
    calendar_events = relationship("StrategyCalendarEvent", back_populates="strategy", lazy="dynamic")
    department_objectives = relationship("DepartmentObjective", back_populates="strategy", lazy="dynamic")

    __table_args__ = (
        Index("idx_strategies_code", "code"),
        Index("idx_strategies_year", "year"),
        Index("idx_strategies_status", "status"),
        Index("idx_strategies_active", "is_active"),
    )

    def __repr__(self):
        return f"<Strategy {self.code}>"


class CSF(Base, TimestampMixin):
    """关键成功要素 - BSC 四维度"""

    __tablename__ = "csfs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="关联战略")

    # 基本信息
    dimension = Column(String(20), nullable=False, comment="BSC维度：FINANCIAL/CUSTOMER/INTERNAL/LEARNING")
    code = Column(String(50), nullable=False, comment="CSF 编码，如 CSF-F-001")
    name = Column(String(200), nullable=False, comment="要素名称")
    description = Column(Text, comment="详细描述")

    # 导出方法
    derivation_method = Column(String(50), comment="导出方法：FOUR_PARAM/FIVE_SOURCE/VALUE_CHAIN/INTANGIBLE")

    # 权重与排序
    weight = Column(Numeric(5, 2), default=0, comment="权重占比（%）")
    sort_order = Column(Integer, default=0, comment="排序")

    # 责任人
    owner_dept_id = Column(Integer, ForeignKey("departments.id"), comment="责任部门")
    owner_user_id = Column(Integer, ForeignKey("users.id"), comment="责任人")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    strategy = relationship("Strategy", back_populates="csfs")
    owner_dept = relationship("Department", foreign_keys=[owner_dept_id])
    owner = relationship("User", foreign_keys=[owner_user_id])
    kpis = relationship("KPI", back_populates="csf", lazy="dynamic")
    annual_key_works = relationship("AnnualKeyWork", back_populates="csf", lazy="dynamic")

    __table_args__ = (
        Index("idx_csfs_strategy", "strategy_id"),
        Index("idx_csfs_dimension", "dimension"),
        Index("idx_csfs_code", "code"),
        Index("idx_csfs_owner_dept", "owner_dept_id"),
        Index("idx_csfs_active", "is_active"),
    )

    def __repr__(self):
        return f"<CSF {self.code}>"


class KPI(Base, TimestampMixin):
    """KPI 指标 - IPOOC 度量"""

    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    csf_id = Column(Integer, ForeignKey("csfs.id"), nullable=False, comment="关联 CSF")

    # 基本信息
    code = Column(String(50), nullable=False, comment="KPI 编码")
    name = Column(String(200), nullable=False, comment="指标名称")
    description = Column(Text, comment="指标描述")

    # IPOOC 分类
    ipooc_type = Column(String(20), nullable=False, comment="IPOOC类型：INPUT/PROCESS/OUTPUT/OUTCOME")

    # 指标定义
    unit = Column(String(20), comment="单位（%、万元、天、个）")
    direction = Column(String(10), default="UP", comment="方向：UP（越大越好）/DOWN（越小越好）")

    # 目标与当前值
    target_value = Column(Numeric(14, 2), comment="目标值")
    baseline_value = Column(Numeric(14, 2), comment="基线值")
    current_value = Column(Numeric(14, 2), comment="当前值")

    # 阈值设置
    excellent_threshold = Column(Numeric(14, 2), comment="优秀阈值")
    good_threshold = Column(Numeric(14, 2), comment="良好阈值")
    warning_threshold = Column(Numeric(14, 2), comment="警告阈值")

    # 数据源配置
    data_source_type = Column(String(20), default="MANUAL", comment="数据源类型：MANUAL/AUTO/FORMULA")
    data_source_config = Column(Text, comment="数据源配置（JSON）")

    # 更新频率
    frequency = Column(String(20), default="MONTHLY", comment="更新频率：DAILY/WEEKLY/MONTHLY/QUARTERLY")
    last_collected_at = Column(DateTime, comment="最后采集时间")

    # 权重
    weight = Column(Numeric(5, 2), default=0, comment="权重占比（%）")

    # 责任人
    owner_user_id = Column(Integer, ForeignKey("users.id"), comment="责任人")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    csf = relationship("CSF", back_populates="kpis")
    owner = relationship("User", foreign_keys=[owner_user_id])
    history = relationship("KPIHistory", back_populates="kpi", lazy="dynamic")
    data_sources = relationship("KPIDataSource", back_populates="kpi", lazy="dynamic")

    __table_args__ = (
        Index("idx_kpis_csf", "csf_id"),
        Index("idx_kpis_code", "code"),
        Index("idx_kpis_ipooc", "ipooc_type"),
        Index("idx_kpis_source_type", "data_source_type"),
        Index("idx_kpis_owner", "owner_user_id"),
        Index("idx_kpis_active", "is_active"),
    )

    def __repr__(self):
        return f"<KPI {self.code}>"


class KPIHistory(Base, TimestampMixin):
    """KPI 历史快照"""

    __tablename__ = "kpi_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False, comment="关联 KPI")

    # 快照时间
    snapshot_date = Column(Date, nullable=False, comment="快照日期")
    snapshot_period = Column(String(20), comment="快照周期：DAILY/WEEKLY/MONTHLY/QUARTERLY/YEARLY")

    # 值
    value = Column(Numeric(14, 2), comment="KPI 值")
    target_value = Column(Numeric(14, 2), comment="目标值（快照时）")

    # 完成率
    completion_rate = Column(Numeric(5, 2), comment="完成率（%）")

    # 健康度
    health_level = Column(String(20), comment="健康等级：EXCELLENT/GOOD/WARNING/DANGER")

    # 数据来源
    source_type = Column(String(20), comment="来源类型：MANUAL/AUTO/FORMULA")
    source_detail = Column(Text, comment="来源详情")

    # 备注
    remark = Column(Text, comment="备注")

    # 记录人
    recorded_by = Column(Integer, ForeignKey("users.id"), comment="记录人")

    # 关系
    kpi = relationship("KPI", back_populates="history")
    recorder = relationship("User", foreign_keys=[recorded_by])

    __table_args__ = (
        Index("idx_kpi_history_kpi", "kpi_id"),
        Index("idx_kpi_history_date", "snapshot_date"),
        Index("idx_kpi_history_kpi_date", "kpi_id", "snapshot_date"),
    )

    def __repr__(self):
        return f"<KPIHistory kpi={self.kpi_id} date={self.snapshot_date}>"


class KPIDataSource(Base, TimestampMixin):
    """KPI 数据源配置"""

    __tablename__ = "kpi_data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False, comment="关联 KPI")

    # 数据源类型
    source_type = Column(String(20), nullable=False, comment="类型：AUTO/FORMULA")

    # 自动采集配置
    source_module = Column(String(50), comment="来源模块：project_cost/finance/hr 等")
    query_type = Column(String(20), comment="查询类型：aggregate/latest/count")
    metric = Column(String(100), comment="度量字段")
    filters = Column(Text, comment="过滤条件（JSON）")
    aggregation = Column(String(20), comment="聚合方式：sum/avg/count/max/min")

    # 公式计算配置
    formula = Column(Text, comment="计算公式（使用 simpleeval）")
    formula_params = Column(Text, comment="公式参数（JSON）")

    # 状态
    is_primary = Column(Boolean, default=False, comment="是否主数据源")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 最后执行
    last_executed_at = Column(DateTime, comment="最后执行时间")
    last_result = Column(Numeric(14, 2), comment="最后结果")
    last_error = Column(Text, comment="最后错误信息")

    # 关系
    kpi = relationship("KPI", back_populates="data_sources")

    __table_args__ = (
        Index("idx_kpi_data_source_kpi", "kpi_id"),
        Index("idx_kpi_data_source_type", "source_type"),
        Index("idx_kpi_data_source_active", "is_active"),
    )

    def __repr__(self):
        return f"<KPIDataSource kpi={self.kpi_id} type={self.source_type}>"
