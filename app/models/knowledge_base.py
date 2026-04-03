# -*- coding: utf-8 -*-
"""
知识自动沉淀模块 - 数据模型
项目结项时自动提取经验教训、最佳实践，支持坑点预警和知识检索
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


# ── 枚举 ──────────────────────────────────────────────


class KnowledgeSourceEnum(str, enum.Enum):
    """知识来源"""

    RISK = "RISK"  # 风险记录
    ISSUE = "ISSUE"  # 问题记录
    ECN = "ECN"  # 变更单
    LOG = "LOG"  # 进度日志
    REVIEW = "REVIEW"  # 复盘报告
    MANUAL = "MANUAL"  # 人工录入


class KnowledgeTypeEnum(str, enum.Enum):
    """知识类型"""

    RISK_RESPONSE = "RISK_RESPONSE"  # 已发生风险 + 应对措施
    ISSUE_SOLUTION = "ISSUE_SOLUTION"  # 典型问题 + 解决方案
    CHANGE_PATTERN = "CHANGE_PATTERN"  # 高频变更类型 + 原因分析
    DELAY_CAUSE = "DELAY_CAUSE"  # 关键节点延误原因
    BEST_PRACTICE = "BEST_PRACTICE"  # 最佳实践
    PITFALL = "PITFALL"  # 坑点/陷阱


class KnowledgeStatusEnum(str, enum.Enum):
    """知识条目状态"""

    DRAFT = "DRAFT"  # 草稿（自动提取，待审核）
    PUBLISHED = "PUBLISHED"  # 已发布
    ARCHIVED = "ARCHIVED"  # 已归档


# ── 主表 ──────────────────────────────────────────────


class KnowledgeEntry(Base, TimestampMixin):
    """知识库条目表 — 所有沉淀知识的统一存储"""

    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    entry_code = Column(String(50), unique=True, nullable=False, comment="知识编号，如 KE-20260327-001")

    # 分类
    knowledge_type = Column(
        SQLEnum(KnowledgeTypeEnum), nullable=False, comment="知识类型"
    )
    source_type = Column(
        SQLEnum(KnowledgeSourceEnum), nullable=False, comment="来源类型"
    )

    # 内容
    title = Column(String(300), nullable=False, comment="标题")
    summary = Column(Text, nullable=False, comment="摘要/简述")
    detail = Column(Text, comment="详细内容（Markdown）")

    # 问题 → 方案
    problem_description = Column(Text, comment="问题描述/风险描述/变更原因")
    solution = Column(Text, comment="解决方案/应对措施/改进方法")
    root_cause = Column(Text, comment="根因分析")
    impact = Column(Text, comment="影响范围/影响程度")
    prevention = Column(Text, comment="预防措施")

    # 来源追溯
    source_project_id = Column(Integer, ForeignKey("projects.id"), comment="来源项目ID")
    source_record_id = Column(Integer, comment="来源记录ID（risk_id / issue_id / ecn_id …）")
    source_record_type = Column(String(30), comment="来源记录表名，如 project_risks / issues / ecn")

    # 适用范围
    project_type = Column(String(50), comment="适用项目类型")
    product_category = Column(String(50), comment="适用产品类别")
    industry = Column(String(50), comment="适用行业")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="关联客户ID")
    applicable_stages = Column(JSON, comment="适用阶段列表 [\"S1\",\"S2\"...]")

    # 标签与检索
    tags = Column(JSON, comment="标签列表")
    risk_type = Column(String(30), comment="风险类型（复用 RiskTypeEnum 值）")
    issue_category = Column(String(30), comment="问题分类（复用 IssueCategoryEnum 值）")
    change_type = Column(String(30), comment="变更类型（复用 ecn_type）")

    # 统计
    view_count = Column(Integer, default=0, comment="查看次数")
    cite_count = Column(Integer, default=0, comment="引用次数")
    usefulness_score = Column(Float, default=0.0, comment="有用性评分 0-5")
    vote_count = Column(Integer, default=0, comment="投票数")

    # 状态
    status = Column(
        SQLEnum(KnowledgeStatusEnum),
        default=KnowledgeStatusEnum.DRAFT,
        nullable=False,
        comment="状态",
    )

    # AI
    ai_generated = Column(Boolean, default=False, comment="是否AI自动提取")
    ai_confidence = Column(Numeric(5, 4), comment="AI置信度 0-1")

    # 审核
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(DateTime, comment="审核时间")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # ── 关系 ──
    source_project = relationship("Project", foreign_keys=[source_project_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])
    alerts = relationship("KnowledgeAlert", back_populates="knowledge_entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ke_code", "entry_code"),
        Index("idx_ke_type", "knowledge_type"),
        Index("idx_ke_source_type", "source_type"),
        Index("idx_ke_source_project", "source_project_id"),
        Index("idx_ke_project_type", "project_type"),
        Index("idx_ke_product_category", "product_category"),
        Index("idx_ke_industry", "industry"),
        Index("idx_ke_customer", "customer_id"),
        Index("idx_ke_status", "status"),
        Index("idx_ke_risk_type", "risk_type"),
        Index("idx_ke_issue_category", "issue_category"),
        Index("idx_ke_change_type", "change_type"),
        {"comment": "知识库条目表"},
    )

    def __repr__(self):
        return f"<KnowledgeEntry {self.entry_code}: {self.title}>"


# ── 坑点预警记录表 ─────────────────────────────────────


class KnowledgeAlert(Base, TimestampMixin):
    """知识预警推送记录 — 新项目创建时自动推送的坑点/风险"""

    __tablename__ = "knowledge_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 目标项目
    target_project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="目标项目ID")

    # 关联知识
    knowledge_entry_id = Column(
        Integer, ForeignKey("knowledge_entries.id"), nullable=False, comment="知识条目ID"
    )

    # 匹配信息
    match_reason = Column(String(200), comment="匹配原因，如：同类产品/同客户/同行业")
    match_score = Column(Float, default=0.0, comment="匹配度评分 0-1")

    # 状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_adopted = Column(Boolean, comment="是否采纳（用户反馈）")
    feedback = Column(Text, comment="用户反馈")

    # ── 关系 ──
    target_project = relationship("Project", foreign_keys=[target_project_id])
    knowledge_entry = relationship("KnowledgeEntry", back_populates="alerts")

    __table_args__ = (
        Index("idx_ka_target_project", "target_project_id"),
        Index("idx_ka_knowledge_entry", "knowledge_entry_id"),
        Index("idx_ka_is_read", "is_read"),
        {"comment": "知识预警推送记录表"},
    )

    def __repr__(self):
        return f"<KnowledgeAlert project={self.target_project_id} entry={self.knowledge_entry_id}>"
