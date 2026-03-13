# -*- coding: utf-8 -*-
"""
技术评估模板与工作流模型

包含：
- AssessmentTemplate: 评估模板（五维评分模板）
- AssessmentItem: 评估项（模板中的具体评分项）
- AssessmentRisk: 评估风险记录（评估过程中识别的风险）
- AssessmentVersion: 评估版本（支持评估历史追溯）
"""

from datetime import datetime
from enum import Enum
from typing import Optional

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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


# ==================== 枚举定义 ====================


class TemplateCategoryEnum(str, Enum):
    """模板类别"""

    STANDARD = "STANDARD"  # 标准设备
    CUSTOM = "CUSTOM"  # 定制设备
    RETROFIT = "RETROFIT"  # 改造项目
    SOFTWARE = "SOFTWARE"  # 软件项目
    SERVICE = "SERVICE"  # 服务项目


class AssessmentDimensionEnum(str, Enum):
    """评估维度（五维评分）"""

    TECHNICAL = "TECHNICAL"  # 技术可行性
    COMMERCIAL = "COMMERCIAL"  # 商业价值
    RESOURCE = "RESOURCE"  # 资源匹配
    RISK = "RISK"  # 风险水平
    TIMELINE = "TIMELINE"  # 交付周期


class RiskLevelEnum(str, Enum):
    """风险等级"""

    LOW = "LOW"  # 低
    MEDIUM = "MEDIUM"  # 中
    HIGH = "HIGH"  # 高
    CRITICAL = "CRITICAL"  # 严重


class RiskStatusEnum(str, Enum):
    """风险状态"""

    OPEN = "OPEN"  # 开放
    MITIGATING = "MITIGATING"  # 缓解中
    RESOLVED = "RESOLVED"  # 已解决
    ACCEPTED = "ACCEPTED"  # 已接受
    ESCALATED = "ESCALATED"  # 已升级


# ==================== 评估模板 ====================


class AssessmentTemplate(Base, TimestampMixin):
    """评估模板

    定义五维评分体系的具体评分项和权重配置。
    不同类型的项目（标准/定制/改造等）可以使用不同的模板。
    """

    __tablename__ = "assessment_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    category = Column(
        String(20),
        default=TemplateCategoryEnum.STANDARD,
        comment="模板类别"
    )
    description = Column(Text, comment="模板描述")

    # 五维权重配置
    dimension_weights = Column(JSON, comment="维度权重配置(JSON)")

    # 一票否决规则配置
    veto_rules = Column(JSON, comment="一票否决规则(JSON)")

    # 评分阈值配置
    score_thresholds = Column(JSON, comment="评分阈值配置(JSON)")

    # 版本控制
    version = Column(String(20), default="V1.0", comment="模板版本")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认模板")

    # 审核信息
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    items = relationship(
        "AssessmentItem",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("idx_assessment_template_code", "template_code"),
        Index("idx_assessment_template_category", "category"),
        Index("idx_assessment_template_active", "is_active"),
        {"comment": "技术评估模板表"},
    )

    def __repr__(self):
        return f"<AssessmentTemplate {self.template_code}>"

    @staticmethod
    def get_default_weights():
        """获取默认五维权重"""
        return {
            AssessmentDimensionEnum.TECHNICAL.value: 30,
            AssessmentDimensionEnum.COMMERCIAL.value: 25,
            AssessmentDimensionEnum.RESOURCE.value: 15,
            AssessmentDimensionEnum.RISK.value: 20,
            AssessmentDimensionEnum.TIMELINE.value: 10,
        }


class AssessmentItem(Base, TimestampMixin):
    """评估项

    模板中的具体评分项，包含评分标准和权重。
    """

    __tablename__ = "assessment_items"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_id = Column(
        Integer,
        ForeignKey("assessment_templates.id"),
        nullable=False,
        comment="模板ID"
    )

    # 评估项信息
    item_code = Column(String(50), nullable=False, comment="评估项编码")
    item_name = Column(String(200), nullable=False, comment="评估项名称")
    dimension = Column(
        String(20),
        nullable=False,
        comment="所属维度"
    )
    description = Column(Text, comment="评估项描述")

    # 评分配置
    max_score = Column(Integer, default=10, comment="满分")
    weight = Column(Numeric(5, 2), default=1.0, comment="权重")

    # 评分标准（JSON数组，描述各分数段的标准）
    scoring_criteria = Column(JSON, comment="评分标准(JSON)")

    # 是否为否决项
    is_veto_item = Column(Boolean, default=False, comment="是否为一票否决项")
    veto_threshold = Column(Integer, comment="否决阈值（低于此分数触发否决）")

    # 是否必填
    is_required = Column(Boolean, default=True, comment="是否必填")

    # 排序
    sort_order = Column(Integer, default=0, comment="排序顺序")

    # 关系
    template = relationship("AssessmentTemplate", back_populates="items")

    __table_args__ = (
        Index("idx_assessment_item_template", "template_id"),
        Index("idx_assessment_item_dimension", "dimension"),
        UniqueConstraint("template_id", "item_code", name="uq_assessment_item_code"),
        {"comment": "评估项表"},
    )

    def __repr__(self):
        return f"<AssessmentItem {self.item_code}>"


class AssessmentRisk(Base, TimestampMixin):
    """评估风险记录

    在技术评估过程中识别的风险，支持风险跟踪和缓解。
    """

    __tablename__ = "assessment_risks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联评估
    assessment_id = Column(
        Integer,
        ForeignKey("technical_assessments.id"),
        nullable=False,
        comment="技术评估ID"
    )

    # 风险信息
    risk_code = Column(String(50), unique=True, nullable=False, comment="风险编码")
    risk_title = Column(String(200), nullable=False, comment="风险标题")
    risk_category = Column(String(50), comment="风险类别")
    risk_description = Column(Text, nullable=False, comment="风险描述")

    # 风险评级
    probability = Column(
        String(10),
        comment="发生概率: LOW/MEDIUM/HIGH"
    )
    impact = Column(
        String(10),
        comment="影响程度: LOW/MEDIUM/HIGH"
    )
    risk_level = Column(
        String(20),
        default=RiskLevelEnum.MEDIUM,
        comment="风险等级"
    )
    risk_score = Column(Integer, comment="风险分值(概率*影响)")

    # 应对措施
    mitigation_plan = Column(Text, comment="缓解计划")
    contingency_plan = Column(Text, comment="应急预案")

    # 责任人
    owner_id = Column(Integer, ForeignKey("users.id"), comment="风险负责人ID")

    # 状态追踪
    status = Column(
        String(20),
        default=RiskStatusEnum.OPEN,
        comment="风险状态"
    )
    due_date = Column(DateTime, comment="预期解决日期")
    resolved_at = Column(DateTime, comment="实际解决时间")
    resolution_notes = Column(Text, comment="解决说明")

    # 关系
    assessment = relationship("TechnicalAssessment", foreign_keys=[assessment_id])
    owner = relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_assessment_risk_assessment", "assessment_id"),
        Index("idx_assessment_risk_level", "risk_level"),
        Index("idx_assessment_risk_status", "status"),
        Index("idx_assessment_risk_owner", "owner_id"),
        {"comment": "评估风险记录表"},
    )

    def __repr__(self):
        return f"<AssessmentRisk {self.risk_code}>"

    def calculate_risk_score(self) -> int:
        """计算风险分值"""
        prob_scores = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        impact_scores = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

        prob_score = prob_scores.get(self.probability, 2)
        impact_score = impact_scores.get(self.impact, 2)

        return prob_score * impact_score


class AssessmentVersion(Base, TimestampMixin):
    """评估版本

    支持评估的版本历史追溯，每次重新评估生成新版本。
    """

    __tablename__ = "assessment_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联原始评估
    assessment_id = Column(
        Integer,
        ForeignKey("technical_assessments.id"),
        nullable=False,
        comment="技术评估ID"
    )

    # 版本信息
    version_no = Column(String(20), nullable=False, comment="版本号")
    version_note = Column(Text, comment="版本说明")

    # 评估快照
    snapshot_data = Column(JSON, comment="评估数据快照(JSON)")
    dimension_scores = Column(JSON, comment="五维分数快照(JSON)")
    total_score = Column(Integer, comment="总分快照")
    decision = Column(String(30), comment="决策建议快照")

    # 评估人
    evaluator_id = Column(Integer, ForeignKey("users.id"), comment="评估人ID")
    evaluated_at = Column(DateTime, default=datetime.now, comment="评估时间")

    # 关系
    assessment = relationship("TechnicalAssessment", foreign_keys=[assessment_id])
    evaluator = relationship("User", foreign_keys=[evaluator_id])

    __table_args__ = (
        Index("idx_assessment_version_assessment", "assessment_id"),
        UniqueConstraint(
            "assessment_id", "version_no",
            name="uq_assessment_version"
        ),
        {"comment": "评估版本表"},
    )

    def __repr__(self):
        return f"<AssessmentVersion {self.assessment_id}-{self.version_no}>"
