# -*- coding: utf-8 -*-
"""
阶段实例模型 - 项目运行时

包含：
- ProjectStageInstance: 项目阶段实例表
- ProjectNodeInstance: 项目节点实例表
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
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
    StageStatusEnum,
)
from app.models.scheduler_config import JSONType


class ProjectStageInstance(Base, TimestampMixin):
    """项目阶段实例表"""

    __tablename__ = "project_stage_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属项目ID",
    )
    stage_definition_id = Column(
        Integer,
        ForeignKey("stage_definitions.id", ondelete="SET NULL"),
        comment="来源阶段定义ID",
    )
    stage_code = Column(String(20), nullable=False, comment="阶段编码")
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    sequence = Column(Integer, nullable=False, default=0, comment="排序序号")
    status = Column(
        String(20),
        default=StageStatusEnum.PENDING.value,
        nullable=False,
        comment="状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED",
    )
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")
    is_modified = Column(Boolean, default=False, comment="是否被调整过")
    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="stage_instances")
    stage_definition = relationship("StageDefinition")
    nodes = relationship(
        "ProjectNodeInstance",
        back_populates="stage_instance",
        cascade="all, delete-orphan",
        order_by="ProjectNodeInstance.sequence",
    )

    __table_args__ = {"comment": "项目阶段实例表"}


class ProjectNodeInstance(Base, TimestampMixin):
    """项目节点实例表"""

    __tablename__ = "project_node_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属项目ID",
    )
    stage_instance_id = Column(
        Integer,
        ForeignKey("project_stage_instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属阶段实例ID",
    )
    node_definition_id = Column(
        Integer,
        ForeignKey("node_definitions.id", ondelete="SET NULL"),
        comment="来源节点定义ID",
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
    status = Column(
        String(20),
        default=StageStatusEnum.PENDING.value,
        nullable=False,
        comment="状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED",
    )
    completion_method = Column(
        String(20),
        default=CompletionMethodEnum.MANUAL.value,
        nullable=False,
        comment="完成方式",
    )
    dependency_node_instance_ids = Column(JSONType, comment="前置依赖节点实例ID列表")
    is_required = Column(Boolean, default=True, comment="是否必需节点")
    planned_date = Column(Date, comment="计划完成日期")
    actual_date = Column(Date, comment="实际完成日期")
    completed_by = Column(Integer, ForeignKey("users.id"), comment="完成人ID")
    completed_at = Column(DateTime, comment="完成时间")
    attachments = Column(JSONType, comment="上传的附件列表(JSON)")
    approval_record_id = Column(Integer, comment="关联审批记录ID")
    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="node_instances")
    stage_instance = relationship("ProjectStageInstance", back_populates="nodes")
    node_definition = relationship("NodeDefinition")
    completer = relationship("User", foreign_keys=[completed_by])

    __table_args__ = {"comment": "项目节点实例表"}
