# -*- coding: utf-8 -*-
"""
销售漏斗状态机模型

包含：
- SalesFunnelStage: 漏斗阶段定义
- StageGateConfig: 阶段门配置（G1-G4）
- StageDwellTimeConfig: 阶段滞留时间配置
- StageDwellTimeAlert: 滞留时间告警记录
- FunnelTransitionLog: 漏斗状态转换日志
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
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


# ==================== 枚举定义 ====================


class FunnelEntityTypeEnum(str, Enum):
    """漏斗实体类型"""

    LEAD = "LEAD"  # 线索
    OPPORTUNITY = "OPPORTUNITY"  # 商机
    QUOTE = "QUOTE"  # 报价
    CONTRACT = "CONTRACT"  # 合同


class GateTypeEnum(str, Enum):
    """阶段门类型"""

    G1 = "G1"  # 线索转商机
    G2 = "G2"  # 商机转报价
    G3 = "G3"  # 报价转合同
    G4 = "G4"  # 合同转项目


class GateResultEnum(str, Enum):
    """阶段门验证结果"""

    PENDING = "PENDING"  # 待验证
    PASSED = "PASSED"  # 通过
    FAILED = "FAILED"  # 不通过
    WAIVED = "WAIVED"  # 豁免（特批通过）


class AlertSeverityEnum(str, Enum):
    """告警严重程度"""

    INFO = "INFO"  # 提示
    WARNING = "WARNING"  # 警告
    CRITICAL = "CRITICAL"  # 严重


class AlertStatusEnum(str, Enum):
    """告警状态"""

    ACTIVE = "ACTIVE"  # 激活
    ACKNOWLEDGED = "ACKNOWLEDGED"  # 已确认
    RESOLVED = "RESOLVED"  # 已解决
    IGNORED = "IGNORED"  # 已忽略


# ==================== 漏斗阶段定义 ====================


class SalesFunnelStage(Base, TimestampMixin):
    """漏斗阶段定义

    定义销售漏斗的各个阶段，包括阶段属性、转换规则等。
    """

    __tablename__ = "sales_funnel_stages"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 阶段标识
    stage_code = Column(String(50), unique=True, nullable=False, comment="阶段编码")
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    entity_type = Column(
        String(20),
        nullable=False,
        comment="实体类型: LEAD/OPPORTUNITY/QUOTE/CONTRACT"
    )

    # 阶段属性
    sequence = Column(Integer, nullable=False, comment="阶段顺序")
    description = Column(Text, comment="阶段描述")
    color = Column(String(20), comment="展示颜色")
    icon = Column(String(50), comment="展示图标")

    # 概率配置（用于销售预测）
    default_probability = Column(
        Integer,
        default=0,
        comment="默认成交概率(0-100)"
    )

    # 转换配置
    allowed_next_stages = Column(JSON, comment="允许转换到的下一阶段(JSON)")
    required_gate = Column(String(10), comment="需要通过的阶段门(G1-G4)")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_terminal = Column(Boolean, default=False, comment="是否为终止状态")
    is_won = Column(Boolean, default=False, comment="是否为赢单状态")
    is_lost = Column(Boolean, default=False, comment="是否为输单状态")

    __table_args__ = (
        Index("idx_funnel_stage_entity", "entity_type"),
        Index("idx_funnel_stage_sequence", "sequence"),
        UniqueConstraint(
            "entity_type", "sequence",
            name="uq_funnel_stage_sequence"
        ),
        {"comment": "销售漏斗阶段定义表"},
    )

    def __repr__(self):
        return f"<SalesFunnelStage {self.stage_code}>"


# ==================== 阶段门配置 ====================


class StageGateConfig(Base, TimestampMixin):
    """阶段门配置

    定义 G1-G4 阶段门的验证规则和通过条件。
    """

    __tablename__ = "stage_gate_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 阶段门标识
    gate_type = Column(
        String(10),
        unique=True,
        nullable=False,
        comment="阶段门类型: G1/G2/G3/G4"
    )
    gate_name = Column(String(100), nullable=False, comment="阶段门名称")
    description = Column(Text, comment="阶段门描述")

    # 验证规则配置
    validation_rules = Column(JSON, comment="验证规则配置(JSON)")

    # 必填检查项
    required_fields = Column(JSON, comment="必填字段列表(JSON)")

    # 文档检查项
    required_documents = Column(JSON, comment="必需文档列表(JSON)")

    # 审批配置
    requires_approval = Column(Boolean, default=False, comment="是否需要审批")
    approval_roles = Column(JSON, comment="审批角色列表(JSON)")

    # 通知配置
    notification_config = Column(JSON, comment="通知配置(JSON)")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    can_be_waived = Column(Boolean, default=False, comment="是否允许豁免")
    waive_approval_roles = Column(JSON, comment="豁免审批角色(JSON)")

    # 版本
    version = Column(String(20), default="V1.0", comment="配置版本")

    __table_args__ = (
        Index("idx_gate_config_type", "gate_type"),
        {"comment": "阶段门配置表"},
    )

    def __repr__(self):
        return f"<StageGateConfig {self.gate_type}>"


class StageGateResult(Base, TimestampMixin):
    """阶段门验证结果

    记录每次阶段门验证的详细结果。
    """

    __tablename__ = "stage_gate_results"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    entity_type = Column(String(20), nullable=False, comment="实体类型")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    gate_type = Column(String(10), nullable=False, comment="阶段门类型")

    # 验证结果
    result = Column(
        String(20),
        default=GateResultEnum.PENDING,
        comment="验证结果"
    )

    # 详细结果
    validation_details = Column(JSON, comment="验证详情(JSON)")
    passed_rules = Column(JSON, comment="通过的规则(JSON)")
    failed_rules = Column(JSON, comment="失败的规则(JSON)")
    warnings = Column(JSON, comment="警告信息(JSON)")

    # 分数
    score = Column(Integer, comment="验证分数")
    threshold = Column(Integer, comment="通过阈值")

    # 验证信息
    validated_at = Column(DateTime, default=datetime.now, comment="验证时间")
    validated_by = Column(Integer, ForeignKey("users.id"), comment="验证人ID")

    # 豁免信息
    is_waived = Column(Boolean, default=False, comment="是否被豁免")
    waived_by = Column(Integer, ForeignKey("users.id"), comment="豁免人ID")
    waived_at = Column(DateTime, comment="豁免时间")
    waive_reason = Column(Text, comment="豁免原因")

    # 关系
    validator = relationship("User", foreign_keys=[validated_by])
    waiver = relationship("User", foreign_keys=[waived_by])

    __table_args__ = (
        Index("idx_gate_result_entity", "entity_type", "entity_id"),
        Index("idx_gate_result_gate", "gate_type"),
        Index("idx_gate_result_result", "result"),
        {"comment": "阶段门验证结果表"},
    )

    def __repr__(self):
        return f"<StageGateResult {self.entity_type}:{self.entity_id}-{self.gate_type}>"


# ==================== 滞留时间配置 ====================


class StageDwellTimeConfig(Base, TimestampMixin):
    """阶段滞留时间配置

    定义各阶段的预期停留时间和告警阈值。
    """

    __tablename__ = "stage_dwell_time_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联阶段
    stage_id = Column(
        Integer,
        ForeignKey("sales_funnel_stages.id"),
        nullable=False,
        comment="漏斗阶段ID"
    )

    # 时间阈值配置（单位：小时）
    expected_hours = Column(Integer, nullable=False, comment="预期停留时间(小时)")
    warning_hours = Column(Integer, comment="警告阈值(小时)")
    critical_hours = Column(Integer, comment="严重告警阈值(小时)")

    # 按金额分级配置
    amount_thresholds = Column(JSON, comment="金额分级配置(JSON)")

    # 按客户等级配置
    customer_level_config = Column(JSON, comment="客户等级配置(JSON)")

    # 告警配置
    alert_enabled = Column(Boolean, default=True, comment="是否启用告警")
    alert_recipients = Column(JSON, comment="告警接收人配置(JSON)")
    escalation_config = Column(JSON, comment="升级配置(JSON)")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    stage = relationship("SalesFunnelStage", foreign_keys=[stage_id])

    __table_args__ = (
        Index("idx_dwell_config_stage", "stage_id"),
        UniqueConstraint("stage_id", name="uq_dwell_config_stage"),
        {"comment": "阶段滞留时间配置表"},
    )

    def __repr__(self):
        return f"<StageDwellTimeConfig stage_id={self.stage_id}>"


class StageDwellTimeAlert(Base, TimestampMixin):
    """滞留时间告警记录

    记录因超过滞留时间阈值而触发的告警。
    """

    __tablename__ = "stage_dwell_time_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    entity_type = Column(String(20), nullable=False, comment="实体类型")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    stage_id = Column(
        Integer,
        ForeignKey("sales_funnel_stages.id"),
        nullable=False,
        comment="阶段ID"
    )

    # 告警信息
    alert_code = Column(String(50), unique=True, nullable=False, comment="告警编码")
    severity = Column(
        String(20),
        default=AlertSeverityEnum.WARNING,
        comment="严重程度"
    )
    alert_message = Column(Text, comment="告警消息")

    # 滞留信息
    entered_stage_at = Column(DateTime, comment="进入阶段时间")
    dwell_hours = Column(Integer, comment="已滞留时间(小时)")
    threshold_hours = Column(Integer, comment="触发阈值(小时)")

    # 相关金额
    amount = Column(Numeric(15, 2), comment="相关金额")

    # 负责人
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    owner_name = Column(String(50), comment="负责人姓名")

    # 状态
    status = Column(
        String(20),
        default=AlertStatusEnum.ACTIVE,
        comment="告警状态"
    )

    # 处理信息
    acknowledged_by = Column(Integer, ForeignKey("users.id"), comment="确认人ID")
    acknowledged_at = Column(DateTime, comment="确认时间")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution_note = Column(Text, comment="处理说明")

    # 关系
    stage = relationship("SalesFunnelStage", foreign_keys=[stage_id])
    owner = relationship("User", foreign_keys=[owner_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])

    __table_args__ = (
        Index("idx_dwell_alert_entity", "entity_type", "entity_id"),
        Index("idx_dwell_alert_stage", "stage_id"),
        Index("idx_dwell_alert_status", "status"),
        Index("idx_dwell_alert_severity", "severity"),
        Index("idx_dwell_alert_owner", "owner_id"),
        {"comment": "滞留时间告警记录表"},
    )

    def __repr__(self):
        return f"<StageDwellTimeAlert {self.alert_code}>"


# ==================== 状态转换日志 ====================


class FunnelTransitionLog(Base, TimestampMixin):
    """漏斗状态转换日志

    记录所有销售漏斗实体的状态变更历史。
    """

    __tablename__ = "funnel_transition_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 实体信息
    entity_type = Column(String(20), nullable=False, comment="实体类型")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    entity_code = Column(String(50), comment="实体编码")

    # 状态变更
    from_stage = Column(String(50), comment="原阶段")
    to_stage = Column(String(50), comment="目标阶段")

    # 阶段门信息
    gate_type = Column(String(10), comment="触发的阶段门")
    gate_result_id = Column(
        Integer,
        ForeignKey("stage_gate_results.id"),
        comment="阶段门验证结果ID"
    )

    # 变更原因
    transition_reason = Column(Text, comment="变更原因")

    # 操作人
    transitioned_by = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    transitioned_at = Column(DateTime, default=datetime.now, comment="变更时间")

    # 额外信息
    extra_data = Column(JSON, comment="额外数据(JSON)")

    # 滞留时间
    dwell_hours = Column(Integer, comment="在原阶段停留时间(小时)")

    # 关系
    operator = relationship("User", foreign_keys=[transitioned_by])
    gate_result = relationship("StageGateResult", foreign_keys=[gate_result_id])

    __table_args__ = (
        Index("idx_transition_log_entity", "entity_type", "entity_id"),
        Index("idx_transition_log_time", "transitioned_at"),
        Index("idx_transition_log_from", "from_stage"),
        Index("idx_transition_log_to", "to_stage"),
        {"comment": "漏斗状态转换日志表"},
    )

    def __repr__(self):
        return f"<FunnelTransitionLog {self.entity_type}:{self.entity_id}>"


# ==================== 漏斗统计快照 ====================


class FunnelSnapshot(Base, TimestampMixin):
    """漏斗统计快照

    定期记录销售漏斗各阶段的统计数据，用于趋势分析。
    """

    __tablename__ = "funnel_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 快照时间
    snapshot_date = Column(DateTime, nullable=False, comment="快照日期")
    snapshot_type = Column(
        String(20),
        default="DAILY",
        comment="快照类型: DAILY/WEEKLY/MONTHLY"
    )

    # 阶段统计
    stage_counts = Column(JSON, comment="各阶段数量(JSON)")
    stage_amounts = Column(JSON, comment="各阶段金额(JSON)")

    # 转换率
    conversion_rates = Column(JSON, comment="阶段转换率(JSON)")

    # 滞留统计
    dwell_stats = Column(JSON, comment="滞留时间统计(JSON)")

    # 预测数据
    forecast_data = Column(JSON, comment="销售预测数据(JSON)")

    # 创建人（系统自动或手动触发）
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    __table_args__ = (
        Index("idx_funnel_snapshot_date", "snapshot_date"),
        Index("idx_funnel_snapshot_type", "snapshot_type"),
        {"comment": "漏斗统计快照表"},
    )

    def __repr__(self):
        return f"<FunnelSnapshot {self.snapshot_date}>"
