# -*- coding: utf-8 -*-
"""
任职资格体系 ORM 模型
包含：任职资格等级、岗位能力模型、员工任职资格、评估记录
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from enum import Enum


# ==================== 枚举定义 ====================

class PositionTypeEnum(str, Enum):
    """岗位类型"""
    SALES = 'SALES'                    # 销售岗位
    ENGINEER = 'ENGINEER'              # 工程师岗位
    CUSTOMER_SERVICE = 'CUSTOMER_SERVICE'  # 客服岗位
    WORKER = 'WORKER'                  # 生产工人岗位


class EngineerSubtypeEnum(str, Enum):
    """工程师子类型"""
    ME = 'ME'          # 机械工程师
    EE = 'EE'          # 电气工程师
    SW = 'SW'          # 软件工程师
    TE = 'TE'          # 测试工程师


class QualificationStatusEnum(str, Enum):
    """任职资格状态"""
    PENDING = 'PENDING'        # 待认证
    APPROVED = 'APPROVED'      # 已认证
    EXPIRED = 'EXPIRED'        # 已过期
    REVOKED = 'REVOKED'       # 已撤销


class AssessmentTypeEnum(str, Enum):
    """评估类型"""
    INITIAL = 'INITIAL'        # 初始评估
    PROMOTION = 'PROMOTION'    # 晋升评估
    ANNUAL = 'ANNUAL'          # 年度评估
    REASSESSMENT = 'REASSESSMENT'  # 重新评估


class AssessmentResultEnum(str, Enum):
    """评估结果"""
    PASS = 'PASS'              # 通过
    FAIL = 'FAIL'              # 不通过
    PARTIAL = 'PARTIAL'        # 部分通过


# ==================== 任职资格等级 ====================

class QualificationLevel(Base, TimestampMixin):
    """任职资格等级定义表"""
    __tablename__ = 'qualification_level'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    level_code = Column(String(20), unique=True, nullable=False, comment='等级编码 (ASSISTANT/JUNIOR/MIDDLE/SENIOR/EXPERT)')
    level_name = Column(String(50), nullable=False, comment='等级名称 (助理级/初级/中级/高级/专家级)')
    level_order = Column(Integer, nullable=False, comment='排序顺序')
    role_type = Column(String(50), comment='适用角色类型 (SALES/ENGINEER/CUSTOMER_SERVICE/WORKER)')
    description = Column(Text, comment='等级描述')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 关系
    competency_models = relationship('PositionCompetencyModel', back_populates='level')
    employee_qualifications = relationship('EmployeeQualification', back_populates='level')

    __table_args__ = (
        Index('idx_qual_level_code', 'level_code'),
        Index('idx_qual_level_order', 'level_order'),
        Index('idx_qual_level_role_type', 'role_type'),
        {'comment': '任职资格等级表'}
    )

    def __repr__(self):
        return f"<QualificationLevel {self.level_code}: {self.level_name}>"


# ==================== 岗位能力模型 ====================

class PositionCompetencyModel(Base, TimestampMixin):
    """岗位能力模型表"""
    __tablename__ = 'position_competency_model'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    position_type = Column(String(50), nullable=False, comment='岗位类型')
    position_subtype = Column(String(50), comment='岗位子类型 (ME/EE/SW/TE等)')
    level_id = Column(Integer, ForeignKey('qualification_level.id'), nullable=False, comment='等级ID')
    
    # 能力维度要求 (JSON格式)
    # 结构示例:
    # {
    #   "technical_skills": {
    #     "name": "专业技能",
    #     "weight": 40,
    #     "items": [
    #       {"name": "设计能力", "description": "...", "score_range": [0, 100]},
    #       {"name": "编程能力", "description": "...", "score_range": [0, 100]}
    #     ]
    #   },
    #   "business_skills": {...},
    #   "communication_skills": {...},
    #   "learning_skills": {...},
    #   "project_management_skills": {...},  # 适用于工程师
    #   "customer_service_skills": {...}    # 适用于销售和客服
    # }
    competency_dimensions = Column(JSON, nullable=False, comment='能力维度要求 (JSON)')
    
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 关系
    level = relationship('QualificationLevel', back_populates='competency_models')

    __table_args__ = (
        Index('idx_comp_model_position', 'position_type', 'position_subtype'),
        Index('idx_comp_model_level', 'level_id'),
        Index('idx_comp_model_active', 'is_active'),
        {'comment': '岗位能力模型表'}
    )

    def __repr__(self):
        return f"<PositionCompetencyModel {self.position_type}-{self.position_subtype or ''} Level {self.level_id}>"


# ==================== 员工任职资格 ====================

class EmployeeQualification(Base, TimestampMixin):
    """员工任职资格记录表"""
    __tablename__ = 'employee_qualification'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    position_type = Column(String(50), nullable=False, comment='岗位类型')
    current_level_id = Column(Integer, ForeignKey('qualification_level.id'), nullable=False, comment='当前等级ID')
    
    # 认证信息
    certified_date = Column(Date, comment='认证日期')
    certifier_id = Column(Integer, ForeignKey('users.id'), comment='认证人ID')
    status = Column(String(20), default='PENDING', comment='认证状态')
    
    # 评估详情 (JSON格式)
    # 结构示例:
    # {
    #   "technical_skills": {"score": 85, "items": {...}},
    #   "business_skills": {"score": 80, "items": {...}},
    #   ...
    # }
    assessment_details = Column(JSON, comment='能力评估详情 (JSON)')
    
    # 有效期
    valid_until = Column(Date, comment='有效期至')

    # 关系
    employee = relationship('Employee', foreign_keys=[employee_id])
    level = relationship('QualificationLevel', back_populates='employee_qualifications')
    certifier = relationship('User', foreign_keys=[certifier_id])
    assessments = relationship('QualificationAssessment', back_populates='qualification')

    __table_args__ = (
        Index('idx_emp_qual_employee', 'employee_id'),
        Index('idx_emp_qual_level', 'current_level_id'),
        Index('idx_emp_qual_status', 'status'),
        Index('idx_emp_qual_position', 'position_type'),
        {'comment': '员工任职资格表'}
    )

    def __repr__(self):
        return f"<EmployeeQualification Employee {self.employee_id} Level {self.current_level_id}>"


# ==================== 任职资格评估记录 ====================

class QualificationAssessment(Base, TimestampMixin):
    """任职资格评估记录表"""
    __tablename__ = 'qualification_assessment'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    qualification_id = Column(Integer, ForeignKey('employee_qualification.id'), comment='任职资格ID')
    
    # 评估信息
    assessment_period = Column(String(20), comment='评估周期 (如: 2024-Q1)')
    assessment_type = Column(String(20), nullable=False, comment='评估类型')
    
    # 各维度得分 (JSON格式)
    # 结构示例:
    # {
    #   "technical_skills": 85,
    #   "business_skills": 80,
    #   "communication_skills": 75,
    #   "learning_skills": 90,
    #   "project_management_skills": 70
    # }
    scores = Column(JSON, comment='各维度得分 (JSON)')
    
    total_score = Column(Numeric(5, 2), comment='综合得分')
    result = Column(String(20), comment='评估结果')
    
    # 评估人信息
    assessor_id = Column(Integer, ForeignKey('users.id'), comment='评估人ID')
    comments = Column(Text, comment='评估意见')
    assessed_at = Column(DateTime, comment='评估时间')

    # 关系
    employee = relationship('Employee', foreign_keys=[employee_id])
    qualification = relationship('EmployeeQualification', back_populates='assessments')
    assessor = relationship('User', foreign_keys=[assessor_id])

    __table_args__ = (
        Index('idx_assess_employee', 'employee_id'),
        Index('idx_assess_qualification', 'qualification_id'),
        Index('idx_assess_period', 'assessment_period'),
        Index('idx_assess_type', 'assessment_type'),
        {'comment': '任职资格评估记录表'}
    )

    def __repr__(self):
        return f"<QualificationAssessment Employee {self.employee_id} Type {self.assessment_type}>"

