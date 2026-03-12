# -*- coding: utf-8 -*-
"""
成本对标模型

支持历史项目对标分析，帮助评估新项目成本的合理性
"""

from datetime import datetime
from enum import Enum

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

from app.models.base import Base, TimestampMixin


class SimilarityLevelEnum(str, Enum):
    """相似度级别枚举"""

    HIGH = "HIGH"  # 高度相似 (80%+)
    MEDIUM = "MEDIUM"  # 中度相似 (50-80%)
    LOW = "LOW"  # 低度相似 (30-50%)
    MINIMAL = "MINIMAL"  # 相似度较低 (<30%)


class ProjectCostBenchmark(Base, TimestampMixin):
    """
    项目成本对标记录

    记录当前项目与历史相似项目的成本对比分析
    """

    __tablename__ = "project_cost_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 当前项目
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="当前项目ID")

    # 对标项目
    benchmark_project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="对标项目ID"
    )

    # 相似度评分
    similarity_score = Column(Numeric(5, 2), default=0, comment="综合相似度评分(0-100)")
    similarity_level = Column(String(20), comment="相似度级别")

    # 相似度分项评分
    industry_score = Column(Numeric(5, 2), default=0, comment="行业相似度(0-100)")
    test_type_score = Column(Numeric(5, 2), default=0, comment="测试类型相似度(0-100)")
    scale_score = Column(Numeric(5, 2), default=0, comment="规模相似度(0-100)")
    complexity_score = Column(Numeric(5, 2), default=0, comment="复杂度相似度(0-100)")
    customer_score = Column(Numeric(5, 2), default=0, comment="客户类型相似度(0-100)")

    # 成本对比
    current_estimated_cost = Column(Numeric(14, 2), comment="当前项目预估成本")
    benchmark_actual_cost = Column(Numeric(14, 2), comment="对标项目实际成本")
    cost_variance = Column(Numeric(14, 2), comment="成本差异")
    cost_variance_ratio = Column(Numeric(5, 2), comment="成本差异率(%)")

    # 分类成本对比 (JSON)
    # {
    #   "MECHANICAL": {"current": 50000, "benchmark": 48000, "variance": 2000, "ratio": 4.17},
    #   "ELECTRICAL": {"current": 40000, "benchmark": 42000, "variance": -2000, "ratio": -4.76},
    #   ...
    # }
    category_comparison = Column(JSON, comment="分类成本对比（JSON格式）")

    # 工时对比
    current_estimated_hours = Column(Numeric(10, 2), comment="当前项目预估工时")
    benchmark_actual_hours = Column(Numeric(10, 2), comment="对标项目实际工时")
    hours_variance = Column(Numeric(10, 2), comment="工时差异")
    hours_variance_ratio = Column(Numeric(5, 2), comment="工时差异率(%)")

    # 差异分析
    variance_analysis = Column(Text, comment="差异分析说明")
    risk_factors = Column(JSON, comment="风险因素（JSON格式）")
    recommendations = Column(JSON, comment="建议措施（JSON格式）")

    # 分析状态
    is_primary = Column(Boolean, default=False, comment="是否主要对标项目")
    analyzed_at = Column(DateTime, default=datetime.now, comment="分析时间")
    analyzed_by = Column(Integer, ForeignKey("users.id"), comment="分析人ID")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    benchmark_project = relationship("Project", foreign_keys=[benchmark_project_id])
    analyzer = relationship("User", foreign_keys=[analyzed_by])

    __table_args__ = (
        Index("idx_benchmark_project", "project_id"),
        Index("idx_benchmark_benchmark_project", "benchmark_project_id"),
        Index("idx_benchmark_similarity", "similarity_score"),
        Index("idx_benchmark_unique", "project_id", "benchmark_project_id", unique=True),
        {"comment": "项目成本对标记录表"},
    )

    def __repr__(self):
        return f"<ProjectCostBenchmark {self.project_id} vs {self.benchmark_project_id}>"


class BenchmarkConfiguration(Base, TimestampMixin):
    """
    对标配置

    配置相似度计算的权重和阈值
    """

    __tablename__ = "benchmark_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 配置名称
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")

    # 相似度权重配置 (总和应为1.0)
    industry_weight = Column(Numeric(3, 2), default=0.25, comment="行业权重")
    test_type_weight = Column(Numeric(3, 2), default=0.25, comment="测试类型权重")
    scale_weight = Column(Numeric(3, 2), default=0.20, comment="规模权重")
    complexity_weight = Column(Numeric(3, 2), default=0.20, comment="复杂度权重")
    customer_weight = Column(Numeric(3, 2), default=0.10, comment="客户类型权重")

    # 相似度阈值
    high_threshold = Column(Numeric(5, 2), default=80, comment="高相似度阈值")
    medium_threshold = Column(Numeric(5, 2), default=50, comment="中相似度阈值")
    low_threshold = Column(Numeric(5, 2), default=30, comment="低相似度阈值")

    # 对标数量配置
    max_benchmarks = Column(Integer, default=5, comment="最大对标项目数")
    min_similarity = Column(Numeric(5, 2), default=30, comment="最小相似度要求")

    # 预警配置
    cost_variance_warning = Column(Numeric(5, 2), default=10, comment="成本差异预警阈值(%)")
    cost_variance_alert = Column(Numeric(5, 2), default=20, comment="成本差异警报阈值(%)")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否默认配置")

    # 审计
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    __table_args__ = (
        Index("idx_benchmark_config_active", "is_active"),
        Index("idx_benchmark_config_default", "is_default"),
        {"comment": "对标配置表"},
    )

    def __repr__(self):
        return f"<BenchmarkConfiguration {self.name}>"
