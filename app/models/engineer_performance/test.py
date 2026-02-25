# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 测试工程师专属模型
"""

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


class TestBugRecord(Base, TimestampMixin):
    """测试Bug记录"""
    __tablename__ = 'test_bug_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    reporter_id = Column(Integer, ForeignKey('users.id'), comment='报告人ID')
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='处理人ID')

    # Bug信息
    bug_code = Column(String(50), comment='Bug编号')
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, comment='描述')
    severity = Column(String(20), comment='严重程度')
    bug_type = Column(String(30), comment='Bug类型')
    found_stage = Column(String(30), comment='发现阶段')

    # 处理信息
    status = Column(String(20), default='open', comment='状态')
    priority = Column(String(20), default='normal', comment='优先级')
    found_time = Column(DateTime, comment='发现时间')
    resolved_time = Column(DateTime, comment='解决时间')
    fix_duration_hours = Column(Numeric(6, 2), comment='修复时长(小时)')
    resolution = Column(Text, comment='解决方案')

    # 附件
    attachments = Column(JSON, comment='附件')

    # 关系
    reporter = relationship('User', foreign_keys=[reporter_id])
    assignee = relationship('User', foreign_keys=[assignee_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_test_bug_project', 'project_id'),
        Index('idx_test_bug_assignee', 'assignee_id'),
        Index('idx_test_bug_severity', 'severity'),
        Index('idx_test_bug_status', 'status'),
        {'comment': '测试Bug记录表'}
    )


class CodeReviewRecord(Base, TimestampMixin):
    """代码评审记录
    
    【状态】未启用 - 代码评审记录"""
    __tablename__ = 'code_review_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='作者ID')
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评审人ID')

    # 评审信息
    review_title = Column(String(200), comment='评审标题')
    code_module = Column(String(100), comment='代码模块')
    language = Column(String(30), comment='编程语言')
    lines_changed = Column(Integer, comment='修改行数')

    # 评审结果
    review_date = Column(Date, comment='评审日期')
    result = Column(String(20), comment='评审结果')
    is_first_pass = Column(Boolean, comment='是否一次通过')
    issues_found = Column(Integer, default=0, comment='发现问题数')
    comments = Column(Text, comment='评审意见')

    # 关系
    author = relationship('User', foreign_keys=[author_id])
    reviewer = relationship('User', foreign_keys=[reviewer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_code_review_project', 'project_id'),
        Index('idx_code_review_author', 'author_id'),
        Index('idx_code_review_reviewer', 'reviewer_id'),
        {'comment': '代码评审记录表'}
    )


class CodeModule(Base, TimestampMixin):
    """代码模块库"""
    __tablename__ = 'code_module'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contributor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='贡献者ID')

    # 模块信息
    module_name = Column(String(100), nullable=False, comment='模块名称')
    module_code = Column(String(50), comment='模块编号')
    category = Column(String(50), comment='分类')
    language = Column(String(30), comment='编程语言')
    description = Column(Text, comment='描述')

    # 版本信息
    version = Column(String(20), comment='版本')
    repository_url = Column(String(500), comment='仓库地址')

    # 复用统计
    reuse_count = Column(Integer, default=0, comment='复用次数')
    projects_used = Column(JSON, comment='使用项目列表')
    rating_score = Column(Numeric(3, 2), comment='平均评分')
    rating_count = Column(Integer, default=0, comment='评分次数')

    # 状态
    status = Column(String(20), default='active', comment='状态')

    # 关系
    contributor = relationship('User', foreign_keys=[contributor_id])

    __table_args__ = (
        Index('idx_code_module_contributor', 'contributor_id'),
        Index('idx_code_module_category', 'category'),
        Index('idx_code_module_language', 'language'),
        {'comment': '代码模块库表'}
    )
