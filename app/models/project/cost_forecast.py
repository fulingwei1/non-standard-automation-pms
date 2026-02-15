# -*- coding: utf-8 -*-
"""
项目成本预测模型 - CostForecast, CostAlert
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
    JSON,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class CostForecast(Base, TimestampMixin):
    """
    成本预测表

    用途：存储项目成本预测结果
    - 支持多种预测方法（线性/指数/历史平均）
    - 记录预测数据（月度/累计）
    - 计算预测准确率
    """

    __tablename__ = "cost_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 项目关联
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    project_code = Column(String(50), comment="项目编号（冗余）")
    project_name = Column(String(200), comment="项目名称（冗余）")

    # 预测方法
    forecast_method = Column(
        String(50),
        nullable=False,
        default="LINEAR",
        comment="预测方法：LINEAR/EXPONENTIAL/HISTORICAL_AVERAGE/MOVING_AVERAGE",
    )

    # 预测时间
    forecast_date = Column(Date, nullable=False, comment="预测日期（预测时的日期）")
    forecast_month = Column(String(7), comment="预测月份(YYYY-MM)")

    # 预测结果
    forecasted_completion_cost = Column(
        Numeric(14, 2), nullable=False, comment="预测完工成本"
    )
    forecasted_completion_date = Column(Date, comment="预测完工日期")

    # 当前状态（预测时的数据）
    current_progress_pct = Column(Numeric(5, 2), comment="当前完成进度(%)")
    current_actual_cost = Column(Numeric(14, 2), comment="当前实际成本")
    current_budget = Column(Numeric(14, 2), comment="当前预算金额")

    # 月度预测数据（JSON格式）
    monthly_forecast_data = Column(
        JSON,
        comment="月度预测数据 [{month, forecasted_cost, cumulative_cost}]",
    )

    # 趋势数据（JSON格式）
    trend_data = Column(
        JSON,
        comment="趋势数据 {slope, intercept, r_squared, growth_rate}",
    )

    # 预测准确率（回填）
    actual_completion_cost = Column(Numeric(14, 2), comment="实际完工成本（用于验证）")
    forecast_accuracy = Column(Numeric(5, 2), comment="预测准确率(%) - 事后计算")
    forecast_error = Column(Numeric(14, 2), comment="预测误差（实际-预测）")
    forecast_error_pct = Column(Numeric(5, 2), comment="预测误差率(%)")

    # 参数记录
    parameters = Column(JSON, comment="预测参数（JSON）")

    # 备注
    description = Column(Text, comment="预测说明")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_cost_forecast_project", "project_id"),
        Index("idx_cost_forecast_date", "forecast_date"),
        Index("idx_cost_forecast_month", "forecast_month"),
        Index("idx_cost_forecast_method", "forecast_method"),
        {"comment": "成本预测表"},
    )

    def __repr__(self):
        return f"<CostForecast {self.project_code}-{self.forecast_method}>"


class CostAlert(Base, TimestampMixin):
    """
    成本预警表

    用途：记录项目成本预警事件
    - 超支预警（实际成本 > 预算 × 阈值）
    - 进度预警（完成度 vs 成本消耗比例）
    - 趋势预警（成本增长率异常）
    """

    __tablename__ = "cost_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 项目关联
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    project_code = Column(String(50), comment="项目编号（冗余）")
    project_name = Column(String(200), comment="项目名称（冗余）")

    # 预警类型
    alert_type = Column(
        String(50),
        nullable=False,
        comment="预警类型：OVERSPEND/PROGRESS_MISMATCH/TREND_ANOMALY/FORECAST_OVERRUN",
    )

    # 预警级别
    alert_level = Column(
        String(20),
        nullable=False,
        default="WARNING",
        comment="预警级别：INFO/WARNING/CRITICAL",
    )

    # 预警时间
    alert_date = Column(Date, nullable=False, comment="预警日期")
    alert_month = Column(String(7), comment="预警月份(YYYY-MM)")

    # 预警数据
    current_cost = Column(Numeric(14, 2), comment="当前实际成本")
    budget_amount = Column(Numeric(14, 2), comment="预算金额")
    threshold = Column(Numeric(5, 2), comment="阈值(%)")
    current_progress = Column(Numeric(5, 2), comment="当前进度(%)")
    cost_consumption_rate = Column(Numeric(5, 2), comment="成本消耗率(%)")

    # 预警详情
    alert_title = Column(String(200), nullable=False, comment="预警标题")
    alert_message = Column(Text, nullable=False, comment="预警消息")
    alert_data = Column(JSON, comment="预警详细数据（JSON）")

    # 状态
    status = Column(
        String(20),
        default="ACTIVE",
        comment="状态：ACTIVE/ACKNOWLEDGED/RESOLVED/IGNORED",
    )
    acknowledged_by = Column(Integer, ForeignKey("users.id"), comment="确认人ID")
    acknowledged_at = Column(DateTime, comment="确认时间")
    resolved_at = Column(DateTime, comment="解决时间")

    # 处理信息
    resolution_note = Column(Text, comment="处理说明")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])

    __table_args__ = (
        Index("idx_cost_alert_project", "project_id"),
        Index("idx_cost_alert_type", "alert_type"),
        Index("idx_cost_alert_level", "alert_level"),
        Index("idx_cost_alert_date", "alert_date"),
        Index("idx_cost_alert_status", "status"),
        {"comment": "成本预警表"},
    )

    def __repr__(self):
        return f"<CostAlert {self.project_code}-{self.alert_type}>"


class CostAlertRule(Base, TimestampMixin):
    """
    成本预警规则表

    用途：配置成本预警规则
    - 全局规则（适用于所有项目）
    - 项目特定规则（覆盖全局规则）
    """

    __tablename__ = "cost_alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 规则名称
    rule_name = Column(String(200), nullable=False, comment="规则名称")
    rule_code = Column(String(50), unique=True, nullable=False, comment="规则编码")

    # 项目关联（为空表示全局规则）
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID（空=全局规则）")

    # 规则类型
    alert_type = Column(
        String(50),
        nullable=False,
        comment="预警类型：OVERSPEND/PROGRESS_MISMATCH/TREND_ANOMALY/FORECAST_OVERRUN",
    )

    # 规则配置（JSON格式）
    rule_config = Column(
        JSON,
        nullable=False,
        comment="规则配置 {threshold, warning_level, critical_level, ...}",
    )

    # 是否启用
    is_enabled = Column(Boolean, default=True, comment="是否启用")

    # 优先级（数字越小优先级越高）
    priority = Column(Integer, default=100, comment="优先级")

    # 通知配置
    notification_enabled = Column(Boolean, default=True, comment="是否发送通知")
    notification_recipients = Column(JSON, comment="通知接收人列表（user_ids）")

    # 描述
    description = Column(Text, comment="规则描述")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_cost_alert_rule_project", "project_id"),
        Index("idx_cost_alert_rule_type", "alert_type"),
        Index("idx_cost_alert_rule_enabled", "is_enabled"),
        {"comment": "成本预警规则表"},
    )

    def __repr__(self):
        return f"<CostAlertRule {self.rule_code}>"
