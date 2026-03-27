# -*- coding: utf-8 -*-
"""
阶段模板模型 - 定义层

包含：
- StageTemplate: 阶段模板表
- StageDefinition: 大阶段定义表
- NodeDefinition: 小节点定义表
- StageTemplateChangeLog: 模板变更历史表
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
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
    updated_by = Column(Integer, ForeignKey("users.id"), comment="最近更新人ID")
    change_description = Column(Text, comment="最近修改说明")

    # 关系
    stages = relationship(
        "StageDefinition",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="StageDefinition.sequence",
    )
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    change_logs = relationship(
        "StageTemplateChangeLog",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="StageTemplateChangeLog.id.desc()",
    )

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
    category = Column(
        String(20),
        default="execution",
        comment="阶段分类: sales/presales/execution/closure",
    )
    estimated_days = Column(Integer, comment="预计工期(天)")
    description = Column(Text, comment="阶段描述")
    is_required = Column(Boolean, default=True, comment="是否必需阶段")
    is_milestone = Column(Boolean, default=False, comment="是否关键里程碑")
    is_parallel = Column(Boolean, default=False, comment="是否支持并行执行")

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

    # 责任分配与交付物
    owner_role_code = Column(String(50), comment="负责角色编码")
    participant_role_codes = Column(JSONType, comment="参与角色编码列表(JSON数组)")
    deliverables = Column(JSONType, comment="交付物清单(JSON数组)")

    # 关系
    stage = relationship("StageDefinition", back_populates="nodes")

    __table_args__ = {"comment": "小节点定义表"}


class StageTemplateChangeLog(Base, TimestampMixin):
    """模板变更历史表"""

    __tablename__ = "stage_template_change_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        Integer,
        ForeignKey("stage_templates.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属模板ID",
    )
    action = Column(
        String(30),
        nullable=False,
        comment="操作类型: CREATE/UPDATE_TEMPLATE/ADD_STAGE/UPDATE_STAGE/DELETE_STAGE/"
        "ADD_NODE/UPDATE_NODE/DELETE_NODE/REORDER_STAGES/REORDER_NODES/"
        "COPY/IMPORT/SET_DEFAULT",
    )
    target_type = Column(String(20), comment="目标类型: TEMPLATE/STAGE/NODE")
    target_id = Column(Integer, comment="目标ID")
    target_name = Column(String(100), comment="目标名称(快照)")
    change_description = Column(Text, comment="修改说明")
    change_detail = Column(JSONType, comment="变更详情(JSON: {field: {old, new}})")
    changed_by = Column(Integer, ForeignKey("users.id"), comment="操作人ID")

    # 关系
    template = relationship("StageTemplate", back_populates="change_logs")
    operator = relationship("User", foreign_keys=[changed_by])

    __table_args__ = (
        Index("idx_changelog_template", "template_id"),
        Index("idx_changelog_action", "action"),
        {"comment": "模板变更历史表"},
    )
