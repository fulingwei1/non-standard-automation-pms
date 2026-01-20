# -*- coding: utf-8 -*-
"""
阶段模板模型 - 定义层

包含：
- StageTemplate: 阶段模板表
- StageDefinition: 大阶段定义表
- NodeDefinition: 小节点定义表
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    CompletionMethodEnum,
    NodeTypeEnum,
    TemplateProjectTypeEnum,
)
from app.models.scheduler_config import JSONType


class StageTemplate(Base, TimestampMixin):
    """阶段模板表"""

    __tablename__ = "stage_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    project_type = Column(
        String(20),
        default=TemplateProjectTypeEnum.CUSTOM.value,
        comment="适用项目类型: NEW/REPEAT/SIMPLE/CUSTOM",
    )
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    stages = relationship(
        "StageDefinition",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="StageDefinition.sequence",
    )
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = {"comment": "阶段模板表"}


class StageDefinition(Base, TimestampMixin):
    """大阶段定义表"""

    __tablename__ = "stage_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        Integer,
        ForeignKey("stage_templates.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属模板ID",
    )
    stage_code = Column(String(20), nullable=False, comment="阶段编码")
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    sequence = Column(Integer, nullable=False, default=0, comment="排序序号")
    estimated_days = Column(Integer, comment="预计工期(天)")
    description = Column(Text, comment="阶段描述")
    is_required = Column(Boolean, default=True, comment="是否必需阶段")

    # 关系
    template = relationship("StageTemplate", back_populates="stages")
    nodes = relationship(
        "NodeDefinition",
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by="NodeDefinition.sequence",
    )

    __table_args__ = {"comment": "大阶段定义表"}


class NodeDefinition(Base, TimestampMixin):
    """小节点定义表"""

    __tablename__ = "node_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_definition_id = Column(
        Integer,
        ForeignKey("stage_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属阶段ID",
    )
    node_code = Column(String(20), nullable=False, comment="节点编码")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    node_type = Column(
        String(20),
        default=NodeTypeEnum.TASK.value,
        nullable=False,
        comment="节点类型: TASK/APPROVAL/DELIVERABLE",
    )
    sequence = Column(Integer, nullable=False, default=0, comment="排序序号")
    estimated_days = Column(Integer, comment="预计工期(天)")
    completion_method = Column(
        String(20),
        default=CompletionMethodEnum.MANUAL.value,
        nullable=False,
        comment="完成方式: MANUAL/APPROVAL/UPLOAD/AUTO",
    )
    dependency_node_ids = Column(JSONType, comment="前置依赖节点ID列表(JSON数组)")
    is_required = Column(Boolean, default=True, comment="是否必需节点")
    required_attachments = Column(Boolean, default=False, comment="是否需上传附件")
    approval_role_ids = Column(JSONType, comment="审批角色ID列表(JSON数组)")
    auto_condition = Column(JSONType, comment="自动完成条件配置(JSON)")
    description = Column(Text, comment="节点描述")

    # 关系
    stage = relationship("StageDefinition", back_populates="nodes")

    __table_args__ = {"comment": "小节点定义表"}
