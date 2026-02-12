# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 通用模型
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
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

from app.models.base import Base, TimestampMixin


class EngineerProfile(Base, TimestampMixin):
    """工程师档案 - 扩展用户信息"""
    __tablename__ = 'engineer_profile'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, comment='关联用户ID')

    # 岗位信息
    job_type = Column(String(20), nullable=False, comment='岗位类型')
    job_level = Column(String(20), default='junior', comment='职级')

    # 技能标签
    skills = Column(JSON, comment='技能标签')
    certifications = Column(JSON, comment='资质证书')

    # 时间信息
    job_start_date = Column(Date, comment='当前岗位开始日期')
    level_start_date = Column(Date, comment='当前级别开始日期')

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='engineer_profile')

    __table_args__ = (
        Index('idx_engineer_profile_job_type', 'job_type'),
        Index('idx_engineer_profile_job_level', 'job_level'),
        {'comment': '工程师档案表'}
    )


class EngineerDimensionConfig(Base, TimestampMixin):
    """五维权重配置（只能按岗位+级别配置，不能针对个人）"""
    __tablename__ = 'engineer_dimension_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 配置维度
    job_type = Column(String(20), nullable=False, comment='岗位类型')
    job_level = Column(String(20), comment='职级（为空表示适用所有级别）')

    # 配置范围（新增）
    department_id = Column(Integer, comment='部门ID（为空表示全局配置）')
    is_global = Column(Boolean, default=True, comment='是否全局配置（True=全局，False=部门级别）')

    # 五维权重（百分比，总和100）
    technical_weight = Column(Integer, default=30, comment='技术能力权重')
    execution_weight = Column(Integer, default=25, comment='项目执行权重')
    cost_quality_weight = Column(Integer, default=20, comment='成本/质量权重')
    knowledge_weight = Column(Integer, default=15, comment='知识沉淀权重')
    collaboration_weight = Column(Integer, default=10, comment='团队协作权重')

    # 生效时间
    effective_date = Column(Date, nullable=False, comment='生效日期')
    expired_date = Column(Date, comment='失效日期')

    # 配置信息
    config_name = Column(String(100), comment='配置名称')
    description = Column(Text, comment='配置说明')
    operator_id = Column(Integer, ForeignKey('users.id'), comment='操作人ID')

    # 审批状态（部门级别配置需要审批）
    approval_status = Column(String(20), default='APPROVED', comment='审批状态（PENDING/APPROVED/REJECTED）')
    approval_reason = Column(Text, comment='审批理由')

    __table_args__ = (
        Index('idx_dimension_config_job_type', 'job_type'),
        Index('idx_dimension_config_effective', 'effective_date'),
        Index('idx_dimension_config_dept', 'department_id'),
        Index('idx_dimension_config_global', 'is_global'),
        {'comment': '五维权重配置表'}
    )


class CollaborationRating(Base, TimestampMixin):
    """跨部门协作评价"""
    __tablename__ = 'collaboration_rating'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), nullable=False, comment='考核周期ID')

    # 评价双方
    rater_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评价人ID')
    ratee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='被评价人ID')
    rater_job_type = Column(String(20), comment='评价人岗位类型')
    ratee_job_type = Column(String(20), comment='被评价人岗位类型')

    # 四维评分（1-5分）
    communication_score = Column(Integer, comment='沟通配合')
    response_score = Column(Integer, comment='响应速度')
    delivery_score = Column(Integer, comment='交付质量')
    interface_score = Column(Integer, comment='接口规范')

    # 总分
    total_score = Column(Numeric(4, 2), comment='总分')

    # 评价备注
    comment = Column(Text, comment='评价备注')

    # 项目关联
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')

    # 关系
    rater = relationship('User', foreign_keys=[rater_id])
    ratee = relationship('User', foreign_keys=[ratee_id])
    period = relationship('PerformancePeriod', foreign_keys=[period_id])

    __table_args__ = (
        Index('idx_collab_rating_period', 'period_id'),
        Index('idx_collab_rating_rater', 'rater_id'),
        Index('idx_collab_rating_ratee', 'ratee_id'),
        {'comment': '跨部门协作评价表'}
    )


class KnowledgeContribution(Base, TimestampMixin):
    """知识贡献记录"""
    __tablename__ = 'knowledge_contribution'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contributor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='贡献者ID')

    # 贡献类型
    contribution_type = Column(String(30), nullable=False, comment='贡献类型')
    job_type = Column(String(20), comment='所属岗位领域')

    # 贡献内容
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, comment='描述')
    file_path = Column(String(500), comment='文件路径')
    tags = Column(JSON, comment='标签')

    # 复用统计
    reuse_count = Column(Integer, default=0, comment='复用次数')
    rating_score = Column(Numeric(3, 2), comment='平均评分')
    rating_count = Column(Integer, default=0, comment='评分次数')

    # 审核状态
    status = Column(String(20), default='draft', comment='状态')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    approved_at = Column(DateTime, comment='审核时间')

    # 关系
    contributor = relationship('User', foreign_keys=[contributor_id])

    __table_args__ = (
        Index('idx_knowledge_contrib_user', 'contributor_id'),
        Index('idx_knowledge_contrib_type', 'contribution_type'),
        Index('idx_knowledge_contrib_status', 'status'),
        {'comment': '知识贡献记录表'}
    )


class KnowledgeReuseLog(Base):
    """知识复用记录"""
    __tablename__ = 'knowledge_reuse_log'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contribution_id = Column(Integer, ForeignKey('knowledge_contribution.id'), nullable=False, comment='贡献ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='使用者ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')

    # 复用信息
    reuse_type = Column(String(30), comment='复用类型')
    rating = Column(Integer, comment='评分')
    feedback = Column(Text, comment='反馈')

    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 关系
    contribution = relationship('KnowledgeContribution', foreign_keys=[contribution_id])
    user = relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_knowledge_reuse_contrib', 'contribution_id'),
        Index('idx_knowledge_reuse_user', 'user_id'),
        {'comment': '知识复用记录表'}
    )
