# -*- coding: utf-8 -*-
"""
智能缺料预警系统 - 增强模型

Team 3: 智能缺料预警系统
提供智能预警、自动处理、影响分析功能
"""
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, ForeignKey, Index, Integer, JSON, 
    Numeric, String, Text, Boolean, Date
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ShortageAlert(Base, TimestampMixin):
    """
    缺料预警表（增强版）
    
    包含智能预警、影响分析、自动处理等功能
    """
    __tablename__ = 'shortage_alerts_enhanced'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_no = Column(String(50), unique=True, nullable=False, comment='预警单号')
    
    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    
    # 物料信息快照
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    material_spec = Column(String(200), comment='物料规格')
    
    # 需求与库存
    required_qty = Column(Numeric(14, 4), nullable=False, comment='需求数量')
    available_qty = Column(Numeric(14, 4), default=0, comment='可用数量')
    shortage_qty = Column(Numeric(14, 4), nullable=False, comment='缺料数量')
    in_transit_qty = Column(Numeric(14, 4), default=0, comment='在途数量')
    
    # 预警级别与时间
    alert_level = Column(String(20), nullable=False, comment='预警级别: INFO/WARNING/CRITICAL/URGENT')
    alert_date = Column(Date, nullable=False, default=datetime.now, comment='预警日期')
    required_date = Column(Date, comment='需求日期')
    expected_arrival_date = Column(Date, comment='预计到货日期')
    days_to_shortage = Column(Integer, default=0, comment='距离缺料天数')
    
    # 影响分析
    impact_projects = Column(JSON, comment='受影响项目列表')
    estimated_delay_days = Column(Integer, default=0, comment='预计延期天数')
    estimated_cost_impact = Column(Numeric(14, 2), default=0, comment='预计成本影响')
    is_critical_path = Column(Boolean, default=False, comment='是否关键路径')
    risk_score = Column(Numeric(5, 2), default=0, comment='风险评分 0-100')
    
    # 预测信息
    demand_forecast_id = Column(Integer, ForeignKey('material_demand_forecasts.id'), comment='需求预测ID')
    confidence_level = Column(Numeric(5, 2), comment='预测置信度 0-100')
    forecast_accuracy = Column(Numeric(5, 2), comment='历史预测准确率')
    
    # 状态与处理
    status = Column(String(20), default='PENDING', comment='状态: PENDING/PROCESSING/RESOLVED/CLOSED/CANCELLED')
    auto_handled = Column(Boolean, default=False, comment='是否自动处理')
    handling_plan_id = Column(Integer, ForeignKey('shortage_handling_plans.id'), comment='处理方案ID')
    
    # 处理时间
    detected_at = Column(DateTime, default=datetime.now, comment='检测时间')
    notified_at = Column(DateTime, comment='通知时间')
    handled_at = Column(DateTime, comment='处理开始时间')
    resolved_at = Column(DateTime, comment='解决时间')
    
    # 处理结果
    resolution_type = Column(String(50), comment='解决方式: PURCHASE/SUBSTITUTE/TRANSFER/RESCHEDULE')
    resolution_note = Column(Text, comment='解决说明')
    actual_delay_days = Column(Integer, comment='实际延期天数')
    actual_cost_impact = Column(Numeric(14, 2), comment='实际成本影响')
    
    # 扩展信息
    alert_source = Column(String(50), default='AUTO', comment='预警来源: AUTO/MANUAL/SYSTEM')
    priority_boost = Column(Integer, default=0, comment='优先级加成')
    extra_metadata = Column(JSON, comment='扩展数据')  # Renamed from 'metadata' (SQLAlchemy reserved)
    remark = Column(Text, comment='备注')
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    handler_id = Column(Integer, ForeignKey('users.id'), comment='处理人ID')
    
    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    material = relationship('Material', foreign_keys=[material_id])
    creator = relationship('User', foreign_keys=[created_by])
    handler = relationship('User', foreign_keys=[handler_id])
    handling_plan = relationship('ShortageHandlingPlan', foreign_keys=[handling_plan_id], back_populates='alerts')
    demand_forecast = relationship('MaterialDemandForecast', back_populates='alerts')
    
    __table_args__ = (
        Index('idx_shortage_alert_no', 'alert_no'),
        Index('idx_shortage_alert_project', 'project_id'),
        Index('idx_shortage_alert_material', 'material_id'),
        Index('idx_shortage_alert_level', 'alert_level'),
        Index('idx_shortage_alert_status', 'status'),
        Index('idx_shortage_alert_date', 'alert_date'),
        Index('idx_shortage_alert_required_date', 'required_date'),
        Index('idx_shortage_alert_auto_handled', 'auto_handled'),
        {'comment': '缺料预警表（增强版）- 智能预警系统'}
    )


class ShortageHandlingPlan(Base, TimestampMixin):
    """
    缺料处理方案表
    
    AI生成的处理方案，包含自动评分和推荐
    """
    __tablename__ = 'shortage_handling_plans'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    plan_no = Column(String(50), unique=True, nullable=False, comment='方案编号')
    
    # 关联预警
    alert_id = Column(Integer, ForeignKey('shortage_alerts_enhanced.id'), nullable=False, comment='预警ID')
    
    # 方案类型
    solution_type = Column(String(50), nullable=False, comment='方案类型: URGENT_PURCHASE/SUBSTITUTE/TRANSFER/PARTIAL_DELIVERY/RESCHEDULE')
    solution_name = Column(String(200), nullable=False, comment='方案名称')
    solution_description = Column(Text, comment='方案描述')
    
    # 方案详情
    target_material_id = Column(Integer, ForeignKey('materials.id'), comment='目标物料ID（替代料）')
    target_supplier_id = Column(Integer, ForeignKey('vendors.id'), comment='目标供应商ID')
    target_project_id = Column(Integer, ForeignKey('projects.id'), comment='目标项目ID（调拨）')
    
    # 方案参数
    proposed_qty = Column(Numeric(14, 4), comment='建议数量')
    proposed_date = Column(Date, comment='建议日期')
    estimated_lead_time = Column(Integer, comment='预计交期（天）')
    estimated_cost = Column(Numeric(14, 2), comment='预计成本')
    
    # AI评分
    ai_score = Column(Numeric(5, 2), default=0, comment='AI评分 0-100')
    feasibility_score = Column(Numeric(5, 2), default=0, comment='可行性评分')
    cost_score = Column(Numeric(5, 2), default=0, comment='成本评分')
    time_score = Column(Numeric(5, 2), default=0, comment='时间评分')
    risk_score = Column(Numeric(5, 2), default=0, comment='风险评分')
    
    # 评分权重说明
    score_weights = Column(JSON, comment='评分权重 {"feasibility": 0.3, "cost": 0.3, "time": 0.3, "risk": 0.1}')
    score_explanation = Column(Text, comment='评分说明')
    
    # 优缺点分析
    advantages = Column(JSON, comment='优点列表')
    disadvantages = Column(JSON, comment='缺点列表')
    risks = Column(JSON, comment='风险点列表')
    
    # 推荐优先级
    is_recommended = Column(Boolean, default=False, comment='是否推荐')
    recommendation_rank = Column(Integer, default=999, comment='推荐排名')
    
    # 执行状态
    status = Column(String(20), default='PENDING', comment='状态: PENDING/APPROVED/REJECTED/EXECUTING/COMPLETED/FAILED')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approved_at = Column(DateTime, comment='审批时间')
    executed_at = Column(DateTime, comment='执行时间')
    completed_at = Column(DateTime, comment='完成时间')
    
    # 执行结果
    execution_result = Column(JSON, comment='执行结果')
    actual_cost = Column(Numeric(14, 2), comment='实际成本')
    actual_lead_time = Column(Integer, comment='实际交期')
    effectiveness_rating = Column(Integer, comment='方案有效性评分 1-5')
    
    # 扩展信息
    extra_metadata = Column(JSON, comment='扩展数据')  # Renamed from 'metadata' (SQLAlchemy reserved)
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关系
    alerts = relationship('ShortageAlert', foreign_keys='[ShortageAlert.handling_plan_id]', back_populates='handling_plan')
    target_material = relationship('Material', foreign_keys=[target_material_id])
    creator = relationship('User', foreign_keys=[created_by])
    approver = relationship('User', foreign_keys=[approved_by])
    
    __table_args__ = (
        Index('idx_handling_plan_no', 'plan_no'),
        Index('idx_handling_plan_alert', 'alert_id'),
        Index('idx_handling_plan_type', 'solution_type'),
        Index('idx_handling_plan_status', 'status'),
        Index('idx_handling_plan_recommended', 'is_recommended'),
        Index('idx_handling_plan_score', 'ai_score'),
        {'comment': '缺料处理方案表 - AI智能推荐'}
    )


class MaterialDemandForecast(Base, TimestampMixin):
    """
    物料需求预测表
    
    基于历史数据和算法的需求预测
    """
    __tablename__ = 'material_demand_forecasts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    forecast_no = Column(String(50), unique=True, nullable=False, comment='预测编号')
    
    # 预测目标
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID（可选）')
    
    # 预测周期
    forecast_start_date = Column(Date, nullable=False, comment='预测起始日期')
    forecast_end_date = Column(Date, nullable=False, comment='预测结束日期')
    forecast_horizon_days = Column(Integer, default=30, comment='预测周期（天）')
    
    # 预测算法
    algorithm = Column(String(50), nullable=False, comment='预测算法: MOVING_AVERAGE/EXP_SMOOTHING/LINEAR_REGRESSION/ARIMA')
    algorithm_params = Column(JSON, comment='算法参数')
    
    # 预测结果
    forecasted_demand = Column(Numeric(14, 4), nullable=False, comment='预测需求量')
    lower_bound = Column(Numeric(14, 4), comment='预测下限（置信区间）')
    upper_bound = Column(Numeric(14, 4), comment='预测上限（置信区间）')
    confidence_interval = Column(Numeric(5, 2), default=95, comment='置信区间 %')
    
    # 历史基准
    historical_avg = Column(Numeric(14, 4), comment='历史平均需求')
    historical_std = Column(Numeric(14, 4), comment='历史标准差')
    historical_period_days = Column(Integer, default=90, comment='历史数据周期（天）')
    
    # 季节性因素
    seasonal_factor = Column(Numeric(5, 2), default=1.0, comment='季节性系数')
    seasonal_pattern = Column(JSON, comment='季节性模式数据')
    
    # 预测准确率
    accuracy_score = Column(Numeric(5, 2), comment='预测准确率 %')
    mae = Column(Numeric(14, 4), comment='平均绝对误差 MAE')
    rmse = Column(Numeric(14, 4), comment='均方根误差 RMSE')
    mape = Column(Numeric(5, 2), comment='平均绝对百分比误差 MAPE %')
    
    # 实际对比
    actual_demand = Column(Numeric(14, 4), comment='实际需求量')
    forecast_error = Column(Numeric(14, 4), comment='预测误差')
    error_percentage = Column(Numeric(5, 2), comment='误差百分比 %')
    
    # 预测状态
    status = Column(String(20), default='ACTIVE', comment='状态: DRAFT/ACTIVE/EXPIRED/VALIDATED')
    forecast_date = Column(Date, default=datetime.now, comment='预测生成日期')
    validated_at = Column(DateTime, comment='验证时间')
    
    # 影响因素
    influencing_factors = Column(JSON, comment='影响因素 {"project_count": 5, "season": "high", ...}')
    
    # 扩展信息
    extra_metadata = Column(JSON, comment='扩展数据')  # Renamed from 'metadata' (SQLAlchemy reserved)
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关系
    material = relationship('Material', foreign_keys=[material_id])
    project = relationship('Project', foreign_keys=[project_id])
    creator = relationship('User', foreign_keys=[created_by])
    alerts = relationship('ShortageAlert', back_populates='demand_forecast')
    
    __table_args__ = (
        Index('idx_forecast_no', 'forecast_no'),
        Index('idx_forecast_material', 'material_id'),
        Index('idx_demand_forecast_project', 'project_id'),
        Index('idx_forecast_status', 'status'),
        Index('idx_forecast_date', 'forecast_date'),
        Index('idx_forecast_period', 'forecast_start_date', 'forecast_end_date'),
        {'comment': '物料需求预测表 - 智能预测引擎'}
    )
