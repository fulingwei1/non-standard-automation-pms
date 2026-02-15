# -*- coding: utf-8 -*-
"""
项目风险管理模型
包含：风险类型、概率、影响、自动评分等功能
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Numeric,
    Index,
    Enum as SQLEnum,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class RiskTypeEnum(str, enum.Enum):
    """风险类型枚举"""
    TECHNICAL = "TECHNICAL"  # 技术风险
    COST = "COST"  # 成本风险
    SCHEDULE = "SCHEDULE"  # 进度风险
    QUALITY = "QUALITY"  # 质量风险


class RiskStatusEnum(str, enum.Enum):
    """风险状态枚举"""
    IDENTIFIED = "IDENTIFIED"  # 已识别
    ANALYZING = "ANALYZING"  # 分析中
    PLANNING = "PLANNING"  # 规划应对中
    MONITORING = "MONITORING"  # 监控中
    MITIGATED = "MITIGATED"  # 已缓解
    OCCURRED = "OCCURRED"  # 已发生
    CLOSED = "CLOSED"  # 已关闭


class ProjectRisk(Base, TimestampMixin):
    """项目风险表"""
    __tablename__ = 'project_risks'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 基本信息
    risk_code = Column(String(50), unique=True, nullable=False, comment='风险编号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    risk_name = Column(String(200), nullable=False, comment='风险名称')
    description = Column(Text, comment='风险描述')
    
    # 风险分类
    risk_type = Column(
        SQLEnum(RiskTypeEnum),
        nullable=False,
        comment='风险类型：TECHNICAL/COST/SCHEDULE/QUALITY'
    )
    
    # 风险评估（1-5评分）
    probability = Column(Integer, nullable=False, comment='发生概率（1-5）：1=很低，5=很高')
    impact = Column(Integer, nullable=False, comment='影响程度（1-5）：1=很低，5=很高')
    risk_score = Column(Integer, nullable=False, comment='风险评分（probability × impact）')
    
    # 风险等级（根据评分自动计算）
    # 1-4: 低风险, 5-9: 中风险, 10-15: 高风险, 16-25: 极高风险
    risk_level = Column(String(20), comment='风险等级：LOW/MEDIUM/HIGH/CRITICAL')
    
    # 应对措施
    mitigation_plan = Column(Text, comment='应对措施')
    contingency_plan = Column(Text, comment='应急计划')
    
    # 负责人
    owner_id = Column(Integer, ForeignKey('users.id'), comment='负责人ID')
    owner_name = Column(String(50), comment='负责人姓名')
    
    # 状态管理
    status = Column(
        SQLEnum(RiskStatusEnum),
        default=RiskStatusEnum.IDENTIFIED,
        nullable=False,
        comment='风险状态'
    )
    
    # 跟踪信息
    identified_date = Column(DateTime, default=datetime.now, comment='识别日期')
    target_closure_date = Column(DateTime, comment='计划关闭日期')
    actual_closure_date = Column(DateTime, comment='实际关闭日期')
    
    # 发生情况
    is_occurred = Column(Boolean, default=False, comment='是否已发生')
    occurrence_date = Column(DateTime, comment='发生日期')
    actual_impact = Column(Text, comment='实际影响描述')
    
    # 审计字段
    created_by_id = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    created_by_name = Column(String(50), comment='创建人姓名')
    updated_by_id = Column(Integer, ForeignKey('users.id'), comment='最后更新人ID')
    updated_by_name = Column(String(50), comment='最后更新人姓名')
    
    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    owner = relationship('User', foreign_keys=[owner_id])
    created_by = relationship('User', foreign_keys=[created_by_id])
    updated_by = relationship('User', foreign_keys=[updated_by_id])

    __table_args__ = (
        Index('idx_project_risk_code', 'risk_code'),
        Index('idx_project_risk_project_id', 'project_id'),
        Index('idx_project_risk_type', 'risk_type'),
        Index('idx_project_risk_status', 'status'),
        Index('idx_project_risk_level', 'risk_level'),
        Index('idx_project_risk_owner', 'owner_id'),
        {'comment': '项目风险表'}
    )

    def calculate_risk_score(self):
        """计算风险评分"""
        if self.probability and self.impact:
            self.risk_score = self.probability * self.impact
            # 自动计算风险等级
            if self.risk_score <= 4:
                self.risk_level = "LOW"
            elif self.risk_score <= 9:
                self.risk_level = "MEDIUM"
            elif self.risk_score <= 15:
                self.risk_level = "HIGH"
            else:
                self.risk_level = "CRITICAL"

    def __repr__(self):
        return f"<ProjectRisk {self.risk_code}: {self.risk_name}>"
