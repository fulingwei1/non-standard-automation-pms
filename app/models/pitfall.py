# -*- coding: utf-8 -*-
"""
踩坑库 ORM 模型
包含：踩坑记录、推荐记录、学习进度
"""


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
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Pitfall(Base, TimestampMixin):
    """踩坑记录表"""

    __tablename__ = "pitfalls"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    pitfall_no = Column(String(50), unique=True, nullable=False, comment="踩坑编号")

    # === 必填字段（降低录入门槛）===
    title = Column(String(200), nullable=False, comment="标题")
    description = Column(Text, nullable=False, comment="问题描述")
    solution = Column(Text, comment="解决方案")

    # === 多维度分类 ===
    stage = Column(String(20), comment="阶段：S1-S9")
    equipment_type = Column(String(50), comment="设备类型")
    problem_type = Column(String(50), comment="问题类型")
    tags = Column(JSON, comment="标签列表")

    # === 选填字段（逐步完善）===
    root_cause = Column(Text, comment="根因分析")
    impact = Column(Text, comment="影响范围")
    prevention = Column(Text, comment="预防措施")
    cost_impact = Column(Numeric(12, 2), comment="成本影响（元）")
    schedule_impact = Column(Integer, comment="工期影响（天）")

    # === 来源追溯 ===
    source_type = Column(String(20), comment="来源类型")
    source_project_id = Column(Integer, ForeignKey("projects.id"), comment="来源项目ID")
    source_ecn_id = Column(Integer, comment="关联ECN ID")
    source_issue_id = Column(Integer, comment="关联Issue ID")

    # === 权限与状态 ===
    is_sensitive = Column(Boolean, default=False, comment="是否敏感")
    sensitive_reason = Column(String(50), comment="敏感原因")
    visible_to = Column(JSON, comment="可见范围（敏感记录）")
    status = Column(String(20), default="DRAFT", comment="状态")
    verified = Column(Boolean, default=False, comment="是否已验证")
    verify_count = Column(Integer, default=0, comment="验证次数")

    # === 创建人 ===
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # === 关系 ===
    source_project = relationship("Project", foreign_keys=[source_project_id])
    creator = relationship("User", foreign_keys=[created_by])
    recommendations = relationship("PitfallRecommendation", back_populates="pitfall")
    learning_progress = relationship(
        "PitfallLearningProgress", back_populates="pitfall"
    )

    __table_args__ = (
        Index("idx_pitfall_stage", "stage"),
        Index("idx_pitfall_equipment", "equipment_type"),
        Index("idx_pitfall_problem", "problem_type"),
        Index("idx_pitfall_status", "status"),
        Index("idx_pitfall_project", "source_project_id"),
        Index("idx_pitfall_created_by", "created_by"),
        {"comment": "踩坑记录表"},
    )

    def __repr__(self):
        return f"<Pitfall {self.pitfall_no}: {self.title}>"


class PitfallRecommendation(Base, TimestampMixin):
    """踩坑推荐记录表"""

    __tablename__ = "pitfall_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    pitfall_id = Column(
        Integer, ForeignKey("pitfalls.id"), nullable=False, comment="踩坑ID"
    )
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )

    trigger_type = Column(String(20), nullable=False, comment="触发类型")
    trigger_context = Column(JSON, comment="触发上下文")

    is_helpful = Column(Boolean, comment="是否有帮助")
    feedback = Column(Text, comment="反馈详情")

    # === 关系 ===
    pitfall = relationship("Pitfall", back_populates="recommendations")
    project = relationship("Project")

    __table_args__ = (
        Index("idx_pitfall_rec_project", "project_id"),
        Index("idx_pitfall_rec_pitfall", "pitfall_id"),
        {"comment": "踩坑推荐记录表"},
    )

    def __repr__(self):
        return f"<PitfallRecommendation pitfall={self.pitfall_id} project={self.project_id}>"


class PitfallLearningProgress(Base, TimestampMixin):
    """踩坑学习进度表"""

    __tablename__ = "pitfall_learning_progress"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    pitfall_id = Column(
        Integer, ForeignKey("pitfalls.id"), nullable=False, comment="踩坑ID"
    )

    read_at = Column(DateTime, comment="阅读时间")
    is_marked = Column(Boolean, default=False, comment="是否标记已掌握")
    notes = Column(Text, comment="学习笔记")

    # === 关系 ===
    user = relationship("User")
    pitfall = relationship("Pitfall", back_populates="learning_progress")

    __table_args__ = (
        Index("idx_pitfall_learn_user", "user_id"),
        Index("idx_pitfall_learn_pitfall", "pitfall_id"),
        {"comment": "踩坑学习进度表"},
    )

    def __repr__(self):
        return (
            f"<PitfallLearningProgress user={self.user_id} pitfall={self.pitfall_id}>"
        )
