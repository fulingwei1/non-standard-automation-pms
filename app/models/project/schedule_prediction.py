# -*- coding: utf-8 -*-
"""
项目进度预测模型
Project Schedule Prediction Models
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    DECIMAL,
    JSON,
    Text,
    Index,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class ProjectSchedulePrediction(Base):
    """项目进度预测记录表"""

    __tablename__ = "project_schedule_prediction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True, comment="项目ID")
    prediction_date = Column(DateTime, nullable=False, default=datetime.now, comment="预测时间")
    
    # 预测结果
    predicted_completion_date = Column(Date, nullable=True, comment="预测完成日期")
    delay_days = Column(Integer, nullable=True, comment="预计延期天数")
    confidence = Column(DECIMAL(5, 2), nullable=True, comment="置信度 (0-1)")
    risk_level = Column(
        String(20), 
        nullable=True, 
        comment="风险等级: low/medium/high/critical"
    )
    
    # 特征数据（JSON格式存储）
    features = Column(JSON, nullable=True, comment="预测特征数据")
    # features 结构示例:
    # {
    #     "current_progress": 45.5,
    #     "planned_progress": 60.0,
    #     "remaining_days": 30,
    #     "team_size": 5,
    #     "avg_daily_progress": 1.2,
    #     "recent_velocity": 0.8,
    #     "complexity": "high",
    #     "similar_projects_avg": 75
    # }
    
    # 预测详情
    prediction_details = Column(JSON, nullable=True, comment="详细预测结果")
    # prediction_details 结构示例:
    # {
    #     "risk_factors": ["团队规模不足", "进度偏差大"],
    #     "recommendations": ["增加人力", "优化流程"],
    #     "historical_reference": {
    #         "similar_projects": 5,
    #         "avg_delay": 12.5
    #     }
    # }
    
    model_version = Column(String(50), nullable=True, comment="AI模型版本")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联关系
    catch_up_solutions = relationship(
        "CatchUpSolution",
        back_populates="prediction",
        cascade="all, delete-orphan"
    )
    alerts = relationship(
        "ScheduleAlert",
        back_populates="prediction",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_project_prediction_date", "project_id", "prediction_date"),
        Index("idx_risk_level", "risk_level"),
        Index("idx_prediction_date", "prediction_date"),
    )

    def __repr__(self):
        return f"<ProjectSchedulePrediction(id={self.id}, project_id={self.project_id}, delay_days={self.delay_days})>"


class CatchUpSolution(Base):
    """赶工方案表"""

    __tablename__ = "catch_up_solutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True, comment="项目ID")
    prediction_id = Column(
        Integer, 
        ForeignKey("project_schedule_prediction.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="关联的预测记录ID"
    )
    
    # 方案基本信息
    solution_name = Column(String(200), nullable=False, comment="方案名称")
    solution_type = Column(
        String(50),
        nullable=True,
        comment="方案类型: manpower/overtime/process/hybrid"
    )
    description = Column(Text, nullable=True, comment="方案描述")
    
    # 方案详情（JSON格式存储）
    actions = Column(JSON, nullable=True, comment="具体行动计划")
    # actions 结构示例:
    # [
    #     {"action": "从项目A借调2名工程师", "priority": 1},
    #     {"action": "新招1名外包工程师", "priority": 2}
    # ]
    
    # 方案评估
    estimated_catch_up_days = Column(Integer, nullable=True, comment="预计可追回天数")
    additional_cost = Column(DECIMAL(12, 2), nullable=True, comment="额外成本")
    risk_level = Column(
        String(20),
        nullable=True,
        comment="方案风险等级: low/medium/high"
    )
    success_rate = Column(DECIMAL(5, 2), nullable=True, comment="成功率 (0-1)")
    
    # 方案详细评估
    evaluation_details = Column(JSON, nullable=True, comment="评估详情")
    # evaluation_details 结构示例:
    # {
    #     "pros": ["成本低", "风险可控"],
    #     "cons": ["效果有限"],
    #     "prerequisites": ["需要管理层批准"],
    #     "timeline": "7-10天见效"
    # }
    
    # 方案状态
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="状态: pending/approved/rejected/implementing/completed/cancelled"
    )
    is_recommended = Column(Boolean, default=False, comment="是否为推荐方案")
    
    # 审批信息
    approved_by = Column(Integer, nullable=True, comment="审批人ID")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")
    approval_comment = Column(Text, nullable=True, comment="审批意见")
    
    # 实施信息
    implementation_started_at = Column(DateTime, nullable=True, comment="开始实施时间")
    implementation_completed_at = Column(DateTime, nullable=True, comment="完成实施时间")
    actual_catch_up_days = Column(Integer, nullable=True, comment="实际追回天数")
    actual_cost = Column(DECIMAL(12, 2), nullable=True, comment="实际成本")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联关系
    prediction = relationship("ProjectSchedulePrediction", back_populates="catch_up_solutions")
    
    # 索引
    __table_args__ = (
        Index("idx_project_status", "project_id", "status"),
        Index("idx_solution_type", "solution_type"),
    )

    def __repr__(self):
        return f"<CatchUpSolution(id={self.id}, project_id={self.project_id}, status={self.status})>"


class ScheduleAlert(Base):
    """进度预警记录表"""

    __tablename__ = "schedule_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True, comment="项目ID")
    prediction_id = Column(
        Integer,
        ForeignKey("project_schedule_prediction.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="关联的预测记录ID"
    )
    
    # 预警信息
    alert_type = Column(
        String(50),
        nullable=False,
        comment="预警类型: delay_warning/velocity_drop/milestone_risk/critical_path"
    )
    severity = Column(
        String(20),
        nullable=False,
        comment="严重程度: low/medium/high/critical"
    )
    title = Column(String(200), nullable=False, comment="预警标题")
    message = Column(Text, nullable=False, comment="预警消息")
    
    # 预警详情
    alert_details = Column(JSON, nullable=True, comment="预警详细信息")
    # alert_details 结构示例:
    # {
    #     "trigger_condition": "delay_days >= 15",
    #     "current_values": {
    #         "delay_days": 15,
    #         "progress_deviation": -14.5
    #     },
    #     "affected_milestones": [1, 3, 5],
    #     "recommended_actions": ["查看赶工方案", "联系项目经理"]
    # }
    
    # 通知信息
    notified_users = Column(JSON, nullable=True, comment="已通知用户列表")
    # notified_users 结构示例:
    # [
    #     {"user_id": 1, "role": "PM", "notified_at": "2026-02-15T10:00:00"},
    #     {"user_id": 2, "role": "department_head", "notified_at": "2026-02-15T10:01:00"}
    # ]
    
    notification_channels = Column(JSON, nullable=True, comment="通知渠道")
    # notification_channels 结构示例:
    # ["email", "sms", "system_message", "wechat"]
    
    # 预警状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    
    # 确认信息
    acknowledged_by = Column(Integer, nullable=True, comment="确认人ID")
    acknowledged_at = Column(DateTime, nullable=True, comment="确认时间")
    acknowledgement_comment = Column(Text, nullable=True, comment="确认备注")
    
    # 解决信息
    resolved_by = Column(Integer, nullable=True, comment="解决人ID")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")
    resolution_comment = Column(Text, nullable=True, comment="解决说明")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联关系
    prediction = relationship("ProjectSchedulePrediction", back_populates="alerts")
    
    # 索引
    __table_args__ = (
        Index("idx_project_severity", "project_id", "severity"),
        Index("idx_alert_type", "alert_type"),
        Index("idx_is_read", "is_read"),
        Index("idx_is_resolved", "is_resolved"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<ScheduleAlert(id={self.id}, project_id={self.project_id}, severity={self.severity})>"


# ──────────────────────────────────────────────
# 兼容性枚举（供测试和旧代码引用）
# ──────────────────────────────────────────────
import enum

class RiskLevelEnum(str, enum.Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SolutionTypeEnum(str, enum.Enum):
    """追赶方案类型"""
    OVERTIME = "OVERTIME"
    ADD_RESOURCE = "ADD_RESOURCE"
    SCOPE_REDUCTION = "SCOPE_REDUCTION"
    PROCESS_OPTIMIZATION = "PROCESS_OPTIMIZATION"

class AlertTypeEnum(str, enum.Enum):
    """预警类型"""
    SCHEDULE_DELAY = "SCHEDULE_DELAY"
    COST_OVERRUN = "COST_OVERRUN"
    RESOURCE_SHORTAGE = "RESOURCE_SHORTAGE"
    QUALITY_RISK = "QUALITY_RISK"

class SeverityEnum(str, enum.Enum):
    """严重程度"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
