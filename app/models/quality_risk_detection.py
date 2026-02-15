# -*- coding: utf-8 -*-
"""
质量风险检测模型
通过AI分析工作日志和项目数据，提前识别质量风险
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Numeric,
    Index,
    Date,
    DateTime,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


# ==================== 枚举定义 ====================

class RiskLevelEnum(str, Enum):
    """风险等级"""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class RiskSourceEnum(str, Enum):
    """数据来源类型"""
    WORK_LOG = 'WORK_LOG'      # 工作日志
    PROGRESS = 'PROGRESS'       # 项目进度
    MANUAL = 'MANUAL'           # 手动创建


class RiskStatusEnum(str, Enum):
    """风险状态"""
    DETECTED = 'DETECTED'           # 已检测
    CONFIRMED = 'CONFIRMED'         # 已确认
    FALSE_POSITIVE = 'FALSE_POSITIVE'  # 误报
    RESOLVED = 'RESOLVED'           # 已解决


class RiskCategoryEnum(str, Enum):
    """风险类别"""
    BUG = 'BUG'                    # 缺陷
    PERFORMANCE = 'PERFORMANCE'    # 性能
    STABILITY = 'STABILITY'        # 稳定性
    COMPATIBILITY = 'COMPATIBILITY'  # 兼容性


class TestRecommendationStatusEnum(str, Enum):
    """测试推荐状态"""
    PENDING = 'PENDING'           # 待处理
    ACCEPTED = 'ACCEPTED'         # 已接受
    IN_PROGRESS = 'IN_PROGRESS'   # 进行中
    COMPLETED = 'COMPLETED'       # 已完成
    REJECTED = 'REJECTED'         # 已拒绝


class TestPriorityEnum(str, Enum):
    """测试优先级"""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    URGENT = 'URGENT'


# ==================== 质量风险检测表 ====================

class QualityRiskDetection(Base, TimestampMixin):
    """质量风险检测记录"""
    __tablename__ = 'quality_risk_detection'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    module_name = Column(String(200), comment='模块名称')
    task_id = Column(Integer, ForeignKey('tasks.id'), comment='任务ID')
    detection_date = Column(Date, nullable=False, comment='检测日期')

    # 数据来源
    source_type = Column(String(50), nullable=False, comment='数据来源类型')
    source_id = Column(Integer, comment='来源记录ID')

    # 风险信号
    risk_signals = Column(JSON, comment='检测到的风险信号列表')
    risk_keywords = Column(JSON, comment='触发的关键词列表')
    abnormal_patterns = Column(JSON, comment='异常模式描述')

    # 质量风险评估
    risk_level = Column(String(20), nullable=False, comment='风险等级')
    risk_score = Column(Numeric(5, 2), nullable=False, comment='风险评分 (0-100)')
    risk_category = Column(String(50), comment='风险类别')

    # 问题预测
    predicted_issues = Column(JSON, comment='预测可能出现的问题')
    rework_probability = Column(Numeric(5, 2), comment='返工概率 (0-100)')
    estimated_impact_days = Column(Integer, comment='预估影响天数')

    # AI分析结果
    ai_analysis = Column(JSON, comment='AI详细分析结果')
    ai_confidence = Column(Numeric(5, 2), comment='AI置信度 (0-100)')
    analysis_model = Column(String(50), comment='使用的AI模型')

    # 状态管理
    status = Column(String(20), nullable=False, default='DETECTED', comment='状态')
    confirmed_by = Column(Integer, ForeignKey('users.id'), comment='确认人ID')
    confirmed_at = Column(DateTime, comment='确认时间')
    resolution_note = Column(Text, comment='处理说明')

    # 审计字段
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    task = relationship('Task', foreign_keys=[task_id])
    confirmer = relationship('User', foreign_keys=[confirmed_by])
    creator = relationship('User', foreign_keys=[created_by])
    
    # 反向关系：关联的测试推荐
    test_recommendations = relationship(
        'QualityTestRecommendation',
        back_populates='detection',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        Index('idx_qrd_project', 'project_id'),
        Index('idx_qrd_detection_date', 'detection_date'),
        Index('idx_qrd_risk_level', 'risk_level'),
        Index('idx_qrd_status', 'status'),
        Index('idx_qrd_source', 'source_type', 'source_id'),
        Index('idx_qrd_module', 'project_id', 'module_name'),
        {'comment': '质量风险检测表'}
    )

    def __repr__(self):
        return f"<QualityRiskDetection project_id={self.project_id} risk_level={self.risk_level}>"


# ==================== 质量测试推荐表 ====================

class QualityTestRecommendation(Base, TimestampMixin):
    """质量测试推荐记录"""
    __tablename__ = 'quality_test_recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    detection_id = Column(Integer, ForeignKey('quality_risk_detection.id'), comment='关联的风险检测ID')
    recommendation_date = Column(Date, nullable=False, comment='推荐日期')

    # 测试重点区域
    focus_areas = Column(JSON, nullable=False, comment='测试重点区域列表')
    priority_modules = Column(JSON, comment='优先测试模块')
    risk_modules = Column(JSON, comment='高风险模块列表')

    # 测试建议
    test_types = Column(JSON, comment='推荐的测试类型')
    test_scenarios = Column(JSON, comment='测试场景建议')
    test_coverage_target = Column(Numeric(5, 2), comment='目标测试覆盖率 (0-100)')

    # 资源分配建议
    recommended_testers = Column(Integer, comment='推荐测试人员数')
    recommended_days = Column(Integer, comment='推荐测试天数')
    priority_level = Column(String(20), nullable=False, comment='优先级')

    # AI推荐理由
    ai_reasoning = Column(Text, comment='AI推荐理由')
    risk_summary = Column(Text, comment='风险汇总说明')
    historical_data = Column(JSON, comment='参考的历史数据')

    # 测试计划生成
    test_plan_generated = Column(Boolean, nullable=False, default=False, comment='是否已生成测试计划')
    test_plan_id = Column(Integer, comment='关联的测试计划ID')

    # 执行状态
    status = Column(String(20), nullable=False, default='PENDING', comment='状态')
    acceptance_note = Column(Text, comment='接受/拒绝说明')
    actual_test_days = Column(Integer, comment='实际测试天数')
    actual_coverage = Column(Numeric(5, 2), comment='实际测试覆盖率')

    # 效果评估
    bugs_found = Column(Integer, comment='发现的BUG数量')
    critical_bugs_found = Column(Integer, comment='发现的严重BUG数量')
    recommendation_accuracy = Column(Numeric(5, 2), comment='推荐准确度评分 (0-100)')

    # 审计字段
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    detection = relationship('QualityRiskDetection', back_populates='test_recommendations')
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_qtr_project', 'project_id'),
        Index('idx_qtr_recommendation_date', 'recommendation_date'),
        Index('idx_qtr_priority', 'priority_level'),
        Index('idx_qtr_status', 'status'),
        Index('idx_qtr_detection', 'detection_id'),
        {'comment': '质量测试推荐表'}
    )

    def __repr__(self):
        return f"<QualityTestRecommendation project_id={self.project_id} priority={self.priority_level}>"
