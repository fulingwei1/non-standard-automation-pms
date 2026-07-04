# -*- coding: utf-8 -*-
"""Dashboard chart configuration models."""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Index, Integer, String

from app.models.base import Base, TimestampMixin


class DashboardChartConfig(Base, TimestampMixin):
    """Persisted chart configuration for dashboard widgets."""

    __tablename__ = "dashboard_chart_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建用户ID")
    chart_type = Column(String(50), nullable=False, comment="图表类型")
    title = Column(String(200), nullable=False, comment="图表标题")
    x_axis = Column(String(100), comment="X轴字段")
    y_axis = Column(String(100), comment="Y轴字段")
    data_source = Column(String(100), nullable=False, comment="数据源")
    filters = Column(JSON, comment="筛选条件")
    custom_metrics = Column(JSON, comment="自定义指标")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    __table_args__ = (
        Index("idx_dashboard_chart_configs_user", "user_id"),
        Index("idx_dashboard_chart_configs_active", "is_active"),
        {"comment": "仪表盘图表配置表"},
    )
